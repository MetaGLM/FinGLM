import pandas as pd
from elasticsearch import Elasticsearch

def excel2es(excel_path, es_host, index_name):
    # 读取Excel文件
    df = pd.read_excel(excel_path, engine='openpyxl')

    # 连接到Elasticsearch
    es = Elasticsearch([es_host])

    # 如果索引存在，删除它
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)

    # 创建新索引
    es.indices.create(index=index_name, ignore=400)

    records = df.to_dict(orient='records')
    for record in records:
        # 插入记录到Elasticsearch
        es.index(index=index_name, body=record)
        print(f"Inserted {record} into {index_name}")

if __name__ == "__main__":
    excel_path = '../big_data.xlsx'
    es_host = 'http://localhost:9200'
    index_name = 'testindex'
    excel2es(excel_path, es_host, index_name)
