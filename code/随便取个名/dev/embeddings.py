from sentence_transformers import SentenceTransformer, util
import re
from typing import List
import ast
import json
import numpy as np
import multiprocessing
import os
CHUNK_SIZE = 500

##merge
def get_text(file_path):
    text = ""
    with open(file_path) as f:
        lines = f.readlines()
        last_line = ''
        excel_flag = 0
        for line in lines:
            line = re.sub(r'<Page:(\d+)>',r'\1',line)
            line_dict = ast.literal_eval(line)
            if line_dict['inside'].endswith("财务报告"):
                #print(line_dict['inside'])
                text = text + last_line
                break
            if (line_dict['type'] == 'text' and excel_flag == 0) or (line_dict['type'] == 'excel' and excel_flag == 1):
                text = text + last_line
            elif  line_dict['type'] == 'excel' and excel_flag == 0:
                text = text + '\n' + last_line
                excel_flag = 1
            elif line_dict['type'] == 'text' and excel_flag == 1:
                text = text + last_line + '\n'
                excel_flag = 0
            if line_dict['type'] == 'excel':
                excel_row = ast.literal_eval(line_dict['inside'])
                last_line = ''
                for it in excel_row:
                    it.replace(' ', '')
                    if len(it) > 0:
                        last_line = last_line + ',' + it
                last_line = last_line[1:]
            elif line_dict['type'] == 'text':
                last_line = line_dict['inside']
    return text

##short pattern
def split_text_short(text: str) -> List[str]:
    text = re.sub(r'(\.{6,})(\d+)', "\n", text)  # 目录和页码
    text = re.sub(r'([;；!?。！？\?])([^”’])', r"\1\n\2", text)  # 单字符断句符
    # text = re.sub(r'(\.{6})([^"’”」』])', r"\1\n\2", text)  # 英文省略号
    text = re.sub(r'(\…{2})([^"’”」』])', r"\1\n\2", text)  # 中文省略号
    # text = re.sub(r'([;；!?。！？\?]["’”」』]{0,2})([^;；!?，。！？\?])', r'\1\n\2', text) # 分号
    # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
    text = text.rstrip("\n")  # 段尾如果有多余的\n就去掉它
    ls = [i for i in text.split("\n") if i]
    for ele in ls:
        if len(ele) > CHUNK_SIZE:
            ele1 = re.sub(r'([，]["’”」』]{0,2})([^，])', r'\1\n\2', ele)
            ele1_ls = ele1.split("\n")
            for ele_ele1 in ele1_ls:
                if len(ele_ele1) > CHUNK_SIZE:
                    ele_ele2 = re.sub(r'([\n]{1,}| {2,}["’”」』]{0,2})([^\s])', r'\1\n\2', ele_ele1)
                    ele2_ls = ele_ele2.split("\n")
                    for ele_ele2 in ele2_ls:
                        if len(ele_ele2) > CHUNK_SIZE:
                            ele_ele3 = re.sub('( ["’”」』]{0,2})([^ ])', r'\1\n\2', ele_ele2)
                            ele2_id = ele2_ls.index(ele_ele2)
                            ele2_ls = ele2_ls[:ele2_id] + [i for i in ele_ele3.split("\n") if i] + ele2_ls[
                                                                                                    ele2_id + 1:]
                    ele_id = ele1_ls.index(ele_ele1)
                    ele1_ls = ele1_ls[:ele_id] + [i for i in ele2_ls if i] + ele1_ls[ele_id + 1:]

            id = ls.index(ele)
            ls = ls[:id] + [i for i in ele1_ls if i] + ls[id + 1:]
    return ls

###cal vector and save
def get_vector(paths):
    file_path = paths[0]
    save_path = paths[1]
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    vector_path = os.path.join(save_path, 'vector.npy')
    sentence_path = os.path.join(save_path, 'sentence.json')
    
    if os.path.exists(sentence_path) and os.path.exists(vector_path):
        # print(f'save_path exist: {save_path}')
        return
    
    text = get_text(file_path)
    sentences = split_text_short(text)

    #Sentences are encoded by calling model.encode()
    model = SentenceTransformer('moka-ai/m3e-base')
    embeddings = model.encode(sentences)
    #save file
    np.save(vector_path, embeddings)
    with open(sentence_path, 'w', encoding='utf-8') as f:
        json.dump(sentences, f, ensure_ascii=False)

def find_top5(folderpath, question):#filepath是txt文件的路径，包含txt文件名，folderpath是table/公司名_年份
    txt_path = 'data/alltxt/'
    tmp = folderpath.split('/')[-1]
    for x in os.listdir(txt_path):
        if tmp in x:
            filepath = os.path.join(txt_path, x)
            break
    vector_path = os.path.join(folderpath, 'vector.npy')
    sentence_path = os.path.join(folderpath, 'sentence.json')
    #loadfile
    if os.path.exists(sentence_path) and os.path.exists(vector_path):
        pass
    else:
        get_vector([filepath,folderpath])
    
    with open(sentence_path,'r',encoding='utf-8') as fd:
        read_sentense = json.load(fd)
    read_vector = np.load(vector_path)

    model = SentenceTransformer('moka-ai/m3e-base')

    q_embeddings = model.encode(question)
    #print(len(q_embeddings[0]))

    cosine_scores = util.cos_sim(read_vector, q_embeddings).tolist()
    sentence_cosine = sorted(zip(enumerate(read_sentense), cosine_scores), key=lambda x:x[1], reverse=True)
    i = 0
    context = []
    for group, score in sentence_cosine:
        if i == 5:
            break
        i = i + 1
        # print("Sentence:", sentence)
        # print("cosine score:", score)

        # extract from left
        pivot_idx = group[0]
        left_context_window = read_sentense[pivot_idx]
        cur_idx = pivot_idx
        while cur_idx - 1 > 0 and len(read_sentense[cur_idx - 1]) + len(left_context_window) < 500:
            left_context_window = read_sentense[cur_idx - 1] + left_context_window
            cur_idx -= 1

        context_window = left_context_window
        cur_idx = pivot_idx
        while cur_idx + 1 < len(read_sentense) and len(read_sentense[cur_idx + 1]) + len(context_window) < 1000:
            context_window += read_sentense[cur_idx + 1] 
            cur_idx += 1

        context.append(context_window)
    return context

if __name__ == '__main__':
    tablepath = 'data/tables/'
    txtpath = 'data/alltxt/'
    dir_list = []
    with open('data/list-pdf-name.txt', 'r', encoding='utf-8') as f:
        for line in f.readlines():
            dir_list.append(line.replace("\n", "").replace(".pdf", '.txt'))

    count = 0
    amount = 0
    txt_list = [[os.path.join(txtpath, x), os.path.join(tablepath, x.split('__')[3] + '__' + x.split('__')[4])] for x in dir_list if re.match('20.*txt', x)]
    #print(txt_list[1])
    with multiprocessing.Pool(processes=4) as pool:
        pool.map(get_vector, txt_list)
    
    
    # test on find_top
    # ret = find_top5('./data/tables/TCL科技__2019年', question="能否简要介绍公司报告期内研发投入的详情")
    # print(ret)