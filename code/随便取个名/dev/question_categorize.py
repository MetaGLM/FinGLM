import os
import re
import sys
import json
from collections import defaultdict

import torch
from torch.utils.data import DataLoader, Dataset
import jieba
from fuzzywuzzy import process
from transformers import T5Config, T5Tokenizer, T5ForConditionalGeneration

from constant import RATIO_KEY, BASIC_KEY, FINANCIAL_KEY, ANALYSIS_KEY, VAGUE_MAPPING, KEY_REMAPPING

from sql_util import parse_sql_task

def has_digit(input_str):
    pattern = r'\d'  # 正则表达式匹配数字的模式
    return bool(re.search(pattern, input_str))

def has_keys(str, keys):
    for key in keys:
        if key in str:
            return True
    return False


def verbaliser(_str):
    _str = _str.replace('的', '').replace(' ', '').replace('所占', '占').replace('上费用', '费用').replace('总费用', '费用').replace('学历', '').replace('以及', '和').replace('控股股东、实际控制人', '控股股东、实控人')
    _str = re.sub(r'(\d+年)(法定代表人)(对比|与)(\d+年)', r'\1与\4\2', _str)
    
    for k, v in VAGUE_MAPPING.items():
        for x in v:
            _str = _str.replace(x, k)
    return _str
        
def classify_questions(samples):
    ## 使用正则分类
    sql_task_samples = []
    for i in range(len(samples)):
        if len(samples[i]['DATE']) == 0:
            samples[i]['task_key'] = ['特殊问题']

        re_classify_question(samples[i])

        task_key_set = set()
        for key in samples[i]['task_key']:
            if key in ["负债和所有者权益总计", "联营企业和合营企业投资收益"]:
                task_key_set.add(key)
            else:
                for item in key.split("和"):
                    task_key_set.add(item)
        samples[i]['task_key'] = list(task_key_set)
        
        if len(samples[i]['task_key']) == 0:
            print(samples[i])
            continue

        if samples[i]['task_key'][0] in BASIC_KEY:
            samples[i]['category'] = 1
        elif samples[i]['task_key'][0] in RATIO_KEY:
            samples[i]['category'] = 2
        elif samples[i]['task_key'][0] in FINANCIAL_KEY:
            samples[i]['category'] = 3
        elif samples[i]['task_key'][0] in ANALYSIS_KEY:
            samples[i]['category'] = 4
        elif samples[i]['task_key'][0] == 'sql task':
            samples[i]['category'] = 5
            sql_task_samples.append(samples[i])

        else:
            samples[i]['category'] = 0
    
        # key_remapping 
        for j, key in enumerate(samples[i]['task_key']):
            if key in KEY_REMAPPING:
                samples[i]['task_key'][j] = KEY_REMAPPING[key]

    ### special case for : sql tasks
    parse_sql_task(sql_task_samples)

def re_classify_question(sample):
    question = verbaliser(sample['question'])
    if '法定代表人' in question and '相同' in question:
        question = question + '|法定代表人是否相同'
    
    sample['prompt'] = ''
    if not has_digit(question):
        sample['category'] = 0
        sample['task_key'] = '特殊问题'
                
     # sql key
    elif sample['Company_name'] == "":
        sample['category'] = 5
        sample['task_key'] = "sql task"
        
    elif has_keys(question, BASIC_KEY):
        sample['category'] = 1
        for key in BASIC_KEY:
            if key in question:
                break
        sample['task_key'] = key
    
    elif has_keys(question, RATIO_KEY):
        sample['category'] = 2
        for key in RATIO_KEY:
            if key in question:
                break
        sample['task_key'] = key
    
    # 多个financial key
    elif has_keys(question, FINANCIAL_KEY):
        sample['task_key'] = []
        sample['category'] = 3
        for key in FINANCIAL_KEY:
            if key in question:
                if len(sample['task_key']) == 0:
                    sample['task_key'].append(key)
                else:
                    for item in sample['task_key']:
                        if key not in item:
                            sample['task_key'].append(key)

    elif has_keys(question, ANALYSIS_KEY):
        sample['category'] = 4
        for key in ANALYSIS_KEY:
            if key in question:
                break
        sample['task_key'] = key

    else:
        # 使用fuzzywuzzy提取关键词
        sample['category'] = 0
        sample['task_key'] = '特殊问题'

    if not isinstance(sample['task_key'], list):
        sample['task_key'] = [sample['task_key']]

def main():
    samples = []
    path = 'data/parse_question.json'
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = json.loads(line)
            samples.append(line)

    classify_questions(samples)
    with open('data/parse_question.json', 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')

if __name__ == "__main__":
    main()