import os
import re
import sys
import json
from collections import defaultdict
from question_categorize import classify_questions
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline

def has_digit(input_str):
    pattern = r'\d'  # 正则表达式匹配数字的模式
    return bool(re.search(pattern, input_str))

def has_keys(str, keys):
    for key in keys:
        if ',' in key:
            key_list = [k in str for k in key.split(',')]
            if sum(key_list) > 0:
                return True
        elif key in str:
            return True
    return False

def extract_numbers(question):
    # Define a regex pattern for the numbers
    pattern = r'\d{4}'
    # Use the regex pattern to search in the question
    matches = re.findall(pattern, question)
    # Return the list of matches
    return matches

def get_entities(data):
    entities = []
    entity = []
    last_tag = ""
    for item in data:
        tag = item['entity']
        word = item['word']
        if tag.startswith("B-"):
            entity = [word]
            last_tag = tag
        elif tag.startswith("I-") and tag[2:] == last_tag[2:]:
            entity.append(word)
        elif tag.startswith("E-"):
            entity.append(word)
            entities.append((last_tag[2:], "".join(entity)))
            entity = []
        else:
            if entity:
                entities.append((last_tag[2:], "".join(entity)))
            entity = []
    if entity:
        entities.append((last_tag[2:], "".join(entity)))
        
    # parse entity
    ret = {'DATE':[], 'ORG': []}
    for ent in entities:
        if ent[0] not in ['DATE', 'ORG']: continue
        if ent[0] == 'DATE': ret['DATE'].append(ent[1].replace('年', ''))
        elif ent[0] == 'ORG': 
            ret['ORG'] = ent[1].replace('股份有限公司', '')
            
    return ret

def main():
    path = 'data/list-question.json'
    samples = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = json.loads(line)
            samples.append(line)

    company_names_dict = {}
    with open('data/company_names.txt', 'r', encoding='utf-8') as f:
        for line in f.readlines():
            name, short_name = line.strip().split(":")
            company_names_dict[name] = short_name

    # Load pre-trained model and tokenizer
    model_path = "ckiplab/bert-base-chinese-ner"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForTokenClassification.from_pretrained(model_path)

    # NER pipeline
    ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer)

    # 提取出年份和公司名
    special_case = {
        "上海浦东发展银行" : "浦发银行",
        "山东瑞丰高分子" : "瑞丰高材",
    }
    
    for i in range(len(samples)):
        samples[i]['DATE'] = []
        samples[i]['Company_name'] = ''
        if not has_digit(samples[i]['question']): continue
        samples[i]['DATE'] = extract_numbers(samples[i]['question'])
        samples[i]['question'] = samples[i]['question'].replace("(", "").replace(")", "")
        
        for company_name in list(company_names_dict.keys()):
            if company_name in samples[i]['question'] and len(company_names_dict[company_name].replace('股份', '')) > len(samples[i]['Company_name']):
                samples[i]['Company_name'] = company_names_dict[company_name]
                break
                
        if samples[i]['Company_name'] == '':
            for company_name in list(company_names_dict.values()):
                if company_name in samples[i]['question'] and len(company_name.replace('股份', '')) > len(samples[i]['Company_name']):
                    samples[i]['Company_name'] = company_name
                
        # special case:
        if samples[i]['Company_name'] == '':
            for company_name in list(company_names_dict.values()):
                if any(key in samples[i]['question'] for key in special_case):
                    for key in special_case:
                        if key in samples[i]['question']:
                            samples[i]['Company_name'] = special_case[key]
                            break
                
                elif company_name[:-2] in samples[i]['question'] and company_name[-2:] in samples[i]['question']:
                    samples[i]['Company_name'] = company_name
                    break
                    
        # if not in the company dict, using NER MODEL
        if samples[i]['Company_name'] == '':
            results = ner_pipeline(samples[i]['question'])
            entities = get_entities(results)
            # print(samples[i]['question'], samples[i]['id'])
            # print(entities['ORG'])
            samples[i]['Company_name'] = entities['ORG']

            
        if isinstance(samples[i]['Company_name'], list):
            samples[i]['Company_name'] = ''
      
    classify_questions(samples)
         
    with open('./data/parse_question.json', 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        

if __name__ == '__main__':
    main()