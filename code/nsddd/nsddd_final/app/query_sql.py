#checkpoint-90 比较棒
from transformers import AutoModel, AutoTokenizer
import torch
from utils.query_map import query_keyword_map
import tqdm
import json
import os
import sqlite3
import gc
import csv
import pandas as pd
import re

from configs.model_config import sql_chatglm_path, query_path, sql_res_path
def replace_func(m):
    return "注册地址 LIKE '%%%s%%'" % m.group(1)

device = torch.device('cuda:0')
tokenizer = AutoTokenizer.from_pretrained(sql_chatglm_path, trust_remote_code=True)
model = AutoModel.from_pretrained(sql_chatglm_path, trust_remote_code=True).to(device)
model = model.eval()

raw_question=[]
question=[]
prompt_group =[]

# 匹配的字符串
pattern_continue_year = [r'\d{4}-\d{4}',r'\d{4}年-\d{4}',r'\d{4}年到\d{4}', r'\d{4}年至\d{4}', r'\d{4}到\d{4}', r'\d{4}至\d{4}']
pattern_discrete_year = r'2019|2020|2021'

with open(query_path, 'r', encoding='utf-8') as  f:
    for line in f:
        if '最' in line or '前' in line or  '第' in line:
            if '均' in line:
                for continue_year_pattern in pattern_continue_year:
                    range_str = re.findall(continue_year_pattern, line)
                    if len(range_str) == 0:
                        continue
                    # 计算年份
                    continue_year = re.findall(pattern_discrete_year, line)
                    start_year = eval(continue_year[0])
                    end_year = eval(continue_year[1])

                    line = line.replace('均','')
                    line_ori = line
                    for year in range(start_year, end_year+1):
                        line_temp = line_ori
                        raw_question.append(json.loads(line_temp.replace(range_str[0],str(year))))
                    break
            else:
                raw_question.append(json.loads(line))
            # question.append(json.loads(line)['question'])
            
for query in tqdm.tqdm(raw_question,total=len(raw_question)):

    retrieval_query, raw_words = query_keyword_map.question_to_keywords_with_raw_words(query['question'])
    retrieval_query = retrieval_query.split(' ')
    retrieval_query.append('公司名称')
    retrieval_query.append('注册地址')
    retrieval_query.append('年份')
    prompt = f"""你是一个自然语言到SQL转换专家，你的任务是将金融领域问题，转换成对应的SQL查询：生成结果只含SQL语句。
        问题: {query['question']}
        """
    prompt+= "查询需要用到的数据库以及对应的字段如下："
    prompt += f"""表{1}: fin_report, 可用字段: {retrieval_query}"""
    prompt += "SQL查询:"
    prompt_group.append({'question':query['question'],'prompt':prompt,'id':query['id']})
    # break

response_group = []
batch_size=1
for prompt in tqdm.tqdm(prompt_group,total=len(prompt_group)):
    response = model.chat(tokenizer, prompt['prompt'],history=[], temperature=0.01)
    sql = re.sub(r"注册地址='(.*?)'", replace_func, response[0])
    
    response_group.append({'query':prompt['question'],'sql':sql, 'id':prompt['id']})

# with open(sql_res_path,'w',encoding='utf-8') as f:
#     for response in response_group:
#         f.write(json.dumps(response,ensure_ascii=False)+'\n')

df = pd.DataFrame(response_group)
df.to_csv(sql_res_path, index=False)


del model
torch.cuda.empty_cache()

# Force garbage collector to release unused memory
gc.collect()