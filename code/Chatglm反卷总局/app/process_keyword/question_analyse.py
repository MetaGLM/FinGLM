#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import json
import glob

# from tqdm import tqdm
# import requests
import pandas as pd
from collections import defaultdict
import configparser

config = configparser.ConfigParser()
# config.read('./config.ini')
config.read('D:\\UGit\\fjzj\\app\\config.ini')

TEST_QUESTION_PATH = config["guanfang_data"]['test_quesion_path']
PDF_PATH = config["guanfang_data"]['pdf_path']
OUTPUT_PATH = config["question_analyse"]["keyword_question_path"]
PROCESS_KEYWORD_PATH = config["question_analyse"]["process_keyword_path"]


def extract_name(name):
    _, com_full_name, code, com_short_name, year, _ = name.split('__')
    return com_full_name, code, com_short_name, year


def get_calculate_bili(q):
    question = q['question']
    if q['company'] != '':
        question = question.replace(q['company'], '<company>')
    for y in q['match_year']:
        question = question.replace(y + '年', '<year>')
        question = question.replace(y, '<year>')
    rightest_pos = max(question.rfind('<company>')+len('<company>'),
                       question.rfind('<year>')+len('<year>'), question.rfind('公司')+len('公司'))
    question = question[rightest_pos:]
    question = question.strip('企业').strip('的其')
    pattern = re.compile(r'((.+)(?:与|占|在)(.+)(?:中所)?(?:的)?(?:比值|比例|比率))')
    match = pattern.search(question)

    if match:
        full_match = match.group(1)
        if full_match.find('，') > 0:
            full_match = full_match[full_match.find('，')+1:]
        a = match.group(2).strip('的').strip('年报中').strip(
            '企业').replace('经费', '费用').strip('，其')
        if a.find('，') > 0:
            a = a[a.find('，')+1:]
        b = match.group(3).replace(
            '费用', '(研发费用+销售费用+财务费用+管理费用)').strip('的').strip('企业').strip('中所占')
        if b == '利润':
            b = '净利润'
        return full_match, a, b
    else:
        return None, None, None

def judge_tongji(question):
    if ('最大' in question ) or ('最小' in question ) or ('最前' in question ) or ('最后' in question ) or ('最高' in question ) or ('最低' in question ) or ('最多' in question ) or ('最少' in question ):
        return True
    if '倒数' in question:
        return True
    if  re.search('(第|前)[一二三四五六七八九十\d]+', question):
        return True
    return False

