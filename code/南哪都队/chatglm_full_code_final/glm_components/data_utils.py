import os
from pathlib import Path
import pandas as pd
import json
from collections import defaultdict
from tqdm import tqdm
import pickle
from multiprocess import Pool


def extract_all_company_name():
    """_summary_
    从pdf名字种提取所有的公司简称、股票代码、年份等document的metadata
    Returns:
        _type_: _description_
    """
    alltxt_path = os.path.join(os.path.dirname(__file__), "../data/C-list-pdf-name.txt")
    result = []
    for file in open(alltxt_path, 'r', encoding='utf8').readlines():
        basic_info = file.strip().split("__")[:-1]
        result.append(basic_info)
    return pd.DataFrame(result, columns=["date", "full_name", "stock_code", "short_name", "year"])


def load_questions():
    """_summary_
    加载所有的问题
    """
    quests = []
    with open(os.path.join(os.path.dirname(__file__), "../data/C-list-question.json"), 'r') as fp:
        for line in fp.readlines():
            quests.append(json.loads(line)['question'])
    return quests


def load_extracted(name_only=True, with_stock_code=False):
    if with_stock_code:
        file_path = "data/temp/extracted_with_stock_code.json"
    else:
        file_path = "data/temp/retrieved_info.jsonl"
    with open(file_path) as fp:
        lines = fp.readlines()
        company_names = []
        for line in lines:
            if name_only:
                company_names.append(json.loads(line)['info_dict']['公司名称'])
            else:
                company_names.append(json.loads(line))
    return company_names


def load_table_json():
    result_dict = {}
    for file in list(os.listdir("data/excels")):
        metadata = file.replace(".json", "").split("__")
        year = metadata[-2].replace("年", "")
        code = metadata[-4]
        result_dict[(year, code)] = os.path.join("data/excels", file)
    return result_dict


def load_equations():
    return json.load(open('finetune/extract_all/equations.json', 'r'))


def load_filename_mapping():
    mapping_dict = {}
    file_list = [line.strip().replace(".pdf", ".txt") for line in open('data/C-list-pdf-name.txt', 'r', encoding='utf8').readlines()]
    for file in file_list:
        filename = os.path.basename(file)
        _, full_name, stock_code, short_name, year, _ = filename.split("__")
        mapping_dict[(stock_code, int(year.replace("年", "")))] = filename
    return mapping_dict