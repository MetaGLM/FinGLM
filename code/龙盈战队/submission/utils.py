# coding: UTF-8
import os
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
import re
from vector_load import covert_data_vector
from vector_load_opening import covert_data_vector_opening
import config
from collections import Counter

# exceldata1 = "../excel_data/excel_资产"
# exceldata2 = "../excel_data/excel_员工"
# exceldata3 = "../excel_data/excel_母公司"
# exceldata4 = "../excel_data/zichan.json"
# exceldata5 = "../excel_data/base.json"

#path
exceldata1 = "output/zichan.json"
exceldata2 = "output/mugongsi.json"
exceldata3 = "output/base.json"
city_path = 'output/cities.json'

# year = ['2019','2020','2021']
#dict
my_dict = {'一': 1,'二': 2,'三': 3,'四': 4,'五': 5,'六': 6,'七': 7,'八': 8,'九': 9,'十': 10,'十一': 11,'十二': 12,'十三': 13,'十四': 14,
           '十五': 15,'十六': 16,'十七': 17,'十八': 18,'十九': 19,'二十': 20}


pdf_list = []
with open(config.PDF_LIST, 'r',encoding='utf-8') as f:
    values = f.readlines()
    for i in values:
        pdf_list.append(i.strip())
shortname_year_list = []

for i in pdf_list:
    shortname_year = "__".join(i.split("__")[-3:-1])
    shortname_year_list.append(shortname_year)

#导入alltext资产数据表
data_zichan = json.load(open(exceldata1,encoding='utf-8'))
data_mugongsi = json.load(open(exceldata2,encoding='utf-8'))
data_base = json.load(open(exceldata3,encoding='utf-8'))
#导入城市
citis = json.load(open(city_path))
calculate_json = json.load(open('output/calculate_type.json',encoding='utf-8'))

special_key = []
for key,value in calculate_json.items():
    if len(value['关键词'])==1:
        special_key.append(key)

def product_top_ten(question,year,sort_index,match_city,keyword,key_num_list):
    collection_data = defaultdict(list)
    prompt = ''
    for shortname_year in shortname_year_list:
        if shortname_year in data_zichan:
            # if shortname_year == '天宸股份__2019年':
            #     print(111)
            data = data_zichan[shortname_year]
            current_year = data['year']
            current_address = data['address']
            current_name = data['name'].split("__")[1]

            if match_city and current_address not in match_city:
                continue

            if not keyword:
                for key, values in data.items():
                    if isinstance(values, list):
                        sub_keywords = [(i, value[0]) for i, value in enumerate(values) if i > 0 and question.find(value[0]) != -1]
                        sub_keywords_new = [i for i in sub_keywords if i[1] != '']
                        if sub_keywords_new:
                            for index, sub_keyword in sub_keywords_new:
                                row_values = values[index]
                                if len(row_values) > 1:
                                    for index2, row_value in enumerate(row_values[1:]):
                                        row_value = row_value.replace(",", "")
                                        if is_numeric(row_value) and len(row_value) >= 3:
                                            if current_year in year:
                                                collection_data[current_year].append((sub_keyword,float(row_value),current_name))
                                            break
            if keyword:
                exist_data = False
                for key, values in data.items():
                    if isinstance(values, list):
                        for row_values in values:
                            if exist_data:
                                break
                            if row_values[0] == keyword:
                                for index2, row_value in enumerate(row_values):
                                    row_value = row_value.replace(",", "")
                                    if is_numeric(row_value) and len(row_value) >= 3:
                                        if current_year in year:
                                            collection_data[current_year].append((keyword, float(row_value), current_name))
                                        exist_data = True
                                        break
    if collection_data:
        collection_company_list = []
        most_common_item = ''
        for key,value in collection_data.items():
            counter = Counter(item[0] for item in value)
            # 找出出现次数最多的元素
            most_common_item, most_common_count = counter.most_common(1)[0]
            new_value = [i for i in value if i[0] == most_common_item]
            new_value_filter = []
            new_value.sort(key=lambda x: x[1],reverse=True)
            for i in new_value:
                if i[2] not in new_value_filter and len(new_value_filter)<sort_index:
                    new_value_filter.append(i[2])
            collection_company_list.extend(new_value_filter)
        counter2 = Counter(collection_company_list)
        company_result= '、'.join([k for k, v in counter2.items() if v == 3])
        prompt = f'2019-2021年{most_common_item}位列前{sort_index}的上市公司有\n{company_result}。'

    model_product = False
    return prompt, model_product



