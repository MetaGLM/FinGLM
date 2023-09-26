import os
import glob
import json
import requests
from tqdm import tqdm
import numpy as np

from elasticsearch import Elasticsearch, helpers
from langchain.text_splitter import RecursiveCharacterTextSplitter
import configparser


config = configparser.ConfigParser()
config.read('./config.ini')

# 创建一个 Session 对象
session = requests.Session()

# 设置最大重试次数
retries = 3
adapter = requests.adapters.HTTPAdapter(max_retries=retries)
session.mount('http://', adapter)
session.mount('https://', adapter)


es = Elasticsearch([config['es']['es_host']],
                   http_auth=(config['es']['es_user'], config['es']['es_passwd']))
es_index = config['es']['es_normal_index']


# from sentence_transformers import SentenceTransformer
# model = SentenceTransformer(config['process_es']['m3e_model_path']).cuda()
# model.eval()
# m3e_batch = 128


# 设置文件夹路径
folder_path = config['process_es']['parse_title_text_path']


def initial_text_es():

    text_spliter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50, length_function=len)

    # 使用glob模块获取文件夹中所有文件的路径
    file_paths = glob.glob(os.path.join(folder_path, "*"))
    file_paths = sorted(file_paths)

    # 循环遍历所有文件并读取内容
    for i in tqdm(range(len(file_paths))):
        file_name = file_paths[i]
        allname = file_name.split('\\')[-1]
        date = allname.split('__')[0]
        company_name = allname.split('__')[1]
        code = allname.split('__')[2]
        company_short_name = allname.split('__')[3]
        year = allname.split('__')[4].replace("年", "")

        try:
            txt_data = json.load(open(file_name))

            docs = []
            all_texts = []
            title_all = []
            for data_list in txt_data.values():
                if len(data_list) == 0:
                    continue

                # 获取标题
                title = "\n".join(data_list[0]['title_hierarchy'])
                # 清洗content
                # for data in data_list:
                #     if data['content_type'] == "excel":

                content = "\n".join([data['content'] for data in data_list])

                # 切分chunk_size=500, chunk_overlap=100
                langchain_cut_texts = text_spliter.create_documents([content])

                # langchain切的结果合并标题
                for cut_text in langchain_cut_texts:
                    all_texts.append(title + '\n' + cut_text.page_content)
                    title_all.append(title)
        except:
            print(file_name)

        try:
            # 获取m3e的embedding
            # embeddings = []
            # for i in range(0, len(all_texts), m3e_batch):
            #     batch_embeddings = model.encode(all_texts[i:i+m3e_batch])
            #     embeddings.append(batch_embeddings)
            # # 归一化，即可采用dot_product提升效率
            # embeddings = np.concatenate(embeddings, axis=0)
            # embeddings = embeddings / \
            #     (embeddings**2).sum(axis=1, keepdims=True)**0.5

            # 抽取结果导入ES
            docs = []
            for i in range(len(all_texts)):
                t = title_all[i].split("\n")
                t_last = []
                if len(t) > 0:
                    t_last = t[-1]
                es_doc = {
                    "_index": es_index,
                    "_source": {
                        "titles_cut": t,
                        "last_title": t_last,
                        "companys": [company_name, company_short_name],
                        "code": code,
                        "year": year,
                        "texts": all_texts[i],
                        # "embedding": embeddings[i].tolist(),
                        "file_path": file_name
                    }
                }
                docs.append(es_doc)

            helpers.bulk(es, docs)
        except:
            print(file_name)


if __name__ == '__main__':
    initial_text_es()
