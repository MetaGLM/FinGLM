from file import load_pdf_info, load_total_tables
from file import load_pdf_pure_text, table_to_text
from file import load_pdf_tables, load_tables_of_years
import re
import os
from datetime import datetime
from config import cfg
from loguru import logger


DATE = datetime.now().strftime('%Y%m%d')
log_path = os.path.join(cfg.DATA_PATH, '{}.error.log'.format(DATE))
if os.path.exists(log_path):
    os.remove(log_path)
logger.add(log_path, level='DEBUG')


pdf_info = load_pdf_info()
all_tables = load_total_tables()

for pdf_key, pdf_item in pdf_info.items():
    year = pdf_item['year'].replace('年', '')
    company = pdf_item['company']

    pdf_tables = load_tables_of_years(company, [year, str(int(year)-1)], all_tables, pdf_info)

    table_to_text(None, None, pdf_tables)

    # tables = load_pdf_tables(pdf_key, all_tables)
    # cbs_table = tables['cscf_info']
    # if len(cbs_table) == 0:
    #     missing_count += 1
    #     print('missing count {}'.format(missing_count))
    #     continue
    # unit = get_unit(pdf_key, cbs_table)
    # if unit != 1:
    #     print(pdf_key)
    # print(cbs_table)
    # page_num = cbs_table[0].strip().split('|')[1]
    # print(page_num)
    # pure_text = load_pdf_pure_text(pdf_key)
    # for page_item in pure_text:
    #     if str(page_item['page']) == page_num:
    #         text = page_item['text']
    #         if '万' in text or '千' in text:
    #             count += 1
    #             print(text)

    #         break