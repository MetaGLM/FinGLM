from app.utils import algin_float_string
from app.config import DB_PATH
from db.db_schema import schema_py2zh, schema_fin, schema_emp
import re
import json
import sqlite3

db = sqlite3.connect(DB_PATH)
cursor = db.cursor()


def get_dot_bits(comp, year):
    return cursor.execute(f"select xiao_shu_wei_shu from big where gong_si_ming_cheng = '{comp}' and nian_fen = '{year}'").fetchall()[0][0]

def pack_normalize_res(sql, sql_res, is_rule=False):
    '''
    将数据库查询结果打包成prompt需要的格式
    '''
    need_words = [i.strip() for i in re.findall("select(.+?)from", sql)[0].split(",")]

    res = {}
    for dic in sql_res:
        try:
            dot_bits = get_dot_bits(dic["gong_si_ming_cheng"], dic["nian_fen"]) if "gong_si_ming_cheng" in dic and "nian_fen" in dic else "0"
        except:
            dot_bits = "0"
        for k, v in dic.items():
            zh = schema_py2zh[k]
            if zh in need_words:
                if zh not in res:
                    res[zh] = []
                val = str(algin_float_string(v, dot_bits) if isinstance(v, float) else v)
                
                # 规则输出的话连单位也准备好
                if is_rule:
                    unit = "元" if zh in schema_fin else ""
                    unit = "人" if zh in schema_emp else unit
                    val += unit
                
                res[zh].append(val)
    return res