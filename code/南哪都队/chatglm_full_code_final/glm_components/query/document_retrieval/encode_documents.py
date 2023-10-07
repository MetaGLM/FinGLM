from transformers import AutoModel, AutoTokenizer
import json
import faiss
import numpy as np
import torch
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import regex as re


def load_model():
    model_path = "model/sn-xlm-roberta-base-snli-mnli-anli-xnli"
    model = AutoModel.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = model.cuda()
    return model, tokenizer


def load_all_sentences():
    json_data = [json.loads(line) for line in open("documents/open_questions_annotated.txt", 'r', encoding='utf8').readlines()]
    keyword_mapping = {}
    for data in json_data:
        keyword_mapping[data['问题']] = data['关键词']
    return keyword_mapping, list(keyword_mapping.keys())


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


def get_cluster_embeddings(global_embeddings, index_cluster_id_mapping):
    index_mapping_list = np.array([index_cluster_id_mapping[idx] for idx in range(len(index_cluster_id_mapping))])
    max_index = max(index_mapping_list)
    emb_list = []
    for i in range(max_index + 1):
        emb_list.append(global_embeddings[index_mapping_list == i, :].mean(0)[np.newaxis, :])
    return np.concatenate(emb_list, axis=0)


def common_conversation(message, history):
    text = ""
    idx = 0
    for idx, hist in enumerate(history):
        text += f"[Round {idx+1}]\n\n问:{hist[0]}\n\n答：{hist[1]}"
    text += f"[Round {idx+2}]\n\n问:{message}\n\n答："
    return text


def get_question_searcher():
    mapping, sentences = load_all_sentences()
    sentence_cluster_id_mapping = {}
    sentence_index_cluster_id_mapping = {}
    sentence_clusters = defaultdict(lambda :[])
    keyword_set = set()
    keyword_cluster_id_mapping = {}
    for idx, sentence in enumerate(sentences):
        key = tuple(mapping[sentence]) 
        if key not in keyword_set:
            keyword_set.add(key)
            keyword_cluster_id_mapping[key] = len(keyword_cluster_id_mapping)
        sentence_cluster_id_mapping[sentence] = keyword_cluster_id_mapping[key]
        sentence_index_cluster_id_mapping[idx] = keyword_cluster_id_mapping[key]
        sentence_clusters[idx].append(sentence)
    global_embeddings = batch_encode_sentence(sentences)
    # cluster_embeddings = get_cluster_embeddings(global_embeddings, sentence_index_cluster_id_mapping)
    prompt = "提取出以下句子中的关键词："
    def inner(sentence, k=10):
        embedding = batch_encode_sentence([sentence])
        max_indices = np.argsort(-cosine_similarity(embedding, global_embeddings)[0])
        cluster_count = defaultdict(lambda :0)
        filtered_max_indices = []
        for index in max_indices:
            if k == 0:
                break
            if cluster_count[sentence_index_cluster_id_mapping[index]] < 1:
                cluster_count[sentence_index_cluster_id_mapping[index]] += 1
                filtered_max_indices.append(index)
                k -= 1
            else:
                continue
        target_sentences = [np.random.choice(sentence_clusters[index], 1)[0] for index in filtered_max_indices]
        target_keywords = [mapping[sen] for sen in target_sentences]
        history = [[prompt + sentence, '\n'.join(keywords)] for sentence, keywords in zip(target_sentences, target_keywords)]
        message = sentence
        return common_conversation(prompt + message, reversed(history))
    return inner



def neutralize_question(retrieved_info, question):
    year_pattern = r"(2019|2020|2021)年度?"
    brackets_pattern = r'[\(（\)）]'
    # question = retrieved_info['问题']
    company = retrieved_info['公司名称']
    company = re.sub(brackets_pattern, "", company)
    question = re.sub(brackets_pattern, "", question)
    question = question.replace(company, "{company}")
    question = re.sub(year_pattern, "{year}", question)
    return question


if __name__ == '__main__':
    # mapping, sentences = load_all_sentences()
    # batch_encode_sentence(sentences)
    searcher = get_question_searcher()
    text = searcher("请简要分析台海玛努尔核电设备股份有限公司2021年的审计报告中的关键审计事项。")
    print(text)