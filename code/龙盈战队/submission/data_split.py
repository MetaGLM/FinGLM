# coding: UTF-8
import gc
import glob
import multiprocessing

import torch
import threading
import time
import os
import json
import re
from collections import defaultdict
from tqdm import tqdm
from functools import lru_cache
import config
test_path = config.QUESTION_PATH
fout1 = open('output/question_type.json', 'w',encoding='utf-8')
# fout2 = open('output/type_peplenum.json', 'w',encoding='utf-8')
# fout3 = open('output/type_numeral.json', 'w',encoding='utf-8')
# fout4 = open('output/type_basic.json', 'w',encoding='utf-8')
# fout5 = open('output/type_opening.json', 'w',encoding='utf-8')
# fout6 = open('output/type_other.json', 'w',encoding='utf-8')
basic_information = ['名称','简称','代码','网址','地址','信箱','法定代表人','邮政编码']
temp_list = []
with open('output/公式.txt','r',encoding='utf-8') as f:
    a = f.readlines()
    for i in a:
        s = i.split("|")
        temp_list.append(s[0])

count1,count2,count3,count4,count5,count6,count7 = 0,0,0,0,0,0,0


count = 0
test_questions = open(test_path).readlines()
pattern = '\d{4}'
pattern2 = '最高|最低|第.{1,2}高|位列'
pattern3 = '告诉.+数值|告诉.+数据|提供.+数值|提供.+数据'
for test_question in test_questions:
    test_question = json.loads(test_question)
    question = test_question['question']
    match = re.search(pattern, question)




    mark = False
    if match:
        # a = re.findall(pattern,question)
        # if a and len(list(set(a)))>1:
        #     print(test_question)

        match2 = re.search(pattern2, question)
        if match2:
            count1 += 1
            test_question["question_type"] = "statistics"
            fout1.write(json.dumps(test_question, ensure_ascii=False) + "\n")
            continue


        new_question = question.replace("的", '')
        for i in temp_list:
            if i in new_question:
                count2 += 1
                test_question["question_type"] = "calculate"
                fout1.write(json.dumps(test_question,ensure_ascii=False) + "\n")
                mark = True
                break

        if not mark:
            exist_basic = False
            for basic in basic_information:
                if basic in question:
                    exist_basic = True
                    break
            if ('人员' in question or '人数' in question or '员工' in question or '职工' in question or '人数' in question) and \
                    '简要分析' not in question and '简要介绍' not in question and '元' not in question and '职工薪酬' not in question:
                count3 += 1
                test_question["question_type"] = "peplenum"
                fout1.write(json.dumps(test_question, ensure_ascii=False) + "\n")
            elif exist_basic:
                count4 += 1
                test_question["question_type"] = "basic"
                fout1.write(json.dumps(test_question, ensure_ascii=False) + "\n")
            elif '多少' in question or ('单位' in question and '元' in question) or '金额' in question or re.search(pattern3, question):
                count5 += 1
                test_question["question_type"] = "numeral"
                fout1.write(json.dumps(test_question, ensure_ascii=False) + "\n")
            else:
                count6 += 1
                test_question["question_type"] = "opening"
                fout1.write(json.dumps(test_question, ensure_ascii=False) + "\n")
    else:
        count7 += 1
        test_question["question_type"] = "other"
        fout1.write(json.dumps(test_question, ensure_ascii=False) + "\n")

# print(count1,count2,count3,count4,count5,count6,count7)


# peple_num = ['人员','人数','职工','人数','员工',]
#
# test_questions = open(test_path).readlines()
# question_list = []
# for test_question in test_questions:
#     question = json.loads(test_question)
#     if '多少' in question['question'] or '比率' in question['question'] or '增长率' in question['question'] and re.search("\d{4}", question['question']):
#         mark = True
#         if '小数' in question['question']:
#             fout2.write(json.dumps(question, ensure_ascii=False) + "\n")
#         else:
#             for i in peple_num:
#                 if i in question['question'] and '元' not in question['question']:
#                     mark = False
#                     break
#             if mark == True:
#                 fout1.write(json.dumps(question, ensure_ascii=False) + "\n")
#
#
#     else:
#         fout3.write(json.dumps(question, ensure_ascii=False) + "\n")