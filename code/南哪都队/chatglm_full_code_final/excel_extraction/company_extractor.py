from pathlib import Path
import os
import json
from tqdm import tqdm
import regex as re
from itertools import chain
from multiprocessing import Pool


def load_all_txt():
    file_list = list(Path('data/alltxt').rglob('*.txt'))
    for filename in tqdm(file_list, desc="loading data"):
        with open(filename, 'r') as fp:
            lines = fp.readlines()
            basename = os.path.basename(filename)
            yield basename, lines

def process_stock_info(table):
    parsed_result = []
    failed = False
    if ' '.join(eval(table[0])).replace(" ", "") == '公司股票简况':
        table = table[1:]
    if len(table) > 1:
        if len(eval(table[0])) != len(eval(table[1])):
            table_0 = eval(table[0])
            table_1 = eval(table[1])
            for idx in range(min(len(table_0), len(table_1))):
                parsed_result.append([table_0[idx], table_1[idx]])
        else:
            table_0 = eval(table[0])
            table_1 = eval(table[1])
            for idx in range(len(table_0)):
                parsed_result.append([table_0[idx], table_1[idx]])
        return parsed_result    
    if len(table) == 1:
        # 极少数特殊情况处理
        line = table[0]
        if line == "['股票上市交易所上海证券交易所', '股票简称松霖科技', '股票代码603992']":
            return [
                ['股票上市交易所', '上海证券交易所'],
                ['股票简称', '松霖科技'],
                ['股票代码', '603992']
            ]
        elif line == "['股票种类', '股票上市交易所', '股票简称', '股票代码', '变更前股票简称']":
            return []
        elif line == ['A股', '上海证券交易所', '山煤国际', '600546', '中油化建']:
            return [
                ['股票种类', 'A股'],
                ['股票上市交易所', '上海证券交易所'],
                ['股票简称', '山煤国际'],
                ['股票代码', '600546'],
                ['变更前股票简称', '中油化建']
            ]
        elif line == "['股票种类', '股票上市交易所上海证券交易所', '德邦股份', '股票简称', '股票代码603056', '变更前股票简称']":
            return [
                ['股票种类', 'A股'],
                ['股票上市交易所', '上海证券交易所'],
                ['股票简称', '德邦股份'],
                ['股票代码', '603056']
            ]
        else:
            return []
    return []

big_capital_pattern = r'.*[（()]?[零一二三四五六七八九十]+[)）]?[、.0-9]*([\u4e00-\u9fa5]+)'
big_capital_pattern = re.compile(big_capital_pattern)
table_name = ['公司信息', '基本情况简介', '公司股票简况', '公司基本情况']
# table_name = ['公司股票简况']

def process_lines(filename, lines, patience=3):
    filtered_lines = []
    invalid_state = 0
    for idx, line in enumerate(lines):
        try:
            data_json = json.loads(line)
        except json.JSONDecodeError:
            continue
        if 'inside' not in data_json:
            continue
        # if invalid_state == 0:
        #     if data_json['type'] == '页脚':
        #         invalid_state = 1
        #     else:
        #         if data_json['inside'] != "":
        #             filtered_lines.append(line)
        # if invalid_state == 1:
        #     if data_json['type'] == '页眉':
        #         invalid_state = 0
        if data_json['type'] == '页脚' or data_json['type'] == '页眉' or data_json['inside'] == "":
            continue
        filtered_lines.append(line)
    state_pointer = 0
    invalid_times = 0
    result_tables = {}
    one_table = []
    current_key = None
    for line in filtered_lines:
        data_json = json.loads(line) 
        if state_pointer == 0:
            pattern_found = big_capital_pattern.findall(data_json['inside'])
            if len(pattern_found) == 1 and pattern_found[0] in table_name:
                state_pointer = 1
                current_key = pattern_found[0]
        elif state_pointer == 1:
            if data_json['type'] != 'excel':
                invalid_times += 1
                if invalid_times > patience:
                    state_pointer = 0
            else:
                state_pointer = 2
                one_table.append(data_json['inside'])
        else:
            if data_json['type'] != 'excel':
                state_pointer = 0
                result_tables[current_key] = one_table
                one_table = []
                current_key = None
            else:
                one_table.append(data_json['inside'])
    tables = []
    for k, v in result_tables.items():
        if k == '公司股票简况':
            tables.extend([str(line) for line in process_stock_info(v)])
        else:
            tables.extend(v)
    json.dump(tables, 
        open(os.path.join('data/company_info', os.path.basename(filename).replace(".txt", ".json")), 'w'), 
        indent=4, ensure_ascii=False
    )
    return filename, tables


def main():
    pool = Pool(8)
    handles = []
    os.makedirs('data/company_info', exist_ok=True)
    for filename, lines in load_all_txt():
        # if filename == "2020-03-30__黑龙江北大荒农业股份有限公司__600598__北大荒__2019年__年度报告.txt":
        # process_lines(filename, lines)
        handles.append(pool.apply_async(process_lines, (filename, lines)))
    failed_cnt = 0
    zero_cnt = 0
    for idx, handle in enumerate(tqdm(handles, desc="waiting for return")):
        res = handle.get()
        if res is not None:
            filename, table = res
        else:
            print(load_all_txt()[0][idx])
        if len(table) > 0 and len(table) < 9:
            print(filename)
            failed_cnt += 1
        elif len(table) == 0:
            zero_cnt += 1
    print(failed_cnt)
    print(zero_cnt)
    pool.close()
    pool.join()