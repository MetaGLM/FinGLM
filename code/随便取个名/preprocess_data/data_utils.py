import os
import sys
import json
import glob
import shutil
import pandas as pd

def extract_basic_info():
    # readin the basic information json 
    with open('data/basic_information.json', 'r', encoding='utf-8') as f:
        for line in f.readlines():
            record = json.loads(line)
            name = record['文档公司名']
            if name == None:
                print(record['文档公司名'], name)
                continue
            
            if not os.path.exists(f'data/tables/{name}__{record["年份"]}'):
                os.mkdir(f'data/tables/{name}__{record["年份"]}')
            file_path = f'data/tables/{name}__{record["年份"]}/基本信息表.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False))
                
def extract_special_question():
    results = []
    with open('data/result.json', 'r', encoding='utf-8') as f1, open('data/dataset.json', 'r', encoding='utf-8') as f2:
        for line, answer in zip(f1.readlines(),f2.readlines()):
            result = json.loads(line)
            dataset = json.loads(answer)
            if dataset['prompt'] != '':
                result['answer'] = dataset['prompt']
            results.append(result)
    
    with open('data/result1.json', 'w', encoding='utf-8') as f:
        for question in results:
            f.write(json.dumps(question, ensure_ascii=False)+'\n')
    

def get_dataset():
    results = []
    with open('data/result1.json', 'r', encoding='utf-8') as f1, open('data/dataset.json', 'r', encoding='utf-8') as f2:
        for line, answer in zip(f1.readlines(),f2.readlines()):
            result = json.loads(line)
            dataset = json.loads(answer)
            result['prompt'] = dataset['prompt']
            result['target'] = result['prompt']
            result['category'] = dataset['category']
            if result['prompt'] == '':
                result['target'] = result['answer']
                result['prompt'] = '没有查询到对应的信息'
            
            if result['target'] == "":
                result['target'] = "没有查询到对应的信息，根据以上信息无法回答"
            
            result.pop('id')
            result.pop('answer')
            results.append(result)
    
    with open('data/smp2023/dataset.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False)
        # for result in results:
            # f.write(json.dumps(result, ensure_ascii=False)+'\n')

def get_company_name():
    folder_path = 'data/allpdf'
    # 获取文件夹内所有文件名称
    file_names = glob.glob(folder_path + '/*')
    file_names = sorted(file_names, reverse=True)
    
    name_lists = []
    for file_name in file_names:
        if os.path.isdir(file_name): continue
        allname = file_name.split('\\')[-1]
        date = allname.split('__')[0]
        name = allname.split('__')[1]
        short_name = allname.split('__')[3]

        name_lists.append(f"{name}:{short_name}")
        name_lists = list(set(name_lists))
    with open('data/company_names.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(name_lists))


if __name__ == "__main__":
    extract_basic_info()