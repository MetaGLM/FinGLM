import json
import os
from transformers import AutoModel, AutoTokenizer
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from copy import deepcopy
from tqdm import tqdm
import re

from snownlp.sim.bm25 import BM25
import jieba

# os.environ["CUDA_VISIBLE_DEVICES"] = '0'
json_folder = 'data/list_json'
classification_result = json.load(open('company_infos.jsonl', 'r', encoding='utf-8'))
problem_path = 'data/C-list-question.json'
problems = open(problem_path, 'r', encoding='utf-8')
excel_folder = 'data/processed_excels'
MAX_LENGTH = 8192-512

stop_list = ['情况']

def load_model():
    model_path = "model/sn-xlm-roberta-base-snli-mnli-anli-xnli"
    model = AutoModel.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = model.cuda()
    return model, tokenizer

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def batch_encode_sentence(sentences, batch_size=128, model=None, tokenizer=None):
    if model is None or tokenizer is None:
        model, tokenizer = load_model()
    model.eval()
    emb_list = []
    with torch.no_grad():
        for chunk in range(0, int(np.ceil(len(sentences)/batch_size)), 1):
            batch_data = sentences[chunk*batch_size:(chunk+1)*batch_size]
            encoded = tokenizer.batch_encode_plus(batch_data, truncation=True, padding=True, max_length=128, return_tensors='pt', return_attention_mask=True)
            encoded = encoded.to("cuda")
            encoded_emb = model(**encoded)
            emb_list.append(mean_pooling(encoded_emb, encoded['attention_mask']))
    if len(emb_list) > 0:
        return torch.cat(emb_list, dim=0).cpu().numpy()
    else:
        return np.zeros([0, 768])
    
def find_dict_idx(mixed_list):
    for idx, e in enumerate(mixed_list):
        if isinstance(e, dict):
            return idx
    else:
        return -1

def rm_stopwords(sentence):
    for token in stop_list:
        while token in sentence:
            sentence = sentence.replace(token, '')
    return sentence

def rm_tokenized_stopwords(sentence):
    for token in stop_list:
        while token in sentence:
            sentence.remove(token)
    return sentence

def get_titles(title_dict, path, list_json):
    idx = find_dict_idx(list_json)
    if idx != -1:
        for k in list_json[idx]:
            if len(k) < 50:
                title_dict[k] = path+[k]
            title_dict = get_titles(title_dict, path+[k], list_json[idx][k])
    return title_dict

def remove_index(ele):
    template_1 = '(([0-9]*)|[一二三四五六七八九十]{1,3})[、\.,]'
    template_2 = '([\(（](([0-9]*)|[一二三四五六七八九十]{1,3})[\)）])'
    template_3 = '[、\.,]'
    
    def remove_template(template, str_):
        try:
            span = re.match(template, str_).span()
            str_ = str_.replace(str_[span[0]:span[1]], '')
        except AttributeError:
            pass
        return str_
    
    ele = remove_template(template_1, ele)
    ele = remove_template(template_2, ele)
    ele = remove_template(template_3, ele)
    return ele
    
def get_doc(list_json, path):
    while path:
        idx = find_dict_idx(list_json)
        list_json = list_json[idx][path[0]]
        path.pop(0)
    return list_json

def flatten_doc(list_json, res):
    for ele in list_json:
        if isinstance(ele, dict):
            for key in ele:
                res += str(key)
                res += '\n'
                res = flatten_doc(ele[key], res)
        elif isinstance(ele, list):
            flatten_list = ''
            for line in ele:
                line = eval(line)
                flatten_list += '\t'.join([str(e) for e in line])
                if '\t'*10 in flatten_list:
                    flatten_list = ''
                    for line in ele:
                        line = eval(line)
                        flatten_list += ' '.join([str(e) for e in line if e])
                        flatten_list += '\n'
                    break
                flatten_list += '\n'
            res += flatten_list
        elif ele:
            res += str(ele)
            #res += '\n'
    return res

def crop_context(relevant_doc_list, max_length):
    total_length = sum(len(doc) for doc in relevant_doc_list)
    if total_length > max_length:
        remaining_doc_list = []
        total_length = max_length
        for doc in relevant_doc_list:
            if len(doc) < total_length:
                total_length -= len(doc)
                remaining_doc_list.append(doc)
            else:
                remaining_doc_list.append(doc[:total_length])
                break
    else:
        remaining_doc_list = relevant_doc_list
    return remaining_doc_list

def normalize_keyword(keyword):
    if '诚信' in keyword:
        keyword = '控股股东、实际控制人的诚信状况'
    elif '控制人' in keyword:
        keyword = '实际控制人'
    elif '未来发展' in keyword:
        keyword = '发展规划'
    return keyword

