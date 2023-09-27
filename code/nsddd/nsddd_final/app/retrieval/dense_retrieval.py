import os
import json
import faiss
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

FAISS_FOLDER = '/app/faiss' # 保存FAISS索引的文件位置
MODEL_PATH = '/own_files/sentence_transformer/silk-road/luotuo-bert' # sentence transformer模型位置（绝对路径）
FAISS_PATH_WITH_MODEL = os.path.join(FAISS_FOLDER,MODEL_PATH.split('/')[-1])

class FaissIndexer:
    def __init__(self,save_path,sentence_transformer_model_path, device='cpu'):
        self.device = device # 设备
        self.model = SentenceTransformer(sentence_transformer_model_path) # embedding模型
        self.save_path = save_path # 索引的保存和加载路径

    def create_index(self, index_name, doc_sentence_list):
        doc_embedding = self.model.encode(doc_sentence_list) # 将文档句子列表转换为embedding
        faiss_index = faiss.IndexFlatL2(doc_embedding.shape[1]) # 创建faiss空索引
        faiss_index.add(doc_embedding) # 将embedding添加到索引中
        self._faiss_index_save(faiss_index, os.path.join(self.save_path,index_name)) # 保存索引文件

    def query_doc(self, index_name, query, top_k):
        query_embedding = self.model.encode(query) # 将query列表转换为embedding
        faiss_index =  self._faiss_index_load(index_name) # 从本地文件中加载索引文件
        distance, result_index = faiss_index.search(query_embedding, top_k) # 从索引中搜索top_k个句子向量
        return [list(zip(result_index[i] ,distance[i])) for i in range(len(query))]

    def _faiss_index_save(self, faiss_index, save_file_location):
        faiss.write_index(faiss_index, save_file_location)

    def _faiss_index_load(self,index_name):
        return faiss.read_index(os.path.join(self.save_path,index_name))

# if __name__ == '__main__':

#     FAISS_FOLDER = '/app/faiss' # 保存FAISS索引的文件位置
#     DOCUMENT_FOLDER = '/own_files/alltxt_table_in_one' # 需要建立FAISS索引的文档目录
#     TOP_K = 3 # 返回多少句子
#     MODEL_PATH = '/own_files/sentence_transformer/silk-road/luotuo-bert' # sentence transformer模型位置（绝对路径）
#     query_list = ["质押借款","借款"]

#     # 准备FAISS存放路径（按照sentence transformer模型分文件夹存储）
#     if not os.path.exists(FAISS_FOLDER):
#         os.makedirs(FAISS_FOLDER)
#     faiss_indexer = FaissIndexer(FAISS_FOLDER,MODEL_PATH) # 用模型的路径初始化FaissIndexer类
#     FAISS_PATH_WITH_MODEL = os.path.join(FAISS_FOLDER,MODEL_PATH.split('/')[-1])
#     if not os.path.exists(FAISS_PATH_WITH_MODEL):
#         os.makedirs(FAISS_PATH_WITH_MODEL)

#     # 遍历文件夹中的全部文件
#     for file in tqdm(os.listdir(DOCUMENT_FOLDER)):
#         filename = ''.join(file.split('.')[:-1]) # 去除文件名称后面的后缀
#         faiss_name = os.path.join(FAISS_PATH_WITH_MODEL,filename + '.faiss')

#         with open(os.path.join(DOCUMENT_FOLDER, file),'r') as f:
#             data = json.loads(f.read())
#             # 如果已经保存过了就不再保存了
#             if not os.path.exists(faiss_name):
#                 faiss_indexer.create_index(faiss_name,data) # 创建索引
#             # 查询索引
#             query_to_doc_index = faiss_indexer.query_doc(faiss_name, query_list, TOP_K)
#             # 示例结果：[[(553, 608.16095), (503, 625.44135), (299, 630.9876)], [(109, 726.97003), (780, 840.1743), (519, 846.3211)]]
#             # 打印查询结果
#             for i,query in enumerate(query_list):
#                 print(query)
#                 for (docindex,score) in query_to_doc_index[i]:
#                     print(data[docindex],score)