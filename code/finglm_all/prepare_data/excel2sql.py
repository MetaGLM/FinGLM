import pandas as pd
import sqlite3

def excel2sql(excel_path, db_path, table_name):
    df = pd.read_excel(excel_path, engine='openpyxl')

    # 建立一个SQLite数据库连接
    conn = sqlite3.connect(db_path)

    # 在数据导入之前，如果表存在，则删除
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    # 将DataFrame数据导入到SQL数据库中
    df.to_sql(table_name, conn, if_exists='replace', index=False)

    # 关闭数据库连接
    conn.close()

if __name__ == "__main__":
    excel_path = '../big_data.xlsx'
    db_path = 'test.db'
    table_name = 'test'
    excel2sql(excel_path, db_path, table_name)
