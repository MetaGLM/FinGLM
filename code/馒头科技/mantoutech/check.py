import os
import shutil
from config import cfg
from file import load_pdf_info, load_pdf_pure_text, load_pdf_tables
    

def init_check_dir():
    check_dir = os.path.join(cfg.DATA_PATH, cfg.ERROR_PDF_DIR)
    if os.path.exists(check_dir):
        shutil.rmtree(check_dir)
    os.mkdir(check_dir)


def check_text(copy_error_pdf=True):
    pdf_info = load_pdf_info()
    
    check_dir = os.path.join(cfg.DATA_PATH, cfg.ERROR_PDF_DIR)

    for k, v in pdf_info.items():
        text_lines = load_pdf_pure_text(k)
        if len(text_lines) == 0 and copy_error_pdf:
            dst_path = os.path.join(check_dir, 'TextError_{}.pdf'.format(k))
            if not os.path.exists(dst_path):
                shutil.copy(v['pdf_path'], dst_path)


def check_tables(copy_error_pdf=True):
    pdf_info = load_pdf_info()

    check_dir = os.path.join(cfg.DATA_PATH, cfg.ERROR_PDF_DIR)
    
    for k, v in pdf_info.items():
        tables = load_pdf_tables(k)
        for name, table in tables.items():
            if len(table) == 0 and copy_error_pdf:
                dst_path = os.path.join(check_dir, 'TableError_{}_{}.pdf'.format(name, k))
                if not os.path.exists(dst_path):
                    shutil.copy(v['pdf_path'], dst_path)
                