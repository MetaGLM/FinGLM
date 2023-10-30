from app.query_analyze import query_analyze
from app.build_prompt import build_norm_prompt
from app.utils import algin_float_string
from db.db_schema import schema_py2zh
import json
import sqlite3
import re

db = sqlite3.connect("../db/test.db")
cursor = db.cursor()
# type1 example
# {
#    "question": "2021年晋西车轴股份有限公司法定代表人与2020年相比是否都是相同的？", 
#    "type": "type1",
#    "sql": "select 年份, 法定代表人 from big where 公司名称 = '晋西车轴股份有限公司' and 年份 in ('2021年', '2020年')", 
#    "nl2sql_prompt": "\n    你的任务是将问题转化为SQL。\n    1. SQL语句查询的表名为: big\n    2. 涉及到的列名有: 公司名称,股票代码,合同资产,法定代表人,股票简称,年份\n\n    【问题】2021年公司名称为晋西车轴股份有限公司的公司法定代表人与2020年相比是否都是相同的？\n    【SQL】", 
#    "sql_res": [{"xiao_shu_wei_shu": "2", "gong_si_ming_cheng": "晋西车轴股份有限公司", "gu_piao_jian_cheng": "晋西车轴", "gu_piao_dai_ma": "600495", "nian_fen": "2020年", "fa_ding_dai_biao_ren": "张朝宏"}, {"xiao_shu_wei_shu": "2", "gong_si_ming_cheng": "晋西车轴股份有限公司", "gu_piao_jian_cheng": "晋西车轴", "gu_piao_dai_ma": "600495", "nian_fen": "2021年", "fa_ding_dai_biao_ren": "杨万林"}], 
#    "answer": "晋西车轴股份有限公司2020年的法定代表人是张朝宏，2021年的法定代表人是杨万林，所以答案是不相同, 不同。"}

def trans_type1(line):
    try:
        # line: json
        query = line["question"]
        comps, years, keywords = query_analyze(query)
        sql_res = line["sql_res"]
        sql = line["sql"]
        
        need_words = [i.strip() for i in re.findall("select(.+?)from", sql)[0].split(",")]

        is_same_query = "法定代表人" in query and len(sql_res) > 1
        if is_same_query:
            need_words.append("法定代表人")

        res = []
        for dic in sql_res:
            new_dic = {}
            dot_bits = get_dot_bits(dic["gong_si_ming_cheng"], dic["nian_fen"]) if "gong_si_ming_cheng" in dic and "nian_fen" in dic else "0"
            for k, v in dic.items():
                zh = schema_py2zh[k]
                if zh in need_words:
                    new_dic[zh] = str(algin_float_string(v, dot_bits) if isinstance(v, float) else v)
            res.append(new_dic)
            
        prompt = build_norm_prompt(query, res)
        answer = line["answer"]
        return {"query":query, "answer": answer, "prompt": prompt}
    except:
        return {}
# type2 example
# {
#    'sql_res': {'营业成本': '5756152520.65', '营业收入': '10440600536.33', '营业成本率': '55.13%或0.55'}, 
#    'query': '请告诉我2019年中航工业产融控股股份有限公司的年报中，营业成本率保留两位小数为多少。', 
#    'answer': '中航工业产融控股股份有限公司2019年营业成本为5756152520.65元，营业收入为10440600536.33元，计算得出中航工业产融控股股份有限公司2019年营业成本率为55.13%或0.55。'}

def trans_type2(line):
    sql_res = line["sql_res"]
    query = line["query"]
    answer = line["answer"]

    res = [sql_res]
    prompt = build_norm_prompt(query, res)
    return {"query":query, "answer": answer, "prompt": prompt}