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

base_path = config.BASE_PATH
shortname_allname_path = 'output/company/shortname_allname.json'
shortname_allname = json.load(open(shortname_allname_path,"r"))



def docs_add_one(merge_list,page,idx,mark):
    result = []
    metadata = {"source": f'doc_0_{page}-{idx}_{mark}'}
    final_content = "\n".join(merge_list)
    final_content = final_content.strip()
    if isinstance(final_content, str) and final_content:
        result.append(Document(page_content=final_content, metadata=metadata))
    return result

def docs_product(temp_dict):
    docs = []
    for page,value in temp_dict.items():
        idx = 0
        temp_word = []
        temp_excel = []
        for index,split_text in enumerate(value):
            text = split_text['inside']
            type_text = split_text['type']
            if index > 0:
                last_type_text = value[index-1]['type']
            else:
                last_type_text = 'text'
            if type_text == '页眉':
                continue
            post_two_type = value[min(index+2,len(value)-1)]['type']
            if (type_text == 'text' and post_two_type == 'excel' and last_type_text!='excel') or type_text == 'excel':
                if not temp_excel and type_text == 'excel' and index>0:
                    temp_excel.append(value[index-1]['inside'])
                temp_excel.append(text)
                if temp_word:
                    result = docs_add_one(temp_word,page,idx,'word')
                    if result:
                        docs.extend(result)
                        idx += 1
                        temp_word = []
            else:
                temp_word.append(text)
                if temp_excel:
                    result = docs_add_one(temp_excel,page,idx,'excel')
                    if result:
                        docs.extend(result)
                        idx += 1
                        temp_excel = []
            if index == len(value)-1:
                if temp_word:
                    result = docs_add_one(temp_word,page,idx,'word')
                    if result:
                        docs.extend(result)
                if temp_excel:
                    result = docs_add_one(temp_excel,page,idx,'excel')
                    if result:
                        docs.extend(result)

    return docs

def covert_data_vector(company_year,embeddings):
    vector_store = []
    if company_year in shortname_allname:
        file = shortname_allname[company_year]
        temp_dict = defaultdict(list)
        try:
            with open(os.path.join(base_path,file),"r",encoding='utf-8') as f:
                for context in f.readlines():
                    context = eval(context)
                    if 'page' not in context:
                        continue
                    temp_dict[context['page']].append(context)

                docs_result = docs_product(temp_dict)
                vector_store = FAISS.from_documents(docs_result, embeddings)
                torch.cuda.empty_cache()
                gc.collect()
        except Exception as e:
                print(e)
    if vector_store:
        pass
        # print(f"{company_year}向量导入成功。")
    return vector_store
