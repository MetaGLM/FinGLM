# coding: UTF-8
import os
import time

import torch
import pandas as pd
import gc
import json
# os.environ["CUDA_VISIBLE_DEVICES"] = "0"
from transformers import AutoTokenizer, AutoModel
from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
import numpy as np
from tqdm import tqdm
from collections import defaultdict
from utils import content_product,load_prompt,_load_vector,load_prompt_vector,load_prompt_statistic
import re
import config

print("开始预测")
model_dir=config.MODEL_DIR
embedding_model_name = config.EMBEDDING_MODEL
test_path = 'output/question_type.json'
company_path = 'output/company/company.json'
fullname_shortname_path = 'output/company/fullname_shortname.json'
years = ['2019','2020','2021','2022']
text_vector_path = "/data/user0731/yk/finalcial_compition/code/output/vector"
title_vector_path = 'output/title_vector'

test_questions = open(test_path).readlines()
question_list = []
for test_question in test_questions:
    question = json.loads(test_question)
    question_list.append(question)
stock_mapping = json.load(open(company_path,"r"))
fullname_shortname = json.load(open(fullname_shortname_path,"r"))

fout_temp = []




#
#加载chaglm
tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
model = AutoModel.from_pretrained(model_dir, trust_remote_code=True).half().cuda()
model.eval()
#
#
#
#
# #加载pdf标题向量库
docs_company = []
embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)
if not os.path.exists(title_vector_path):
    os.makedirs(title_vector_path)
    idx = 0
    for fullname,shortname in fullname_shortname.items():
        idx += 1
        metadata = {"source": f'{idx}'}
        docs_company.append(Document(page_content=fullname, metadata=metadata))
    vector_company = FAISS.from_documents(docs_company, embeddings)
    vector_company.save_local(title_vector_path)
else:
    vector_company = FAISS.load_local(title_vector_path,embeddings=embeddings)



def trucate(question,trucate_index):
    question = question[trucate_index:]
    cleaned_text = re.sub(r'在\d{4}年|\d{4}年', '', question)
    # temp_list = cleaned_text.split("，")
    # if len(temp_list) > 1:
    #     cleaned_text = "".join(temp_list[1:])
    if '的' == cleaned_text[0]:
        cleaned_text = cleaned_text[1:]
    return cleaned_text


def trucate_opening(question,trucate_index):
    tmp_question = question.split("，")
    if len(tmp_question) == 2 and re.search("20\d{2}",tmp_question[1]):
        return tmp_question[0]
    question = question[trucate_index:]
    cleaned_text = re.sub(r'在\d{4}年|\d{4}年', '', question)
    # temp_list = cleaned_text.split("，")
    # if len(temp_list) > 1:
    #     cleaned_text = "".join(temp_list[1:])
    if '的' == cleaned_text[0]:
        cleaned_text = cleaned_text[1:]
    return cleaned_text

count = 0
no_prompt_question = []

result_dict = defaultdict(list)

