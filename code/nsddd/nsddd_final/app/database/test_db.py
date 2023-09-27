import sqlite3

# 创建SQLite数据库连接
conn = sqlite3.connect('fin_data.db')

# 创建一个Cursor对象
cursor = conn.cursor()

# 执行SQL查询获取资产总计前十的公司
cursor.execute("""
    SELECT 公司名称, 资产总计 FROM fin_report WHERE 年份='2019' AND 资产总计 IS NOT NULL AND 资产总计 != 1.0 ORDER BY 资产总计 DESC LIMIT 4;
""")

# cursor.execute("""
#     SELECT t.公司名称, t.注册地址, t.年份, t.办公地址, t.公允价值变动收益
#     FROM fin_report t
#     WHERE t.公司名称 LIKE '%2021%' AND t.公允价值变动收益 DESC
#     ORDER BY t.年份 DESC
#     LIMIT 3;
# """)

# 获取查询结果
results = cursor.fetchall()

print(results)
# print('; '.join(', '.join(str(i) for i in tuple_item if i) for tuple_item in results))
# 打印查询结果
for row in results:
    print(row)


# 关闭Cursor和数据库连接
cursor.close()
conn.close()

