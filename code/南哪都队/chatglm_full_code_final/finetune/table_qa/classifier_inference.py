from peft import PeftModel
import torch
from transformers import AutoModel, AutoTokenizer, AutoConfig
import os
import sys
sys.path.append("chain")
from data_utils import load_questions
import json


def load_model():
    model_path = "model/chatglm2-6b"
    checkpoint_path = "model/classifier/checkpoint-400"
    config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
    config.prefix_projection = False
    config.pre_seq_len = 128
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_path, config=config, trust_remote_code=True)
    prefix_state_dict = torch.load(os.path.join(checkpoint_path, "pytorch_model.bin"))
    new_prefix_state_dict = {}
    for k, v in prefix_state_dict.items():
        if k.startswith("transformer.prefix_encoder."):
            new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
    model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
    model = model.to("cuda")
    return model, tokenizer

model, tokenizer = load_model()
tokenizer.padding_side = 'left'


def get_response(questions):
    inputs = tokenizer(questions, return_tensors="pt", max_length=2048, truncation=True, padding=True)
    inputs = inputs.to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=256, do_sample=True, top_p=0.7, temperature=0.95)
    response = tokenizer.batch_decode(outputs)
    response = [res[res.index("答：")+2:].strip() for res in response]
    final_response = []
    for res in response:
        try:
            data_json = json.loads(res)
            final_response.append(data_json)
        except json.JSONDecodeError:
            final_response.append(None)
    return final_response

def format_conversation(question):
    return f"[Round 1]\n\n问:提取以下句子的问题类型年份、公司名称、如果是财务类问题，提取出对应的财务指标，以json形式回复：{question}\n\n答："



if __name__ == '__main__':
    from tqdm import tqdm
    model.eval()
    answers = []
    with torch.no_grad():
        question_list = load_questions()
        pbar = enumerate(tqdm(question_list))
        batch_data = []
        for idx, question in pbar:
            batch_data.append(format_conversation(question))
            success = False
            if len(batch_data) == 256 or idx == len(question_list) - 1:
                responses = get_response(batch_data)
                answers.extend(responses)
                batch_data = []
    while len([ans for ans in answers if ans is None]) != 0:
        failed_index = answers.index(None)
        print(f"failed:{failed_index}")
        new_response = get_response([format_conversation(question_list[failed_index])])
        while new_response is None:
            new_response = get_response([format_conversation(question_list[failed_index])])
        answers[failed_index] = new_response
    with open("finetune/table_qa/data/classification.jsonl", 'w', encoding="utf8") as fp:
        for ans in answers:
            fp.write(json.dumps(ans, ensure_ascii=False) + "\n")