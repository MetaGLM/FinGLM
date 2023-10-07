import os
import json
import re
import itertools
from loguru import logger
from difflib import SequenceMatcher
from fastbm25 import fastbm25

from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.retrievers import MultiQueryRetriever

import re_util
from config import cfg
from file import load_pdf_pages


def merge_idx(indexes, total_len, prefix=0, suffix=1):
    merged_idx = []
    for index in indexes:
        start = max(0, index-prefix)
        end = min(total_len, index+suffix+1)
        merged_idx.extend([i for i in range(start, end)])
    merged_idx = sorted(list(set(merged_idx)))

    block_idxes = []

    if len(merged_idx) == 0:
        return block_idxes

    current_block_idxes = [merged_idx[0]]
    for i in range(1, len(merged_idx)):
        if merged_idx[i] - merged_idx[i-1] > 1:
            # block = [lines[idx] for idx in current_block_idxes]
            # text_blocks.append('\n'.join(block))
            block_idxes.append(current_block_idxes)
            current_block_idxes = [merged_idx[i]]
        else:
            current_block_idxes.append(merged_idx[i])
    if len(current_block_idxes) > 0:
        block_idxes.append(current_block_idxes)

    return block_idxes


# def get_exact_match(query, lines, prefix=5, suffix=10, topk=3):
#     matched_idxes = []
#     for line_idx, line in enumerate(lines):
#         overlap_words = list(set(query) & set(line))
#         overlap_ratio = len(overlap_words) / len(query)
#         matched_idxes.append((line_idx, overlap_ratio))
#         # start = max(0, line_idx-prefix)
#         # end = min(len(lines), line_idx+suffix)
#         # matched_idxes.extend([i for i in range(start, end)])
#     matched_idxes = sorted(matched_idxes, key=lambda x: x[1], reverse=True)[:topk]
#     matched_idxes = [idx for idx, _ in matched_idxes]
#     merged_idx = merge_idx(matched_idxes, len(lines), prefix, suffix)

#     text_blocks = []

#     if len(merged_idx) == 0:
#         return text_blocks

#     current_block_idxes = [merged_idx[0]]
#     for i in range(1, len(merged_idx)):
#         if merged_idx[i] - merged_idx[i-1] > 1:
#             block = [lines[idx] for idx in current_block_idxes]
#             text_blocks.append('\n'.join(block))
#             current_block_idxes = [merged_idx[i]]
#         else:
#             current_block_idxes.append(merged_idx[i])
#     if len(current_block_idxes) > 0:
#         block = [lines[idx] for idx in current_block_idxes]
#         text_blocks.append('\n'.join(block))
        
#     return text_blocks


def recall_annual_report_texts(question, key, embeddings: HuggingFaceEmbeddings):
    text_blocks = []
    
    # text_lines = load_pdf_text(key)
    text_pages = load_pdf_pages(key)
    for idx, page in text_pages:
        overlap_words = list(set(question) & set(page))
        text_blocks.append((page, overlap_words))

    text_blocks = sorted(text_blocks, key=lambda x: len(x[1]), reverse=True)
    text_blocks = [text_block[0] for text_block in text_blocks[:3]]
    return text_blocks



# def recall_annual_report_texts(question, key, embeddings: HuggingFaceEmbeddings):
#     text_blocks = []
    
#     # text_lines = load_pdf_text(key)
#     text_pages = load_pdf_pages(key)
    
#     docs = [Document(page_content=page, metadata={}) for page in text_pages]
    
#     if len(docs) == 0:
#         return text_blocks
    
#     vector_store_path = os.path.join(cfg.DATA_PATH, 'pdf_docs', key, 'vector_store')
#     # if os.path.exists(vector_store_path):
#         # logger.info('{} exists'.format(vector_store_path))
#         # vector_store = FAISS.load_local(vector_store_path, embeddings)
#     # else:
#     vector_store = FAISS.from_documents(docs, embeddings)
#     vector_store.save_local(vector_store_path)

#     sim_docs = vector_store.similarity_search(question, k=3)
#     text_blocks = [sim_doc.page_content for sim_doc in sim_docs]

#     # sim_index = []
#     # for sim_doc in sim_docs:
#     #     sim_index.append(sim_doc.metadata['index'])
#     # merged_idx = merge_idx(sim_index, len(text_lines), 10, 10)
 
#     # text_blocks = []

#     # if len(merged_idx) == 0:
#     #     return text_blocks

#     # current_block_idxes = [merged_idx[0]]
#     # for i in range(1, len(merged_idx)):
#     #     if merged_idx[i] - merged_idx[i-1] > 1:
#     #         block = [text_lines[idx]['text'] for idx in current_block_idxes]
#     #         text_blocks.append('\n'.join(block))
#     #         current_block_idxes = [merged_idx[i]]
#     #     else:
#     #         current_block_idxes.append(merged_idx[i])
#     # if len(current_block_idxes) > 0:
#     #     block = [text_lines[idx]['text'] for idx in current_block_idxes]
#     #     text_blocks.append('\n'.join(block))

