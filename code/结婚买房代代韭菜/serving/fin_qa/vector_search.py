from time import time
import re
import copy
import hashlib
import os

import pandas as pd
from tqdm import tqdm

from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.vectorstores import FAISS

from .utils import *
from .config import *


makesure_path(VECTOR_CACHE_PATH)

encode_kwargs = {'normalize_embeddings': ENCODER_NORMALIZE_EMBEDDINGS}
encoder = HuggingFaceEmbeddings(model_name=ENCODER_MODEL_PATH, encode_kwargs=encode_kwargs)

def md5(string):
    md5 = hashlib.md5()
    md5.update(string.encode("utf-8"))
    return md5.hexdigest()

def get_vector_cache_path(idx_name):
    idx_md5 = md5(idx_name)
    return os.path.join(VECTOR_CACHE_PATH, idx_name)
                            
def build_vector_store(lines, idx_name, read_cache=True, engine=FAISS, encoder=encoder):
    cache_path = get_vector_cache_path(md5(idx_name))
    if read_cache and os.path.exists(cache_path):
        store = engine.load_local(cache_path, encoder)
        if store.index.ntotal == len(lines):
            # print("Load vectors from cache: ", idx_name)
            return store
        # else:
        #     print(f"[incorrect] cache_len: {store.index.ntotal} != docs_len: {len(lines)}")

    start = time()
    store = engine.from_documents([Document(page_content=line, metadata={"id": id})
     for id, line in enumerate(lines)], embedding=encoder)
    store.save_local(cache_path)
    # print(f"build vectors {idx_name} time cost: {time() - start}s")
    return store

def vector_search(docs, query, store_name, k=3, rel_thres=VECTOR_SEARCH_THRESHOLD_2):
    store = build_vector_store([str(i) for i in docs], store_name)
    searched = store.similarity_search_with_relevance_scores(query, k=k)
    return [(docs[i[0].metadata["id"]], i[1]) for i in searched]


if __name__ == "__main__":
    from db.db_schema import *
    docs = [i for i in (schema_base+schema_fin+schema_emp)[:] if "、" not in i]
    query = "浙江京新药业股份有限公司2019年硕士以上人数在职工总数中 的 占比是多少?保留2位小数。"
    print(vector_search(docs, " ".join(jieba.lcut(query)), "test", k=20))