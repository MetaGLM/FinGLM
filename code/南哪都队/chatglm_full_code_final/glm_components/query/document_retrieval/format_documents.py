import os
from pathlib import Path
import json
from tqdm import tqdm
import regex as re
import cn2an
from collections.abc import Iterable
import Levenshtein
from .encode_documents import batch_encode_sentence, load_model
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import torch


def load_filename_mapping():
    mapping_dict = {}
    for file in Path("data/alltxt").rglob("*.txt"):
        filename = os.path.basename(file)
        _, full_name, stock_code, short_name, year, _ = filename.split("__")
        mapping_dict[(stock_code, int(year.replace("年", "")))] = filename
    return mapping_dict    

file_name_mapping = load_filename_mapping()


def get_context(file, filter_words=None):
    if filter_words is None:
        filter_words = []
    txt_folder = "data/alltxt"
    context_found = False
    context_end = False
    context_page = -1
    context_lines = []
    context_titles = []
    context_patterns = [
        r"^[0-9\s]{0,3}?第[一二三四五六七八九十零壹贰叁肆伍陆柒捌玖拾零\s]{1,4}[节章]、?·?([\u4e00-\u9fa5、]+)[^\u4e00-\u9fa5]*",
        r"^[0-9\s]{0,3}?[一二三四五六七八九十\s]{1,4}、·?([\u4e00-\u9fa5、]+)[^\u4e00-\u9fa5]*",
        r"^[0-9\s]{0,2}\.?([\u4e00-\u9fa5、]+)[·.…]*[0-9]{1,4}|(错误！未定义书签。)",
        r"^[0-9\s]{1,3}([\u4e00-\u9fa5、]+)$"
    ]
    non_context_lines = []
    for line in open(os.path.join(txt_folder, file), 'r', encoding='utf8').readlines():
        try:
            json_data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "inside" not in json_data:
            continue
        if not context_found and json_data['inside'] == "目录": 
            context_found = True
            context_page = json_data['page']
            continue
        if context_found and not context_end:
            if json_data['type'] != 'text' or json_data['inside'].strip() in ["", "\\l-"]:
                continue
            if json_data['type'] == '页脚' or json_data['page'] != context_page:
                context_end = True
            else:
                for context_pattern in context_patterns:
                    json_data['inside'] = re.sub(r"^_Toc[0-9]+", "", json_data['inside'])
                    context_lines.append(json_data['inside'])
                    matched = re.findall(context_pattern, json_data['inside'])
                    if len(matched) > 0:
                        if not isinstance(matched[0], str):
                            matched_str = matched[0][0]
                        else:
                            matched_str = matched[0]
                        context_titles.append(matched_str)
                        break
        else:
            if json_data['inside'] != "" and json_data['type'] != '页脚' and json_data['type'] != '页眉':
                non_context_lines.append(json_data)
    if len(context_titles) > 0:
        return context_titles, non_context_lines
    return [], non_context_lines


def split_with_context(file, filter_words=None):
    context_titles, report_lines = get_context(file, filter_words)
    if len(context_titles) < 8:
        return transform_to_documents(split_sub_chunk(report_lines))
    context_patterns = [
        r"^[0-9\s]{0,3}?第[一二三四五六七八九十零壹贰叁肆伍陆柒捌玖拾零\s]{1,4}[节章]、?·?([\u4e00-\u9fa5、]+)\s*$",
        r"^[0-9\s]{0,3}?[一二三四五六七八九十\s]{1,4}、·?([\u4e00-\u9fa5、]+)\s*$",
        r"^[0-9\s]{0,2}\.?([\u4e00-\u9fa5、]+)\s*$",
        r"^[0-9\s]{1,3}([\u4e00-\u9fa5、]+)\s*$"
    ]
    found_index = 0

    def check_valid(title, target):
        title = title.replace("、", "")
        target = target.replace("、", "")
        if len(title) >= 4:
            return Levenshtein.distance(title, target) <= 2
        else:
            if len(title) > len(target):
                return target in title
            else:
                return title in target
    chunks = {}
    last_matched = None
    for line in report_lines:
        if found_index >= len(context_titles):
            break
        if line['type'] == 'text':
            text = line['inside']
            found = False
            for pattern in context_patterns:
                matched = re.findall(pattern, text)
                if len(matched) > 0:
                    title = matched[0]
                    if check_valid(title, context_titles[found_index]):
                        found_index += 1
                        chunks[title] = []
                        last_matched = title
                        found = True
                    break
            if found:
                continue

        if last_matched is not None:
            chunks[last_matched].append(line)
    
    if len(context_titles) - found_index <= 2:
        for k, v in chunks.items():
            chunks[k] = split_sub_chunk(v)
        return transform_to_documents(flatten_chunk(chunks))
    else:
        return transform_to_documents(split_sub_chunk(report_lines))


