from sentence_transformers import SentenceTransformer
import re
import json
from collections import OrderedDict

import requests
from elasticsearch import Elasticsearch
from transformers import AutoTokenizer, AutoModel
import configparser
import os
import time

config = configparser.ConfigParser()
config.read('./config.ini')


tokenizer = AutoTokenizer.from_pretrained(
    config['guanfang_data']['chatglm_path'], trust_remote_code=True)
model = AutoModel.from_pretrained(
    config['guanfang_data']['chatglm_path'], trust_remote_code=True).cuda()
model.eval()

# time.sleep(10)

def get_chatglm_answer(prompt, temperature=0.1, cls_history=[]):
    response, history = model.chat(
        tokenizer, prompt, history=cls_history, top_p=0.7, temperature=temperature)
    return response

# M3E_URL = "http://127.0.0.1:8000/embedding"
# CHATGLM_URL = config['guanfang_data']['chatglm_url']


# def get_chatglm_answer(prompt, temperature=0.1, cls_history=[], max_length=4096):
#     response = session.post(CHATGLM_URL, json={
#         "prompt": prompt,
#         "history": cls_history,
#         "top_p": 0.7,
#         "temperature": temperature,
#         "max_length": max_length
#     }, headers={})
#     answer = response.json()['response']
#     return answer


# os.system("systemctl start elasticsearch")

# time.sleep(60)

es = Elasticsearch([config['es']['es_host']],
                   http_auth=(config['es']['es_user'], config['es']['es_passwd']))
es_index_table = config['es']['es_normal_index'] + \
    ',' + config['es']['es_sentence_index']
es_index_normal = config['es']['es_normal_index']


m3e_model = SentenceTransformer(
    config['process_es']['m3e_model_path'], device='cpu')
m3e_model.eval()

time.sleep(5)


# 创建一个 Session 对象
session = requests.Session()
# 设置最大重试次数
retries = 3
adapter = requests.adapters.HTTPAdapter(max_retries=retries)
session.mount('http://', adapter)
session.mount('https://', adapter)


# 替换词表，目前只有一个词
with open('./embedding_method/query_rule_replace.json', 'r') as f:
    query_rule_replace_dict = json.load(f)


# 找到有对应的财报的年份
def get_caibao_years(match_year, caibao_years, question):
    final_year = []
    for year in match_year:
        if year in caibao_years:
            final_year.append(year)
        elif year + 1 in caibao_years:
            # 如果问了基础信息，则后一年找不到对应的
            if any(keyword in question for keyword in ("员工", "人员", "职工", "硕士", "博士", "邮箱", "地址", "信箱", "法定代表", "网址", "网站", "增长率")):
                continue
            final_year.append(year + 1)
    final_year = list(set(final_year))
    return final_year


# 通过向量召回得到文本
def get_context(company, final_year, query, size=3, es_index='tianchi', keyword="", recall_titles={}, title_keyword=""):
    # 召回公司和年份
    force_search_body = {
        "size": size,
        "_source": ["texts"],
        "query": {"bool": {"filter": [
            {"term": {"companys": company}},
            # {"term": {"year": str(max(final_year))}}
            {"terms": {"year": final_year}}
        ]
        }
        }
    }
    # 获取embedding
    # r = requests.post(M3E_URL, json={"sentences": [query]})
    # embeddings = r.json()['data'][0]

    # embeddings = m3e_model.encode([query])[0].tolist()

    # # 向量召回
    # force_search_body['query']['bool']['should'] = [
    #     {"function_score": {
    #         "query": {"match_all": {}},
    #         "script_score": {"script": {
    #             "source": "cosineSimilarity(params.queryVector, 'embedding') + 1.0",
    #             "params": {"queryVector": embeddings}
    #         }}}}]
    force_search_body['query']['bool']['should'] = [
        {"match": {"texts": {"query": query}}}]
    # 如果包含keyword，则加强keyword的召回，包括keyword所在的位置
    if len(keyword) > 0:
        # force_search_body['query']['bool']['should'].append({"constant_score": {
        #                                                     "filter": {"match_phrase": {"texts": {"query": keyword}}}, "boost": 0.2}})
        force_search_body['query']['bool']['should'].append(
            {"match_phrase": {"texts": {"query": keyword}}})
        force_search_body['query']['bool']['filter'].append(
            {"terms": {"titles_cut.keyword": recall_titles[keyword]}})
    if len(title_keyword) > 0:
        force_search_body['query']['bool']['should'].append(
            {"match": {"titles_cut": {"query": title_keyword}}})
    print(force_search_body)
    search_result = es.search(index=es_index, body=force_search_body)
    hits = search_result["hits"]["hits"]
    recall_texts = [hit["_source"]["texts"] for hit in hits]
    print('\n\n'.join(recall_texts))
    return recall_texts


