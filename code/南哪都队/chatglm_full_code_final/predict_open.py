from curses.ascii import isdigit
import json 
import os
from glm_components.query_company import BM25EnityExtractor
from glm_components.classifier import dump_classification_results
from glm_components import finance_table_query, company_info_query, personal_query, open_query, common_query, complex_query
from argparse import ArgumentParser
from collections import Counter
import pandas as pd
import regex as re
from finetune.table_qa.classifier import finance_compute_feaures, finance_features, load_equations, financial_alias_inv_mapping
from tqdm import tqdm
from transformers import AutoConfig, AutoModel, AutoTokenizer
from itertools import chain
import torch
from collections import defaultdict
import gc
from pathlib import Path



standard_financial_terms = list(set(finance_features + list(chain(*[key_word_list for key_word_list in load_equations().values()]))))


def get_args():
    parser = ArgumentParser()
    parser.add_argument("--enable_past_year", action="store_true", default=True)
    parser.add_argument('--refresh_classification', action='store_true')
    return parser.parse_args()


args = get_args()


def load_questions():
    """_summary_
    加载所有的问题
    """
    quests = []
    with open(os.path.join(os.path.dirname(__file__), "data/C-list-question.json"), 'r', encoding='utf8') as fp:
        for line in fp.readlines():
            quests.append(json.loads(line)['question'])
    return quests


def load_extracted():
    result = [json.loads(line) for line in open('finetune/table_qa/data/classification.jsonl', 'r', encoding='utf8').readlines()]
    for idx, res in enumerate(result):
        if isinstance(res, list):
            result[idx] = {
                "类型": "未知"
            }
    return result


