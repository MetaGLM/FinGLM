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



text_path = config.BASE_PATH
output_path = "output"
vector_path = "output/vector"
embedding = config.EMBEDDING_MODEL


if not os.path.exists(output_path):
    os.makedirs(output_path)
if not os.path.exists(vector_path):
    os.makedirs(vector_path)

file_df = glob.glob(f"{text_path}/*.txt")

#获取公司名称
company_path = os.path.join(output_path,'company')
if not os.path.exists(company_path):
    os.makedirs(company_path)
    company_list = []
    fullname_shortname = {}
    fullname = []
    for file in os.listdir(text_path):
        company = file.split("__")[-3]
        company_list.append(company)
    company_list = list(set(company_list))
    print("公司数量是",len(company_list))
    json.dump(company_list, open(f'{company_path}/company.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

   #创建公司全程-简称的字典
    fullname_shortname = {}
    for file in os.listdir(text_path):
        fullname = file[12:-4]
        shortname = file.split("__")[-3]
        fullname_shortname[fullname] = shortname
    json.dump(fullname_shortname, open(f'{company_path}/fullname_shortname.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

# # #加载embedding
# embedding_model_name = embedding
# embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)
#
#
#
#
#
#
#
# def docs_add_one(merge_list,doc_id,page,idx,mark):
#     result = []
#     metadata = {"source": f'doc_{doc_id}_{page}-{idx}_{mark}'}
#     final_content = "\n".join(merge_list)
#     final_content = final_content.strip()
#     if isinstance(final_content, str) and final_content:
#         result.append(Document(page_content=final_content, metadata=metadata))
#     return result
#
# def docs_product(temp_dict,doc_id):
#     docs = []
#     for page,value in temp_dict.items():
#         idx = 0
#         temp_word = []
#         temp_excel = []
#         for index,split_text in enumerate(value):
#             text = split_text['inside']
#             type_text = split_text['type']
#             if index > 0:
#                 last_type_text = value[index-1]['type']
#             else:
#                 last_type_text = 'text'
#             if type_text == '页眉':
#                 continue
#             post_two_type = value[min(index+2,len(value)-1)]['type']
#             if (type_text == 'text' and post_two_type == 'excel' and last_type_text!='excel') or type_text == 'excel':
#                 if not temp_excel and type_text == 'excel' and index>0:
#                     temp_excel.append(value[index-1]['inside'])
#                 temp_excel.append(text)
#                 if temp_word:
#                     result = docs_add_one(temp_word,doc_id,page,idx,'word')
#                     if result:
#                         docs.extend(result)
#                         idx += 1
#                         temp_word = []
#             else:
#                 temp_word.append(text)
#                 if temp_excel:
#                     result = docs_add_one(temp_excel,doc_id,page,idx,'excel')
#                     if result:
#                         docs.extend(result)
#                         idx += 1
#                         temp_excel = []
#             if index == len(value)-1:
#                 if temp_word:
#                     result = docs_add_one(temp_word,doc_id,page,idx,'word')
#                     if result:
#                         docs.extend(result)
#                 if temp_excel:
#                     result = docs_add_one(temp_excel,doc_id,page,idx,'excel')
#                     if result:
#                         docs.extend(result)
#
#     return docs
#
# def covert_data_dict():
#     for index,file in enumerate(tqdm(file_df)):
#         temp_dict = defaultdict(list)
#         with open(file,"r",encoding='utf-8') as f:
#             for context in f.readlines():
#                 context = eval(context)
#                 if 'page' not in context:
#                     continue
#                 temp_dict[context['page']].append(context)
#         try:
#             docs_result = docs_product(temp_dict,index)
#             company_year = file.split('/')[-1].split("__")[-3:-1]
#             vecotor_name = "__".join(company_year)
#             vector_store = FAISS.from_documents(docs_result, embeddings)
#             vector_store.save_local(vector_path, index_name=vecotor_name)
#         except Exception as e:
#             print(e)
#
# covert_data_dict()
# print("生成向量成功",f"向量个数为{len(os.listdir(vector_path))}")