def load_prompt_statistic(question):
    year = re.findall("20(?:\d{2})", question)
    head_num = 20

    if year == ['2019','2021']:
        year = ['2019', '2020', '2021']
        input_year = '2019-2021'
    else:
        input_year = '和'.join(year)


    key_num_list = []
    match_city = []
    keyword = ''
    prompt = ''
    model_product = True
    if '注册' in question:
        for city in citis:
            if city in question:
                match_city.append(city)

    if '其他非流动资产' in question:
        keyword = '其他非流动资产'
    elif '其他流动资产' in question:
        keyword = '其他流动资产'
    elif '其他非流动金融资产' in question:
        keyword = '其他非流动金融资产'
    elif '非流动金融资产' in question:
        keyword = '非流动金融资产'
    elif '非流动资产' in question:
        keyword = '非流动资产合计'
    elif '流动资产' in question:
        keyword = '流动资产合计'
    elif '资产总' in question or '总资产' in question:
        keyword = '资产总计'

    elif '非流动负债' in question:
        keyword = '非流动负债合计'
    elif '流动负债' in question:
        keyword = '流动负债合计'
    elif '负债总' in question or '总负债' in question:
        keyword = '负债合计'

    elif '货币总' in question:
        keyword = '货币资金'

    tmp_eval1 = re.findall("位列前([一二三四五六七八九十]{1})", question)
    tmp_eval2 = re.findall("位列前(\d{1,2})", question)
    if year == ['2019', '2020', '2021'] and (tmp_eval1 or tmp_eval2):
        sort_index = ''
        if tmp_eval1 and len(tmp_eval1) == 1:
            sort_index = my_dict[tmp_eval1[0]]
        elif tmp_eval2 and len(tmp_eval2) == 1:
            sort_index = int(tmp_eval2[0])
        else:
            pass
        if sort_index:
            final_result_special = product_top_ten(question,year,sort_index,match_city,keyword,key_num_list)
            return final_result_special


    for shortname_year in shortname_year_list:
        if shortname_year in data_zichan:
            # if shortname_year == '天宸股份__2019年':
            #     print(111)
            data = data_zichan[shortname_year]
            current_year = data['year']
            current_address = data['address']
            current_name = data['name'].split("__")[1]

            if match_city and current_address not in match_city:
                continue
            if current_year not in year:
                continue
            if not keyword:
                for key, values in data.items():
                    if isinstance(values, list):
                        sub_keywords = [(i, value[0]) for i, value in enumerate(values) if i > 0 and question.find(value[0]) != -1]
                        sub_keywords_new = [i for i in sub_keywords if i[1] != '']
                        if sub_keywords_new:
                            for index, sub_keyword in sub_keywords_new:
                                row_values = values[index]
                                if len(row_values) > 1:
                                    for index2, row_value in enumerate(row_values[1:]):
                                        row_value = row_value.replace(",", "")
                                        if is_numeric(row_value) and len(row_value) >= 3:
                                            key_num_list.append((sub_keyword,float(row_value),current_name))
                                            break
            if keyword:
                exist_data = False
                for key, values in data.items():
                    if isinstance(values, list):
                        for row_values in values:
                            if exist_data:
                                break
                            if row_values[0] == keyword:
                                for index2, row_value in enumerate(row_values):
                                    row_value = row_value.replace(",", "")
                                    if is_numeric(row_value) and len(row_value) >= 3:
                                        key_num_list.append((keyword,float(row_value),current_name))
                                        exist_data = True
                                        break
    if key_num_list:
        counter = Counter(item[0] for item in key_num_list)
        # 找出出现次数最多的元素
        most_common_item, most_common_count = counter.most_common(1)[0]
        new_key_num_list = [i for i in key_num_list if i[0] == most_common_item]
        tmp_company = []
        key_num_list_filter = []
        new_key_num_list.sort(key=lambda x: x[1], reverse=True)
        for i in new_key_num_list:
            if i[2] not in tmp_company:
                tmp_company.append(i[2])
                key_num_list_filter.append(i)

        #筛选序号确定
        head_num1 = re.findall("([一二三四五六七八九十]{1})家", question)
        head_num2 = re.findall("哪([一二三四五六七八九十]{1})个", question)
        head_num3 = re.findall("(\d{1})家", question)
        if head_num1:
            if head_num1[0] in my_dict:
                head_num = my_dict[head_num1[0]]
        elif head_num2:
            if head_num2[0] in my_dict:
                head_num = my_dict[head_num2[0]]
        elif head_num3:
            head_num = int(head_num3[0])


        if '最低' not in question and not match_city:

            a = re.findall("第(\d{1,2})高", question)
            b = re.findall("第([一二三四五六七八九十]{1,2})高", question)
            if b and len(b) == 1 and b[0] in my_dict:
                sub_index = my_dict[b[0]] - 1
                if sub_index < len(key_num_list_filter):
                    sub_company = key_num_list_filter[sub_index][2]
                    final_result = f"{input_year}年{most_common_item}第{b[0]}高的上市公司是{sub_company}，金额是{key_num_list_filter[sub_index][1]}元。"
                    model_product = False
                    return final_result, model_product
            elif a and len(a) == 1:
                sub_index = int(a[0]) - 1
                if sub_index < len(key_num_list_filter):
                    sub_company = key_num_list_filter[sub_index][2]
                    final_result = f"{input_year}年{most_common_item}第{a[0]}高的上市公司是{sub_company}，金额是{key_num_list_filter[sub_index][1]}元。"
                    model_product = False
                    return final_result, model_product

            prompt += f"上下文内容是和问题相关的{most_common_item}数据，包括公司名字及具体金额，并按金额数值从高到低进行了排序，第2高就是排名第二，第3高就是排名第三，依次类推。请从上下文中抽取答案，不要胡编乱造。\n上下文内容：\n"
            for index, i in enumerate(key_num_list_filter[:head_num]):
                if index == 0:
                    prompt += f"{most_common_item}最高的上市公司是{i[2]}，金额为{i[1]}元。\n"
                else:
                    prompt += f"{most_common_item}第{index + 1}高的上市公司是{i[2]}，金额为{i[1]}元。\n"
        elif '最低' not in question and match_city:
            match_city_strs = '和'.join(match_city)
            prompt += f"上下文内容是{input_year}年在{match_city_strs}注册的公司和其{most_common_item}数值，并按金额数值从高到低进行了排序，第1高也就是最高的意思，第2高就是排名第二，第3高就是排名第三，依次类推。请从上下文中抽取答案，不要胡编乱造。\n上下文内容：\n"
            for index, i in enumerate(key_num_list_filter[:head_num]):
                if index == 0:
                    prompt += f"{most_common_item}最高的上市公司是{i[2]}，金额为{i[1]}元。\n"
                else:
                    prompt += f"{most_common_item}第{index + 1}高的上市公司是{i[2]}，金额为{i[1]}元。\n"
        else:
            final_result = f"{input_year}年{key_num_list_filter[-1][2]}的{most_common_item}最低，为{key_num_list_filter[-1][1]}元。"
            model_product = False
            return final_result, model_product

        prompt += f"\n===\n请根据上下文回答：{question}"

    return prompt, model_product