def question_analyse():
    # 1、提取所有公司名，形成正则所需词典
    com_full_names = []
    com_short_names = []
    com_year_mapping = defaultdict(set)

    file_paths = glob.glob(os.path.join(PDF_PATH, "*"))
    for filename in file_paths:
        # train_df = pd.read_csv('train.csv')
        # for index, data in train_df.iterrows():
        # filename = data['name']
        com_full_name, code, com_short_name, year = extract_name(
            filename.strip('.pdf').strip('.json').strip('.txt'))
        com_full_names.append(com_full_name)
        com_short_names.append(com_short_name)
        com_year_mapping[com_full_name].add(year.strip('年'))
        com_year_mapping[com_short_name].add(year.strip('年'))
    com_year_mapping = {c: list(com_year_mapping[c]) for c in com_year_mapping}
    with open(os.path.join(PROCESS_KEYWORD_PATH, 'com_full_names.txt'), 'w', encoding='utf-8') as file:
        for _ in com_full_names:
            file.write(_+'\n')
    with open(os.path.join(PROCESS_KEYWORD_PATH, 'com_short_names.txt'), 'w', encoding='utf-8') as file:
        for _ in com_short_names:
            file.write(_+'\n')
    with open(os.path.join(PROCESS_KEYWORD_PATH, 'company_year_mapping.json'), "w", encoding="utf-8") as file:
        json.dump(com_year_mapping, file, ensure_ascii=False, indent=4)

    # 2、对问题进行后续精细化提取
    attr_mapping_title = defaultdict(set)
    with open(os.path.join(PROCESS_KEYWORD_PATH, '字典.txt'), encoding='utf-8') as file:
        for line in file.readlines():
            d = eval(line.strip())
            for k in d:
                attr_mapping_title[k] |= set(d[k])

    attr_value = {}
    with open(os.path.join(PROCESS_KEYWORD_PATH, '字典2.txt'), encoding='utf-8') as file:
        for line in file.readlines():
            d = eval(line.strip())
            attr_value.update(d)

    com_normal_attr_mapping_title = {}
    with open(os.path.join(PROCESS_KEYWORD_PATH, '字典3.txt'), encoding='utf-8') as file:
        for line in file.readlines():
            d = eval(line.strip())
            com_normal_attr_mapping_title.update(d)

    gongshi_mapping = {}
    gongshi_mapping_attr = defaultdict(list)
    with open(os.path.join(PROCESS_KEYWORD_PATH, '公式.txt'), encoding='utf-8') as file:
        for line in file.readlines():
            gongshi_keyword, gongshi = line.strip().split(',')
            gongshi_attrs = list(re.split(r'[\=|\(|\)|（|）|\+|\-|/]', gongshi))
            gongshi_attrs = [a for a in gongshi_attrs if a != ''][1:]
            for a in gongshi_attrs:
                gongshi_mapping_attr[gongshi_keyword].append(a)
            gongshi_mapping[gongshi_keyword] = gongshi

    find_keywords = list(attr_mapping_title.keys() | gongshi_mapping.keys() | com_normal_attr_mapping_title.keys())
    find_keywords.sort(key=len, reverse=True)
    attr_regex_pattern = r'(?:' + '|'.join(find_keywords) + r')'
    attr_regex = re.compile(attr_regex_pattern, re.IGNORECASE)

    with open(os.path.join(PROCESS_KEYWORD_PATH, 'com_full_names.txt'), 'r', encoding='utf-8') as file:
        com_full_names = [c.strip() for c in file.readlines()]
    with open(os.path.join(PROCESS_KEYWORD_PATH, 'com_short_names.txt'), 'r', encoding='utf-8') as file:
        com_short_names = [c.strip() for c in file.readlines()]
    dictionary_words = [c for c in set(com_full_names + com_short_names)]
    dictionary_words.sort(key=len, reverse=True)
    com_regex_pattern = r'(?:' + '|'.join(dictionary_words) + r')'
    com_regex = re.compile(com_regex_pattern, re.IGNORECASE)
    year_regex_pattern = r'2\d{3}(?=年|\D|$)'
    year_regex = re.compile(year_regex_pattern)
    with open(os.path.join(PROCESS_KEYWORD_PATH, 'company_year_mapping.json'), "r", encoding='utf-8') as file:
        com_year_mapping = json.load(file)

    question_list = []
    with open(TEST_QUESTION_PATH, encoding='utf-8') as file:
        for line in file.readlines():
            question_list.append(json.loads(line))

    question_keyword_list = []
    for q in question_list:
        # 1、年份提取
        year_regex_pattern = r'2\d{3}(?=年|\D|$)'
        year_regex = re.compile(year_regex_pattern)
        year_match = year_regex.findall(q['question'])
        year_match = [y.strip('年') for y in year_match]
        q['match_year'] = year_match
        if len(q['match_year']) == 1:
            now_year = int(q['match_year'][0])
            if '前年' in q['question']:
                q['match_year'].append(str(now_year-2))
            elif '上一年' in q['question'] or '去年' in q['question'] or '上年' in q['question']:
                q['match_year'].append(str(now_year-1))
            elif '前两年' in q['question']:
                q['match_year'].append(str(now_year-1))
                q['match_year'].append(str(now_year-2))
        if '2019-2021' in q['question'] or '2019至2021' in q['question'] or '2019年至2021' in q['question'] or '2019年到2021' in q['question'] or '2019到2021' in q['question']:
            q['match_year'] = ['2019','2020','2021']
        com_match = com_regex.findall(
            q['question'].replace('(', '').replace(')', '').replace('（', '').replace('）', ''))
        # 2、公司提取
        if len(com_match) > 0:
            com_match = max(com_match, key=len)
        else:
            com_match = ''
        q['company'] = com_match
        caibao_years = com_year_mapping[com_match] if com_match in com_year_mapping else []
        q['caibao_years'] = caibao_years
        
        # 3、关键词提取
        attr_match = attr_regex.findall(q['question'])
        attr_match.extend(attr_regex.findall(q['question'].replace('的','')))
        keywords = list(set(attr_match))
        keywords = [k for k in keywords if k != '']
        q['keywords'] = keywords
        com_normal_keywords = [k for k in keywords if k in com_normal_attr_mapping_title]
        com_info_keywords = [k for k in keywords if k not in com_normal_keywords]
        
        # 4、问题分类
        if '保留' in q['question'] and com_match != '':
            question_type = 'calculate'
        elif com_match != '' and len(year_match) > 0 and ('分析' in q['question'] or '介绍' in q['question'] or '如何' in q['question'] or '描述' in q['question'] or '是否' in q['question'] or '原因' in q['question'] or '哪些' in q['question'] or len(com_normal_keywords) > 0) and '元' not in q['question'] and len(com_info_keywords) == 0:
            question_type = 'com_normal'
        elif com_match != '' and len(year_match) > 0:
            # 这里补充下用大模型抽取keyword
            question_type = 'com_info'
        elif com_match == '' and judge_tongji(q['question']):
            question_type = 'com_statis'
        else:
            question_type = 'normal'
        q['question_type'] = question_type
        if '增长率' in q['question']:
            q['question_type'] = 'com_info'

        # 用大模型补充提取关键词
        
        
        # 5、元素定位
        q['gongshi'] = []
        recall_titles = {}
        recall_columns = {}
        # 5-1 判断出是需要计算的题
        if '比例' in q['question'] or '比值' in q['question'] or ('占' in q['question'] and '比率' in q['question']):
            gongshi_res, a, b = get_calculate_bili(q)
            if gongshi_res is not None:
                generate_gongshi = gongshi_res + '=' + a + '/' + b
                if a in attr_mapping_title:
                    recall_titles[a] = list(attr_mapping_title[a])
                    recall_columns[a] = attr_value[a]
                if b in attr_mapping_title:
                    recall_titles[b] = list(attr_mapping_title[b])
                    recall_columns[b] = attr_value[b]
                if b == '(研发费用+销售费用+财务费用+管理费用)':
                    for _ in ['研发费用', '销售费用', '财务费用', '管理费用']:
                        recall_titles[_] = list(attr_mapping_title[_])
                        recall_columns[b] = attr_value[_]
                q['gongshi'].append(generate_gongshi)
            q['question_type'] = 'calculate'
        # 5-2 识别出是公式
        elif any([k for k in q['keywords'] if k in gongshi_mapping.keys()]) and q['company'] != '':
            gongshi = [gongshi_mapping[k]
                    for k in q['keywords'] if k in gongshi_mapping.keys()]
            for g in gongshi:
                ga = list(re.split(r'[\=|\(|\)|（|）|\+|\-|/]', g))
                ga = [a for a in ga if a != ''][1:]
                for a in ga:
                    recall_titles[a] = list(attr_mapping_title[a])
                    recall_columns[a] = attr_value[a]
            q['gongshi'] = gongshi
            q['question_type'] = 'calculate'
        # 5-3 com_normal类型抽取
        elif q['question_type'] == 'com_normal':
            for a in q['keywords']:
                # com_normal类指定标题
                if a in com_normal_attr_mapping_title:
                    recall_titles[a] = com_normal_attr_mapping_title[a]
        # 5-4 其他类型(com_info+calculate)
        else:
            for a in q['keywords']:
                if a in attr_mapping_title:
                    recall_titles[a] = list(attr_mapping_title[a])
                    recall_columns[a] = attr_value[a]
                elif a in gongshi_mapping:
                    for ga in gongshi_mapping_attr[a]:
                        recall_titles[ga] = list(attr_mapping_title[ga])
                        recall_columns[ga] = attr_value[ga]
                    q['gongshi'].append(gongshi_mapping[a])
                    q['question_type'] = 'calculate'
        q['recall_titles'] = recall_titles
        q['recall_columns'] = recall_columns
        question_keyword_list.append(q)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as file2:
        file2.write(json.dumps(question_keyword_list,
                    ensure_ascii=False, indent=4))


