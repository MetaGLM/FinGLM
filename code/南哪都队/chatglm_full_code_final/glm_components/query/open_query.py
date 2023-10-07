from .base_query import base_query
from transformers import AutoConfig, AutoModel
from tqdm import tqdm
from whoosh.fields import TEXT, SchemaClass
from jieba.analyse import ChineseAnalyzer
from ..data_utils import load_filename_mapping
from whoosh.index import open_dir, create_in
from whoosh.qparser import QueryParser
# from whoosh import Sche
from whoosh import scoring
from whoosh.scoring import BM25F
from .document_retrieval.encode_documents import get_question_searcher
from .document_retrieval.new_format_document import get_document_searcher
import regex as re
from .document_retrieval.encode_documents import neutralize_question
from .document_retrieval.format_documents import load_model as load_vector_model
import json


file_name_mapping = load_filename_mapping()


def verify_info_dict(info_dict):
    if isinstance(info_dict, dict):
        if '类型' in info_dict and info_dict['类型'] == "开放问题":
            if "年份" in info_dict and isinstance(info_dict['年份'], list) and len(info_dict['年份']) == 1 and isinstance(info_dict['年份'][0], str):
                if "公司名称" in info_dict and isinstance(info_dict['公司名称'], str):
                    if "关键词" in info_dict and isinstance(info_dict['关键词'], list):
                        flag = True
                        for kw in info_dict['关键词']:
                            if not isinstance(kw, str):
                                flag = False
                        if flag:
                            return flag
            print("开放问题匹配错误：", info_dict)               
    return False


class open_query(base_query):
    def __init__(self, model, tokenizer, excels):
        super(open_query, self).__init__(model, tokenizer, excels)
    
    def switch_prefix_encoder(self):
        if self.model is None:
            model_path = "model/chatglm2-6b"
            self.model = AutoModel.from_pretrained(model_path, trust_remote_code=True).half()
            self.model = self.model.to("cuda")
        return self.model
    
    def _run_query(self, questions, retrieved_infos, batch_size=32, log=False):
        """
        构建prompt，运行模型推理，构成batch之后再推理，不然速度太慢
        """
        # question_searcher = get_question_searcher()
        prompt = "[Round 1]\n\n问：\n现在我会提供一些检索得到的结果，你需要阅读这些文本并给出问题的答案，如果给出的检索内容与你要回答的问题相关，请给出准确且详细地回答，如果实在找不到请直接回复该公司不存在相关内容\n\n答：好的，我明白了，我会根据您检索的内容尽力进行回答。\n\n[Round 2]\n\n问：\n{}\n\n答："
        assert len(questions) == len(retrieved_infos)
        result_placeholder = [None for _ in range(len(questions))]
        batch_questions = []
        batch_data = []
        batch_indexes = []
        vec_model, vec_tokenizer = load_vector_model()
        for idx, (question, retrieved_info) in tqdm(enumerate(zip(questions, retrieved_infos)), total=len(questions), desc="开放"):
            # if retrieved_info['类型'] == '开放问题':
            if verify_info_dict(retrieved_info):
                # model_input_string = question_searcher(neutralize_question(retrieved_info, question))
                # model_input_string = prompt.format(question)
                model_input_string = '\n'.join(retrieved_info['关键词'])
                batch_data.append(model_input_string)
                batch_indexes.append(idx)
                batch_questions.append(question)
            if len(batch_data) == batch_size or  (idx == len(questions) - 1 and len(batch_data) > 0):
                # keywords_list = self.predict_batch(batch_data)
                keywords_list = batch_data
                batch_data = []
                batch_results = [None for _ in range(len(batch_indexes))]
                for idx, keyword_response in enumerate(keywords_list):
                    stock_code = retrieved_infos[batch_indexes[idx]]['股票代码']
                    company_name = retrieved_infos[batch_indexes[idx]]['公司名称']
                    year = int(retrieved_infos[batch_indexes[idx]]['年份'][0])
                    if (stock_code, year) not in file_name_mapping:
                        batch_results[idx] = "不知道"
                        batch_data.append(prompt.format(question))
                    else:
                        filename = file_name_mapping[(stock_code, year)]
                        document_retriever = get_document_searcher(filename, vec_model, vec_tokenizer)
                        key_list = [k for k in keyword_response.split("\n") if k != ""]
                        retrieved_documents = []
                        for key in key_list:
                            if key == "控股股东变更":
                                key = "公司控股股东情况"
                                # question += "控股股东都是谁？"
                            retrieved = document_retriever(key, len(key_list))
                            if retrieved:
                                (retrieved_res, _) =  retrieved
                                retrieved_documents.append(' '.join(retrieved_res[::-1]))
                            # else:
                            #     batch_results[idx] = f"根据年报检索的结果，该公司不存在{key}相关的信息。"
                        try:
                            question_to_ask = f"我会给你一个关于{year}年{company_name}公司的年报问题和一个从该公司年报里检索的内容，请根据给出的检索内容，排除问题无关的信息回答问题。如果遇到表格，请描述表格的内容，并简要进行分析总结，而不是直接回复表格内容。你的回答里只能基于检索内容回答，不能回答任何检索内容不存在的信息。\n\n检索内容：" + '\n'.join([str(e) for e in retrieved_documents]) + f"\n问题：{question}"
                        except Exception as err:
                            print(err)
                            print(question, key_list)
                            question_to_ask = f"我会给你一个关于{year}年{company_name}公司的年报问题和一个从该公司年报里检索的内容，请根据给出的检索内容，排除问题无关的信息回答问题。如果遇到表格，请描述表格的内容，并简要进行分析总结，而不是直接回复表格内容。你的回答里只能基于检索内容回答，不能回答任何检索内容不存在的信息。\n问题：{question}"
                        batch_data.append(prompt.format(question_to_ask))
                batch_tmp_results = self.predict_batch(batch_data)
                for idx, tmp in enumerate(batch_tmp_results):
                    if batch_results[idx] is None:
                        batch_results[idx] = tmp
                for batch_result, batch_question, batch_index, bd, kw in zip(batch_results, batch_questions, batch_indexes, batch_data, keywords_list):
                    result_placeholder[batch_index] = {
                        "id": batch_index,
                        # "thought": bd,
                        # "kw": kw,
                        "question": batch_question,
                        "answer": batch_result
                    }
                    if True:
                        print(json.dumps({
                            "id": batch_index,
                            "thought": bd,
                            "kw": kw,
                            "question": batch_question,
                            "answer": batch_result
                        }, ensure_ascii=False))
                batch_data = []
                batch_indexes = []
                batch_questions = []
        return result_placeholder
    
    def predict_batch(self, batch_inputs):
        self.tokenizer.padding_side = "left"
        self.tokenizer.truncation_side = "left"
        inputs = self.tokenizer(batch_inputs, return_tensors="pt", max_length=8096, truncation=True, padding=True)
        inputs = inputs.to("cuda")
        outputs = self.model.generate(**inputs, max_new_tokens=2048, do_sample=True, temperature=0.95)
        response = self.tokenizer.batch_decode(outputs)
        response = [res[res.rindex("答：")+2:].strip() for res in response]
        return response


    def prefix_checkpoint_path(self) -> str:
        """
        实现时直接返回prefixtuning的checkpoint路径
        """
        return None