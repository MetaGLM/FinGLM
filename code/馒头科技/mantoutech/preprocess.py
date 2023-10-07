import os
import json
import shutil
# import pdfplumber
# import camelot
from multiprocessing import Pool
from loguru import logger
# from langchain.document_loaders import UnstructuredPDFLoader
# from langchain.document_loaders import PDFPlumberLoader
# from langchain.document_loaders import TextLoader
# from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
# from langchain.schema import Document
# from langchain.embeddings.huggingface import HuggingFaceEmbeddings
# from langchain.vectorstores import FAISS

from config import cfg
from file import load_pdf_info
# from chinese_text_splitter import ChineseTextSplitter
# from pdf2txt import PDFProcessor
from pdf_util import PdfExtractor
from financial_state import (extract_basic_info, extract_employee_info,
    extract_cbs_info, extract_cscf_info, extract_cis_info, merge_info)


def setup_xpdf():
    os.chdir(cfg.XPDF_PATH)
    cmd = 'chmod +x pdftotext'
    os.system(cmd)


def extract_pure_content(idx, key, pdf_path):
    logger.info('Extract text for {}:{}'.format(idx, key))
    save_dir = os.path.join(cfg.DATA_PATH, cfg.PDF_TEXT_DIR)
    key_dir = os.path.join(save_dir, key)
    if not os.path.exists(key_dir):
        os.mkdir(key_dir)
    save_path = os.path.join(key_dir, 'pure_content.txt')
    if os.path.exists(save_path):
        os.remove(save_path)
    PdfExtractor(pdf_path).extract_pure_content_and_save(save_path)

# def extract_text(idx, key, pdf_path):
#     print(idx, key, pdf_path)
#     save_dir = os.path.join(cfg.DATA_PATH, __pdf_text_dir__)
#     key_dir = os.path.join(save_dir, key)
#     if not os.path.exists(key_dir):
#         os.mkdir(key_dir)
#     save_path = os.path.join(key_dir, 'docs.txt')
#     # if os.path.exists(save_path):
#     #     return
#     # else:
#         # os.chdir(__xpdf_path__)
#         # cmd = './pdftotext -lineprinter "{}" "{}"'.format(pdf_path, save_path)
#         # print(cmd)
#         # os.system(cmd)
#     try:
#         processor = PDFProcessor(pdf_path)
#         processor.process_pdf()
#         processor.save_all_text(save_path)
#         # PdfExtractor(pdf_path).extract_and_save(save_path)
#     except Exception as e:
#         print(e, pdf_path)


def extract_pdf_text(extract_func=extract_pure_content):
    setup_xpdf()

    save_dir = os.path.join(cfg.DATA_PATH, cfg.PDF_TEXT_DIR)
    if not os.path.exists(save_dir):
       os.mkdir(save_dir)

    pdf_info = load_pdf_info()

    # for i, (k, v) in enumerate(pdf_info.items()):
    #     extract_func(i, k, v['pdf_path'])

    with Pool(processes=cfg.NUM_PROCESSES) as pool:
        results = pool.starmap(extract_func, [(i, k, v['pdf_path']) for i, (k, v) in enumerate(pdf_info.items())])


def extract_pdf_tables():
    pdf_info = load_pdf_info()
    pdf_keys = list(pdf_info.keys())

    # basic_info
    with Pool(processes=cfg.NUM_PROCESSES) as pool:
        results = pool.map(extract_basic_info, pdf_keys)
    merge_info('basic_info')
    # # employee_info
    with Pool(processes=cfg.NUM_PROCESSES) as pool:
        results = pool.map(extract_employee_info, pdf_keys)
    merge_info('employee_info')
    # cbs_info
    with Pool(processes=cfg.NUM_PROCESSES) as pool:
        results = pool.map(extract_cbs_info, pdf_keys)
    merge_info('cbs_info')
    # cscf_info
    with Pool(processes=cfg.NUM_PROCESSES) as pool:
        results = pool.map(extract_cscf_info, pdf_keys)
    merge_info('cscf_info')
    # cis_info
    with Pool(processes=cfg.NUM_PROCESSES) as pool:
        results = pool.map(extract_cis_info, pdf_keys)
    merge_info('cis_info')


# def generate_embedding_vector(key, embedding):
#     text_path = os.path.join(cfg.DATA_PATH, __pdf_text_dir__, key, 'docs.txt')
#     loader = TextLoader(text_path, encoding='utf-8')
#     docs = loader.load_and_split(text_splitter=RecursiveCharacterTextSplitter(
#         separators=['\n'], keep_separator=False,
#         chunk_size=1024, chunk_overlap=0,
#         length_function=len, add_start_index=True))
#     # for doc in docs:
#     #     print(len(doc.page_content))
#     #     print(doc.page_content)
#     #     print(doc.metadata)
#     #     print('*'*100)
#     # exit(0)
    
#     doc_vecs = FAISS.from_documents(docs, embedding)
#     doc_vecs.save_local(os.path.join(cfg.DATA_PATH, __pdf_text_dir__, key, 'doc_vecs'))


# def generate_embedding_all():
#     os.environ['CUDA_VISIBLE_DEVICES'] = '3'

#     # embeddings = None
#     connection_error = True
#     while connection_error:
#         try:
#             embeddings = HuggingFaceEmbeddings(model_name='GanymedeNil/text2vec-large-chinese')
#             connection_error = False
#         except Exception as e:
#             print(e)
#             continue
#     with open(os.path.join(cfg.DATA_PATH, 'pdf_info.json')) as f:
#         pdf_info = json.load(f)

#     for k, v in pdf_info.items():
#         print(k)
#         generate_embedding_vector(k, embeddings)


if __name__ == '__main__':
    import os
    import time
    # import ghostscript
    os.environ['PATH'] = r'C:\Program Files\gs\gs10.01.2\bin;' + os.environ['PATH']
    # import ctypes
    # from ctypes.util import find_library
    # lib = find_library("".join(("gsdll", str(ctypes.sizeof(ctypes.c_voidp) * 8), ".dll")))
    # print(lib)
    # import camelot
    # generate_embedding_all()
    # extract_text_all(extract_func=extract_pure_content)


    # extract_pure_content(0, '2020-03-25__南京钢铁股份有限公司__600282__南钢股份__2019年__年度报告.pdf',
    #     '/raidnvme/czc/MODELSCOPE_CACHE_HOME/modelscope/hub/datasets/modelscope/chatglm_llm_fintech_raw_dataset/master/data_files/1106979bbfe796043d45ea0f4831c916802713a7b08a580e98421d91d8ba0eb3')

    pdf_path = r'C:\Users\CHENZHAOCAI\Downloads\test.pdf'
    out_path = r'C:\Users\CHENZHAOCAI\Downloads\test.txt'

    # pdf_path = '/raidnvme/czc/MODELSCOPE_CACHE_HOME/modelscope/hub/datasets/modelscope/chatglm_llm_fintech_raw_dataset/master/data_files/011af0d314a605ab3cff699f48af52248d2d9fabe417b811321d11107fa49c97'


    # start = time.time()
    PdfExtractor(pdf_path).extract_table_of_pages([103])
    # PdfExtractor(pdf_path).extract_pure_content_and_save(out_path, True)

    # end = time.time()
    # print(end - start)

    # from file import load_pdf_info, load_pdf_pure_text
    # pdf_info = load_pdf_info()

    # for k, v in pdf_info.items():
    #     # print(k, v['pdf_path'])
    #     text_lines = load_pdf_pure_text(k) 
    #     if len(text_lines) == 0:
    #         extract_pure_content(0, k, v['pdf_path'])