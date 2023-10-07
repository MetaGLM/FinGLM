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
import re
import config

print("开始预测")
model_dir=config.MODEL_DIR
embedding_model_name = config.EMBEDDING_MODEL
test_path = config.QUESTION_PATH
company_path = 'output/company/company.json'
fullname_shortname_path = 'output/company/fullname_shortname.json'
years = ['2019','2020','2021','2022']
text_vector_path = "output/vector"
title_vector_path = 'output/title_vector'

test_questions = open(test_path).readlines()
question_list = []
for test_question in test_questions:
    question = json.loads(test_question)
    question_list.append(question)

fout = open(config.OUT_DIR, 'w', encoding='utf8')
# #加载chaglm
tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
model = AutoModel.from_pretrained(model_dir, trust_remote_code=True).cuda()
model.eval()






count = 0
no_prompt_question = []

result_dict = defaultdict(list)

for row_question in tqdm(question_list):
    # if ii != 4625:
    #     continue
    question = row_question['question']
    answer, history = model.chat(tokenizer, question, history=[])
    print(question,answer)
    fout.write(json.dumps(row_question, ensure_ascii=False) + "\n")
    #     # 释放缓存
    torch.cuda.empty_cache()
    gc.collect()


