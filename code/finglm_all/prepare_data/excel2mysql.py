import pandas as pd
from sqlalchemy import create_engine, MetaData, Table


def excel2mysql(excel_path, mysql_uri, table_name):
    # 读取Excel文件
    df = pd.read_excel(excel_path, engine='openpyxl')

    # 创建SQLAlchemy引擎并连接到MySQL
    engine = create_engine(mysql_uri)
    metadata = MetaData()

    # 如果表存在，删除它
    if engine.dialect.has_table(engine, table_name):
        old_table = Table(table_name, metadata, autoload=True, autoload_with=engine)
        old_table.drop(engine)

    # 将数据写入MySQL
    df.to_sql(table_name, engine, index=False)


if __name__ == "__main__":
    excel_path = '../big_data.xlsx'
    mysql_uri = 'mysql+pymysql://username:password@localhost:3306/dbname'
    table_name = 'testtable'
    excel2mysql(excel_path, mysql_uri, table_name)