def _load_vector(text_vector_path,company_name,year,embeddings,question_type):
    temp_year = int(year)
    use_prompt = False
    temp_faiss = []
    while True:
        try:
            company_year = f"{company_name}__{temp_year}年"
            if question_type == "opening":
                temp_faiss = covert_data_vector_opening(company_year, embeddings)
            else:
                temp_faiss = covert_data_vector(company_year,embeddings)
            use_prompt = True
            break
        except Exception as e:
            temp_year += 1
            # print(e)
            if temp_year == int(year)+2:
                break
    return temp_faiss


#
# def _load_vector(text_vector_path,company_name,year,embeddings):
#     temp_year = int(year)
#     use_prompt = False
#     temp_faiss = []
#     while True:
#         try:
#             temp_year_vector = f"{company_name}__{temp_year}年"
#             temp_faiss = FAISS.load_local(text_vector_path,embeddings=embeddings, index_name=temp_year_vector)
#             use_prompt = True
#             break
#         except Exception as e:
#             temp_year += 1
#             # print(e)
#             if temp_year == int(year)+2:
#                 break
#     return temp_faiss


def is_numeric(s):
    try:
        float(s)  # 尝试将字符串转换为浮点数
        return True
    except ValueError:
        return False

def search_float(sub_keyword,row_title,row_values,year):
    new_search_result = ''
    if len(row_values) == len(row_title):
        if int(year) in row_title:
            index = row_title.index(int(year))
            search_result = row_values[index]
            if re.search('\d{2,}', search_result):
                new_search_result = f"{year}年{sub_keyword}为{search_result}。"
    return new_search_result


def search_float_calculate(sub_keyword,row_title,row_values,year):
    new_search_result = ''
    if len(row_values) == len(row_title):
        if int(year) in row_title:
            index = row_title.index(int(year))
            search_result = row_values[index]
            search_result = search_result.replace(",", "")
            if is_numeric(search_result) and len(search_result) >= 3:
                new_search_result = search_result

    return new_search_result