def judge_validity(relevant_doc_list):
    if len(relevant_doc_list) == 0:
        return False
    elif len(relevant_doc_list) == 1:
        special_list = ['退市', '破产重整', '非标准审计报告', '重大诉讼、仲裁事项', '处罚及整改情况']
        for key in special_list:
            if key in relevant_doc_list[0]:
                if len(relevant_doc_list[0])<50:
                    return False
    return True

def parse_file_name(file_name):
    time, long_company_name, code, short_company_name, year, _ = file_name.split('__')
    year = year.replace('年', '')
    return long_company_name, code, short_company_name, year

class summarize_model():
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
    
    def switch_prefix_encoder(self):
        if self.model is None:
            model_path = "model/chatglm2-6b"
            self.model = AutoModel.from_pretrained(model_path, trust_remote_code=True).half()
            self.model = self.model.to("cuda")
        return self.model
    
    def predict_batch(self, batch_inputs):
        self.tokenizer.padding_side = "left"
        self.tokenizer.truncation_side = "left"
        inputs = self.tokenizer(batch_inputs, return_tensors="pt", max_length=8096, truncation=True, padding=True)
        inputs = inputs.to("cuda")
        outputs = self.model.generate(**inputs, max_new_tokens=2048, do_sample=True, temperature=0.95)
        response = self.tokenizer.batch_decode(outputs)
        response = [res[res.rindex("回答：")+3:].strip() for res in response][0]
        return response
    
    def summarize(self, document):
        prompt = '问题：现在我会给你一个从年报中获得的部分文本，这段信息文本很长，而且里面可能包含很多表格，请你对其中的关键信息进行概括总结，你的概括要尽可能详细，不能缺少内容，也不能编造内容，对于表格要尽可能地归纳出表格里传达的关键信息，不能简单地重复表格。\n文本信息如下：\n' + document + "回答："
        return self.predict_batch([prompt])

