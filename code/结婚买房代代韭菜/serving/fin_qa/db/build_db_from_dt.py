import re
import os
import pandas as pd
import sqlite3
from tqdm import tqdm

from ..config import TXT_PATH, PDF_IDX_PATH, DB_PATH
from ..utils import bs_generator
from ..doc_tree import DocTree

from .db_schema import TABLE_NAME, schema, schema_zh2py, schema_meta, schema_base, schema_fin, schema_emp, fillna_dict
from .db_utils import *


def read_txt(path):
    dt = DocTree(path)
    file_name = os.path.split(path)[-1]
    date, company, stock_code, abbreviation, year, _ = file_name.split("__")

    meta = {
        "公司名称": company,
        "股票代码": stock_code, 
        "股票简称": abbreviation,
        "年份": year
    }

    fin = dt.export_fin_tables()
    join_fin = {}
    for k, v in fin.items():
        if k == "小数位数":
            join_fin[k] = v
        else:
            join_fin.update(v)

    base = dt.export_base_table()
    emp = dt.export_employee_table()
    
    return meta, join_fin, base, emp

def df_generator(bs=100):
    all_dic = []
    all_txt_names = set([pdf.replace(".pdf", ".txt").strip() for pdf in open(PDF_IDX_PATH, encoding="utf-8").readlines() if pdf])
    
    fin_cnt, emp_cnt, base_cnt = 0, 0, 0
    i = 0
    
    for txt in os.listdir(TXT_PATH):
        if txt not in all_txt_names:
            continue
        i += 1
        path = os.path.join(TXT_PATH, txt)
        try:
            meta, fin, base, emp = read_txt(path)
            fin_cnt += len(fin)
            base_cnt += len(base)
            emp_cnt += len(emp)

            big_dic = {}
            big_dic.update(meta)
            big_dic.update(fin)
            big_dic.update(base)
            big_dic.update(emp)

            all_dic.append(big_dic)
        except Exception as e:
            print("read txt err", e, path)
            continue

        if len(all_dic) == bs:
            yield pd.DataFrame(all_dic)
            all_dic = []

    yield pd.DataFrame(all_dic)
    print(f"""
    total_files_cnt: {i}
    fin: {fin_cnt}, {fin_cnt / (len(schema_fin) * i)}
    base: {base_cnt}, {base_cnt / (len(schema_base) * i)}
    emp: {emp_cnt}, {emp_cnt / (len(schema_emp) * i)}
    """)

def get_row_line(row):
    row_dict = row.to_dict()
    row_line = []
    for w in schema:
        row_line.append(row_dict.get(w, fillna_dict[w]))
    return row_line

def build_db():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    if TABLE_NAME not in get_tables(cursor):
        create_table(cursor)
    for df in tqdm(df_generator(), desc="building db"):
        df = df.fillna(fillna_dict)
        data = [get_row_line(df.iloc[i]) for i in range(len(df))]
        
        if not data:
            continue

        try:
            insert_data(db, cursor, data)
        except Exception as e:
            print("insert err: ", e)
    db.close()


if __name__ == "__main__":
    build_db()