from peft import PeftModel
import torch
from transformers import AutoModel, AutoTokenizer, AutoConfig
import os
import sys
from .data_utils import load_questions
import json
from tqdm import tqdm


def load_model():
    model_path = "model/chatglm2-6b"
    checkpoint_path = "model/classifier/sql_enhance_checkpoint"
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
    model = model.half()
    model = model.cuda()
    return model, tokenizer

model, tokenizer = None, None
# tokenizer.padding_side = 'left'


def get_response(questions):
    global model, tokenizer
    if model is None:
        model, tokenizer = load_model()
    inputs = tokenizer(questions, return_tensors="pt", max_length=512, truncation=True, padding=True)
    inputs = inputs.to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=256, do_sample=True, top_p=0.7, temperature=0.95, num_beams=4)
    response = tokenizer.batch_decode(outputs)
    response = [res[res.index("答：")+2:].strip() for res in response]
    final_response = []
    for res in response:
        try:
            data_json = json.loads(res)
            final_response.append(data_json)
        except json.JSONDecodeError:
            print(res)
            final_response.append(None)
    return final_response

def format_conversation(question):
    return f"[Round 1]\n\n问：提取以下句子的问题类型年份、公司名称，如果是开放问题，提取出对应的财报章节，如果是查询问题，请提供SQL查询和回答模板，如果是财务类问题，提取出对应的财务指标，对非复杂计算的指标，请给出回答模板，以json形式回答:{question}\n\n答："


def dump_classification_results(file_path=None, refresh=True):
    if file_path is None:
        file_path = "finetune/table_qa/data/classification.jsonl"
    if os.path.exists(file_path) and not refresh:
        return
    global model, tokenizer
    if model is None:
        model, tokenizer = load_model()
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
            if len(batch_data) == 16 or idx == len(question_list) - 1:
                responses = get_response(batch_data)
                answers.extend(responses)
                batch_data = []
    max_try = 0
    failed_cnt = 0
    while len([ans for ans in answers if ans is None]) != 0:
        failed_index = answers.index(None)
        print(f"failed:{failed_index}")
        new_response = get_response([format_conversation(question_list[failed_index])])[0]
        tries = 0
        while new_response is None and tries < max_try:
            new_response = get_response([format_conversation(question_list[failed_index])])[0]
            tries += 1
        answers[failed_index] = new_response
        if tries == max_try:
            answers[failed_index] = {"类型": "失败"}
            failed_cnt += 1
            print(question_list[failed_index])
    with open(file_path, 'w', encoding="utf8") as fp:
        for ans in answers:
            if ans is not None and isinstance(ans, dict) and '关键词' in ans and len(ans['关键词']) == 1 and '类型' in ans:
                if "外文名称" in ans["关键词"][0] and ans['类型'] != '公司问题':
                    ans['类型'] = '公司问题'
                if isinstance(ans["关键词"][0], str) and ans["关键词"][0] in ['现金流', '现金流量'] and ans['类型'] != '开放问题':
                    ans['类型'] = '开放问题'
                    ans['关键词'][0] = "现金流"
            fp.write(json.dumps(ans, ensure_ascii=False) + "\n")
    model.cpu()
    del model
    return answers

if __name__ == '__main__':
    pass