# 清洗context
def clean_context(recall_context):
    # 去重
    context = list(OrderedDict.fromkeys(recall_context).keys())
    context = "\n\n".join(context)
    # 匹配带逗号的数字，去除逗号
    pattern = re.compile(r'(?<=\d),(?=\d{3})')
    context = pattern.sub('', context)
    return context


# 用最普通的方式获取答案（向量召回+chatglm）
def get_common_answer(company, final_year, query, es_index, temperature=0.1, answer_recall_text=0):
    recall_context = get_context(
        company, final_year, query, size=3, es_index=es_index)
    context = clean_context(recall_context)
    # 调用chatglm2b获取答案
    prompt = "'''\n{}\n'''\n根据以上信息回答问题：'{}'，不需要计算".format(
        context, query)
    answer = get_chatglm_answer(prompt, temperature=temperature)

    if (answer_recall_text or ("无法" in answer)) and len(context) > 0:
        context_list = context.split("\n\n")
        if len(context[0]) < 200:
            new_context = '\n\n'.join(context_list[:2])
        else:
            new_context = '\n\n'.join(context_list[:1])
        answer = answer + f'\n召回文本：{new_context}'
    return answer


# 接收抽取关键词后的test_question
def chat(test_question):
    question_id = test_question['id']
    question = test_question['question']
    company = test_question['company']
    keywords = test_question['keywords']
    recall_titles = test_question['recall_titles']
    question_type = test_question['question_type']
    if len(company) > 0:
        match_year = list(map(lambda x: int(x), test_question['match_year']))
        caibao_years = list(
            map(lambda x: int(x), test_question['caibao_years']))
    else:
        match_year = []
        caibao_years = []
        question_type = 'normal'
    answer = ""
    context = ""

    # 如果是normal类型，直接调用chatglm得到结果
    if question_type == 'normal':
        answer = get_chatglm_answer(prompt=question)
    # 否则找到对应的公司和年份进行检索返回
    else:
        # 找到对应的财报的年份
        final_year = get_caibao_years(match_year, caibao_years, question)
        # mask掉公司名
        query = question.replace("(", "").replace(
            ")", "").replace("（", "").replace("）", "")
        query = question.replace(company, "")

        # 替换关键词，如果替换了，在答案的部分要替换回来
        replaced_dict = {}
        for replace_word_before, replace_word_after in query_rule_replace_dict.items():
            if replace_word_before in query:
                query = query.replace(
                    replace_word_before, replace_word_after)
                replaced_dict[replace_word_after] = replace_word_before

        # 如果没有对应年份得财报
        if len(final_year) == 0:
            answer = "根据提供的信息，无法回答。"
        elif question_type in ['com_normal', 'com_statis']:
            if len(recall_titles) > 0:
                # 如果有多个关键词，则用每个关键词分别召回
                if len(recall_titles) > 1:
                    size = 2
                    recall_texts = []
                    for keyword in recall_titles.keys():
                        recall_keyword_query = '和'.join(
                            [str(x) for x in match_year]) + '年的' + keyword + "是？"
                        recall_texts.extend(
                            get_context(company, final_year, recall_keyword_query, size, es_index_normal, keyword, recall_titles))
                # 否则直接用原句召回
                else:
                    size = 3
                    keyword = list(recall_titles.keys())[0]
                    recall_texts = get_context(
                        company, final_year, query, size, es_index_normal, keyword, recall_titles)

                if len(recall_texts) > 0:
                    context = clean_context(recall_texts)
                    test_question['context'] = context
                    # 调用chatglm2b获取答案
                    prompt = "'''\n{}\n'''\n根据以上信息，回答问题：'{}'".format(
                        context, query)

                    answer = get_chatglm_answer(prompt=prompt)

                # 如果没有context，则获取最普通的答案
                else:
                    answer = get_common_answer(
                        company, final_year, query, es_index_normal, answer_recall_text=1)
            else:
                if len(keywords) > 0:
                    title_keyword = ",".join(keywords)

                    recall_context = get_context(
                        company, final_year, query, size=3, es_index=es_index_normal, title_keyword=title_keyword)
                    context = clean_context(recall_context)
                    # 调用chatglm2b获取答案
                    prompt = "'''\n{}\n'''\n根据以上信息回答问题：'{}'".format(
                        context, query)
                    answer = get_chatglm_answer(prompt=prompt)
                    if len(context) > 0:
                        context_list = context.split("\n\n")
                        if len(context[0]) < 200:
                            new_context = '\n\n'.join(context_list[:2])
                        else:
                            new_context = '\n\n'.join(context_list[:1])
                        answer = answer + f'\n召回文本：{new_context}'                    
                else:
                    answer = get_common_answer(
                        company, final_year, query, es_index_normal, answer_recall_text=1)
        # 如果有对应财报，且是简单抽取问题：
        elif question_type in ['com_info']:

            # 如果存在规则关键词，则需要在对应标题的表格上寻找答案
            if len(recall_titles) > 0:
                # 如果有多个关键词，则用每个关键词分别召回
                if len(recall_titles) > 1:
                    size = 2
                    recall_texts = []
                    for keyword in recall_titles.keys():
                        recall_keyword_query = '和'.join(
                            [str(x) for x in match_year]) + '年的' + keyword + "是多少？"
                        recall_texts.extend(
                            get_context(company, final_year, recall_keyword_query, size, es_index_table, keyword, recall_titles))
                # 否则直接用原句召回
                else:
                    size = 3
                    keyword = list(recall_titles.keys())[0]
                    recall_texts = get_context(
                        company, final_year, query, size, es_index_table, keyword, recall_titles)

                if len(recall_texts) > 0:
                    context = clean_context(recall_texts)
                    test_question['context'] = context
                    # 调用chatglm2b获取答案
                    prompt = "'''\n{}\n'''\n根据以上信息回答问题：'{}'，不需要计算".format(
                        context, query)

                    answer = get_chatglm_answer(prompt=prompt)

                    retry_count = 3
                    while (retry_count):
                        if "增长率" in answer and "增长率" not in question:
                            answer = get_chatglm_answer(prompt=prompt)
                            retry_count -= 1
                        else:
                            break

                    retry_count = 3
                    while (retry_count):
                        if "不" not in answer and "法定" in question and len(match_year) > 1:
                            answer = get_chatglm_answer(
                                prompt=prompt + "，先展示各个年份的法定代表人是谁，再判断\"相同\"还是\"不相同\"", temperature=1)
                            # print(answer)
                            retry_count -= 1
                        else:
                            answer = answer.replace("不同", "不相同")
                            break

                    # print(answer)
                # 如果没有context，则获取最普通的答案
                else:
                    answer = get_common_answer(
                        company, final_year, query, es_index_normal)

            # 如果没有关键词，则获取最普通的答案
            else:
                answer = get_common_answer(
                    company, final_year, query, es_index_normal)

            # if '增长率' not in question:
            #     answer = answer.replace(" ", "").replace(".00元", "元").replace(".10元", ".1元").replace(".20元", ".2元").replace(".30元", ".3元").replace(
            #         ".40元", ".4元").replace(".50元", ".5元").replace(".60元", ".6元").replace(".70元", ".7元").replace(".80元", ".8元").replace(".90元", ".9元")

        elif question_type == 'calculate':
            gongshi = test_question['gongshi']

            # 如果存在规则关键词，则需要在对应标题的表格上寻找答案
            if len(recall_titles) > 1:
                size = 2
                if len(recall_titles) > 2:
                    size = 1

                recall_texts = []
                for keyword in recall_titles.keys():
                    recall_keyword_query = '和'.join(
                        [str(x) for x in match_year]) + '年的' + keyword + "是多少？"
                    recall_texts.extend(
                        get_context(company, final_year, recall_keyword_query, size, es_index_table, keyword, recall_titles))

                if len(recall_texts) > 0:
                    context = clean_context(recall_texts)
                    prompt = """
'''
{}
'''
根据以上信息回答问题：\"{}\"
其中公式为:
{}
先获取{}，这一步不需要计算
再带入以上对应的公式，用'='号结尾
""".format(context, query, '\n'.join(gongshi),  "和".join(["\"" + "年与".join([str(x) for x in match_year]) + "年的" + keyword + "\"" for keyword in recall_titles.keys()]))

                    # print(prompt)

                    # 重试调用多次，直到模型输出公式
                    retry_count = 5
                    while (retry_count):
                        retry_count -= 1
                        answer = get_chatglm_answer(prompt=prompt)

                        # 抽取answer中的公式
                        pattern = r'\(*\-?\d[\d\.\+\-\*/\(\)% ]*[\+\-\*/][\d\.\+\-\*/\(\)% ]*\d\)*'
                        formulas = re.findall(pattern, answer)

                        # 计算公式替换原来的结果，最后一个结果直接替换，前面的公式后面添加
                        if len(formulas) == 1:
                            try:
                                # 查看公式中数字的数量是否和公式的数量相同
                                formula = formulas[-1]
                                if formula.endswith("*100"):
                                    formula = formula[:-4]
                                elif formula.endswith("* 100"):
                                    formula = formula[:-5]
                                formula_numbers = len(
                                    re.findall(r'\d+(?:\.\d+)?', formula))
                                pattern = r"[\+\-\*/]"
                                gongshi_num = len(
                                    re.split(pattern, gongshi[0]))
                                if gongshi_num != formula_numbers:
                                    continue

                                formula_result = eval(formula)
                                if "每股" in query:
                                    formula_result = "{:.2f}".format(
                                        formula_result) + "元"
                                else:
                                    formula_result = "{:.2%}".format(
                                        round(formula_result, 4)) + '或' + "{:.2f}".format(formula_result)
                                formula_index = answer.index(formula)
                                answer = answer[:formula_index +
                                                len(formula)] + '=' + formula_result + '。'

                                break
                            except:
                                # print("wrong_fomula:" + str(formula))
                                pass

                else:
                    retry_count = 3
                    while (retry_count):
                        retry_count -= 1
                        answer = get_common_answer(
                            company, final_year, query, es_index_table)

                        pattern = r'\(*\-?\d[\d\.\+\-\*/\(\)% ]*[\+\-\*/][\d\.\+\-\*/\(\)% ]*\d\)*'
                        formulas = re.findall(pattern, answer)

                        # 计算公式替换原来的结果，最后一个结果直接替换，前面的公式后面添加
                        if len(formulas) == 1:
                            try:
                                formula = formulas[-1]
                                if formula.endswith("*100"):
                                    formula = formula[:-4]
                                elif formula.endswith("* 100"):
                                    formula = formula[:-5]
                                formula_result = eval(formula)
                                if "每股" in query:
                                    formula_result = "{:.2f}".format(
                                        formula_result) + "元"
                                else:
                                    formula_result = "{:.2%}".format(
                                        round(formula_result, 4)) + '或' + "{:.2f}".format(formula_result)
                                formula_index = answer.index(formula)
                                answer = answer[:formula_index +
                                                len(formula)] + '=' + formula_result + '。'
                                break
                            except:
                                # print("wrong_fomula:" + str(formula))
                                pass

            # 如果没有关键词，复用之前的答案
            else:
                answer = get_common_answer(
                    company, final_year, query, es_index_table)

            # 如果前面有query替换，则替换回来
            if len(replaced_dict) > 0:
                for replaced_word_after, replaced_word_before in replaced_dict.items():
                    answer = answer.replace(
                        replaced_word_after, replaced_word_before)

        # else:
        #     raise
    # if question_type in ['com_info', 'calculate']:
    #     answer = question + answer
    if question_type != 'normal':
        answer = '根据{}的年报信息，'.format(company) + answer

    test_question['answer'] = answer

    answer = {
        "test_question": test_question,
        "context": context,
        "result": {
            "id": question_id,
            "question": question,
            "answer": answer
        },
        "status": 200
    }
    return answer