def load_prompt_vector(curret_faiss,question, question_type,cleaned_text,company,year):
    #对于每股净资产单独处理
    if ('每股净资产' in cleaned_text or '每股收益' in cleaned_text) and company and year:
        temp_year = int(year)
        try:
            temp_year_vector = f"{company}__{temp_year}年"
            if temp_year_vector in data_zichan:
                data_dict = data_zichan[temp_year_vector]
            equity,stock_capital,eps,net_assets = '','',0,0
            for key, values in data_dict.items():
                if key == '合并资产负债表':
                    for i, value in enumerate(values):
                        if "归属于母公司所有者权益" in value[0] and len(value)>1:
                            for j in value[1:]:
                                j = j.replace(",", "")
                                if is_numeric(j):
                                    equity = j
                                    break
                        if '股本' in value[0] or '实收资本' in value[0] and len(value)>1:
                            for j in value[1:]:
                                j = j.replace(",", "")
                                if is_numeric(j):
                                    stock_capital = j
                                    break
                if key == '合并利润表':
                    for i, value in enumerate(values):
                        if "基本每股收益" in value[0] and len(value)>1:
                            for j in value[1:]:
                                j = j.replace(",", "")
                                if is_numeric(j):
                                    eps = j
                                    break
            if equity and stock_capital:
                net_assets = eval(f"{equity}/{stock_capital}")
                net_assets = "{:.4f}".format(net_assets)
            input_text = f"每股净资产为{net_assets}元，每股收益为{eps}元。"
            prompt = f'请仿照以下问题的回答风格，从给出的上下文内容中抽取出答案，答案均在上下文内容中。\n\n【回答风格】：\n上下文内容：2019年工商银行每股净资产和每股收益数据：每股净资产为2.45元，每股收益为2.68元。\n问题：2019年中国工商银行每股收益和每股净资产是多少？\n答案：2019年中国工商银行每股收益2.68元，每股净资产2.45元。' \
                     f'\n=======\n上下文内容：{year}年{company}每股净资产和每股收益数据：{input_text}\n问题：{question}\n答案：'
            return prompt

        except Exception as e:
            print(e)


    #对于每股经营现金流量单独处理
    if '每股经营现金流量' in cleaned_text and company and year:
        temp_year = int(year)
        try:
            temp_year_vector = f"{company}__{temp_year}年"
            if temp_year_vector in data_zichan:
                data_dict = data_zichan[temp_year_vector]
            stock_capital,liuliang,single_ll = '','',0
            for key, values in data_dict.items():
                if key == '合并资产负债表':
                    for i, value in enumerate(values):
                        if '股本' in value[0] or '实收资本' in value[0] and len(value)>1:
                            for j in value[1:]:
                                j = j.replace(",", "")
                                if is_numeric(j):
                                    stock_capital = j
                                    break
                if key == '合并现金流量表':
                    for i, value in enumerate(values):
                        if "经营活动产生的现金流量净额" in value[0] and len(value)>1:
                            for j in value[1:]:
                                j = j.replace(",", "")
                                if is_numeric(j):
                                    liuliang = j
                                    break
            if liuliang and stock_capital:
                single_ll = eval(f"{liuliang}/{stock_capital}")
                single_ll = "{:.3f}".format(single_ll)
            input_text = f"每股现金流量为{single_ll}元。"
            prompt = f'请仿照以下问题的回答风格，从给出的上下文内容中抽取出答案，答案均在上下文内容中。\n\n【回答风格】：\n上下文内容：2019年工商银行每股现金流量数据：每股现金流量为2.453元。\n问题：2019年中国工商银行每股现金流量是多少？\n答案：2019年中国工商银行每股现金流量是2.453元。' \
                     f'\n=======\n上下文内容：{year}年{company}每股现金流量数据：{input_text}\n问题：{question}\n答案：'
            return prompt

        except Exception as e:
            print(e)

    if question_type == 'opening':
        try:
            if curret_faiss:
                vector_store, temp_dict = curret_faiss
                top_content = vector_store.similarity_search(cleaned_text, k=4)
                page_content_list = []
                for i, content in enumerate(top_content):
                    value = content.page_content
                    new_content = f"{value}"
                    page_content_list.append(new_content)
                page_content_newlist = sorted(set(page_content_list), key=page_content_list.index)
                page_content_newlist_add = []
                for index,j in enumerate(page_content_newlist):
                    a = f"内容{index+1}：\n{j}"
                    page_content_newlist_add.append(a)
                top_content_merge = "\n\n".join(page_content_newlist_add)
                if len(top_content_merge) > 4000:
                    top_content_merge = top_content_merge[:4000]
                prompt = f'{top_content_merge}\n=====\n上文是和问题【{question}】相关的年报内容。请根据上文用简洁的语言回答用户的问题。\n{question}'
            else:
                prompt = f'我的知识库中没有和下述问题相关的数据，请直接回答不知道即可，不要回答其它内容。\n{question}'
            return prompt
        except Exception as e:
            print(e)
            return question



    if curret_faiss:
        top_content = curret_faiss.similarity_search(cleaned_text, k=5)
        page_content_list = []
        for i, content in enumerate(top_content):
            value = content.page_content
            type_value = content.metadata['source'].split("_")[-1]
            if type_value == "word":
                data_type = '文本数据'
            elif type_value == "excel":
                data_type = '表格数据'
            else:
                data_type = ''
                print("无法识别的内容类型", type_value)
            new_content = f"内容{i + 1}---{data_type}\n{value}"
            page_content_list.append(new_content)
        page_content_newlist = sorted(set(page_content_list), key=page_content_list.index)
        top_content_merge = "\n\n".join(page_content_newlist)
        if len(top_content_merge) > 3800:
            top_content_merge = top_content_merge[:3800]
        prompt = f'{top_content_merge}\n=====\n上文是和问题【{question}】相关的年报内容，包含文本数据或者表格数据。请根据上文用简洁的语言回答用户的问题。\n{question}'
    else:
        prompt = question
    return prompt



