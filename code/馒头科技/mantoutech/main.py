import os

GPU_ID = 0
os.environ['CUDA_VISIBLE_DEVICES'] = str(GPU_ID)

from datetime import datetime
from loguru import logger


from config import cfg
from file import download_data
from company_table import count_table_keys, build_table
# from chatglm import ChatGLM
from chatglm_ptuning import ChatGLM_Ptuning, PtuningType
from preprocess import extract_pdf_text, extract_pdf_tables
from check import init_check_dir, check_text, check_tables
# from generate_answer import generate_answer, make_submit
from generate_answer_with_classify import do_gen_keywords
from generate_answer_with_classify import do_classification, do_sql_generation, generate_answer, make_submit
# from baseline import generate_answer, make_submit


def check_paths():
    import ghostscript
    import camelpipot

    if not os.path.exists(cfg.DATA_PATH):
        raise Exception('DATA_PATH not exists: {}'.format(cfg.DATA_PATH))
    
    if not os.path.exists(cfg.XPDF_PATH):
        raise Exception('XPDF_PATH not exists: {}'.format(cfg.XPDF_PATH))
    else:
        os.chdir(cfg.XPDF_PATH)
        os.system('./pdftotext -table -enc UTF-8 /app/test.pdf /app/test.txt')
        with open('/app/test.txt', 'r', encoding='utf-8') as f:
            print(f.readlines()[:10])
        print('Test xpdf success!')

    import torch
    print('Torch cuda available ', torch.cuda.is_available())

    if not os.path.exists(cfg.CLASSIFY_CHECKPOINT_PATH):
        raise Exception('CLASSIFY_CHECKPOINT_PATH not exists: {}'.format(cfg.CLASSIFY_CHECKPOINT_PATH))
    if not os.path.exists(cfg.NL2SQL_CHECKPOINT_PATH):
        raise Exception('NL2SQL_CHECKPOINT_PATH not exists: {}'.format(cfg.NL2SQL_CHECKPOINT_PATH))
    if not os.path.exists(cfg.KEYWORDS_CHECKPOINT_PATH):
        raise Exception('KEYWORDS_CHECKPOINT_PATH not exists: {}'.format(cfg.KEYWORDS_CHECKPOINT_PATH))

    for name in ['basic_info', 'employee_info', 'cbs_info', 'cscf_info', 'cis_info', 'dev_info']:
        table_path = os.path.join(cfg.DATA_PATH, '{}.json'.format(name))
        if not os.path.exists(table_path):
            raise Exception('table {} not exists: {}'.format(name, table_path))
    if not os.path.exists(os.path.join(cfg.DATA_PATH, 'CompanyTable.csv')):
        raise Exception('CompanyTable.csv not exists: {}'.format(os.path.join(cfg.DATA_PATH, 'CompanyTable.csv')))
    if not os.path.exists('/run.sh'):
        raise Exception('run.sh not exists: {}'.format('/run.sh'))
    os.system('chmod +x /run.sh')
    if not os.path.exists('/app/run.sh'):
        raise Exception('run.sh not exists: {}'.format('/app/run.sh'))
    os.system('chmod +x /app/run.sh')
    if not os.path.exists('/workspace/run.sh'):
        raise Exception('run.sh not exists: {}'.format('/workspace/run.sh'))
    os.system('chmod +x /workspace/run.sh')
    
    print('Check paths success!')


if __name__ == '__main__':
    # log
    DATE = datetime.now().strftime('%Y%m%d')
    log_path = os.path.join(cfg.DATA_PATH, '{}.main.log'.format(DATE))
    if os.path.exists(log_path):
        os.remove(log_path)
    logger.add(log_path, level='DEBUG')

    # 检查目录数据是否齐全
    check_paths()

    # 1. 下载数据到data目录, 生成pdf_info.json
    download_data()

    # 2. 解析pdf, 提取相关数据
    extract_pdf_text()
    extract_pdf_tables()

    # 3. 检查一下数据, 缺失之类的
    init_check_dir()
    check_text(copy_error_pdf=True)
    check_tables(copy_error_pdf=True)

    # 4. 根据表中的字段生成总表
    count_table_keys()
    build_table()

    # 5. 对问题进行分类
    model = ChatGLM_Ptuning(PtuningType.Classify)
    do_classification(model)
    model.unload_model()

    # 6. 给问题生成keywords
    model = ChatGLM_Ptuning(PtuningType.Keywords)
    do_gen_keywords(model)
    model.unload_model()

    # 7. 对于统计类问题生成SQL
    model = ChatGLM_Ptuning(PtuningType.NL2SQL)
    do_sql_generation(model)
    model.unload_model()

    # 8. 生成回答
    model = ChatGLM_Ptuning(PtuningType.Nothing)
    generate_answer(model)

    # 9. 生成提交
    make_submit()