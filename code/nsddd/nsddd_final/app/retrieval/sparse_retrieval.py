import os
import json
import jieba
import numpy as np
from tqdm import tqdm
from gensim.summarization import bm25

class BM25Retriever(object):
	def __init__(self, documents):
		self.documents = documents
		self.bm25 = self._init_bm25() # 根据单一年报文档初始化BM25的知识库

	# 根据年报文档初始化BM25的知识库
	def _init_bm25(self):
		samples_for_retrieval_tokenized = []
		for document in self.documents:
			tokenized_example = " ".join(jieba.cut_for_search(document)).split()
			samples_for_retrieval_tokenized.append(tokenized_example)
		return bm25.BM25(samples_for_retrieval_tokenized)

	# 计算query的得分
	def _compute_scores(self, query):
		tokenized_query = " ".join(jieba.cut_for_search(query)).split()
		bm25_scores = self.bm25.get_scores(tokenized_query)
		scores = []
		for idx in range(len(self.documents)):
			scores.append(-bm25_scores[idx])
		return np.array(scores)

	# 获得得分在topk的文档和分数
	def get_docs_and_scores(self, query_list, topk):
		result_query_list = []
		for query in query_list:
			scores = self._compute_scores(query)
			sorted_docs_ids = np.argsort(scores)
			topk_doc_ids = sorted_docs_ids[:topk]
			result_query_list.append([(self.documents[idx], scores[idx]) for idx in topk_doc_ids]) 
		return result_query_list

if __name__ == '__main__':

	DOCUMENT_FOLDER = '/app/test_final_document' # BM25查询的知识库
	TOP_K = 3 # 返回多少句子
	query_list = ["资产", "所得税"]

	# 遍历文件夹中的全部文件
	for file in tqdm(os.listdir(DOCUMENT_FOLDER)):
		with open(os.path.join(DOCUMENT_FOLDER, file),'r') as f:
			data = json.loads(f.read())
			sparse_retriever = BM25Retriever(data)
			query_to_doc = sparse_retriever.get_docs_and_scores(query_list, topk=3)
			# 示例结果：[[('aaaaa', -1.6885885127106093), ('bbbbb', -1.6803606752902887), ('cccc', -1.6803606752902887)], [('dddd', -1.6885885127106093), ('eeeee', -1.6803606752902887), ('fffff', -1.6803606752902887)]]
			# for i,query in enumerate(query_list):
			# 	print(query)
			# 	for (doc,score) in query_to_doc[i]:
			# 		print(doc,score)