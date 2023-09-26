import json
import os
import jieba
from tqdm import tqdm

from keywords import *
from config import *
from db.db_schema import schema_emp

import re


def makesure_path(path):
    if not os.path.exists(path):
        os.mkdir(path)

# 公共utils
def bs_generator(items, bs):
    for i in range(0, len(items), bs):
        yield items[i:i+bs]  
        
def json_lines_dump(lines, path):
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
            
def json_lines_load(path):
    return [json.loads(line) for line in open(path, encoding="utf-8") if line]

def is_number(string): return string in '1234567890' or re.fullmatch("-{0,1}[\d]+\.{0,1}[\d]+", strip_comma(string)) != None

def is_int(string): return is_number(string) and "." not in string

def is_float(string): return is_number(string) and "." in string

def judge_is_number_excel(doc):
    try:
        if isinstance(doc, str):
            doc = json.loads(doc)
        def is_number_helper(item):
            if isinstance(item, dict):
                return any([is_number_helper(v) for v in item.values()])
            else:
                return is_number(item)
        return is_number_helper(doc)
    except Exception as e:
        print(e)
        print(doc)
        return False
    
def test_chat(prompt, temperature=0.1):
    return chatglm2.chat(tokenizer, prompt, temperature=temperature)[0]

def get_txt_path(pdf):
    return os.path.join(TXT_PATH, pdf.replace(".pdf", ".txt"))

def get_dt_path(pdf):
    return os.path.join(DT_PATH, os.path.split(pdf)[-1].replace(".txt", ".dt"))

def clean_dict(dic, kw):
    if isinstance(dic, dict):
        if any([kw in k for k in dic]):
            pop_keys = []
            for k, v in dic.items():
                if kw not in k:
                    pop_keys.append(k)
                else:
                    dic[k] = clean_dict(v, kw)
            for k in pop_keys:
                dic.pop(k)
        else:
            for k, v in dic.items():
                dic[k] = clean_dict(v, kw)
    return dic

def klg_cleaner(klgs, year):
    new_klgs = []
    for klg in klgs:
        for sub in klg.split("\n"):
            try:
                sub = json.loads(sub)
                new_klgs.append(re.sub("_\d+", "", json.dumps(clean_dict(sub, year[:-1]), ensure_ascii=False)))
            except:
                new_klgs.append(re.sub("_\d+", "", sub))
    return new_klgs

def year_add(year, delta): return str(int(year[:-1]) + delta) + "年"

def get_year_doc(comp_name, year):
    docs = comp_title_dict[comp_name]
    for doc in docs:
        if year in doc:
            return doc
    
    for doc in docs:
        if year_add(year, 1) in doc:
            return doc
        
    for doc in docs:
        if year_add(year, -1) in doc:
            return doc
    
    return docs[0] if docs else None

def strip_comma(string): return string.replace(",", "")

def my_float(string):
    if not string: return 0.
    try:
        return float(string)
    except Exception as e:
        print(e)
        return 0.
    return 0.

def my_int(string):
    if not string: return 0
    try:
        return int(string)
    except Exception as e:
        print(e)
        return 0
    return 0

# 判断保留几位小数
def find_dot(num):
    if not isinstance(num, float):
        return -1
    str_num = str(num)
    return len(str_num) - str_num.find(".") - 1

def find_res_value(raw_res, keyword):
    if raw_res == '':
        return ''
    res = raw_res
    raw_keyword = keyword
    keyword = str(keyword)
    res = re.sub("\d{4}年", "", res)
    res = re.sub("股票/证券代码\d+", "", res)
    res = re.sub('".+"', "", res)
    start = res.find(keyword) + len(keyword)
    values = re.findall("[-\d,.]+", res[start:])
    values = [i for i in values if i not in "-,."]
    res_v = None
    try:
        if len(values) > 0:
            res_v = strip_comma(values[0])

        if res_v != None:
            return res_v
    except Exception as e:
        print(e)
        return ''
    return ''

def is_zh(string):
    return re.fullmatch("[\u4e00-\u9fa5]+", string) != None

def edit_distance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

def algin_float_string(v, dot_bits):
    format_v_string = "{:." + dot_bits + "f}"
    v = format_v_string.format(v)
    return v

def gen_sql_res_json(desc, res):
    cols = [i[0] for i in desc]
    res_json = []
    for line in res:
        res_json.append({k: v for k, v in zip(cols, line)})
    return res_json

def lcs_sub(s1, s2):
    max_len = 0
    sub = ''
    
    dp = [[0 for __ in range(len(s2))] for _ in range(len(s1))]
    for i in range(len(s1)):
        for j in range(len(s2)):
            if s1[i] == s2[j]:
                dp[i][j] = dp[i-1][j-1]+1 if (i>0 and j>0) else 1
            if dp[i][j] > max_len:
                max_len = dp[i][j]
                sub = s1[i-max_len+1:i+1]
    return sub


if __name__ == "__main__":
    # test_cases = [456.0, 456.1]
    # for v in test_cases:
    #     print(v, isinstance(v, float) and find_dot(v) == 1 and str(v)[-1] == '0')

    print(algin_float_string(4.0, "0"))