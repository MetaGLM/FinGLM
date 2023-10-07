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
import pandas as pd

if 4 == "5":
    print(111)
else:
    print(2222)
# # test_questions = open('output/question_type.json').readlines()
# # pattern = '\d{4}'
# # result_dict = defaultdict(list)
# # for test_question in test_questions:
# #     test_question = json.loads(test_question)
# #     result_dict['id'].append(test_question['id'])
# #     result_dict['question'].append(test_question['question'])
# #     result_dict['question_type'].append(test_question['question_type'])
# #
# # df = pd.DataFrame(result_dict)
# # excel_filename = 'output/eda_finalv2.csv'
# # df.to_csv(excel_filename, index=False)
#
# list1 = ['资产总','货币总','总资产','负债总','总负债','非流动资产','流动资产']
#
# test_questions = open('output/question_type.json').readlines()
# pattern = '\d{4}'
# result_dict = defaultdict(list)
# result_dict2 = defaultdict(list)
# for test_question in test_questions:
#     test_question = json.loads(test_question)
#     mark = False
#     if test_question['question_type'] == "statistics":
#         for i in list1:
#             if i in test_question['question']:
#                 mark = True
#                 result_dict['id'].append(test_question['id'])
#                 result_dict['question'].append(test_question['question'])
#                 result_dict['question_type'].append(test_question['question_type'])
#         if not mark:
#             result_dict2['id'].append(test_question['id'])
#             result_dict2['question'].append(test_question['question'])
#             result_dict2['question_type'].append(test_question['question_type'])
#
# df = pd.DataFrame(result_dict)
# excel_filename = 'output/eda_0.csv'
# df.to_csv(excel_filename, index=False)
#
#
# df = pd.DataFrame(result_dict2)
# excel_filename = 'output/eda_1.csv'
# df.to_csv(excel_filename, index=False)
#
# #
# # test_questions = open(test_path).readlines()
# # question_list = []
# # for test_question in test_questions:
# #     question = json.loads(test_question)
# #     if '多少' in question['question'] or '比率' in question['question'] or '增长率' in question['question'] and re.search("\d{4}", question['question']):
# #         mark = True
# #         if '小数' in question['question']:
# #             fout2.write(json.dumps(question, ensure_ascii=False) + "\n")
# #         else:
# #             for i in peple_num:
# #                 if i in question['question'] and '元' not in question['question']:
# #                     mark = False
# #                     break
# #             if mark == True:
# #                 fout1.write(json.dumps(question, ensure_ascii=False) + "\n")
# #
# #
# #     else:
# #         fout3.write(json.dumps(question, ensure_ascii=False) + "\n")