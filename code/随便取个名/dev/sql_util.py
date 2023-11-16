import re
import os
import sys
import json
import torch
from torch.utils.data import DataLoader, Dataset
import jieba
from fuzzywuzzy import process, fuzz

from transformers import AutoModel, AutoTokenizer

from constant import FINANCIAL_KEY, CITIES

def zh2num(num: str):
    mapping = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, \
               '十': 10, '百': 100, '千': 1000}
    result = 0
    curValue = 0
    lastValue = 0

    for i in range(len(num)):
        ch = num[i]
        if ch in mapping:
            curValue = mapping[ch]
        else:
            return -1

        if curValue == 10:
            if lastValue == 0:
                result += curValue
            else:
                result += lastValue * curValue
                lastValue = 0
        elif curValue < 10:
            if lastValue == 0:
                lastValue = curValue
            else:
                lastValue *= curValue
                result += lastValue
                lastValue = 0
        else:
            if lastValue == 0:
                lastValue = curValue
            else:
                lastValue *= curValue

    result += lastValue
    return result

def adjusted_ratio_fn(str1, str2):
    # 根据字符串长度计算一个权重，用于调整相似度得分
    len_weight = min(len(str1), len(str2)) / max(len(str1), len(str2))
    
    # 计算标准的相似度得分
    similarity_score = fuzz.WRatio(str1, str2)
    
    # 根据长度权重调整得分
    score = similarity_score * len_weight
    return score

def output_parser(output):
    output = output.replace("关键词:", "")
    word_set = output.split('、')
    return word_set

def similarity_match(set, candidate_key):
    similar_word = []
    for word in set:
        best_match = process.extractOne(word, candidate_key, scorer=adjusted_ratio_fn)
        similar_word.append(best_match)
    if len(similar_word) > 0:
        similar_word = sorted(similar_word, key=lambda x: -x[1])
    return similar_word[0][0]


# 编译地点名正则  
# 创建包含所有城市名称的正则表达式模式
cities = list(set(CITIES))

# 将城市名称列表转换为正则表达式模式，用于匹配
city_pattern = r"|".join(re.escape(city) for city in cities)
location_pattern = re.compile(fr'({city_pattern})')

# 编译关键词正则
financial_keys = list(set(FINANCIAL_KEY))
financial_key_pattern = r"|".join(re.escape(key) for key in financial_keys)
keyword_pattern = re.compile(fr'(负债总金额|负债总额|资产总金额|资产总额|货币总额|总负债|总资产|营业成本|货币资金|营业收入|利润总额|净利润|营业外收入|流动资产|其他流动资产|其他非流动资产|其他非流动金融资产|营业利润|{financial_key_pattern})')

def parse_sql_task(samples):
    model_path = "THUDM/chatglm2-6b"
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_path, trust_remote_code=True).half().cuda()

    for sample in samples:
        question = sample['question']
        # 先匹配地点 
        location_match = location_pattern.search(question)
        if location_match:
            sample['location'] = location_match.group(1)
        else:
            sample['location'] = "None"
        
        # 匹配rank
        sample["rank"] = 1
        flag = 1 
        if "高" in question:
            flag = 1
        elif "低" in question:
            flag = -1
        numbers = re.findall(r'[一二三四五六七八九十百千万零\d]+', question)
        
        for num in numbers:
            if not num.isdigit():
                num = zh2num(num)
            if num not in ["2019", "2020", "2021"]:
                sample["rank"] = flag * int(num)
        
        if "低" in question and sample['rank'] > 0:
            sample['rank'] = - sample['rank'] 
        # intersect 字段
        sample["intersect"] = False
        if "均位列" in question:
            sample["intersect"] = True

        # range 字段
        sample["range"] = True
        if "第" in question or sample["rank"] in [-1, 1]:
            sample["range"] = False

        # require_money 字段
        sample["require_money"] = False
        if "金额是" in question or "金额为" in question:
            sample["require_money"] = True

        # 再单独匹配关键词
        keyword_match = keyword_pattern.search(question)
        if keyword_match:
            keyword = [keyword_match.group(1)]
        else:
            # 使用chatglm进行匹配
            query = "简洁专业的提取出关键词:" + sample['question']
            ret,_ = model.chat(tokenizer, query, temperature=0.01, history=[])
            keyword = output_parser(ret)
        
        # 加上fuzzywuzzy
        if keyword[0] == "负债总金额":
            keyword[0] = "负债合计"
        if keyword[0] == "流动资产":
            keyword[0] = "流动资产合计"
        if keyword[0] == "非流动资产":
            keyword[0] = "非流动资产合计"

        sample['task_key'] = [similarity_match(keyword, FINANCIAL_KEY)]


def main():
    path = 'data/sql_task.json'
    samples = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = json.loads(line)
            samples.append(line)

    parse_sql_task(samples)        
    with open('data/parse_sql_task.json', 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')


if __name__ == "__main__":
    main()