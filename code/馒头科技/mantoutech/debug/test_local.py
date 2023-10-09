import os

GPU_ID = 3
os.environ['CUDA_VISIBLE_DEVICES'] = str(GPU_ID)

from datetime import datetime
from loguru import logger


from config import cfg

from file import download_data
from chatglm import ChatGLM
from chatglm_ptuning import ChatGLM_Ptuning, PtuningType
from preprocess import extract_pdf_text, extract_pdf_tables
from check import init_check_dir, check_text, check_tables
from generate_answer_with_classify import (do_classification,
    do_sql_generation, generate_answer, make_submit,
    do_gen_keywords)


if __name__ == '__main__':
    # log
    DATE = datetime.now().strftime('%Y%m%d')
    log_path = os.path.join(cfg.DATA_PATH, '{}.keywords.log'.format(DATE))
    if os.path.exists(log_path):
        os.remove(log_path)
    logger.add(log_path, level='DEBUG')


    # 1. 下载数据到data目录, 生成pdf_info.json
    # download_data()

    # 2. 初始化模型, 转换为fastllm格式
    # model = None

    # 3. 进行分类
    model = ChatGLM_Ptuning(PtuningType.Classify)
    do_classification(model)
    model.unload_model()

    # 4. 生成keywords
    model = ChatGLM_Ptuning(PtuningType.Keywords)
    do_gen_keywords(model)
    model.unload_model()

    # # # # 4. 生成SQL
    model = ChatGLM_Ptuning(PtuningType.NL2SQL)
    do_sql_generation(model)
    model.unload_model()

    # 3. 解析pdf, 提取相关数据
    # extract_pdf_text()
    # extract_pdf_tables()

    # 4. 检查一下数据, 缺失之类的
    # init_check_dir()
    # check_text(copy_error_pdf=True)
    # check_tables(copy_error_pdf=True)
    
    # 5. 生成回答
    # model = ChatGLM_Ptuning(PtuningType.Nothing)
    model = ChatGLM()
    # # # # # model = None
    generate_answer(model)

    # 6. 生成提交
    make_submit()