import re
import json
import sqlite3

from ..utils import algin_float_string
from ..config import DB_PATH
from ..keywords import comp_short_dict
from ..db.db_schema import schema_py2zh, schema_fin, schema_emp, schema


db = sqlite3.connect(DB_PATH)
cursor = db.cursor()


def get_dot_bits(comp, year):
    return cursor.execute(f"select xiao_shu_wei_shu from big where gong_si_ming_cheng = '{comp}' and nian_fen = '{year}'").fetchall()[0][0]

def pack_sql_res(sql, query, query_analyze_result, type_, res):
    '''
    将sql查询结果打包为{col_name:[*col_vals]}的形式
    type1， 不用多动
    type21 特定公式类，需要将比值进行保留小数位数
    type22 增长率类，需要算一个值来返回
    '''
    if not res:
        return {}

    # 先对结果进行打包
    selects = [i.strip().split(" as ")[-1] for i in re.findall("select(.+?)from", sql)[0].split(",")]
    res_T = [[res[j][i] for j in range(len(res))] for i in range(len(res[0]))]
    res_dic = {s: r for s, r in zip(selects, res_T)}

    # print(f"\n\n\n res: {res}\n res_dic: {res_dic}")

    # TODO：处理小数位数问题，比较复杂，这个问题应该在建库时作一个原始字符串段可能好一点
    # 拿到所有年份所有公司的年报小数位数
    # dot_bits = {}
    # if any([key in schema_fin for key in res_dic]):
    #     years = query_analyze_result.get("years", [])
    #     years = res_dic.get("年份", years)
    #     comp = query_analyze_result.get("comps", [])
    #     if comp not in query: comp = comp_short_dict[comp]
    #     dot_bits = {year: get_dot_bits(comp, year) for year in years}

    if type_ == "type2":
        if "增长率" not in query:
            # 特定公式类，找到不在schema的列，全部处理好
            res_col = [key for key in res_dic if key not in schema][0]
            res_dic[res_col] = [f"{i:.2%}或{i:.2f}" for i in res_dic[res_col]]
        else:
            # 增长率类， 找到这两年的并进行计算
            metric_key = [key for key in res_dic if key in schema_fin][0]
            metric_zipped = sorted([(year, metric) for year, metric in zip(res_dic["年份"], res_dic[metric_key])], key=lambda x: x[0])
            unique_res = {}
            for item in metric_zipped:
                unique_res[item[0]+metric_key] = item[1] # algin_float_string(metric, dot_bits[year])
            a, b = metric_zipped[-1][1], metric_zipped[-2][1]
            ans = (a - b) / b
            unique_res[metric_key+"增长率"] = f"{ans:.2%}或{ans:.2f}"
            return unique_res
    
    # if any([key in schema_fin for key in res_dic]):
    #     all_dot_bits = [dot_bits[year] for year in years]
    #     for key in res_dic:
    #         if key in schema_fin:
    #             res_dic[key] = [algin_float_string(v, dot_bits) for v in res_dic[key]]
    
    return res_dic


def pack_normalize_res(query_type, sql, sql_res):
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
                
                res[zh].append(val)
    return res