def load_prompt(top_content,prompt_company,prompt_year,question,question_type,cleaned_text):
    if question_type=="numeral":
        prompt = f'请仿照以下问题的回答风格，根据上下文内容生成答案，答案在上下文中，并且你只能从上下文内容中抽取答案，答案中应包含公司名称和具体的数值。\n\n【回答风格】：\n问题：2019年中国工商银行财务费用是多少元?\n答案：2019年中国工商银行财务费用是12345678.9元。\n' \
                 f'问题：工商银行2019年营业外支出和营业外收入分别是多少元?\n答案：工商银行2019年营业外支出为12345678.9元，营业外收入为2345678.9元。\n\n【上下文内容】：\n{prompt_company}年报数据：{top_content}\n\n问题：{question}\n答案：'
    if question_type=="calculate":
        num_list = top_content.split("\n\n")
        new_question = cleaned_text.replace("的", '')

        keyword_num = {}
        if '非流动负债比率' in new_question:
            formula = calculate_json['非流动负债比率']['公式']
            keywords = calculate_json['非流动负债比率']['关键词']
            is_percentage = calculate_json['非流动负债比率']['是否百分比']
            sub_key = '非流动负债比率'
        else:
            for key in calculate_json.keys():
                if key in new_question:
                    formula = calculate_json[key]['公式']
                    keywords = calculate_json[key]['关键词']
                    is_percentage = calculate_json[key]['是否百分比']
                    sub_key = key

        if len(keywords)==1 and len(num_list)==2:
            new_keyword = "上年" + keywords[0]
            keyword_num = {keywords[0]:num_list[0],new_keyword:num_list[1]}
        else:
            for keyword,num in zip(keywords,num_list):
                keyword_num[keyword] = num

        #利用公式进行计算
        expression = formula
        keyword_num_sorted_keys = sorted(keyword_num.keys(), key=len, reverse=True)
        for key in keyword_num_sorted_keys:
            expression = expression.replace(key, keyword_num[key])
        result = eval(expression)

        extra_result_strs = ''
        if is_percentage == 1:
            result_final = "{:.2f}%".format(result*100)
            if '比值' in sub_key or '比率' in sub_key or '比重' in sub_key or '比例' in sub_key:
                extra_result = "{:.2f}".format(result)
                extra_result_strs = f'最终结果转化为小数是{extra_result}。'
        else:
            result_final = "{:.2f}".format(result)
            if '比值' in sub_key or '比率' in sub_key or '比重' in sub_key or '比例' in sub_key:
                extra_result = "{:.2f}%".format(result*100)
                extra_result_strs = f'最终结果转化为百分比是{extra_result}。'

        #拼接最后结果
        answer = ''

        #补充关键信息
        supplement_keywords = []

        start = 0
        for key,value in keyword_num.items():
            temp_str = f"{key}是{value}元。"
            answer += temp_str
            supplement_keywords.append((key,value))


        #补充最终结果
        supplement_answer = (result_final,f"{prompt_company}{prompt_year}的{sub_key}为{result_final}。")

        prompt = f"根据问题及答案所需涉及的关键信息，组织生成新答案，新答案应包含所用公式、公式计算用到的变量数值和最后结果。下文已给出相关示例，请仿照示例的回答格式书写。\n" \
                 f"【相关示例1】：\n问题：中国工商银行2021年净利润增长率是多少?保留2位小数。\n关键信息:净利润是12345678.90。上年净利润是22345678.90。公式：净利润增长率=(净利润-上年净利润)/上年净利润。结果：81.00%。\n新答案：中国工商银行2021年净利润为12345678.90元，2020年净利润为22345678.90元，根据公式，净利润增长率=(净利润-上年净利润)/上年净利润，得出结果中国工商银行2021年净利润增长率81.00%。\n" \
                 f"【相关示例2】：\n问题：中国农业银行2022年流动比率为多少?保留2位小数。\n关键信息:流动资产合计是2745.93。流动负债合计是8569.50。公式：流动比率=流动资产合计/流动负债合计。结果：0.32。\n新答案：中国农业银行2022年流动资产合计是2745.93元，2022年流动负债合计是8569.50，根据公式，流动比率=流动资产合计/流动负债合计，得出结果中国农业银行2022年流动比率是0.32。" \
                 f"\n====\n问题：{question}\n关键信息：{answer}\n新答案："
        return (prompt,supplement_keywords,supplement_answer,extra_result_strs)
    if question_type=="peplenum":
        post_text = ''
        if "|||" not in top_content:
            prompt = f'请根据上下文内容回答问题，请仔细阅读上下文，正确答案均在上下文内容中。下文已经给出回答示例，请按照示例的风格来作答。\n\n【回答示例】：\n上下文内容：\n工商银行年报数据：在职员工的数量合计人员数量为13989。生产人员数量为10600。销售人员数量为35。技术人员数量为1363。\n问题：2021年中国工商银行销售人员数量是什么?\n答案：2021年中国工商银行销售人员数量是35人。\n=====\n上下文内容：\n{prompt_company}年报数据：{top_content}\n问题：{question}\n答案：'
        else:
            list1 = top_content.split("|||")
            prompt = f"根据问题及计算结果，组织生成新答案。下文已给出相关示例，请仿照示例的回答格式书写。\n\n" \
                     f"【相关示例】：\n问题：中国工商银行2019年企业硕士及以上人员占职工人数比例具体是什么？\n计算结果:0.05。\n新答案：中国工商银行2019年企业硕士及以上人员占职工人数比例为0.05。\n" \
                     f"\n====\n问题：{question}\n计算结果：{list1[0]}\n新答案："
            post_text = list1[1]
        return prompt,post_text
    if question_type=="basic":
        post_text = ''
        if '法定代表人' in question:
            top_content = top_content.split("\n\n")
            if top_content[-1] == '相同':
                post_text = '相同'
                top_content = '\n'.join(top_content[:-1])
            else:
                top_content = '\n'.join(top_content)
            prompt = f'上下文内容中给出了从2019-2021年公司的法定代表人名字，请根据上下文内容回答问题，请严格按照上下文内容来回答问题，不要胡编乱造，下文已经给出几个回答示例。' \
                     f'\n\n【回答示例1】：\n上下文内容：\n2019年法定代表人名字是：王颖。\n2020年法定代表人名字是：王刚。\n2021年法定代表人名字是：王颖。\n问题：浦东金桥2020-2021年的法定代表人是否都相同？\n答案：不相同。浦东金桥2020年法定代表人是王刚。\n2021年法定代表人是王颖。' \
                     f'\n\n【回答示例2】：\n上下文内容：\n2019年法定代表人名字是：李刚。\n2020年法定代表人名字是：李刚。\n2021年法定代表人名字是：李刚。\n问题：工商银行2019-2021年的法定代表人是否都相同？\n答案：相同。工商银行2019-2021年法定代表人都是李刚。' \
                     f'\n\n===\n上下文内容：{top_content}\n问题：{question}\n答案：'
        else:
            prompt = f'请仿照以下问题的回答风格，从上下文中抽取答案，请仔细阅读上下文，正确答案均在上下文内容中。\n\n【回答风格】：\n上下文内容：\n中国工商银行年报数据：\n公司注册地址为黑龙江省哈尔滨市南岗区长江路368号。公司注册地址的邮政编码为150090。公司办公地址为黑龙江省哈尔滨市南岗区嵩山路109号。\n\n问题：中国工商银行在2019年的注册地址是什么？\n答案：中国工商银行在2019年的注册地址是黑龙江省哈尔滨市南岗区长江路368号。\n====\n上下文内容：\n{prompt_company}年报数据：\n{top_content}\n\n问题：{question}\n答案：'
        return prompt,post_text
    if question_type=="opening":
        return ''
    return prompt



