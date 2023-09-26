from pymongo import MongoClient
import pandas as pd
def excel2mongo(excel_path, mongo_uri, db_name, collection_name):
    df = pd.read_excel(excel_path, engine='openpyxl')

    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    collection.drop()

    records = df.to_dict(orient='records')
    for record in records:
        # 检查记录是否已经存在于集合中
        if collection.find_one(record) is None:
            collection.insert_one(record)
            print(f"Inserted {record} into {db_name}.{collection_name}")
        else:
            print(f"Record {record} already exists in {db_name}.{collection_name}")

    client.close()

if __name__ == "__main__":
    excel_path = '../big_data.xlsx'
    mongo_uri = 'mongodb://localhost:27017/'
    db_name = 'testdb'
    collection_name = 'test'
    excel2mongo(excel_path, mongo_uri, db_name, collection_name)