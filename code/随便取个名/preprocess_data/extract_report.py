import os
import re
import sys
import json
import ast
import shutil
import numpy as np
import pandas as pd
import multiprocessing
from data_utils import extract_basic_info

def get_title(path):
    hash = {}
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = re.sub(r'<Page:(\d+)>', r'\1', line)
            line = ast.literal_eval(line)
            if '年度报告' in line['inside'] and len(line['inside']) < 30:
                if line['inside'] not in hash:
                    hash[line['inside']] = 1
                else:
                    hash[line['inside']] += 1
    if len(hash) == 0: return 'No title found'
    return max(hash, key=hash.get)

def clean_line(str, title):
    if len(str) == 0 or str == title or str.replace('/', '').isdigit():
        return True
    if str in ['2021年年度报告', '2020年年度报告', '2019年年度报告']:
        return True
    return False  

# pd.set_option('display.max_rows', None)
def table2DF(table):
    data = []
    for line in table:
        if all(val == '' for val in eval(line['inside'])): continue
        data.append(eval(line['inside']))
    df = pd.DataFrame(data)
    if len(df.index) == 0: return None
    df.columns = df.iloc[0]
    df = df[1:]
    df[df==''] = np.nan
    
    # drop some columns
    if '' in df.columns:
        df = df.drop(columns=[''])
    if '附注' in df.columns:
        df = df.drop(columns=['附注'])
    if None in df.columns:
        df = df.drop(columns=[None])
    df = df.dropna(axis=0,subset=df.columns[1:-1])
    return df

def extract_report(path, output_dir):
    # output to a directory
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    files = os.listdir(output_dir)
    # 避免重复提取
    if any(file.endswith('.csv') for file in files):
        return
    
    title = get_title(path)
    new_lines = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = re.sub(r'<Page:(\d+)>', r'\1', line)
            line = ast.literal_eval(line)
            if line['type'] == "页脚" or line['type'] == "页眉" or (line['type'] == 'text' and clean_line(line['inside'], title)): continue
            new_lines.append(line)

    tables = []
    flag = False
    table_title = ['合并资产负债表', '合并利润表', '合并现金流量表', '资产及负债状况分析']

    def has_title(str):
        for title in table_title:
            if title in str:
                return True
        if title.endswith('、利润表') or  title.endswith('、资产负债表'):
            return True
        return False
    
    # extract different table
    tolerance = 0
    for line in new_lines:
        if line['type'] == 'excel':
            if flag == False: continue
            tolerance = 0
            table.append(line)
        elif line['type'] == 'text':
            if flag == True:
                # 刚开始的时候去除表头
                if tolerance != -1:
                    tolerance += 1
                if tolerance >= 2:
                    tables.append(table2DF(table))
                    flag = False
                    tolerance = 0
            else:
                # 添加表名
                line['inside'] = line['inside'].replace(title, '')
                if has_title(line['inside']):
                    if line['inside'].endswith('合并利润表') or line['inside'].endswith('、利润表') :
                        line['inside'] = '合并利润表'
                    elif line['inside'].endswith('合并资产负债表') or line['inside'].endswith('、资产负债表'):
                        line['inside'] = '合并资产负债表'
                        
                    if len(line['inside']) < 15:
                        tables.append(line)
                        table = []
                        flag = True
                        tolerance = -1
                    

    name = ''
    table_num = 0
    for item in tables:
        if isinstance(item, dict):
            name = item['inside']
            
        elif isinstance(item, pd.DataFrame) and '调整数' not in item.columns and item.shape[1] <= 4:
            item.to_csv(os.path.join(output_dir,f'{name}_{table_num}.csv'))
            table_num += 1
            name = ''

def process_file(file_path):
    company_name = file_path.split('/')[-1].split('__')[3]
    year = file_path.split('/')[-1].split('__')[4]
    output_dir = f'data/tables/{company_name}__{year}'
    try:
        extract_report(file_path, output_dir)
    except Exception as e:
            print(f"Exception occurred: {e}")

def main():
    dir_path = 'data/alltxt'
    table_path = 'data/tables'
    if not os.path.exists(table_path):
        os.mkdir(table_path)
    
    file_paths = []
    test_name = []
    with open('data/list-pdf-name.txt', 'r', encoding='utf-8') as f:
        for line in f.readlines():
            test_name.append(line.replace("\n", "").replace(".pdf", ".txt"))
    for path in os.listdir(dir_path):
        if path in test_name:
            file_paths.append(os.path.join(dir_path, path))
    num_processes = 64

    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(process_file, file_paths)
    # 拆解基本信息
    extract_basic_info()

if __name__ == '__main__':
    main()