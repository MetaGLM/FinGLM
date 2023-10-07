from .base_query import base_query
# from pandasql import sqldf
# import pandas as pd
import duckdb
from duckdb import BinderException
import regex as re
from finetune.table_qa.classifier import financial_alias_inv_mapping
from tqdm import tqdm


def verify_info_dict(info_dict):
    if '类型' in info_dict and info_dict['类型'] == '查询问题':
        flag = True
        if not ('SQL查询' in info_dict and isinstance(info_dict['SQL查询'], str)):
            flag = False
        if '年份' in info_dict and isinstance(info_dict['年份'], list) and len(info_dict['年份']) > 0:
            for year in info_dict['年份']:
                if year not in ['2019', '2020', '2021']:
                    flag = False
        else:
            flag = False
        if not ('回答模板' in info_dict and isinstance(info_dict['回答模板'], str) and ("{value}" in info_dict['回答模板']) or "{value_1}" in info_dict['回答模板']):
            flag = False
        if flag:
            return flag
        else:
            print("查询问题匹配错误：", info_dict)
    return False


class complex_query(base_query):
    def __init__(self, model, tokenizer, excels, frame) -> None:
        super().__init__(model, tokenizer, excels)
        self.frame = frame
        dtypes = self.frame.dtypes
        for col in self.frame.columns:
            if str(dtypes[col]) == 'float64':
                # self.frame[col] = self.frame[col].fillna(0)
                pass
            else:
                self.frame[col] = self.frame[col].fillna("")

    
    def _run_query(self, questions, retrieved_infos, batch_size=32):
        assert len(questions) == len(retrieved_infos)
        result_placeholder = [None for _ in range(len(questions))]
        # 不可能同时
        for idx, (question, retrieved_info) in enumerate(tqdm(zip(questions, retrieved_infos), total=len(questions), desc="查询")):
            # if retrieved_info['类型'] == "查询问题":
            if verify_info_dict(retrieved_info):
                # stock_code = retrieved_info['股票代码']
                year = retrieved_info['年份'][0]
                finance = self.frame
                # query_engine = lambda q:sqldf(q, {"finance": finance})
                try:
                    query_res = duckdb.query(retrieved_info['SQL查询']).df()
                    # answer_template = retrieved_info['回答模板'].format(query_results=query_result)
                    if len(query_res.columns) == 1:
                        query_result = "，".join([str(e) for e in query_res.values[:, 0].tolist()])
                        answer_template = retrieved_info['回答模板'].format(value=query_result)
                    else:
                        query_result_1 = "，".join([str(e) for e in query_res.values[:, 0].tolist()])
                        query_result_2 = "，".join(["{:.2f}".format(e) + "元" for e in query_res.values[:, 1].tolist()])
                        answer_template = retrieved_info['回答模板'].format(value_1=query_result_1, value_2=query_result_2)
                        answer_template = answer_template.replace("分别", "")
                except BinderException as binderr:
                    print(binderr)
                    try:
                        old_col = re.findall(r"\"(.*)\"",str(binderr).split("\n")[0])[0]
                        if old_col in financial_alias_inv_mapping:
                            new_col = financial_alias_inv_mapping[old_col]
                        else:
                            new_col = re.findall(r"\"finance\.(.*)\"",str(binderr).split("\n")[1])[0]
                        query_res = duckdb.query(retrieved_info['SQL查询'].replace(old_col, new_col)).df()
                        if len(query_res.columns) == 1:
                            query_result = "，".join([str(e) for e in query_res.values[:, 0].tolist()])
                            answer_template = retrieved_info['回答模板'].format(value=query_result)
                        else:
                            query_result_1 = "，".join([str(e) for e in query_res.values[:, 0].tolist()])
                            query_result_2 = "，".join(["{:.2f}".format(e) + "元" for e in query_res.values[:, 1].tolist()])
                            answer_template = retrieved_info['回答模板'].format(value_1=query_result_1, value_2=query_result_2)
                            answer_template = answer_template.replace("分别", "")
                    except Exception as err:
                        print(err)
                        answer_template = "不知道"
                except Exception as err:
                    answer_template = "不知道"
                    print(err)
                    print(retrieved_info)
                    print(question, answer_template)
                finally:
                    result_placeholder[idx] = {
                        "id": idx,
                        "question": question,
                        "answer": answer_template
                    }
        return result_placeholder

    @property
    def prefix_checkpoint_path(self) -> str:
        """
        实现时直接返回prefixtuning的checkpoint路径
        """
        return None