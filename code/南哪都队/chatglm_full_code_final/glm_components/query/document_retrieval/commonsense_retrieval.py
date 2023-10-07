import json
import jieba
from snownlp.sim.bm25 import BM25
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(__file__))
from new_format_document import flatten_doc
from tqdm import tqdm

excel = json.load(open('data/retrieval_result.json', 'r', encoding='utf-8'))
key_list = list(excel.keys())
stop_list = ['什么', '是', '指', '是指', '意思', '影响', '属于', '年报', '请', '简要', '介绍', '，', '？', '。', '如何', '定义']

def rm_stopwords(sentence):
    for token in stop_list:
        while token in sentence:
            sentence.remove(token)
    return sentence

key_corpus = [rm_stopwords(jieba.lcut(name)) for name in key_list]
model = BM25(key_corpus)



def retrieve(question, max_length = 8192-512):
    question = rm_stopwords(jieba.lcut(question))
    neg_sim_list = -np.array(model.simall(question))
    index_list = np.argsort(neg_sim_list)[0:3]
    res = []
    
    for idx in index_list:
        if (sim := neg_sim_list[idx]) == 0:
            break
        key = key_list[idx]
        doc = flatten_doc(excel[key], str(key)+'：') + '\n'
        len_doc = len(doc)
        if max_length>len_doc:
            max_length -= len_doc
            res.append(doc)
        else:
            if not res:
                res.append(doc[:max_length])
            break
    return '\n'.join(res[::-1])

if __name__ == '__main__':
    problems = []
    problems_file = open('data/C-list-question.json', 'r', encoding='utf-8')
    for line in problems_file.readlines():
        line = line.rstrip()
        problems.append(eval(line))

    res = []
    for problem in tqdm(problems):
        problem = problem['question']
        if '2019' in problem or '2020' in problem or '2021' in problem:
            continue
        doc = retrieve(problem, 8192-512)
        res.append({'question': problem, 'retrieved': doc})
    with open('retrieval_result.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent = 4)