def load_excels():
    header_set = defaultdict(lambda :0)
    def verify_header(header):
        return tuple(header) in {
            ('项目', '2021年12月31日', '2020年12月31日'), 
            ('项目', '2020年12月31日', '2019年12月31日'), 
            ('项目', '2019年12月31日', '2018年12月31日'),
            ('项目', '2019年12月31日'),
            ('项目', '2020年12月31日'),
            ('项目', '2021年12月31日'),
            ('项目', '2021年度', '2020年度'),
            ('项目', '2020年度', '2019年度'),
            ('项目', '2019年度', '2018年度'),
        }

    # attribute_fix_pattern = r"^([（\(].*[\)）])|([一二三四五六七八九十]*、)|(其中[\s:：]*)|([加减][\s:：]*)|[0-9]*|([^\u4e00-\u9fa5]*)"
    attribute_fix_pattern = r"([（\(].*[\)）])"
    attribute_list = []
    def preprocess_excels(excel, year):
        year_0, year_1 = str(int(year) - 1), year
        finance_dict = defaultdict(lambda :{})
        if '合并资产负债表' in excel and len(excel['合并资产负债表']) > 0 and verify_header(excel['合并资产负债表'][0]):
            # year_0, year_1 = excel['合并资产负债表'][0][2][:4], excel['合并资产负债表'][0][1][:4]
            for line in excel['合并资产负债表'][1:]:
                line[0] = re.sub(attribute_fix_pattern, "", line[0].replace(" ","").strip())
                # line[0] = line[0].replace(" ", "").strip()
                if line[0] in financial_alias_inv_mapping:
                    line[0] = financial_alias_inv_mapping[line[0]]
                attribute_list.append(line[0])
                if len(line) == 2:
                    if line[0] not in finance_dict[year] or finance_dict[year][line[0]] == "":
                        finance_dict[year][line[0]] = line[-1]
                else:
                    if line[0] not in finance_dict[year_0] or finance_dict[year_0][line[0]] == "":
                        finance_dict[year_0][line[0]] = line[-1]
                    if line[0] not in finance_dict[year_1] or finance_dict[year_1][line[0]] == "":
                        finance_dict[year_1][line[0]] = line[-2]
        if '合并现金流量表' in excel and len(excel['合并现金流量表']) > 0 and verify_header(excel['合并现金流量表'][0]):
            # year_0, year_1 = excel['合并现金流量表'][0][2][:4], excel['合并现金流量表'][0][1][:4]
            for line in excel['合并现金流量表'][1:]:
                line[0] = re.sub(attribute_fix_pattern, "", line[0].replace(" ","").strip())
                # line[0] = line[0].replace(" ", "").strip()
                if line[0] in financial_alias_inv_mapping:
                    line[0] = financial_alias_inv_mapping[line[0]]
                attribute_list.append(line[0])
                if len(line) == 2:
                    if line[0] not in finance_dict[year] or finance_dict[year][line[0]] == "":
                        finance_dict[year][line[0]] = line[-1]
                else:
                    if line[0] not in finance_dict[year_0] or finance_dict[year_0][line[0]] == "":
                        finance_dict[year_0][line[0]] = line[-1]
                    if line[0] not in finance_dict[year_1] or finance_dict[year_1][line[0]] == "":
                        finance_dict[year_1][line[0]] = line[-2]
        if '合并利润表' in excel and len(excel['合并利润表']) > 0 and verify_header(excel['合并利润表'][0]):
            # year_0, year_1 = excel['合并利润表'][0][2][:4], excel['合并利润表'][0][1][:4]
            for line in excel['合并利润表'][1:]:
                if '基本每股收益' in line[0] or '每股收益' == line[0]:
                    if len(line) == 2:
                        if line[0] not in finance_dict[year] or finance_dict[year][line[0]] == "":
                            finance_dict[year]['每股收益'] = line[-1]
                    else:
                        if line[-1].strip() != '':
                            finance_dict[year_0]['每股收益'] = line[-1]
                        if line[-2].strip() != '':
                            finance_dict[year_1]['每股收益'] = line[-2]
                else:
                    line[0] = re.sub(attribute_fix_pattern, "", line[0].replace(" ","").strip())
                    # line[0] = line[0].replace(" ", "").strip()
                    if line[0] in financial_alias_inv_mapping:
                        line[0] = financial_alias_inv_mapping[line[0]]
                    attribute_list.append(line[0])
                    if len(line) == 2:
                        if line[0] not in finance_dict[year] or finance_dict[year][line[0]] == "":
                            finance_dict[year][line[0]] = line[-1]
                    else:
                        if line[0] not in finance_dict[year_0] or finance_dict[year_0][line[0]] == "":
                            finance_dict[year_0][line[0]] = line[-1]
                        if line[0] not in finance_dict[year_1] or finance_dict[year_1][line[0]] == "":
                            finance_dict[year_1][line[0]] = line[-2]
        # if '股本' in excel and excel['股本'] != None:
        #     assert excel['股本'][1][0] == '期末余额'
        #     attribute_list.append('总股数')
        #     if excel['股本'][1][1] is not None:
        #         finance_dict[year_1]['总股数'] = excel['股本'][1][1].replace(" ","").strip().replace(",", "").replace("，", "")
        #     if excel['股本'][0][1] is not None:
        #         finance_dict[year_0]['总股数'] = excel['股本'][0][1].replace(" ","").strip().replace(",", "").replace("，", "")
        #     if excel['股本'][1][1] is not None and excel['股本'][0][1] is not None:
        #         finance_dict[year_1]['平均总股数'] = str((float(finance_dict[year_1]['总股数']) + float(finance_dict[year_0]['总股数'])) / 2)
        # if '主要会计数据和财务指标' in excel:
            # header_set[tuple(excel['主要会计数据和财务指标'][0][:3])] += 1
        excel['财务报表'] = finance_dict
        return excel

    def process_single_column_excel(excel, year):
        # excel = excel[1:]
        # financial_dict = {}
        # for k, v in excel:
        #     if k not in title_list:
        #         financial_dict[k] = v
        # return financial_dict
        pass

    def load_merged_excels():
        excel_mapping = {}
        file_list = [line.strip().replace(".pdf", ".json") for line in open('data/C-list-pdf-name.txt', 'r', encoding='utf8').readlines()]
        for file in tqdm(file_list, desc="preprocessing excels"):
            filename = os.path.basename(file)
            _, full_name, stock_code, short_name, year, _ = filename.split("__")
            year = year.replace("年", "")
            if os.path.exists(os.path.join('data/processed_excels', file)):
                if args.enable_past_year:
                    excel_mapping[(stock_code, year)] = preprocess_excels(json.load(open(os.path.join('data/processed_excels', file), 'r', encoding='utf8')), year)
                else:
                    financial_dict = process_single_column_excel(json.load(open(os.path.join('data/final_excels', file), 'r', encoding='utf8')), year)
                    excel_mapping[(stock_code, year)] = json.load(open(os.path.join('data/processed_excels', file), 'r', encoding='utf8'))
                    excel_mapping[(stock_code, year)]['财务报表'] = financial_dict

        return excel_mapping

    def load_company_infos():
        company_mapping = {}
        file_list = [line.strip().replace(".pdf", ".json") for line in open('data/C-list-pdf-name.txt', 'r', encoding='utf8').readlines()]
        for file in file_list:
            filename = os.path.basename(file)
            _, full_name, stock_code, short_name, year, _ = filename.split("__")
            year = year.replace("年", "")
            if os.path.exists(os.path.join('data/processed_excels', file)):
                company_mapping[(stock_code, year)] = json.load(open(os.path.join('data/company_info',file), 'r', encoding='utf8'))
        return company_mapping

    excel_mapping = load_merged_excels()
    company_infos = load_company_infos()
    for k in excel_mapping:
        excel_mapping[k]['公司信息'] = company_infos[k]
    new_counter = {}
    old_counter = Counter(attribute_list)
    for k in finance_features:
        if k in old_counter:
            new_counter[k] = old_counter[k]
        else:
            print(k)
    print(json.dumps(new_counter, ensure_ascii=False, indent=4))
    print(json.dumps({k:v for k,v in old_counter.items() if v > 20}, ensure_ascii=False, indent=4))
    # print(json.dumps({','.join(k):v for k,v in header_set.items() if v > 20}, ensure_ascii=False, indent=4))
    return excel_mapping