def content_product_numeral(question,company_name, year, cleaned_text):
    temp_year = int(year)
    use_prompt = False
    prompt_list = []
    sub_key_word = ''
    if '母公司' in question:
        sub_key_word = '母公司'

    while True:
        try:
            temp_year_vector = f"{company_name}__{temp_year}年"
            if sub_key_word:
                data_dict = data_mugongsi[temp_year_vector]
            else:
                data_dict = data_zichan[temp_year_vector]

            for i in ['非流动资产','流动资产','非流动负债',"流动负债"]:
                replace_text = i+"合计"
                cleaned_text = cleaned_text.replace(i,replace_text)

            for key,values in data_dict.items():
                if isinstance(values,list) and len(values)>0:
                    sub_keywords = [(i,value[0]) for i,value in enumerate(values) if (i>0 and cleaned_text.find(value[0]) != -1)]
                    sub_keywords_new = [i for i in sub_keywords if i[1]!='']
                    if sub_keywords_new:
                        for index,sub_keyword in sub_keywords_new:
                            row_values = values[index]
                            prompt = ''
                            if len(row_values)>1:
                                count = 0
                                search_result = search_float(sub_keyword,values[0],row_values,year)

                                if not search_result:
                                    for index2,row_value in enumerate(row_values):
                                        if count > 1:
                                            break
                                        title = f"{temp_year-count}年"
                                        if re.search('\d{2,}', row_value):
                                            prompt += f"{title}{sub_keyword}为{row_value}。"
                                            count += 1
                                else:
                                    prompt = search_result
                                        # if count > 1:
                                        #     break
                                        # title = f"{temp_year-count}年"

                                        # new_row_value = row_value.replace(",",'').strip()
                                        # if len(row_value) > 2 and is_numeric(new_row_value):
                                        #     prompt += f"{title}{sub_keyword}为{row_value}。"
                                        #     count += 1

                                        # if index2 > 0 and row_value != '':
                                        #     title = values[0][index2]
                                        #     if title.isdigit() and len(title) == 4:
                                        #         title = title + "年"
                                        #     prompt += f"{title}{sub_keyword}为{row_value}。"
                            if prompt != '':
                                prompt_list.append(prompt)
            if prompt_list:
                use_prompt = True
            break
        except Exception as e:
            temp_year += 1
            # print(e)
            if temp_year == 2023:
                break
    return prompt_list,use_prompt


