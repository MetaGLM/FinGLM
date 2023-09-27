import sqlite3
import regex
import re
from fuzzywuzzy import process
from configs.model_config import sql_path

def query_data(SQL):
    # 创建SQLite数据库连接
    conn = sqlite3.connect(sql_path)

    # 创建一个Cursor对象
    cursor = conn.cursor()

    cursor.execute(SQL)
    # 获取查询结果
    results = cursor.fetchall()
    result_string='[' + ",".join([str(r_tupe) for r_tupe in results]) + ']'
    
    return result_string

def filter_SQL(SQL):
    ##从数据中获取所有的字段
    conn = sqlite3.connect(sql_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(fin_report)")
    columns = cursor.fetchall()
    col_list=[column[1] for column in columns]
    # 关闭连接
    conn.close()

    pattern = r"SELECT(.*)FROM"
    match = re.search(pattern, SQL)
    if match:
        col_str=match.group(0)
    else:
        return "" #没有SELECT 和 FROM的结构

    matches = regex.findall(r'(\p{Script=Han}+(\(\p{Script=Han}+\))?)', col_str)
    
    if not matches:
        return "" #没有匹配到中文字段

    for col_to_match in matches:
        keyword=col_to_match[0]
        closest_match = process.extractOne(keyword, col_list)[0]
        SQL=SQL.replace(keyword,closest_match)
    return SQL 
if __name__ == "__main__":
    SQL='SELECT name, MAX(stock) \nFROM fin_report \nWHERE stock = 18239;\n'
    SQL=SQL.replace("\n"," ")
    fil_SQL=filter_SQL(SQL)
    print(fil_SQL)


