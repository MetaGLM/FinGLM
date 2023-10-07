# coding: UTF-8
import gc
import glob

import torch
import time
import os
import json
from collections import defaultdict
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.vectorstores import FAISS
from tqdm import tqdm
import config
import re

base_path = config.BASE_PATH
shortname_allname_path = 'output/company/shortname_allname.json'
shortname_allname = json.load(open(shortname_allname_path,"r"))


text_path = "../../alltxt"
output_path = "output"
vector_path = "output/vector_bert"
chinese_numbers = "一二三四五六七八九十"
english_numbers = "123456789"
pattern = f"^([{chinese_numbers}]+、|\([{chinese_numbers}]\)|（[{chinese_numbers}]）|[{english_numbers}]、|\([{english_numbers}]\)|（[{english_numbers}]）|[{english_numbers}].)"
pattern_1 = f"^([{chinese_numbers}]+、)"
pattern_2 = f"^(\([{chinese_numbers}]\)|（[{chinese_numbers}]）|[{english_numbers}]、|\([{english_numbers}]\)|（[{english_numbers}]）|[{english_numbers}].)"
pattern2 = f"^([{chinese_numbers}]+、)"








def docs_add_one(strs,doc_id,):
    result = []
    metadata = {"source": f'doc_{doc_id}'}
    if isinstance(strs, str):
        result.append(Document(page_content=strs, metadata=metadata))
    return result


def split_context(all_content,end_page,start_allrow):
    docs = []
    temp_dict2 = {}
    temp_dict2_new = {}
    for index,context in enumerate(all_content):
        context = eval(context)
        if not context:
            continue
        inside = context['inside']
        page = context['page']
        allrow = int(context['allrow'])
        if int(page) < end_page and int(allrow) >= start_allrow:
            # 在文本中查找所有匹配项
            matches1 = re.findall(pattern_1, inside)
            matches2 = re.findall(pattern_2, inside)
            if len(inside)<30:
                if matches1:
                    temp_dict2[inside] = all_content[index+1:index + 180]
                elif matches2:
                    temp_dict2[inside] = all_content[index+1:index + 60]

    doc_id = 0
    for key,values in temp_dict2.items():
        strs = ''

        max_lengh = 1
        if re.findall(pattern_1, key):
            max_lengh = 2200
        elif re.findall(pattern_2, key):
            max_lengh = 800

        for index_tmp,value in enumerate(values):
            value = eval(value)
            if not value:
                continue
            inside = value['inside']
            text_type = value['type']
            matches2 = re.findall(pattern2, inside)
            if (matches2 and index_tmp > 4) or (len(strs)>max_lengh):
                break
            if text_type == '页眉' or text_type == '页脚' or inside == '':
                continue
            strs += f'\n{inside}'

        if strs:
            new_key = re.sub(pattern,'', key)
            if new_key:
                temp_dict2_new[new_key] = strs
                # input_text = new_key
                input_text = new_key + "：\n" + strs
                single_vector = docs_add_one(input_text,doc_id)
                docs.extend(single_vector)
                doc_id += 1
    return temp_dict2_new,docs





def covert_data_vector_opening(company_year,embeddings):
    vector_store = []
    temp_dict2 = {}
    if company_year in shortname_allname:
        file = shortname_allname[company_year]
    try:
        with open(os.path.join(base_path, file), "r", encoding='utf-8') as f:
            all_content = f.readlines()
            start_allrow = 3
            end_page = 1000
            for context in all_content:
                context = eval(context)
                if not context:
                    continue
                inside = context['inside']
                page = context['page']
                allrow = int(context['allrow'])
                if int(page) <= 10:
                    if inside == '一、公司信息':
                        start_allrow = allrow
                    end_page_list = re.findall(r'第.+节财务报告\.+(\d+)', inside)
                    if end_page_list:
                        end_page = int(end_page_list[0])+10
                else:
                    break
            temp_dict2,docs = split_context(all_content,end_page,start_allrow)
            vector_store = FAISS.from_documents(docs, embeddings)
            torch.cuda.empty_cache()
            gc.collect()

    except Exception as e:
        print(e)
    if vector_store and temp_dict2:
        # print(f"{company_year}向量导入成功。")
        return (vector_store,temp_dict2)
    else:
        return []


