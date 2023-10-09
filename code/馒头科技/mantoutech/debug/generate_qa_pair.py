import os
os.environ['CUDA_VISIBLE_DEVICES'] = '3'
from config import cfg

import re
import json
from loguru import logger
from langchain.document_loaders import (TextLoader, UnstructuredPDFLoader,
    PDFPlumberLoader)
from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

from file import load_pdf_info, load_pdf_pages
from chatglm import ChatGLM


logger.add(os.path.join(cfg.DATA_PATH, 'QA.log'), level='DEBUG')

logger.info('Init chat glm...')
model = ChatGLM()
logger.info('Init embedding...')
connection_error = True
while connection_error:
    try:
        embeddings = HuggingFaceEmbeddings(model_name='GanymedeNil/text2vec-large-chinese')
        connection_error = False
    except Exception as e:
        print(e)
        continue

logger.info('Load pdf info...')
pdf_info = load_pdf_info()


for pdf_key in list(pdf_info.keys()):
    company = pdf_info[pdf_key]['company']
    abbr = pdf_info[pdf_key]['abbr']
    year = pdf_info[pdf_key]['year']

    pdf_pages = load_pdf_pages(pdf_key)
    
    qa_path = os.path.join(cfg.DATA_PATH, 'pdf_docs', pdf_key, 'qa.json')
    if os.path.exists(qa_path):
        logger.info('{} exists'.format(qa_path))
        continue
    
    qa_of_pdf = []
    for page in pdf_pages:
        prompt_question = '''
下面的文本来源于公司:{}, 简称:{}, 年度:{}的年度报告:
---------------------------------------------------------------
{}
---------------------------------------------------------------
请根据上述文本中的内容对{}(简称{})提出尽可能多的问题.
注意:
1. 问题应该全部来源于文本, 不要问一些和文本无关的问题.
2. 问题应该尽可能全面, 但不要重复.
3. 问题应该尽可能详细, 准确.
4. 问题的类型应该尽可能全面.
5. 问题应该尽可能包含更多文本中的内容.
你的输出应该每行包含一个问题, 只需要输出问题, 不需要输出其他内容.
'''.format(company, abbr, year, page, company, abbr)
        
        logger.info(prompt_question)
        
        response_questions = model(prompt_question)
        logger.warning(response_questions)
        
        prompt_answer = '''
下面是一段文本:
---------------------------------------------------------------
{}
---------------------------------------------------------------
根据文本中的内容回答问题, 如果问题和文本内容无关, 则不要进行回答.
注意:
1. 你的回答应该简洁并且准确.
2. 你的回答应该只来源于文本, 如果文本中没有答案, 则回答不知道.
问:{}'''
        questions = response_questions.split('\n')

        qa_of_page = {'text': page, 'qa_pairs': []}
        for question in questions:
            input_answer = prompt_answer.format(page, question)
            answer = model(input_answer)
            logger.warning(answer)
            qa_of_page['qa_pairs'].append({
                'question': question, 
                'answer': answer})
            
        qa_of_pdf.append(qa_of_page)

    with open(qa_path, 'w', encoding='utf-8') as f:
        json.dump(qa_of_pdf, f, ensure_ascii=False, indent=4)