def extract_company_names(extracted_info):
    res = []
    for line in extracted_info:
        if '公司名称' in line:
            res.append(line['公司名称'])
        else:
            res.append('无')
    return res


def query_stock_code(companies):
    extractor = BM25EnityExtractor()
    return extractor.query_company_names(companies)


def set_stock_code(company_infos):
    company_names = extract_company_names(company_infos)
    stock_codes = query_stock_code(company_names)
    for company_info, stock_code in zip(company_infos, stock_codes):
        if '公司名称' in company_info:
            company_info['股票代码'] = stock_code
    return company_infos

def load_model():
    model_path = "model/chatglm2-6b"
    config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
    config.prefix_projection = False
    config.pre_seq_len = 128
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    tokenizer.padding_size = 'left'
    model = AutoModel.from_pretrained(model_path, config=config, trust_remote_code=True)
    model = model.half()
    model = model.to("cuda")
    return model, tokenizer


def load_frames():
    title_list = ['所有者权益：', '所有者权益', '教育程度', '学历结构类别', '研发人员年龄构成', '专业构成', '研发人员学历结构', '研发人员年龄结构',
    '教育程度类别', '专业构成类别', '', '学历结构类别 学历结构人数', '项目', '备', '列）', '研发人员学历', '非流动负债：',
    '每股收益：', '-', '非流动资产：', '按经营持续性分类', '按所有权归属分类', '总额', '流动资产：']
    brackets_pattern = r'([(（][^)）]*[)）])'
    result = defaultdict(lambda :[])
    counter = defaultdict(int)
    file_list = [line.strip().replace(".pdf", ".json") for line in open('data/C-list-pdf-name.txt', 'r', encoding='utf8').readlines()]
    for file in tqdm(file_list, desc="loading frames"):
        file = os.path.join('data/final_excels', file)
        filename = os.path.basename(file)
        _, full_name, stock_code, short_name, year, _ = filename.split("__")
        sample_dict = {}
        if not os.path.exists(file):
            print(file)
            continue
        for line in json.load(open(file, 'r', encoding='utf8'))[1:]:
            if len(line) != 2:
                continue
            k, v = line
            k = re.sub(brackets_pattern, "", k)
            if len(k) < 2:
                continue
            if k in sample_dict:
                if sample_dict[k] == 0 and v != 0:
                    sample_dict[k] = [v]
            else:
                sample_dict[k] = [v]
                counter[k] += 1
        if len(sample_dict) == 0:
            continue
        sample_dict['公司的中文名称'] = sample_dict['long_company_name']
        sample_dict['公司的中文缩写'] = sample_dict['short_company_name']
        sample_dict.pop('long_company_name')
        sample_dict.pop('short_company_name')
        df = pd.DataFrame(sample_dict, index=[stock_code])
        df = df.drop(list(set(title_list) & set(df.columns)), axis=1)
        result[year.replace("年", "")].append(df)
    filtered_columns = [k for k, v in counter.items() if v >= 200]
    for k, v in result.items():
        for idx, item in enumerate(v):
            v[idx] = item[list(set(item.columns) & set(filtered_columns))]
    # print(result['2019'])
    result_list = []
    for k, v in tqdm(result.items(), desc="merging frames, columns:{}".format(len(filtered_columns))):
        result_list.append(pd.concat(v, axis=0).assign(年份=k))
    # print(result['2019'])
    return pd.concat(result_list, axis=0)

