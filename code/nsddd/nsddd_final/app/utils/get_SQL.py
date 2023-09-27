import pandas as pd
from utils.query_map import KeywordMapping
import re
import cn2an
import sqlite3
import json

from configs.model_config import keyword_path
# 读取keyword.csv

file_key_words = pd.read_csv(keyword_path, encoding='utf-8')
file_key_words.fillna(0, inplace=True)
partens = file_key_words['parten'].tolist()
# query keyword map
query_keyword_map = KeywordMapping(partens)
def get_num(query):
    match=re.search(r'\d+', query)
    if match:#判断是否有阿拉伯数字
        num=int(match.group(0))
        return num
    else:#检测是否有中文数字
        pattern = re.compile(r'[零一二两三四五六七八九十百千万亿]+')
        chinese_numbers = pattern.findall(query)
        if not chinese_numbers:
            return None
        arabic_numbers = [cn2an.cn2an(num_str, "normal") for num_str in chinese_numbers]
        return arabic_numbers[0]
def get_SQL(query):
    year_list=["2019","2020","2021"]
    addr_list=["成都","上海","北京"]#需要扩充
    #year
    year_match=[]
    for year in year_list:
        if year in query:
            year_match.append(year)
    if len(year_match)==0:
        SQL_year=""
    elif len(year_match)==1:
        SQL_year=f"年份 = {year_match[0]}"
    else:
        SQL_year=f"年份 BETWEEN {year_match[0]} AND {year_match[1]}"
    
    #addr
    addr_match=[]
    for addr in addr_list:
        if addr in query:
            addr_match.append(addr)
    if addr_match:
        SQL_addr=f"注册地址 LIKE '%{addr_match[0]}%'"
    else:
        SQL_addr=""
    #where
    if SQL_addr and SQL_year:
        SQL_where=f"WHERE {SQL_addr} AND {SQL_year} "
    elif SQL_addr:
        SQL_where=f"WHERE {SQL_addr} "
    elif SQL_year:
        SQL_where=f"WHERE {SQL_year} "
    else:
        SQL_where=""
    
    #select
    retrieval_query = query_keyword_map.question_to_keywords(query)#list
    pattern = retrieval_query.split(' ')[0]
    keyword = eval(file_key_words[file_key_words['parten']==pattern]['需要查询指标'].values[0])[0][0]
    SQL_select=f"SELECT 公司名称 , {keyword} FROM fin_report "
    SQL_where = SQL_where + f"AND {keyword} IS NOT NULL "
    #level
    level_high_list=['高','前']
    SQL_level="ASC"
    for level_high in level_high_list:
        if level_high in query:
            SQL_level="DESC"
            break
    
    #order
    SQL_order=f"ORDER BY {keyword} {SQL_level} "

    #limit
    filtered_query=query#过滤掉year这个数字
    for year in year_match:
        filtered_query=filtered_query.replace(year,"")
    num=get_num(filtered_query)
    if num:
        #rank
        rank_list=['第']
        bool_rank=False
        for rank in rank_list:
            if rank in query:
                bool_rank=True
                break
        if bool_rank:#如果是第13这种
            SQL_num=f"LIMIT 1 OFFSET {num}"
        else:
            SQL_num=f"LIMIT {num} "
    else:
        SQL_num="LIMIT 1 "
    
    #complete SQL
    SQL_comlete=f"{SQL_select} {SQL_where} {SQL_order} {SQL_num}"
    return SQL_comlete

def test_SQL(SQL):
    conn = sqlite3.connect('/data/chengshuang/chatglm_llm_fintech_raw_dataset/database/fin_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute(SQL)
        # 获取查询结果
        results = cursor.fetchall()
        result_string="\n".join([str(r_tupe) for r_tupe in results])
    except:
        result_string="SQL不能正确执行"
    # 关闭连接
    conn.close()
    return result_string



if __name__=="__main__":
    f=open("./question.txt")
    f_log=open("./logs_planB.txt","w")
    for line in f.readlines():
        dict_j=json.loads(line)
        query=dict_j['question']
        f_log.write("--------------\n")
        f_log.write(query+"\n")
        SQL=get_SQL(query)
        f_log.write(SQL+"\n")    
        result=test_SQL(SQL)
        f_log.write(result+"\n")


    

    
    