if __name__ == '__main__':
    question_analyse()

# def get_question_keyword(question):
#     prompt = f'''
#     帮我提取关键词,比如下面的输入和输出,
#     例子1：
#     输入：<year><company>的企业名称是什么?
#     输出：{{"value":["企业名称"]}}

#     例子2：
#     输入：<company><year>的总负债增长率是多少？请保留两位小数。
#     输出：{{"value":["总负债增长率"]}}

#     例子3：
#     输入：<company><year>办公地址是什么?
#     输出：{{"value":["办公地址"]}}

#     例子4：
#     输入：什么是资本回报率？
#     输出：{{"value":["资本回报率"]}}

#     例子5：
#     输入：请简要分析<company><year>公司员工情况
#     输出：{{"value":["员工情况"]}}
#     例子6：
#     输入：<company><year>固定资产和无形资产分别是多少元?
#     输出：{{"value":["固定资产","无形资产"]}}

#     例子7：
#     输入：<year>，<company>的销售费用和管理费用分别是多少元?
#     输出：{{"value":["销售费用","管理费用"]}}

#     例子8：
#     输入：请简要分析<company><year>核心竞争力的情况。
#     输出：{{"value":["核心竞争力"]}}

#     请仿照上面的方式尽可能精确地输出关键词，直接输出json格式。
#     文本：{question}
#     输出：
#     '''
#     response = requests.post("http://127.0.0.1/chat", json={
#         "prompt": prompt,
#         "history": [],
#         "top_p": 0.7,
#         "temperature": 0
#     })
#     match = re.search(r'\{.*?\}', response.json()['response'], re.DOTALL)
#     if match:
#         json_string = match.group()
#         try:
#             keywords = eval(json_string)['value']
#             # 排除一些错误情况
#             for k in keywords:
#                 if '<year>' in k or '<company>' in k:
#                     raise
#             if len(keywords) > 3:
#                 raise
#         except:
#             return {'keywords': []}
#         return {'keywords': keywords}
#     else:
#         return {'keywords': []}

    # 3、对问题使用chatglm提取关键问题项
    # with open("test_questions_info.json") as file:
    #     question_list = json.load(file)
    # for q in tqdm(question_list):
    #     if len(q['keywords']) > 0:
    #         continue
    #     while True:
    #         try:
    #             # 把时间和公司名进行遮盖
    #             question = q['question']
    #             question = question.replace(q['company'],'<company>')
    #             for y in q['match_year']:
    #                 question = question.replace(y+'年','<year>')
    #                 question = question.replace(y, '<year>')
    #             keywords_dict = get_question_keyword(question)
    #             q.update(keywords_dict)
    #             break
    #         except:
    #             print('出错文本',q)