def get_response(company_infos):
    excels = load_excels()
    questions = load_questions()
    # model, tokenizer = load_model()
    # for question, company_info in zip(questions, company_infos):
    #     if '公司名称' in company_info is not None and company_info['股票代码'] is None:
    #         print(question, company_info['公司名称'])
    # finance_querier = finance_table_query(model, tokenizer, excels, finance_features, finance_compute_feaures, args)
    # finance_answers = finance_querier.run_query(questions, company_infos, batch_size=16)
    # complex_querier = complex_query(None, tokenizer, excels, frame=load_frames())
    # complex_answers = complex_querier.run_query(questions, company_infos, batch_size=16)
    # personal_querier = personal_query(model, tokenizer, excels)
    # personal_answers = personal_querier.run_query(questions, company_infos, batch_size=16)
    # company_querier = company_info_query(model, tokenizer, excels)
    # company_answers = company_querier.run_query(questions, company_infos, batch_size=16)
    # common_querier = common_query(None, tokenizer, excels)
    # model.cpu()
    # del model
    # del personal_querier
    # del finance_querier
    # del company_querier
    # gc.collect()
    tokenizer = AutoTokenizer.from_pretrained("model/chatglm2-6b", trust_remote_code=True)
    # common_answers = common_querier.run_query(questions, company_infos)
    open_querier = open_query(None, tokenizer, excels)
    open_answers = open_querier.run_query(questions, company_infos, batch_size=1, log=True)
    result = []
    for idx in range(len(company_infos)):
        if company_infos[idx]['类型'] == '开放问题' and open_answers[idx] is not None:
            result.append(open_answers[idx])
    return result


def dump_answers(json_data):
    with open('result/open_query_result.json', 'w', encoding='utf8') as fp:
        for item in json_data:
            # assert item is not None
            fp.write(json.dumps(item, ensure_ascii=False) + "\n")


def inference_flow():
    # 生成分类结果
    dump_classification_results(refresh=args.refresh_classification)
    # 提取公司代码
    company_infos = set_stock_code(load_extracted())
    # 匹配pdf/表格
    answers = get_response(company_infos)
    dump_answers(answers)


if __name__ == '__main__':
    inference_flow()
    # load_frames()