def get_document_searcher(filename, model=None, tokenizer=None, summarizer=None):
    list_json = json.load(open(os.path.join(json_folder, filename.replace(".txt", '.json')), 'r', encoding = 'utf-8'))
    title_dict = get_titles({}, [], list_json)
    titles = list(title_dict.keys())
    filtered_titles = [rm_stopwords(remove_index(title)) for title in titles]
    title_embeddings = batch_encode_sentence(filtered_titles, model=model, tokenizer=tokenizer)
    
    key_corpus = [rm_tokenized_stopwords(jieba.lcut(remove_index(name))) for name in titles]
    BM25_model = BM25(key_corpus)
    
    def search(keyword, keywords_num):
        max_length = MAX_LENGTH // keywords_num
        keyword = normalize_keyword(keyword)
        '''
        if keyword == '现金流':
            excel = json.load(open(os.path.join(excel_folder, filename.replace(".txt", ".json")), 'r', encoding = 'utf-8'))
            table = excel['合并现金流量表']
            res = '合并现金流量表：\n'
            for line in table:
                res += '\t'.join([str(ele) for ele in line])
            return ([res], [len(res)])
        '''    
        if not len(title_embeddings):
            return False
        key_emb = batch_encode_sentence([keyword], model=model, tokenizer=tokenizer)
        sorted_score_indices = np.argsort(-cosine_similarity(key_emb, title_embeddings)[0])
        max_score_indices = sorted_score_indices[:2]
        sorted_titles = [filtered_titles[index] for index in sorted_score_indices]
        matched_titles = []
        if len(keyword) <= 10:
            minimum_common_characters = max(len(keyword)//2, 2)
        else:
            minimum_common_characters = max(len(keyword)*3//4, 2)
        for index in max_score_indices:
            if len(set(filtered_titles[index]) & set(keyword)) >= minimum_common_characters:
                matched_titles.append(titles[index])
            else:
                continue
        if keyword == '董事、监事、高级管理人员变动情况':
            matched_titles = matched_titles[:1]
        relevant_json_list = [get_doc(deepcopy(list_json), title_dict[title]) for title in matched_titles]
        relevant_doc_list = [flatten_doc(rel, remove_index(title)+'：\n')+'\n' for rel, title in zip(relevant_json_list, matched_titles) \
            if len(flatten_doc(rel, remove_index(title))) >= 25]
        relevant_doc_list = crop_context(relevant_doc_list, max_length)
        if summarizer:
            for i in range(len(relevant_doc_list)):
                if len(relevant_doc_list[i])>600:
                    relevant_doc_list[i] = relevant_doc_list[i][:relevant_doc_list[i].find('：')] + '：' + summarizer.summarize(relevant_doc_list[i])
        len_list = [len(doc) for doc in relevant_doc_list]
        
        if not judge_validity(relevant_doc_list):
            print('Embedding empty retrieved:', keyword, filename)
            if len(matched_titles) == 0:
                embedding_retrieved = BM25_search(keyword, keywords_num)
                if embedding_retrieved:
                    relevant_doc_list, len_list = embedding_retrieved
                    return (relevant_doc_list, len_list)
                
            output_doc = str(keyword) + '：\n' + '本公司本年度经营状况良好，无重大经营风险，不存在与{}相关的内容。\n'.format(keyword)
            return ([output_doc], [len(output_doc)])
            #return False
        
        return (relevant_doc_list, len_list)

    def BM25_search(keyword, keywords_num):
        max_length = MAX_LENGTH // keywords_num
        keyword = normalize_keyword(keyword)
        '''
        if keyword == '现金流':
            excel = json.load(open(os.path.join(excel_folder, filename.replace(".txt", ".json")), 'r', encoding = 'utf-8'))
            table = excel['合并现金流量表']
            res = '合并现金流量表：\n'
            for line in table:
                res += '\t'.join([str(ele) for ele in line])
            return ([res], [len(res)])
        '''    
        if not len(key_corpus):
            return False

        tokenized_keyword = rm_tokenized_stopwords(jieba.lcut(keyword))
        neg_sim_list = -np.array(BM25_model.simall(tokenized_keyword))
        sorted_score_indices = np.argsort(neg_sim_list)
        max_score_indices = sorted_score_indices[:2]
        
        #key_emb = batch_encode_sentence([keyword], model=model, tokenizer=tokenizer)
        #sorted_score_indices = np.argsort(-cosine_similarity(key_emb, title_embeddings)[0])
        #max_score_indices = sorted_score_indices[:2]
        sorted_titles = [key_corpus[index] for index in sorted_score_indices]
        matched_titles = []
        if len(keyword) <= 10:
            minimum_common_characters = max(len(keyword)//2, 2)
        else:
            minimum_common_characters = max(len(keyword)*3//4, 2)
        for index in max_score_indices:
            if len(set(filtered_titles[index]) & set(keyword)) >= minimum_common_characters:
                matched_titles.append(titles[index])
            else:
                continue

        relevant_json_list = [get_doc(deepcopy(list_json), title_dict[title]) for title in matched_titles]
        relevant_doc_list = [flatten_doc(rel, remove_index(title)+'：\n')+'\n' for rel, title in zip(relevant_json_list, matched_titles) \
            if len(flatten_doc(rel, remove_index(title))) >= 25]
        relevant_doc_list = crop_context(relevant_doc_list, max_length)
        if summarizer:
            for i in range(len(relevant_doc_list)):
                if len(relevant_doc_list[i])>600:
                    relevant_doc_list[i] = relevant_doc_list[i][:relevant_doc_list[i].find('：')] + '：' + summarizer.summarize(relevant_doc_list[i])
        len_list = [len(doc) for doc in relevant_doc_list]
        
        if not judge_validity(relevant_doc_list):
            print('BM25 empty retrieved:', keyword, filename)
            return False
        
        return (relevant_doc_list, len_list)
    
    return search

def test_main():
    def find_filename(stock, year):
        try:
            for file in os.listdir(json_folder):
                if stock in file and year + '年' in file:
                    return file
        except:
            return False
        return False
    
    res = []
    
    model, tokenizer = load_model()
    
    GLM_tokenizer = AutoTokenizer.from_pretrained("model/chatglm2-6b", trust_remote_code=True)
    summarizer = summarize_model(None, GLM_tokenizer)
    summarizer.switch_prefix_encoder()
    
    for idx, line in tqdm(enumerate(problems.readlines())):
        line = line.rstrip()
        if classification_result[idx]['类型'] == '开放问题':
            current = {}
            problem = eval(line)["question"]
            keywords = classification_result[idx]["关键词"]
            stock_code = classification_result[idx]['股票代码']
            #if '600316' != stock_code:
            #    continue
            year = classification_result[idx]['年份'][0]
            current['problem'] = problem
            current['doc'] = {}
            if not (filename := find_filename(stock_code, year)):
                #print(problem)
                current['doc'] = '年报缺失' + str(stock_code)
                res.append(current)
                continue

            for keyword in keywords:
                if searcher_res := get_document_searcher(filename, model, tokenizer, summarizer)(keyword, len(keywords)):
                    (relevant_doc_list, len_list) = searcher_res
                    current['doc'][keyword] = [{'doc':doc, 'len': doc_len} for (doc, doc_len) in zip(relevant_doc_list, len_list)]
                else:
                    current['doc'][keyword] = []
                    
            current['公司名称'] = classification_result[idx]['公司名称']
            current['年份'] = classification_result[idx]['年份'][0]
            res.append(current)
        with open('retrieval_result.json', 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent = 4)

if __name__ == '__main__':
    test_main()