#     return text_blocks


def filter_header_footer(text_block):
    lines = text_block.split('\n')
    lines = [line for line in lines if not re_util.is_header_footer(line)]
    return '\n'.join(lines)


# top2 5 25 84.5085
# def recall_annual_report_texts(anoy_question: str, keywords: str, key, embeddings: HuggingFaceEmbeddings):
#     anoy_question = re.sub(r'(公司|年报|根据|数据|介绍)', '', anoy_question)
#     logger.info('anoy_question: {}'.format(anoy_question.replace('<', '')))

#     text_pages = load_pdf_pages(key)
#     text_lines = list(itertools.chain(*[page.split('\n') for page in text_pages]))
#     text_lines = [line for line in text_lines if len(line) > 0]
#     if len(text_lines) == 0:
#         return []
#     model = fastbm25(text_lines)
#     # result_question = model.top_k_sentence(anoy_question, k=1)
#     result_keywords = model.top_k_sentence(keywords, k=1)
#     result_question = []
#     top_match_indexes = [t[1] for t in result_question + result_keywords]
#     block_line_indexes = merge_idx(top_match_indexes, len(text_lines), 0, 40)
#     text_blocks = ['\n'.join([text_lines[idx] for idx in line_indexes]) for line_indexes in block_line_indexes]
#     text_blocks = [filter_header_footer(text_block) for text_block in text_blocks]
#     text_blocks = [re.sub(' {3,}', '\t', text_block) for text_block in text_blocks]
#     text_blocks = [t[:1500] if len(t) > 1500 else t for t in text_blocks]
#     text_blocks = ['```\n{}\n```'.format(t) for t in text_blocks]
#     return text_blocks


def recall_annual_report_texts(glm_model, anoy_question: str, keywords: str, key, embeddings: HuggingFaceEmbeddings):
    anoy_question = re.sub(r'(公司|年报|根据|数据|介绍)', '', anoy_question)
    logger.info('anoy_question: {}'.format(anoy_question.replace('<', '')))

    text_pages = load_pdf_pages(key)
    text_lines = list(itertools.chain(*[page.split('\n') for page in text_pages]))
    text_lines = [line for line in text_lines if len(line) > 0]
    if len(text_lines) == 0:
        return []
    model = fastbm25(text_lines)
    result_keywords = model.top_k_sentence(keywords, k=3)
    result_question = model.top_k_sentence(anoy_question, k=3)
    top_match_indexes = [t[1] for t in result_question + result_keywords]
    block_line_indexes = merge_idx(top_match_indexes, len(text_lines), 0, 30)
    
    text_blocks = ['\n'.join([text_lines[idx] for idx in line_indexes]) for line_indexes in block_line_indexes]
    # text_blocks = [filter_header_footer(text_block) for text_block in text_blocks]
    text_blocks = [re.sub(' {3,}', '\t', text_block) for text_block in text_blocks]
    
    text_blocks = [(t, SequenceMatcher(None, anoy_question, t, autojunk=False).find_longest_match().size) for t in text_blocks]
    for text_block, match_size in text_blocks:
        match = SequenceMatcher(None, anoy_question, text_block, autojunk=False).find_longest_match()
        print(anoy_question[match.a: match.a + match.size])
    max_match_size = max([t[1] for t in text_blocks])
    text_blocks = [t[0] for t in text_blocks if t[1] == max_match_size]
    
    if sum([len(t) for t in text_blocks]) > 2000:
        max_avg_len = int(2000 / len(text_blocks))
        text_blocks = [t[:max_avg_len] for t in text_blocks]

    text_blocks = [rewrite_text_block(t) for t in text_blocks]
    text_blocks = ['```\n{}\n```'.format(t) for t in text_blocks]
    return text_blocks


def rewrite_text_block(text):
    for word in ['是', '否', '适用', '不适用']:
        text = text.replace('□{}'.format(word), '')
    return text


def recall_annual_names(question):
    pass




if __name__ == '__main__':
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from chinese_text_splitter import ChineseTextSplitter
    from langchain.document_loaders import TextLoader
    from langchain.vectorstores import FAISS
    from config import cfg
    from file import load_embedding, load_pdf_info

    # embeddings = load_embedding()


    # key = '2021-04-30__顾家家居股份有限公司__603816__顾家家居__2020年__年度报告.pdf'

    # query = '销售费用和管理费用分别是多少元？'
    
    # recall_annual_report_texts(query, key, embeddings)

    pdf_info = load_pdf_info()

    for key in pdf_info.keys():
        print(key)
        load_pdf_text(key)