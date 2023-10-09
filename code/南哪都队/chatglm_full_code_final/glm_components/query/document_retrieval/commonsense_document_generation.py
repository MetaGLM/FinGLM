import json
import os
from tqdm import tqdm
import sys
import re

json_folder = 'data/list_json'
#output_folder = 'data/retrieved_data'
#if not os.path.exists(output_folder):
#    os.mkdir(output_folder)

def find_dict_idx(mixed_list):
    for idx, e in enumerate(mixed_list):
        if isinstance(e, dict):
            return idx
    else:
        return -1
    
def dfs_find(excel, target, res):
    idx = find_dict_idx(excel)
    if idx != -1:
        excel = excel[idx]
        for key in excel:
            if target in key:
                res += excel[key]
            else:
                res = dfs_find(excel[key], target, res)
    return res


def remove_index(ele):
    template_1 = '(([0-9]*)|[一二三四五六七八九十]{1,3})[、\.,]'
    template_2 = '([\(（](([0-9]*)|[一二三四五六七八九十]{1,3})[\)）])'
    template_3 = '[、\.,]'
    
    def remove_template(template, str_):
        try:
            span = re.match(template, str_).span()
            str_ = str_.replace(str_[span[0]:span[1]], '')
        except AttributeError:
            pass
        return str_
    
    ele = remove_template(template_1, ele)
    ele = remove_template(template_2, ele)
    ele = remove_template(template_3, ele)
    return ele

def get_dict_info(mixed_list):
    for ele in mixed_list:
        if isinstance(ele, dict):
            key_list = list(ele.keys())
            for key in key_list:
                new_key = remove_index(key)
                ele[new_key] = ele.pop(key)
            break
    else:
        return False
    return ele

def judge_validity(line):
    rm_list = ['本公司', '本集团']
    for word in rm_list:
        if word in line:
            return False
    if re.search('[0-9][0-9,.]+[0-9]', line):
        return False
    return True

def filtering(mixed_dict):
    rm_list = []
    for key in mixed_dict:
        if len(key) > 20:
            rm_list.append(key)
            continue
        reserved = []
        idx = find_dict_idx(mixed_dict[key])
        for ele in mixed_dict[key]:
            if isinstance(ele, str):
                if not judge_validity(ele):
                    break
                else:
                    reserved.append(ele)
        if idx != -1:
            if temp := filtering(mixed_dict[key][idx]):
                reserved.append(temp)
        if reserved:
            mixed_dict[key] = reserved
        else:
            rm_list.append(key)
    for key in rm_list:
        del mixed_dict[key]
    return mixed_dict

def merge(total_res, res):
    for k in res:
        if total_res.get(k):
            if sys.getsizeof(res[k]) > sys.getsizeof(total_res[k]):
                total_res[k] = res[k] 
        else:
            total_res[k] = res[k]
    return total_res

def main():
    total_res = {}
    for file in tqdm(os.listdir(json_folder)):
        excel = json.load(open(os.path.join(json_folder, file), 'r', encoding = 'utf-8'))
        res = dfs_find(excel, '重要会计政策及会计估计', [])
        if res := get_dict_info(res):
            res = filtering(res)
            total_res = merge(total_res, res)
        pass
    with open('data/retrieval_result.json', 'w', encoding='utf-8') as f:
        json.dump(total_res, f, ensure_ascii=False, indent = 4)
    pass

if __name__ == '__main__':
    main()