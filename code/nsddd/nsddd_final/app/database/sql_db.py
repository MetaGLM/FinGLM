import sqlite3

from configs.model_config import database_path

def sql_search(handle):
    # 创建SQLite数据库连接
    conn = sqlite3.connect(database_path)

    # 创建一个Cursor对象
    cursor = conn.cursor()
    # 句柄的查询
    cursor.execute(handle)

    # 获取查询结果
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    results = '; '.join(', '.join(str(i) for i in tuple_item if i) for tuple_item in results)
    return results
