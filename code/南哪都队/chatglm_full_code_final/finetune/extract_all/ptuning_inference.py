from peft import PeftModel
import torch
from transformers import AutoModel, AutoTokenizer, AutoConfig
import os
import sys
sys.path.append("chain")
from data_utils import load_questions
import json


model_path = "model/chatglm2-6b"
checkpoint_path = "model/table_qa/checkpoint-100"
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


def get_response(text):
    inputs = tokenizer([text], return_tensors="pt", max_length=2048, truncation=True)
    inputs = inputs.to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=256, do_sample=True, top_p=0.7, temperature=0.95)
    outputs = outputs.tolist()[0][len(inputs['input_ids'][0]):]
    response = tokenizer.decode(outputs)
    return response


def common_conversation(question):
    text = f"[Round 1]\n\n问:提取以下句子的问题类型、关键词、年份、公司名称、如果需要计算返回表达式，以json形式回答:{question}\n\n答:"
    response = get_response(text)
    return response



if __name__ == '__main__':
    from tqdm import tqdm
    model.eval()
    if os.path.exists("data/temp/retrieved_info.jsonl"):
        progress = len(open("data/temp/retrieved_info.jsonl", 'r').readlines())
    else:
        progress = 0
    with torch.no_grad():
        with open("data/temp/retrieved_info.jsonl", 'a+') as fp:
            pbar = tqdm(load_questions()[progress:])
            for question in pbar:
                success = False
                while not success:
                    try:
                        info_dict = common_conversation(question)
                        fp.write(json.dumps({
                            "question": question,
                            "info_dict": json.loads(info_dict)
                        }, ensure_ascii=False)+ "\n")
                        success = True
                    except json.decoder.JSONDecodeError:
                        pbar.set_description(info_dict)
                        success = False
                fp.flush()