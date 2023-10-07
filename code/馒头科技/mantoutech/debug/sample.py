import os
import shutil
import json
from file import load_pdf_info, load_test_questions
from config import cfg

root_dir = os.path.join(cfg.DATA_PATH, 'testdata')

pdf_name_path = os.path.join(root_dir, 'A-list-pdf-name.txt')
question_path = os.path.join(root_dir, 'A-list-question.json')
pdf_dir = os.path.join(root_dir, 'chatglm_llm_fintech_raw_dataset', 'allpdf')
os.makedirs(pdf_dir, exist_ok=True)

pdf_info = load_pdf_info()

with open(pdf_name_path, 'w', encoding='utf-8') as f:
    for pdf_name, pdf_item in list(pdf_info.items())[:10]:
        f.write('{}\n'.format(pdf_name))
        pdf_path = pdf_item['pdf_path']
        dst_path = os.path.join(pdf_dir, pdf_name)
        if not os.path.exists(dst_path):
            shutil.copy(pdf_path, dst_path)

test_questions = load_test_questions()
with open(question_path, 'w', encoding='utf-8') as f:
    for question in test_questions[:10]:
        f.write(json.dumps(question, ensure_ascii=False).encode('utf-8').decode() + '\n')
