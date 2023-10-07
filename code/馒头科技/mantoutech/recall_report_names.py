import re
from difflib import SequenceMatcher
from loguru import logger
from config import cfg

from langchain.vectorstores import FAISS


# def get_name_embedding(pdf_info, embeddings):
#     name_texts = ['{}{}'.format(v['abbr'], v['year'].replace('年', '')) for v in pdf_info.values()]
#     name_vectors = FAISS.from_texts(name_texts, embeddings)
#     return name_vectors


# def recall_overlap(question, pdf_info):
#     match_info = []
#     for k, v in pdf_info.items():
#         name_text = '{}{}{}'.format(v['company'], v['abbr'], v['year'])
#         overlap_text = set(question) & set(name_text)
#         match_info.append((k, overlap_text))

#     match_info = sorted(match_info, key=lambda x: len(x[1]), reverse=True)[:3]
#     logger.warning(match_info)
#     matched_names = [k for k, _ in match_info]
#     return matched_names


# def recall_semantic(question, embedding_vectors):
#     sim_texts = embedding_vectors.similarity_search_with_score(question, k=10)
#     sim_names = [sim_text.meta_data['key'] for sim_text, _ in sim_texts]
#     return sim_names


# def recall_annual_report_names(question, pdf_info: dict):
#     # match_info = []
#     # for k, v in pdf_info.items():
#     #     name_text = '{}{}{}'.format(v['company'], v['abbr'], v['year'])
#     #     overlap_text = set(question) & set(name_text)
#     #     match_info.append((k, overlap_text))

#     # match_info = sorted(match_info, key=lambda x: len(x[1]), reverse=True)[:3]
#     # logger.warning(match_info)
#     # match_info = [k for k, _ in match_info]

#     # sim_texts = embedding_vectors.similarity_search_with_score(question, k=10)
#     # for sim_text, sim_score in sim_texts:
#     #     print(sim_text.page_content, sim_score)
#     # return sim_texts

#     matched_names = recall_extact_match(question, pdf_info)
#     return matched_names


# def recall_pdf_names(company, year, pdf_info:dict):
#     matched_names = []
#     for k, v in pdf_info.items():
#         if company == v['company'] and year in v['year']:
#             matched_names.append(k)
#         elif company == v['abbr'] and year in v['year']:
#             matched_names.append(k)
#     return matched_names


def recall_pdf_tables(keywords, years, tables, valid_tables=None, invalid_tables=None, 
        min_match_number=3, top_k=None):
    logger.info('recall words {}'.format(keywords))
    
    # valid_keywords = re.sub('(公|司|的|主|要)', '', keywords)
    valid_keywords = keywords

    matched_lines = []
    for table_row in tables:
        table_name, row_year, row_name, row_value = table_row
        row_name = row_name.replace('"', '')
        if row_year not in years:
            continue
        # min_match_number = 2 if table_name in ['basic_info', 'employee_info'] else 3
        
        if valid_tables is not None and table_name not in valid_tables:
            continue

        if invalid_tables is not None and table_name in invalid_tables:
            continue
        
        # find exact match, only return this row
        if row_name == valid_keywords:
            matched_lines = [(table_row, len(row_name))]
            break

        tot_match_size = 0
        matches = SequenceMatcher(None, valid_keywords, row_name, autojunk=False)
        for match in matches.get_matching_blocks():
            inter_text = valid_keywords[match.a:match.a+match.size]
            # if match.size >= min_match_number or inter_text in ['存货']:
                # matched_lines.append(table_row)
                # break
            tot_match_size += match.size
        if tot_match_size >= min_match_number or row_name in valid_keywords:
            # print(table_row, tot_match_size)
            matched_lines.append([table_row, tot_match_size])
        # if len(matched_lines) > 0:
        #     # if name in ['basic_info', 'employee_info']:
        #     #     macthed_tables[name] = lines
        #     # else:
        #     macthed_tables[name] = matched_lines
    matched_lines = sorted(matched_lines, key=lambda x: x[1], reverse=True)
    matched_lines = [t[0] for t in matched_lines]
    if top_k is not None and len(matched_lines) > top_k:
        matched_lines = matched_lines[:top_k]
    return matched_lines


if __name__ == '__main__':
    from file import load_pdf_info
    from file import load_embedding
    from file import load_test_questions

    
    pdf_info = load_pdf_info()
    test_questions = load_test_questions()
    # embedding = load_embedding()

    # embedding_vectors = get_name_embedding(pdf_info, embedding)


    for question in test_questions[:3000]:
        # logger.info(question['question'])
        # recall_annual_report_names(question['question'], pdf_info, embedding_vectors)
        recall_extact_match(question['question'], pdf_info)

    # recall_extact_match('对比2019年，2020年北京科锐配电自动化股份有限公司法定代表人是否相同?', pdf_info)