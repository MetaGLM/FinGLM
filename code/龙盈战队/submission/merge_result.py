# coding: UTF-8
import os
import json
# os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import re
import copy
from tqdm import tqdm
output1 = 'output/final_0831v1.json'
output2 = 'output/final_0831_10.json'
# #
# # #
# # #
fout = open('output/final_submissionv5.json', 'w', encoding='utf8')
# #
# # # 使用正则表达式匹配带逗号和小数点的数字
# pattern = r'\d{1,3}(?:,\d{3})+(?:\.\d+)?'
# #
# #
# #
# #
# #
out1_result = open(output1,encoding='utf-8').readlines()
out2_result = open(output2,encoding='utf-8').readlines()
#






new_data_dict = {}
for i in tqdm(out2_result):
    result = json.loads(i)
    new_answer = result['answer']
    id = result['id']
    new_data_dict[id] = result



for i in out1_result:
    result = json.loads(i)
    id = result['id']
    if id in new_data_dict:
        value = new_data_dict[id]
        fout.write(json.dumps(value, ensure_ascii=False) + "\n")
    else:
        fout.write(json.dumps(result, ensure_ascii=False) + "\n")