def flatten_chunk(chunks):
    structured_documnts = {}
    for k, v in chunks.items():
        structured_documnts[k] = v['']
        v.pop('')
        structured_documnts.update(v)
    return structured_documnts


def split_sub_chunk(documents):
    chapter_title_pattern = r'([\(（][①-⑩a-zA-Z一二三四五六七八九十零壹贰叁肆伍陆柒捌玖拾零0-9]{1,3}[\)）]|[①-⑩a-zA-Z一二三四五六七八九十零壹贰叁肆伍陆柒捌玖拾零0-9]{1,3})[、.]?([\u4e00-\u9fa55GIP2019][\u4e00-\u9fa5、5GIP2019\(\)（）]{1,31})$'
    # invalid_chunk_pattern = r"(单位|元|无)"
    last_title = ''
    structured_documents = {'':[]}
    for document in documents:
        if document['type'] == 'text':
            # if re.match(chapter_title_pattern_without_cn_constraint, document['inside']) \
            matched = re.match(chapter_title_pattern, document['inside'])
            if matched:
                last_title = matched[-1]
                structured_documents[last_title] = []
                continue
        structured_documents[last_title].append(document)
    return structured_documents            


def transform_to_documents(flatten_documents):
    for k, v in flatten_documents.items():
        flatten_documents[k] = ['\t'.join(eval(line['inside'])) if line['type'] == 'excel' else line['inside'] for line in v]
    for k in list(flatten_documents.keys()):
        if len(flatten_documents[k]) == 0:
            flatten_documents.pop(k)
    return flatten_documents


def prepare_multi_process():
    from multiprocess import Pool
    failed_cnt = 0
    async_results = []
    pool = Pool(24)
    for file in tqdm(file_name_mapping.values()):
        async_results.append(pool.apply_async(split_with_context, (file,)))
    for idx, res in enumerate(tqdm(async_results)):
        async_results[idx] = res.get()
    pool.close()
    pool.join()
    print(sum([item * 1 for item in async_results]))



def crop_prompt(retrieved_content, max_length=4096):
    if sum(len(s) for s in retrieved_content) < max_length:
        return "\n".join(reversed(retrieved_content))
    if len(retrieved_content) == 1:
        return retrieved_content[:max_length]
    if len(retrieved_content) == 2:
        weight = [1, 1/3]
    elif len(retrieved_content) == 3:
        weight = [1, 1/3, 1/4]
    remained_length = max_length
    content_list = []
    for content, w in zip(reversed(retrieved_content), reversed(weight)):
        target_length = int(w * remained_length)
        content = content[:target_length]
        remained_length -= len(content)
        content_list.append(content)
    return '\n\n'.join(content_list)



def get_document_searcher(file, model=None, tokenizer=None):
    # document_path = os.path.join("documents/formatted_documents", file)
    # if os.path.exists(document_path):
    #     chunks = json.load(open(document_path, 'r'))
    # else:
    chunks = split_with_context(file)
    # json.dump(chunks, open(document_path, 'w'), ensure_ascii=False)
    titles = list(chunks.keys())
    # vector_path = os.path.join("documents/title_vectors", file.replace(".txt", ".pt"))
    # if os.path.exists(vector_path):
    #     title_embeddings = torch.load(open(vector_path, 'rb'))
    # else:
    title_embeddings = batch_encode_sentence(titles, model=model, tokenizer=tokenizer)
    # torch.save(title_embeddings, open(vector_path, 'wb'))

    def search(keyword):
        key_emb = batch_encode_sentence([keyword], model=model, tokenizer=tokenizer)
        max_score_indices = np.argsort(-cosine_similarity(key_emb, title_embeddings)[0])[:3]
        matched_titles = []
        for index in max_score_indices:
            if len(set(titles[index]) & set(keyword)) >= 2:
                matched_titles.append(titles[index])
            else:
                break
        if len(matched_titles) == 0:
            return ""
        content_list = []
        for title in matched_titles:
            content_chunk = '\n'.join(chunks[title])
            content_list.append(f"{title}:\n{content_chunk}")
        return crop_prompt(content_list)

    return search



if __name__ == '__main__':
    # prepare_multi_process()
    model, tokenizer = load_model()
    for file in tqdm(list(file_name_mapping.values())):
        if file == "2022-06-08__台海玛努尔核电设备股份有限公司__002366__台海核电__2021年__年度报告.txt":
            searcher = get_document_searcher(file, model, tokenizer)
            print(searcher("关键审计事项"))