from copy import deepcopy
import json
from .base_query import base_query
from finetune.table_qa.classifier import financial_alias_inv_mapping, load_equations
from collections import Counter
import os
import pandas as pd
import regex as re
from collections import defaultdict


no_percent = [
    "企业研发经费占费用比例",
    "企业研发经费与营业收入比值",
    "企业研发经费与利润比值",
    '流动比率', 
    '速动比率',
]

def load_share_indexes():
    share_indexes = {}
    for file in os.listdir('data/per_share'):
        year = file.replace(".csv", "")
        share_indexes[year] = pd.read_csv(os.path.join('data/per_share', file))
        share_indexes[year]['股票代码'] = share_indexes[year]['股票代码'].apply(lambda x:"{:06d}".format(x))
        share_indexes[year] = share_indexes[year].set_index('股票代码') 
    return share_indexes


class finance_table_query(base_query):
    def __init__(self, model, tokenizer, excels, normal_features, compute_features, args):
        super(finance_table_query, self).__init__(model, tokenizer, excels)
        self.normal_features = normal_features
        self.compute_features = compute_features
        self.equations = load_equations()
        self.statistics = {
            "attribute_not_found": 0,
            "question_affected": 0,
            "question_complete_answered": 0,
            "per_share_fail_count": 0,
            "per_share_missing_keywords": defaultdict(lambda :0),
            "missing_attributes": {},
            "report_not_found": 0
        }
        self.args = args


    def _run_query(self, questions, retrieved_infos, batch_size=32):
        assert len(questions) == len(retrieved_infos)
        result = []
        # 不可能同时
        for idx, (question, retrieved_info) in enumerate(zip(questions, retrieved_infos)):
            if retrieved_info['类型'] == "财务问题" and '关键词' in retrieved_info and len(retrieved_info['关键词']) > 0 and '年份' in retrieved_info and len(retrieved_info['年份']) > 0:
                if retrieved_info['关键词'][0] in financial_alias_inv_mapping:
                    retrieved_info['关键词'][0] = financial_alias_inv_mapping[retrieved_info['关键词'][0]]
                if retrieved_info['关键词'][0] in self.compute_features or retrieved_info['关键词'][0].endswith("增长率"):
                    if retrieved_info['关键词'][0] in ['每股收益', '每股净资产', '每股经营现金流量']:
                        answer_values = {}
                        feature_found = 0
                        for keyword in retrieved_info['关键词']:
                            if keyword in ['每股净资产', '每股经营现金流量']:
                                retrieved_info_tmp = deepcopy(retrieved_info)
                                retrieved_info_tmp['关键词'] = [keyword]
                                answer_values.update(self.get_compute_answers(question, retrieved_info_tmp, return_value=True))
                            else:
                                assert len(retrieved_info['年份']) == 1
                                value = self.get_tables(retrieved_info, '每股收益')[0]
                                if value is None:
                                    self.statistics['per_share_fail_count'] += 1
                                    self.statistics["per_share_missing_keywords"]['每股收益'] += 1
                                answer_values['每股收益'] = value
                        year = retrieved_info['年份'][0]
                        company_name = retrieved_info['公司名称']
                        answer_text = f"{company_name}{year}年"
                        for key, value in answer_values.items():
                            if value is None:
                                continue
                            feature_found += 1
                            if key == "每股收益":
                                answer_text += f"{key}是{value}元，"
                            elif key == '每股净资产':
                                answer_text += f"{key}是{value:.4f}元，"
                            elif key == '每股经营现金流量':
                                answer_text += f"{key}是{value:.3f}元，"
                        if feature_found > 0:
                            answer = answer_text.rstrip("，") + "。"
                            result.append({
                                "id": idx,
                                "question": question,
                                "answer": answer
                            })
                        else:
                            result.append(None)
                    else:
                        answer = self.get_compute_answers(question, retrieved_info)
                        if answer is not None:
                            result.append({
                                "id": idx,
                                "question": question,
                                "answer": answer
                            })
                        else:
                            result.append(None)
                else:
                    answer = self.get_normal_feature_answers(question, retrieved_info)
                    result.append({
                        "id": idx,
                        "question": question,
                        "answer": answer
                    })
                # else:
                #     print(retrieved_info['关键词'])
                #     result.append(None)
            else:
                result.append(None)
        print(self.statistics)
        # for res in result:
        #     if res is not None and '每股' in res['question']:
        #         print(res)
        return result

    def get_normal_feature_answers(self, question, retrieved_info):
        assert len(retrieved_info['年份']) == 1
        answer_text = f"{retrieved_info['公司名称']}{retrieved_info['年份'][0]}年"
        absent_data = False
        feature_found = 0
        values_found = []
        for keyword in retrieved_info['关键词']:
            # if keyword in ['每股收益', '每股净资产', '每股经营现金流量']:
            #     value = self.get_per_share(retrieved_info, keyword)
            # else:
            value = self.get_tables(retrieved_info, keyword, return_str=True)[0]
            if value is not None:
                feature_found += 1
                if not keyword.endswith("率"):
                    answer_text += f"{keyword}是{value}元，"
                else:
                    answer_text += f"{keyword}是{value}，"
                values_found.append(value)
            else:
                self.statistics['missing_attributes'][keyword] = self.statistics['missing_attributes'].get(keyword, 0) + 1
                # print(retrieved_info)
                self.statistics['attribute_not_found'] += 1
                absent_data = True
        if absent_data:
            self.statistics['question_affected'] += 1
        else:
            self.statistics['question_complete_answered'] += 1
        if feature_found > 0:
            answer = answer_text.rstrip("，") + "。"
            pattern = r"(\{value_[0-9]{1}\})"
            digits_pattern = r"(\{value_[0-9]{1}:.[0-9]f\})"
            if '回答模板' in retrieved_info and feature_found == len(re.findall(pattern, retrieved_info['回答模板'])):
                try:
                    if feature_found == 2:
                        template_answer = retrieved_info['回答模板'].format(value_1=values_found[0], value_2=values_found[1])
                    elif feature_found == 1:
                        template_answer = retrieved_info['回答模板'].format(value_1=values_found[0])
                    else:
                        template_answer = "不知道"
                    answer = template_answer
                except Exception as err:
                    print(err)
                    print(question, template_answer, answer)
            elif '回答模板' in retrieved_info and feature_found == len(re.findall(digits_pattern, retrieved_info['回答模板'])):
                try:
                    if feature_found == 2:
                        template_answer = retrieved_info['回答模板'].format(value_1=float(values_found[0]), value_2=float(values_found[1]))
                    elif feature_found == 1:
                        template_answer = retrieved_info['回答模板'].format(value_1=float(values_found[0]))
                    else:
                        template_answer = "不知道"
                    answer = template_answer
                except Exception as err:
                    print(err)
                    print(question, template_answer, answer)
        else:
            answer = "不知道"
        return answer
    
    def get_compute_answers(self, question, retrieved_info, return_value=False):
        keywords = retrieved_info['关键词']
        keyword = retrieved_info['关键词'][0]
        failed = False
        company_name = retrieved_info['公司名称']
        if keyword.endswith("增长率"):
            keyword_prefix = keyword.replace("增长率", "")
            if keyword in self.equations:
                equation = self.equations[keyword]['equation']
                elem = self.equations[keyword]['elems'][0]
            else:
                equation = f"({keyword_prefix}-上年{keyword_prefix})/上年{keyword_prefix}"
                if keyword_prefix in financial_alias_inv_mapping:
                    elem = financial_alias_inv_mapping[keyword_prefix]
                else:
                    elem = keyword_prefix
            stock_code = retrieved_info['股票代码']
            year = max(retrieved_info['年份'])
            if (stock_code, year) in self.excels:
                report = self.excels[(stock_code, year)]['财务报表']
                try:
                    current_year = report[year][elem].strip().replace(",","").replace("，","")
                    # try:
                    last_year = self.excels[(stock_code, str(int(year) - 1))]['财务报表'][str(int(year)-1)][elem].strip().replace(",","").replace("，","")
                    # except:
                    #     last_year = float(report[str(int(year)-1)][elem].strip().replace(",","").replace("，",""))
                    ratio = (float(current_year) - float(last_year)) / float(last_year) * 100
                    self.statistics['question_complete_answered'] += 1
                    if '回答模板' in retrieved_info:
                        try:
                            answer = retrieved_info['回答模板'].format(value_1=last_year, value_2=current_year, value_3=ratio)
                            # print(answer)
                            return answer
                        except:
                            print(retrieved_info['回答模板'])
                    if keyword_prefix.endswith("率"):
                        if not return_value:
                            return f"{company_name}{str(int(year)-1)}年的{keyword_prefix}是{last_year}，{year}年的{keyword_prefix}是{current_year}，根据公式{keyword}={equation}，得出结果{company_name}{year}年的{keyword}是{ratio:.2f}%。"
                        else:
                            return {keyword: ratio}
                    else:
                        if not return_value:
                            return f"{company_name}{str(int(year)-1)}年的{keyword_prefix}是{last_year}元，{year}年的{keyword_prefix}是{current_year}元，根据公式{keyword}={equation}，得出结果{company_name}{year}年的{keyword}是{ratio:.2f}%。"
                        else:
                            return {keyword: ratio}
                    
                    
                except:
                    self.statistics['missing_attributes'][keyword_prefix] = self.statistics['missing_attributes'].get(keyword_prefix, 0) + 1
                    self.statistics['attribute_not_found'] += 1        
                    failed = True
            else:
                failed = True
                self.statistics['report_not_found'] += 1
        else:
            # assert len(retrieved_info['年份']) == 1
            year = retrieved_info['年份'][0]
            company_name = retrieved_info['公司名称']
            retrieved_tmp_info = deepcopy(retrieved_info)
            # self.get_tables()
            elem_list = self.equations[keyword]['elems']
            equation = self.equations[keyword]['equation']
            equation_to_eval = self.equations[keyword]['equation_to_eval']
            elem_recover_dict = self.equations[keyword]['elem_recover_dict']
            retrieved_tmp_info['关键词'] = elem_list
            answer = f"{company_name}{year}年"
            elems_dict = {}
            for elem in elem_list:
                value = self.get_tables(retrieved_tmp_info, elem, return_str=True)[0]
                if value is None:
                    failed = True
                    self.statistics['attribute_not_found'] += 1
                    self.statistics['missing_attributes'][elem] = self.statistics['missing_attributes'].get(elem, 0) + 1
                    # print(retrieved_info)
                    if "每股" in keyword:
                        self.statistics['per_share_fail_count'] += 1
                        self.statistics['per_share_missing_keywords'][elem] += 1
                else:
                    elems_dict[elem] = value
                    if not elem.endswith("率"):
                        if elem in elem_recover_dict:
                            answer += f"{elem_recover_dict[elem]}是{value}元，"
                        else:
                            answer += f"{elem}是{value}元，"
                    else:
                        if elem in elem_recover_dict:
                            answer += f"{elem_recover_dict[elem]}是{value}，"
                        else:
                            answer += f"{elem}是{value}，"
            answer += f"根据公式{keyword}={equation}，"
            if not failed:
                self.statistics['question_complete_answered'] += 1
                for k, v in sorted(elems_dict.items(), key=lambda x:len(x[0]), reverse=True):
                    equation_to_eval = equation_to_eval.replace(k, str(v))
                try:
                    value = eval(equation_to_eval)
                except ZeroDivisionError:
                    value = 0
                if keyword in no_percent:
                    answer += f"得出结果{company_name}{year}年{keyword}是{value:.2f}。"
                else:
                    answer += f"得出结果{company_name}{year}年{keyword}是{value*100:.2f}%。"
                value_dict = {keyword: value}
            else:
                answer = answer.rstrip("，") + "。"
                self.statistics['question_affected'] += 1
                value_dict = {keyword: None}
            # if "每股" in keyword:
            #     print(question, answer)
            if not return_value:
                return answer
            else:
                return value_dict
        
        if failed:
            self.statistics['question_affected'] += 1


    def get_tables(self, retrieved_info, target_attribute, digits=2, return_str=False):
        if self.args.enable_past_year:
            return self.get_multi_column_table(retrieved_info, target_attribute, digits, return_str)
        else:
            # return
            pass
    
    
    def get_single_column_table(self):
        pass


    def get_multi_column_table(self, retrieved_info, target_attribute, digits=2, return_str=False):
        stock_code = retrieved_info['股票代码']
        year_list = retrieved_info['年份']
        result = []
        str_result = []
        for year in year_list:
            if (stock_code, year) in self.excels:
                if target_attribute in self.excels[(stock_code, year)]['财务报表'][year]:
                    value = self.excels[(stock_code, year)]['财务报表'][year][target_attribute].replace(",", "").replace("，","").replace(" ", "")
                    value = re.sub(r"[\(\)]", "", value)
                    if value == "":
                        value = "0.00"
                        float_value = 0.
                    else:
                        try:
                            float_value = float(value)
                        except:
                            # print(value)
                            float_value = None
                    result.append(float_value)
                    str_result.append(value)
                else:
                    result.append(None)
                    str_result.append(None)
                if result[-1] is None:
                    print(retrieved_info)
            # elif (stock_code, str(int(year) + 1)) in self.excels and "增长率" not in target_attribute:
            #     if target_attribute in self.excels[(stock_code, str(int(year) + 1))]['财务报表'][str(int(year) + 1)]:
            #         try:
            #             value = self.excels[(stock_code, str(int(year) + 1))]['财务报表'][year][target_attribute].replace(",", "").replace("，","").replace(" ", "")
            #             value = re.sub(r"[\(\)]", "", value)
            #         except:
            #             value = None
            #         if value == "":
            #             value = "0.00"
            #             float_value = 0.
            #         else:
            #             try:
            #                 float_value = float(value)
            #             except:
            #                 float_value = None
            #         result.append(float_value)
            #         str_result.append(value)
            #     else:
            #         result.append(None)
            #         str_result.append(None)
            #     if result[-1] is None:
            #         print(retrieved_info)
            else:
                result.append(None)
                str_result.append(None)
                # print(retrieved_info)
        if return_str:
            return str_result
        else:
            return result
        

    def exact_match(self, table, target_attribute):
        pass

    @property
    def prefix_checkpoint_path(self) -> str:
        """
        实现时直接返回prefixtuning的checkpoint路径
        """
        return None
