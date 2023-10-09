import os
import json
from transformers import AutoTokenizer
import numpy as np
from tqdm import tqdm

tokenizer = AutoTokenizer.from_pretrained("model/chatglm2-6b", trust_remote_code=True)

def convert_file(filename, train_sample_ratio):
    with open(filename, 'r') as fp:
        lines = fp.readlines()
        num_train_samples = int(train_sample_ratio * len(lines))
        lengths = []
        with open(filename.replace(".json", "") + "_train.json", 'w') as fp:
            for line in lines[:num_train_samples]:
                data_json = json.loads(line)
                length = len(tokenizer(data_json['prompt'])['input_ids'])
                lengths.append(length)
                if length > 512:
                    continue
                data_json['hsitory'] = []
                fp.write(json.dumps(data_json, ensure_ascii=False) + "\n")
        with open(filename.replace(".json", "") + "_dev.json", 'w') as fp:
            for line in lines[num_train_samples:]:
                data_json = json.loads(line)
                data_json['hsitory'] = []
                length = len(tokenizer(data_json['prompt'])['input_ids'])
                lengths.append(length)
                if length > 512:
                    continue
                fp.write(json.dumps(data_json, ensure_ascii=False) + "\n")
        print(np.quantile(lengths, 0.995))

prompt = "提取以下句子的问题类型年份、公司名称、如果是财务类问题，提取出对应的财务指标，对非复杂计算的指标，请给出回答模板，如果是开放问题，提取出对应的财报章节，如果是查询问题，请提供SQL查询和回答模板，以json形式回答:"

def convert_classify_file():
    result = []
    lengths = []
    src_len = []
    with open('finetune/table_qa/data/auto_annotated.json', 'r') as fp:
        lines = fp.readlines()
        for line in tqdm(lines):
            data_json = json.loads(line)
            data_point = {
                "prompt": prompt + data_json['question'],
                "response": json.dumps(data_json['info_dict'], ensure_ascii=False)
            }
            length = len(tokenizer(data_point['response'])['input_ids'])
            src_length = len(tokenizer(data_point['prompt'])['input_ids'])
            lengths.append(length)
            src_len.append(src_length)
            if length < 512:
                result.append(data_point)
    cut_point = int(len(result) * .95)
    print(max(src_len))
    with open('finetune/table_qa/data/auto_annotated_train.json', 'w') as fp:
        for data_point in result[:cut_point]:
            fp.write(json.dumps(data_point, ensure_ascii=False) + "\n")
    with open('finetune/table_qa/data/auto_annotated_dev.json', 'w') as fp:
        for data_point in result[cut_point:]:
            fp.write(json.dumps(data_point, ensure_ascii=False) + "\n")    

if __name__ == '__main__':
    # convert_file('finetune/table_qa/data/company_info.json', train_sample_ratio=0.9)
    convert_classify_file()