for index,row_question in enumerate(tqdm(question_list)):
    question = row_question['question']
    question_type = row_question['question_type']


    exist_year = False
    exist_shortname = False
    use_excel = False
    prompt_year = ''
    prompt_company = ''
    short_name = ''
    exist_company_list = []
    curret_faiss = []
    cleaned_text = question

    if question_type == "statistics":
        prompt_statistic,model_product = load_prompt_statistic(question)
        if prompt_statistic and model_product:
            answer_statistic, history = model.chat(tokenizer, prompt_statistic, history=[])
        elif prompt_statistic and not model_product:
            answer_statistic = prompt_statistic
        else:
            answer_statistic = question
        row_question['answer'] = answer_statistic
        row_question.pop('question_type')
        fout_temp.append(row_question)
        # print(prompt_statistic,answer_statistic)
        # #     # 释放缓存
        torch.cuda.empty_cache()
        gc.collect()

        # result_dict['id'].append(row_question['id'])
        # result_dict['question_type'].append(question_type)
        # result_dict['question'].append(question)
        # result_dict['prompt'].append(prompt_statistic)
        # result_dict['answer'].append(answer_statistic)
        # result_dict['company'].append('')
        # result_dict['use_excel'].append("yes")

        continue

    years_list = re.findall("20(?:\d{2})", question)
    if years_list:
        exist_year = True

    for stock_mapping_one in stock_mapping:
        temp_index = question.find(stock_mapping_one)
        if temp_index != -1:
            exist_shortname = True
            exist_company_list.append((stock_mapping_one,temp_index,temp_index+len(stock_mapping_one)))

    if exist_year and exist_shortname:
        if len(exist_company_list) > 1:
            exist_company_list.sort(key=lambda x: x[1])

        #去除公司及年份，截断问题
        index1 = question.find(exist_company_list[0][0])
        index2 = question.find('公司')
        trucate_index = max(index1+len(exist_company_list[0][0]),index2+2)
        cleaned_text = trucate(question,trucate_index)

        if question_type == "opening":
            cleaned_text = trucate_opening(question, trucate_index)

        content_list = []
        for year in years_list:
            content_year,use_excel = content_product(question,exist_company_list[0][0],year,cleaned_text,question_type)
            content_list.extend(content_year)
            if question_type == "basic" or question_type=='peplenum':
                break
        content_list = sorted(set(content_list), key=content_list.index)

        if not use_excel:
            curret_faiss = _load_vector(text_vector_path, exist_company_list[0][0], year,embeddings,question_type)
            no_prompt_question.append(row_question)
        prompt_year = year
        prompt_company = exist_company_list[0][0]



    elif exist_year and not exist_shortname:
        similar_fullname = vector_company.similarity_search(question,1)[0].page_content
        short_name = fullname_shortname[similar_fullname]

        # 去除公司及年份，截断问题
        index1 = question.find('公司')
        if index1 != -1:
            cleaned_text = trucate(question, index1+2)
            if question_type == "opening":
                cleaned_text = trucate_opening(question, index1+2)
        else:
            cleaned_text = question

        content_list = []
        for year in years_list:
            content_year,use_excel = content_product(question,short_name,year,cleaned_text,question_type)
            content_list.extend(content_year)
            if question_type == "basic" or question_type=='peplenum':
                break
        content_list = sorted(set(content_list), key=content_list.index)

        if not use_excel:
            curret_faiss = _load_vector(text_vector_path, short_name, year,embeddings,question_type)
            no_prompt_question.append(row_question)
        prompt_year = year
        prompt_company = similar_fullname.split("__")[0]

    if not use_excel:
        if short_name:
            prompt = load_prompt_vector(curret_faiss,question, question_type,cleaned_text,short_name,prompt_year)
        else:
            prompt = load_prompt_vector(curret_faiss,question, question_type, cleaned_text, prompt_company,prompt_year)


        answer, history = model.chat(tokenizer, prompt, history=[])

        row_question['answer'] = answer

        # result_dict['id'].append(row_question['id'])
        # result_dict['question_type'].append(question_type)
        # result_dict['question'].append(question)
        # result_dict['prompt'].append(prompt)
        # result_dict['answer'].append(answer)
        # result_dict['company'].append(prompt_company)
        # result_dict['use_excel'].append("no")

        row_question.pop('question_type')
        # print(question, row_question['answer'])
        fout_temp.append(row_question)
        # #     # 释放缓存
        torch.cuda.empty_cache()
        gc.collect()


    else:
        count += 1
        query = prompt_year + '的' +cleaned_text
        top_content = '\n\n'.join(content_list)
        post_text = ''
        prompt_tmp = load_prompt(top_content,prompt_company,prompt_year,question,question_type,cleaned_text)


        if question_type=="calculate":
            prompt = prompt_tmp[0]
        elif question_type=="peplenum" or question_type=="basic":
            prompt = prompt_tmp[0]
            post_text = prompt_tmp[1]

        else:
            prompt = prompt_tmp





        answer, history = model.chat(tokenizer, prompt, history=[])

        if question_type == 'basic' and post_text:
            answer = answer.replace("不相同", "相同")
            if '相同' in question and '法定代表人' in question and '相同' not in answer:
                answer = '法定代表人相同。' + answer
            row_question['answer'] = answer
        else:
            row_question['answer'] = answer+post_text


        temp_answer = re.sub("20\d{2}",'',answer)
        if question_type == "numeral":
            if not re.search("\d", temp_answer):
                print('mark111')
                top_content_split = top_content.split("。")
                sub_sentence = []
                for i in top_content_split:
                    if prompt_year in i:
                        sub_sentence.append(i+"元")
                if sub_sentence:
                    new_answer = "。".join(sub_sentence)
                    row_question['answer'] = f"在{prompt_company}公司，" + new_answer
                else:
                    row_question['answer'] = f"在{prompt_company}公司，" + top_content

        if question_type == "calculate":
            supplement_keywords, supplement_answer,extra_result_strs = prompt_tmp[1],prompt_tmp[2],prompt_tmp[3]
            is_add_keywods = False
            if supplement_answer[0] not in answer:
                answer = supplement_answer[1]
            if supplement_keywords[0][1] not in answer:
                for i in supplement_keywords:
                    answer += f"{i[0]}是{i[1]}元。"
            row_question['answer'] = answer+extra_result_strs

        if question_type == 'peplenum' or question_type == 'basic':
            if '抱歉' in row_question['answer'] or '无法确定' in row_question['answer'] or '无法回答' in row_question['answer'] or '无法找到' in row_question['answer']:
                row_question['answer'] = f"{top_content}"




        # answer = ''
        # result_dict['id'].append(row_question['id'])
        # result_dict['question_type'].append(question_type)
        # result_dict['question'].append(question)
        # result_dict['prompt'].append(prompt)
        # result_dict['answer'].append(row_question['answer'])
        # result_dict['company'].append(prompt_company)
        # result_dict['use_excel'].append("yes")

        # print(question,row_question['answer'])
        row_question.pop('question_type')
        fout_temp.append(row_question)
        #     # 释放缓存
        torch.cuda.empty_cache()
        gc.collect()

#
#后处理去掉数字之间的","
time.sleep(10)
pattern = r'\d{1,3}(?:,\d{3})+(?:\.\d+)?'
# print(f'fout_temp数量是{len(fout_temp)}')
fout_final = open(config.OUT_DIR, 'w', encoding='utf8')

num = 0
for result in fout_temp:
    new_answer = result['answer']
    matches = re.finditer(pattern, new_answer)
    for single_match in matches:
        sub_str = single_match.group()
        temp_str = sub_str.replace(",", "")
        new_answer = new_answer.replace(sub_str, temp_str)
    result['answer'] = new_answer

    fout_final.write(json.dumps(result, ensure_ascii=False) + "\n")
    num+=1

print(num)
# print(count)
# df = pd.DataFrame(result_dict)
# excel_filename = 'output/eval.csv'
# df.to_csv(excel_filename, index=False)