def content_product_calculate(company_name, year, cleaned_text):
    temp_year = int(year)
    use_prompt = False
    prompt_list = []
    new_question = cleaned_text.replace("的", '')
    if '非流动负债比率' in new_question:
        keywords = calculate_json['非流动负债比率']['关键词']
    else:
        for key in calculate_json.keys():
            if key in new_question:
                keywords = calculate_json[key]['关键词']
                break

    while True:
        try:
            temp_year_vector = f"{company_name}__{temp_year}年"
            if temp_year_vector in data_zichan:
                data_dict = data_zichan[temp_year_vector]

            values_merge = []
            for key,values in data_dict.items():
                if isinstance(values,list):
                    values_merge.extend(values)
            for keyword in keywords:
                for value in values_merge:
                    if value[0]==keyword:
                        if len(keywords)==1:
                            for i in value[1:]:
                                i = i.replace(",","")
                                if is_numeric(i) and len(i)>=3 and len(prompt_list)<2:
                                    prompt_list.append(i)
                        else:
                            if temp_year - int(year) == 1:
                                numeric_list = []
                                for i in value[1:]:
                                    i = i.replace(",", "")
                                    if is_numeric(i):
                                        numeric_list.append(i)
                                        if len(i) >= 3 and len(numeric_list)==2:
                                            prompt_list.append(i)
                                            break
                            else:
                                for i in value[1:]:
                                    i = i.replace(",", "")
                                    if is_numeric(i) and len(i)>=3:
                                        prompt_list.append(i)
                                        break
                        break

            if len(keywords)==1:
                if len(prompt_list) == 2:
                    use_prompt = True
            else:
                if len(prompt_list) == len(keywords):
                    use_prompt = True

            break
        except Exception as e:
            temp_year += 1
            # print(e)
            if temp_year == 2023:
                break
    return prompt_list,use_prompt


