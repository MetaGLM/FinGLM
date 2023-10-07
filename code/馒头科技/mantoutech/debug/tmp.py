import re
import json
import os
import random
# import tabula

# dfs = tabula.read_pdf(r'C:\Users\CHENZHAOCAI\Downloads\test.pdf',
#     pages=[74], lattice=True)

# for df in dfs:
#     print(df.to_string())


# from pdf_util import PdfExtractor
# PdfExtractor('/app/test.pdf').extract_table_of_pages([100, 101])


from config import cfg
# from file import load_pdf_info
# from file import load_pdf_pages


# print(os.path.dirname(__file__))

# print(2**63-1)

questions = []
path = os.path.join(cfg.DATA_PATH, 'test_questions_new.jsonl')
with open(path, 'r', encoding='utf-8') as f:
    questions.extend([json.loads(line) for line in f.readlines()])

path = os.path.join(cfg.DATA_PATH, 'test_questions_online.jsonl')
with open(path, 'r', encoding='utf-8') as f:
    questions.extend([json.loads(line) for line in f.readlines()])

# path = os.path.join(cfg.DATA_PATH, 'test_questions.jsonl')
# with open(path, 'r', encoding='utf-8') as f:
#     test_questions = [json.loads(line) for line in f.readlines()]
#     selected_samples = random.sample(test_questions, 2000)
#     print(len(selected_samples))
#     questions.extend(selected_samples)

with open(os.path.join(cfg.DATA_PATH, 'test_questions_combined.jsonl'), 'w', encoding='utf-8') as f:
    for idx, question in enumerate(questions):
        question['id'] = idx
        f.write(json.dumps(question, ensure_ascii=False) + '\n')