def content_product_peplenum(question,company_name, year, cleaned_text):
    temp_year = int(year)
    use_prompt = False
    prompt_list = []
    keys_import = ["员工数量","员工情况"]
    sub_key = f"{company_name}__{year}年"

    if sub_key not in data_base:
        return prompt_list,use_prompt

    data = data_base[sub_key]
    if '硕士及以上' in question and ('占比' in question or '比例' in question):
        shuoshi = data['硕士']
        boshi = data['博士']
        sum_peple = data['职工总数']
        result = round((shuoshi+boshi)/sum_peple,2)
        result = "{:.2f}".format(result)
        result_percentage = f"{((shuoshi + boshi) / sum_peple) * 100:.2f}%"
        if boshi==0:
            post_text = f'其中硕士及以上人数为{shuoshi},职工总数为{sum_peple}。最终结果转化为百分比是{result_percentage}。'
        else:
            post_text = f'其中硕士及以上人数为{shuoshi+boshi}，硕士人数为{shuoshi}，博士人数为{boshi}，职工总数为{sum_peple}。最终结果转化为百分比是{result_percentage}。'
        prompt_list.append(f"{result}|||{post_text}")
        return prompt_list,True

    if '研发人员' in question and ('占比' in question or '比例' in question):
        yanfa = data['研发']
        sum_peple = data['职工总数']
        result = round(yanfa/sum_peple,2)
        post_text = f'研发人员人数为{yanfa}，职工总数为{sum_peple}。'
        prompt_list.append(f"{result}|||{post_text}")
        return prompt_list,True

    if '研发' in question and '研发人员' in data:
        for row in data['研发人员']:
            if '人' not in row[0]:
                prompt_list.append(f"{row[0]}人员数量为{row[1]}。")
            else:
                prompt_list.append(f"{row[0]}为{row[1]}。")
        if prompt_list:
            use_prompt = True
        return prompt_list,use_prompt


    for key_import in keys_import:
        if key_import in data:
            for row in data[key_import]:
                if '人' not in row[0]:
                    prompt_list.append(f"{row[0]}人员数量为{row[1]}。")
                else:
                    prompt_list.append(f"{row[0]}为{row[1]}。")

    if prompt_list:
        use_prompt = True
    return prompt_list,use_prompt


def content_product_basic(question,company_name, year, cleaned_text):
    temp_year = int(year)
    use_prompt = False
    prompt_list = []
    basic_information = ['名称', '简称', '代码', '网址', '地址', '信箱', '法定代表人', '邮政编码']
    keys_import = ["公司信息","基本情况简介"]
    sub_key = f"{company_name}__{year}年"

    if '法定代表人' in question:
        sub_data_list = []
        fading_list = []
        for i in [2019,2020,2021]:
            key = f"{company_name}__{i}年"
            if key in data_base:
                data = data_base[key]
                fading = data['法定代表人'].replace("先生",'').strip()
                fading_list.append(fading)
                sub_data = f"{i}年法定代表人名字是：{fading}。"
                sub_data_list.append(sub_data)
        if len(list(set(fading_list))) == 1:
            sub_data_list.append("相同")

        prompt_list = sub_data_list
        if prompt_list:
            use_prompt = True
        return prompt_list,use_prompt

    if sub_key not in data_base:
        return prompt_list,use_prompt

    if '证券' in cleaned_text:
        if '公司信息' in data_base[sub_key]:
            for i in data_base[sub_key]['公司信息']:
                if '证券' in i[0]:
                    prompt_list.append(f"{i[0]}为{i[1]}。")
        if '公司股票简况' in data_base[sub_key]:
            for row in data_base[sub_key]['公司股票简况']:
                if '证券' in row[0]:
                    prompt_list.append(f"{row[0]}为{row[1]}。")
        if prompt_list:
            use_prompt = True
        return prompt_list,use_prompt

    for j in basic_information:
        if j in cleaned_text:
            for key_import in keys_import:
                if key_import in data_base[sub_key]:
                    for row in data_base[sub_key][key_import]:
                        if j in row[0]:
                            prompt_list.append(f"{row[0]}为{row[1]}。")
    if prompt_list:
        use_prompt = True
    return prompt_list,use_prompt


def content_product(question,company_name,year,cleaned_text,question_type):
    if question_type=="numeral":
        content_year,use_prompt = content_product_numeral(question,company_name, year, cleaned_text)
    elif question_type=="calculate":
        content_year,use_prompt = content_product_calculate(company_name, year, cleaned_text)
    elif question_type=="peplenum":
        content_year,use_prompt = content_product_peplenum(question,company_name, year, cleaned_text)
    elif question_type=="basic":
        content_year,use_prompt = content_product_basic(question,company_name, year, cleaned_text)
    elif question_type=="opening":
        return [],False
    else:
        return [],False
    return content_year,use_prompt


