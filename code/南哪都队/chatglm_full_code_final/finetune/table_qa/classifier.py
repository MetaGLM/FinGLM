import json
import os
from collections import defaultdict
from itertools import chain
import regex as re
import numpy as np
from pathlib import Path
from collections import Counter
import cn2an
from multiprocessing import Manager

postfix = [
    "总额",
    "总值",
    "金额",
    '总计',
    '数额'
]

ratio = [
    "比率",
    "比值"
]

growth = [
    "增长率"
]

ratio_template = [
    "<attribute>"
]


finance_features_alias = {
    "研发费用": ["研发经费", "企业研发经费", '花费在研发上的费用'],
    # '收回投资所得的现金': ['收回投资所得现金'],
    '净利润': ['利润', '净利润总额'],
    '利息支出': ['支出的利息'],
    '归属于母公司所有者的净利润': ['归属母公司所有者净利润', '归属母公司净利润', '归属母公司所有者的净利润', '归属于母公司股东的净利润'],
    '归属于母公司所有者权益合计': ['归属于母公司所有者权益（或股东权益）合计', '归属于母公司的所有者权益', '归属于母公司的所有者权益', '归属于母公司所有者权益'],
    '资产合计': ['总资产', '资产总额', '资产总计', '资产总金额'],
    '负债合计': ['总负债', '负债总额', '负债总金额'],
    '收回投资收到的现金': [
        '收到的投资回收现金', '收回投资所得现金', '收回投资所得的现金','收回投资所收到的现金', 
        '收回投资所获得的现金', '收回投资所得到的现金', '收回的投资所得到的现金','收回的投资所得现金', 
        '收回的投资收入', '收回的投资收到的现金', '收回的投资现金', '收到的投资收回的现金'
    ],
    '无形资产': ['无形资产价值'],
    '每股净资产': ['每股净资产价值', '每股的净资产'],
    '流动负债合计': ['流动负债', '流动负债总计'],
    '流动资产合计': ['流动资产', '流动资产总计'],
    '期末现金及现金等价物余额': ['现金及现金等价物余额','期末的现金及现金等价物余额', '现金及现金等价物'],
    '经营活动产生的现金流量': ['经营现金流量'],
    '应付职工薪酬': ['应付的职工薪酬', '需支付的职工薪酬', '职工薪酬'],
    '对联营企业和合营企业的投资收益': ['对其联营企业和合营企业的投资收益'],
    '税金及附加': ['营业税金及附加费用', '营业税金及附加'],
    "固定资产": ['固定资产总额'],
    '非流动负债合计': ['非流动负债', '非流动负债总计'],
    '非流动资产合计': ['非流动资产'],
    '每股经营现金流量': ['每股的经营现金流量'],
    '综合收益': ['综合收益总额', '综合收益总计'],
    '每股收益': ['基本每股收益'],
    '股本': ['实收资本', '总股数'],
    '其他综合收益': ['他综合收益'],
    '所有者权益合计': ['所有者权益总计', '股东权益合计', '净资产'],
    '货币资金': ['货币总额', '货币']
}

finance_compute_alias = {
    "企业研发经费占费用比例": ["企业研发经费占费用的比例", "企业研发经费占总费用的比例", '企业研发经费在总费用中的比例', '研发经费占费用的比例', '研发经费占费用比例', 
                    '研发费用占总费用的比例', '研发费用占总费用的比值', '研发费用占总费用比例', '企业研发费用占总费用比例'],
    "企业研发经费与营业收入比值": ['企业研发经费与营业收入比值', '企业研发经费与营业收入的比值', '研发经费与营业收入的比值', '研发经费与营业收入比值'],
    "企业研发经费与利润比值": ['企业研发经费与利润的比值', '企业的研发经费与利润比值', '研发经费与利润的比值', '研发经费与利润比值', '企业研发经费与利润之比'],
    '投资收益占营业收入比率': ['投资收益占营业收入的比率', '投资收益占营业收入的比例', '投资收益占营业收入比例'],
    '三费比重': ['三费（销售费用、管理费用和财务费用）占比', '三费销售费用、管理费用和财务费用占比', "三费占比"],
}

finance_compute_feaures = [
    "企业研发经费占费用比例",
    "企业研发经费与营业收入比值",
    "企业研发经费与利润比值",
    '流动比率', 
    '速动比率',
    '营业利润率', 
    '资产负债比率', 
    '现金比率',
    '非流动负债比率',
    '流动负债比率', 
    '净资产收益率',
    '净利润率',
    '营业成本率',
    '管理费用率',
    '三费比重',
    '管理费用率', 
    '财务费用率',  
    '毛利率',
    # '净资产增长率',
    '投资收益占营业收入比率',
    # '销售费用增长率',
    # '财务费用增长率',
    # '管理费用增长率',
    # '研发费用增长率',
    # '总负债增长率',
    # '流动负债增长率',
    # '货币资金增长率',
    # '固定资产增长率',
    # '无形资产增长率',
    # '总资产增长率',
    # '营业收入增长率',
    # '营业利润增长率',
    # '净利润增长率',
    # '现金及现金等价物增长率',
    # '投资收益增长率',
    '每股经营现金流量',
    '每股净资产', 
    '每股收益',
]

finance_features = [
    '股本',
    '研发费用', 
    '公允价值变动收益',
    '净利润',  
    '存货',
    # '净资产', 
    '所有者权益合计',
    '利息支出', 
    '利息收入', 
    '利润总额',
    '固定资产', 
    '对联营企业和合营企业的投资收益',
    '应付职工薪酬', 
    '应收款项融资', 
    '归属于母公司所有者权益合计', 
    '归属于母公司所有者的净利润',
    '所得税费用', 
    '投资收益',
    '收回投资收到的现金', 
    '无形资产', 
    '期末现金及现金等价物余额',
    '流动资产合计',
    '流动负债合计',
    '非流动负债合计',
    '研发费用', 
    '筹资活动产生的现金流量', 
    '管理费用', 
    '经营活动产生的现金流量',
    '其他综合收益', 
    '营业利润', 
    '营业外支出', 
    '营业外收入',
    '营业成本', 
    '营业收入',
    '税金及附加', 
    '衍生金融资产', 
    '负债合计', 
    '财务费用', 
    '货币资金',  
    '资产合计', 
    # '负债合计',
    '销售费用', 
    '其他非流动金融资产',
    # '总股数',
    '经营活动产生的现金流量净额',
    # '平均总股数'
]

financial_terms = set(finance_features + finance_compute_feaures + list(chain(*[alias for k, alias in (finance_compute_alias|finance_features_alias).items()])))
financial_alias_inv_mapping = {item:k for k, v in (finance_compute_alias|finance_features_alias).items() for item in v}

def load_equations():
    equation_dict = {}
    with open(os.path.join(os.path.dirname(__file__), 'data/equations.txt'), encoding='utf8') as fp:
        lines = fp.readlines()
        for line in lines:
            feature, equation = line.split("=")
            equation = equation.strip()
            equation_to_eval = equation
            elements = [elem.strip().replace("上年", "") for elem in re.findall(r"[^*/\(\)+-]+", equation)]
            elem_set = set()
            elem_recover_dict = {}
            for elem in elements:
                if elem == "":
                    continue
                if elem in financial_alias_inv_mapping:
                    elem_recover_dict[financial_alias_inv_mapping[elem]] = elem
                    equation_to_eval = equation_to_eval.replace(elem, financial_alias_inv_mapping[elem])
                    elem = financial_alias_inv_mapping[elem]
                    elem_set.add(elem)
                else:
                    elem_recover_dict[elem] = elem
                    elem_set.add(elem)
                assert elem in finance_features, f"{elem}"
            elem_list = sorted(list(elem_set), key=lambda x:equation.index(elem_recover_dict[x]))
            equation_dict[feature] = {
                "equation": equation.strip(),
                "equation_to_eval": equation_to_eval.strip(),
                "elems": elem_list,
                "elem_recover_dict": elem_recover_dict
            }
    return equation_dict

def load_questions():
    """_summary_
    加载所有的问题
    """
    quests = []
    with open(os.path.join(os.path.dirname(__file__), "../../data/chatglm_llm_fintech_raw_dataset/A-list-question.json"), 'r') as fp:
        for line in fp.readlines():
            quests.append(json.loads(line)['question'])
    return quests

def load_extracted():
    quests = []
    with open(os.path.join(os.path.dirname(__file__), "../../data/temp/retrieved_info.jsonl"), 'r') as fp:
        for line in fp.readlines():
            data_json = json.loads(line)
            if data_json['info_dict']['类型'] == '财务问题':
                quests.extend(data_json['info_dict']['关键词'])
    return sorted(list(set(quests)))


# def match_question():
#     pass


# def match_all():
#     category_mapping = defaultdict(lambda :[])
#     questions = load_questions()
#     for question in questions:
#         pass


def match_subset_word(subword, full_word):
    category_mapping = defaultdict(lambda :[])
    questions = load_questions()
    for question in questions:
        if subword in question and full_word not in question:
            print(question)


def analyse_growth():
    growth_keyword = [[feature,feature.replace("增长率", "的增长率")] for feature in finance_compute_feaures if feature.endswith("增长率")]
    growth_keyword = list(chain(*growth_keyword))
    for question in load_questions():
        if "2019" in question or "2020" in question or "2021" in question:
            if "增长" in question:
                found = False
                for word in growth_keyword:
                    if word in question:
                        found = True
                if not found:
                    print(question)

def load_category_keywords():
    finance_keywords = set()
    for key, alias_list in finance_compute_alias.items():
        finance_keywords.add(key)
        finance_keywords |= set(alias_list)
    for key, alias_list in finance_features_alias.items():
        finance_keywords.add(key)
        finance_keywords |= set(alias_list)
    finance_keywords |= set(finance_features) | set(finance_compute_feaures)
    finance_keywords |= set(growth_word.replace("增长率", "的增长率") for growth_word in finance_compute_feaures if "增长率" in growth_word)
    finance_keywords = list(finance_keywords)
    human_resource_keywords = ['员工', '职工总数', '博士', '硕士', '本科', '人员', '职工人数', '职工总人数']
    import sys
    sys.path.append("finetune/table_qa")
    from company_info import company_attribute_alias
    company_info_keywords = set()
    for k, v in company_attribute_alias.items():
        company_info_keywords.add(k)
        company_info_keywords |= set(v)
    return {
        "财务": sorted(finance_keywords, key=lambda x:len(x), reverse=True),
        "人员": sorted(human_resource_keywords, key=lambda x:len(x), reverse=True),
        '公司': sorted(company_info_keywords, key=lambda x:len(x), reverse=True)
    }


def find_company_name(question):
    company_names = sorted(extract_all_company_name(), key=lambda x:len(x), reverse=True)
    question = re.sub(r"[\(\)（）]", "", question)
    found = 0
    for company_name in company_names:
        if company_name in question:
            question = question.replace(company_name, "{company_name}")
            found += 1
            break
    if found == 1:
        return company_name
    else:
        return

category_mapping = load_category_keywords()

def process_open(idx, question, company_name, year):
    return {"id": idx, "question": question, "info_dict": {"类型": "开放问题", "公司名称": company_name, "年份": year}}



def extract_answer_template(original_question, matched_keywords, standard_term, company_name, year):
    if len(matched_keywords) == 2:
        if "小数" in original_question:
            answer_template = f"{company_name}{year}年的" + matched_keywords[0] + "是{value_1:.2f}元，" + matched_keywords[1] + "是{value_2:.2f}元。"
        else:
            answer_template = f"{company_name}{year}年的" + matched_keywords[0] + "是{value_1}元，" + matched_keywords[1] + "是{value_2}元。"
    elif len(matched_keywords) == 1:
        if "增长率" in matched_keywords[0]:
            last_year = str(int(year) - 1)
            keyword_prefix = matched_keywords[0].replace("增长率", "")
            answer_template = f"{company_name}{last_year}年的{keyword_prefix}是" + "{value_1}元，" + f"{year}年的{keyword_prefix}是" + "{value_2}元，" + \
                    f"根据公式{matched_keywords[0]}=({keyword_prefix}-上年{keyword_prefix})/上年{keyword_prefix}，得出结果{company_name}{year}年的{matched_keywords[0]}是"+ "{value_3:.2f}%。"
        elif standard_term[0] in finance_compute_feaures:
            answer_template = None
        else:
            if "小数" in original_question:
                answer_template = f"{company_name}{year}年的" + matched_keywords[0] + "是{value_1:.2f}元。" 
            else:
                answer_template = f"{company_name}{year}年的" + matched_keywords[0] + "是{value_1}元。"
    else:
        return None
    return answer_template


def process_finance(idx, question, company_name, year):
    if len(year) != 1:
        return
    year = year[0]
    input_question = question
    question = question.replace("的增长率", '增长率')
    original_question = question
    finance_mapping = category_mapping['财务']
    keyword_found = 0
    matched = []
    for keyword in finance_mapping:
        if keyword in question:
            keyword_found += 1
            question = question.replace(keyword, "{attribute}")
            matched.append(keyword)
    if keyword_found != 0:
        question = re.sub(r"[\(\)（）]", "", question)
        question = re.sub(company_name, "{company_name}", question)
        question = re.sub(r"(2019|2020|2021)年度?", "{year}", question)
        matched_keywords = sorted(matched, key=lambda x: re.sub(r"[\(\)（）]", "", original_question).index(x))
        standard_term = []
        for index in range(len(matched_keywords)):
            if matched_keywords[index] not in financial_terms:
                return matched_keywords
            else:
                if matched_keywords[index] in financial_alias_inv_mapping:
                    # matched_keywords[index] = financial_alias_inv_mapping[matched_keywords[index]]
                    standard_term.append(financial_alias_inv_mapping[matched_keywords[index]])
                else:
                    standard_term.append(matched_keywords[index])
                # if matched_keywords[index] + "增长率" in original_question:
                #     matched_keywords[index] = matched_keywords[index] + "增长率"
                #     standard_term[index] = standard_term[index] + "增长率"
                # if matched_keywords[index].endswith("增长率"):
                #     keyword_prefix = matched_keywords[index].replace("增长率", "")
                #     if keyword_prefix in financial_alias_inv_mapping:
                #         standard_term[index] = financial_alias_inv_mapping[keyword_prefix] + "增长率"
                #     else:
                #         standard_term[index] = matched_keywords[index]
                #     print(matched_keywords[index], standard_term[index])    
                if "增长率" not in matched_keywords[index] and "增长率" in question:
                    matched_keywords[index] = matched_keywords[index] + "增长率"
                    standard_term[index] = standard_term[index] + "增长率"
                    question = question.replace("增长率", "")
                    # print(matched_keywords[index], standard_term[index])
        assert len(standard_term) == len(matched_keywords)
        answer_template = extract_answer_template(original_question, matched_keywords, standard_term, company_name, year)
        if answer_template is None:
            info_dict = {
                "类型": "财务问题",
                "关键词": standard_term,
                "公司名称": company_name, 
                "年份": [year]
            }
        else:
            info_dict = {
                "类型": "财务问题",
                "关键词": standard_term,
                "公司名称": company_name, 
                "年份": [year],
                "回答模板": answer_template
            }
        return {"id": idx, "question": input_question, "info_dict": info_dict}
    else:
        return


def process_company(idx, question, company_name, year):
    keywords = category_mapping['公司']
    for keyword in keywords:
        if keyword in question:
            if len(re.findall(r"(20[1290]{2}[年至-]+20[1290]{2})", question)) > 0:
                year = list(map(str, list(range(int(year[0]), int(year[1])+1, 1))))
            info_dict = {
                "类型": "公司问题",
                "公司名称": company_name, 
                "年份": year
            }
            return {"id": idx, "question": question, "info_dict": info_dict}
    return



def process_employee(idx, question, company_name, year):
    keywords = category_mapping["人员"]
    question = question.replace("博士眼镜", "").replace("鹏博士电信", "")
    for keyword in keywords:
        if keyword in question:
            info_dict = {
                "类型": "人员问题",
                "公司名称": company_name, 
                "年份": year
            }
            return {"id": idx, "question": question, "info_dict": info_dict}
    return


def process_common(idx, question):
    return {"id": idx, "question": question, "info_dict": {"类型": "常识问题"}}


def read_open_question_format():
    json_data = [json.loads(line) for line in open('documents/open_questions_annotated.txt').readlines()]
    format_mapping = {}
    for json_item in json_data:
        format_mapping[json_item['问题']] = json_item['关键词']
    return format_mapping


def open_question_generator():
    company_names = extract_all_company_name()
    year_list = ['2021年度', '2020年度', '2019年度', '2019年', '2020年', '2021年']
    templates = read_open_question_format()
    while True:
        template = np.random.choice(list(templates.keys()), 1)[0]
        year = np.random.choice(year_list, 1)[0]
        company_name = np.random.choice(company_names, 1)[0]
        yield {
            "question": template.format(company=company_name, year=year),
            "info_dict": {
                "类型": "开放问题",
                "关键词": templates[template],
                "公司名称": company_name,
                "年份": [year.replace("年", "").replace("度", "")]
            } 
        }

manager = Manager()
company_templates = manager.list()
personal_templates = manager.list()

def process_questions(idx, question):
    original_question = question
    question = re.sub(r"[\(\)（）]", "", question)
    if "2019" in question or "2020" in question or "2021" in question:
        year = re.findall(r"(2019|2020|2021)[年度]{0,2}", question)
        company_name = find_company_name(question)
        if company_name is None:
            return
        
        if "简要介绍" in question or '简要分析' in question:
            if process_finance(idx, question, company_name, year) is None and '硕士人数' not in question and '博士及以上人数' not in question:
                info_dict = {
                    "类型": "开放问题",
                    "公司名称": company_name, 
                    "年份": year
                }
                return {"id": idx, "question": original_question,  "info_dict": info_dict}

        financial_result = process_finance(idx, question, company_name, year)
        if financial_result is not None:
            if isinstance(financial_result, list):
                print(question, financial_result)
                return
            return financial_result
            
        company_result = process_company(idx, question, company_name, year)
        if company_result is not None:
            q = question.replace(company_name, "{company_name}")
            for idx, y in enumerate(year):
                q = q.replace(y, f"{{year_{idx+1}}}")
            company_templates.append(q)
            return company_result
        personal_result = process_employee(idx, question, company_name, year)
        if personal_result is not None:
            q = question.replace(company_name, "{company_name}")
            for idx, y in enumerate(year):
                q = q.replace(y, f"{{year_{idx+1}}}")
            personal_templates.append(q)
            return personal_result
        return process_open(idx, question, company_name, year)
    else:
        return process_common(idx, question)
    


def category_rule_classifier():
    category_mapping = load_category_keywords()
    questions = load_questions()
    counter = defaultdict(int)
    info_dict_list = []
    from tqdm import tqdm
    from multiprocessing import Pool
    pool = Pool(8)
    async_results = []
    # lock = Lock()
    for idx, question in enumerate(tqdm(questions)): 
        async_results.append(pool.apply_async(process_questions, (idx, question)))
    for res in tqdm(async_results):
        answer = res.get()
        if answer is not None:
            counter[answer['info_dict']['类型']] += 1
            if '2019-2021' in answer['question']:
                answer['info_dict']['年份'] = ['2019', '2020', '2021']
            info_dict_list.append(answer)
        else:
            counter['失败'] += 1
    pool.close()
    pool.join()
    return info_dict_list, counter


def category_counter():
    category_mapping = load_category_keywords()
    questions = load_questions()
    counter = {
        "常识": 0,
        "财务": 0,
        "人员": 0,
        "公司": 0,
        "开放": 0
    }
    for question in questions:
        if "2019" in question or "2020" in question or "2021" in question:
            if "简要介绍" in question or '简要分析' in question:
                counter['开放'] += 1
                continue
            found = 0
            matched_keywords = []
            for _type in ['财务', '人员', '公司']:
                for keyword in category_mapping[_type]:
                    if keyword == '博士':
                        question = question.replace("博士眼镜", "").replace("鹏博士电信", "")
                    if keyword in question:
                        counter[_type] += 1
                        found += 1
                        matched_keywords.append(keyword)
                        break
            if found == 0:
                # print(f"not found:{question} {matched_keywords}")
                counter['开放'] += 1
 
        else:
            counter['常识'] += 1
    return counter


def extract_all_company_name():
    """_summary_
    从pdf名字种提取所有的公司简称、股票代码、年份等document的metadata
    Returns:
        _type_: _description_
    """
    from pathlib import Path
    import pandas as pd
    alltxt_path = os.path.join(os.path.dirname(__file__), "../../data/alltxt")
    result = []
    for file in Path(alltxt_path).rglob("*.txt"):
        basic_info = os.path.basename(file).split("__")[:-1]
        result.append(basic_info)
    df = pd.DataFrame(result, columns=["date", "full_name", "stock_code", "short_name", "year"])
    return sorted(list(set(df['full_name'].tolist() + df['short_name'].tolist())), key=lambda x:len(x), reverse=True)



def extract_template():
    category_mapping = load_category_keywords()
    year_pattern = r'(2019|2020|2021)年度?'
    company_names = extract_all_company_name()
    category_mapping = sorted(category_mapping['财务'], key=lambda key:len(key), reverse=True)
    questions = load_questions()
    failed_count = 0
    template = set()
    info_dict_list = []
    for idx, question in enumerate(questions):
        info_dict = {}
        if "2019" in question or "2020" in question or "2021" in question:
            question = re.sub(r"[\(\)（）]", "", question)
            # question = re.sub(r"[2两]位", "<digits>", question)
            question = re.sub(year_pattern, "{year}" ,question)
            question = re.sub("增长率", "", question)
            # print(question)
            if "简要介绍" in question or '简要分析' in question:
                continue
            found = 0
            matched = []
            for keyword in category_mapping:
                if keyword in question:
                    question = question.replace(keyword, "{attribute}")
                    matched.append(keyword)
                    found += 1
            if found != 0:
                found = 0
                wrong_list = ['期末', '安徽', '每股的', '净', '付', '比值', '度', '量', '固', '末', '利']
                for company_name in company_names:
                    if company_name in question:
                        question = question.replace(company_name, "{company_name}")
                        found += 1
                if found == 0:
                    # print(0, question)
                    failed_count += 1
                elif found > 1:
                    # print(">1", question)
                    failed_count +=1
                elif sum([(word in question) * 1 for word in wrong_list]) > 0:
                    # print(question, matched)
                    pass
                else:
                    if "集团" in question or "公司" in question:
                        continue
                    template.add(question)
            else:
                # print(question)
                pass
    return template

def random_financial_headers():
    title_list = ['所有者权益：', '所有者权益', '教育程度', '学历结构类别', '研发人员年龄构成', '专业构成', '研发人员学历结构', '研发人员年龄结构',
    '教育程度类别', '专业构成类别', '', '学历结构类别 学历结构人数', '项目', '备', '列）', '研发人员学历', '非流动负债：',
    '每股收益：', '-', '非流动资产：', '按经营持续性分类', '按所有权归属分类', '总额']
    def get_headers(json_data):
        valid_titles = []
        if '合并资产负债表' in json_data:
            for line in json_data['合并资产负债表'][1:]:
                try:
                    float(line[-1].replace(",", "").replace("，", ""))
                    if line[0] not in title_list:
                        valid_titles.append(line[0])
                except:
                    pass
        
        if '合并利润表' in json_data:
            for line in json_data['合并利润表'][1:]:
                try:
                    float(line[-1].replace(",", "").replace("，", ""))
                    if line[0] not in title_list:
                        valid_titles.append(line[0])
                except:
                    pass
        
        if '合并现金流量表' in json_data:
            for line in json_data['合并现金流量表'][1:]:
                try:
                    float(line[-1].replace(",", "").replace("，", ""))
                    if line[0] not in title_list:
                        valid_titles.append(line[0])
                except:
                    pass
        
        return list(set(valid_titles))
    
    titles_occurences = []
    
    for file in Path('data/processed_excels').rglob("*.json"):
        json_data = json.load(open(file, 'r'))
        titles_occurences.extend(get_headers(json_data))
    
    attributes = {re.sub(r"[\(（].*[\)）]?", "", k):v for k,v in Counter(titles_occurences).items() if v >= 2000}
    # print('|'.join(attributes))
    attributes = list(attributes.keys())
    print(len(attributes))
    while True:
        attribute = attributes[np.random.randint(0, len(attributes))]
        if '总' not in attribute and '合' not in attribute and len(attribute) < 8 and np.random.uniform(0, 1) < 0.1:
            revised_attribute = attribute + postfix[np.random.randint(0, len(postfix))]
            # if np.random.uniform(0, 1) < 0.1:
            #     rand_idx = np.random.randint(0, len(revised_attribute))
            #     revised_attribute = revised_attribute[:rand_idx] + revised_attribute[rand_idx+1:]
            yield attribute, revised_attribute
        elif attribute in finance_features_alias and np.random.uniform(0, 1) < 0.4:
            revised_attribute = np.random.choice(finance_features_alias[attribute], 1)[0]
            # if np.random.uniform(0, 1) < 0.1:
            #     rand_idx = np.random.randint(0, len(revised_attribute))
            #     revised_attribute = revised_attribute[:rand_idx] + revised_attribute[rand_idx+1:]
            yield attribute, revised_attribute
        else:
            yield attribute, attribute


def financial_question_generator(growth=False):
    templates = list(extract_template()) + [
        '请提供{year}{company_name}{attribute}的详细数据。',
        '告诉我{year}{company_name}{attribute}的具体情况。',
        '描述一下{year}的{company_name}{attribute}和{attribute}的详细信息。',
        '根据{year}{company_name}的年报，请简要介绍报告期内公司{attribute}的情况，保留2位小数。'
    ]
    company_names = extract_all_company_name()
    equation_attribute_list = list(load_equations().keys())
    year_list = ['2021年度', '2020年度', '2019年度', '2019年', '2020年', '2021年']
    attributes = iter(random_financial_headers())
    while True:
        template = np.random.choice(list(templates), 1)[0]
        year = np.random.choice(year_list, 1)[0]
        company_name = np.random.choice(company_names, 1)[0]
        slots_found = len(re.findall("{attribute}", template))
        question = template.replace("{company_name}", company_name).replace("{year}", year)
        if slots_found == 1:
            keyword, attribute = next(attributes)
            if growth:
                while len(attribute) > 8:
                    keyword, attribute = next(attributes)
                if np.random.uniform(0, 1) < 0.4:
                    keyword, attribute = keyword+"增长率", attribute+"增长率"
                else:
                    keyword = np.random.choice(equation_attribute_list)
                    attribute = keyword
                sample = {
                    "question": question.format(attribute=attribute),
                    "info_dict": {
                        "类型": "财务问题",
                        "关键词": [keyword],
                        "公司名称": company_name,
                        "年份": [year.replace("年", "").replace("度", "")],
                    } 
                }
                answer_template = extract_answer_template(sample['question'], [attribute], [keyword], company_name, year.replace("年", "").replace("度", ""))
                if answer_template is not None:
                    sample['info_dict']['回答模板'] = answer_template
                yield sample
            else:
                sample = {
                    "question": question.format(attribute=attribute),
                    "info_dict": {
                        "类型": "财务问题",
                        "关键词": [keyword],
                        "公司名称": company_name,
                        "年份": [year.replace("年", "").replace("度", "")],
                    } 
                }
                answer_template = extract_answer_template(sample['question'], [attribute], [keyword], company_name, year.replace("年", "").replace("度", ""))
                if answer_template is not None:
                    sample['info_dict']['回答模板'] = answer_template
                yield sample
        elif slots_found == 2 and not growth:
            keyword_1, attribute_1 = next(attributes)
            keyword_2, attribute_2 = next(attributes)
            if keyword_1 == keyword_2:
                continue
            question = question.replace("{attribute}", attribute_1, 1).replace("{attribute}", attribute_2, 1)
            sample = {
                "question": question,
                "info_dict": {
                    "类型": "财务问题",
                    "关键词": [keyword_1, keyword_2],
                    "公司名称": company_name,
                    "年份": [year.replace("年", "").replace("度", "")],
                } 
            }
            answer_template = extract_answer_template(sample['question'], [attribute_1, attribute_2], [keyword_1, keyword_2], company_name, year.replace("年", "").replace("度", ""))
            if answer_template is not None:
                sample['info_dict']['回答模板'] = answer_template
            yield sample


def load_complex_query_templates():
    sql_templates = json.load(open('documents/complex_query/sql_mapping.json', 'r'))
    answer_templates = json.load(open('documents/complex_query/answer_template.json', 'r'))
    question_templates = {
        k: [line.strip() for line in open(f'documents/complex_query/{k}.txt').readlines() if line.strip() != ""] for k in sql_templates
    }
    template_names = list(sql_templates.keys())
    prob = []
    for name in template_names:
        if "cross_year" not in name:
            prob.append(1.)
        else:
            prob.append(0.25)
    sum_prob = sum(prob)
    prob = [p/sum_prob for p in prob]
    while True:
        template_name = np.random.choice(template_names, 1, prob)[0]
        yield template_name, np.random.choice(question_templates[template_name], 1)[0], sql_templates[template_name], answer_templates[template_name]


def load_cities():
    cities = []
    for file in Path("data/final_excels").rglob("*.json"):
        json_data = json.load(open(file, 'r', encoding='utf8'))
        for line in json_data:
            if line[0] == '注册省份' or line[0] == '注册城市' and isinstance(line[1], str):
                cities.append(line[1])
    counter = Counter(cities)
    # print(counter)
    keys = list(counter.keys())
    values = list(counter.values())
    while True:
        yield np.random.choice(keys, 1, p=values / np.sum(values))[0]


def get_first_digit(number):
    if number == 0:
        return 0
    else:
        magnitude = 10 ** (len(str(abs(number))) - 1)
        return (number // magnitude) * magnitude


def complex_query_generator():
    # company_names = extract_all_company_name()
    year_list = ['2019', '2020', '2021']
    attributes = iter(random_financial_headers())
    city_names = iter(load_cities())
    top_nums = [_ for _ in range(1, 20)]
    complex_templates = iter(load_complex_query_templates())
    company_attributes = ['公司的中文名称', '公司的中文简称', '公司的外文名称', '公司的外文名称缩写', '股票代码']
    growth_sql = """(SELECT A.公司的中文名称 AS 公司的中文名称, ((A.{attribute}-B.{attribute})/B.{attribute})*100 AS {attribute}增长率 FROM finance AS A JOIN finance AS B ON CAST(A.年份 AS INT)=CAST(B.年份 AS INT)+1)growth"""
    def format_document(key, value, *templates):
        return [template.replace(key, str(value)) for template in templates]
    while True:
        template_name, question_template, sql_template, answer_template = next(complex_templates)
        slots = list(set(re.findall(r"(\{[^{]*\})", question_template) + re.findall(r"(\{[^{]*\})", answer_template) + re.findall(r"(\{[^{]*\})", sql_template)))
        if "{top_num}" in slots:
            top_num = np.random.choice(top_nums, 1)[0]
            sql_template, = format_document("{top_num}", top_num, sql_template)
            if np.random.uniform(0, 1) < 0.5:
                top_num = cn2an.an2cn(top_num)
            question_template, answer_template = format_document("{top_num}", top_num, question_template, answer_template)
        if "{city_name}" in slots:
            if np.random.uniform(0, 1) < 0.4:
                city_name_list = [next(city_names), next(city_names)]
            else:
                city_name_list = [next(city_names)]
            natural_city_name = np.random.choice(['，','或','和','以及']).join(city_name_list)
            sql_city_name = ','.join(f"'{name}'" for name in city_name_list)
            question_template, answer_template = format_document("{city_name}", natural_city_name, question_template, answer_template)
            sql_template, = format_document("{city_name}", f"{sql_city_name}", sql_template)
        if "{attribute}" in slots:
            keyword, attribute = next(attributes)
            random_number = np.random.uniform(0, 1)
            if random_number < 0.2 and "{company_attribute}" not in slots and "cross_year" not in template_name:
                growth_table = growth_sql.format(attribute=keyword)
                keyword, attribute = keyword + "增长率", attribute + "增长率"
            sql_template, = format_document("{attribute}", keyword, sql_template)
            question_template, answer_template = format_document("{attribute}", attribute, question_template, answer_template)
            sql_template = sql_template.replace("finance", growth_table)
        if "{year}" in slots:
            year = str(np.random.choice(year_list, 1)[0])
            sql_template, = format_document("{year}", f"'{year}'", sql_template)
            question_template, answer_template = format_document("{year}", year, question_template, answer_template)
            candidate_year_list = [year]
        else:
            candidate_year_list = list(map(int, sorted(re.findall(r'(2019|2020|2021)', question_template))))
            assert len(candidate_year_list) == 2
            candidate_year_list = list(map(str, range(candidate_year_list[0], candidate_year_list[1] + 1, 1)))
        if "{company_attribute}" in slots:
            company_attribute = np.random.choice(company_attributes, 1)[0]
            question_template, sql_template, answer_template = format_document("{company_attribute}", company_attribute, question_template, sql_template, answer_template)
        if "{threshold}" in slots:
            random_number = np.random.uniform(0, 1)
            threshold = np.random.randint(1e6, 1e10)
            if random_number < 0.3:
                natural_threshold = "{:,d}".format(threshold)
            elif random_number < 0.6:
                threshold = get_first_digit(threshold)
                natural_threshold = cn2an.an2cn(threshold)
            else:
                natural_threshold = threshold
            sql_template, = format_document("{threshold}", threshold, sql_template)
            question_template, answer_template = format_document("{threshold}", natural_threshold, question_template, answer_template)
        yield {
            "question": question_template,
            "info_dict": {
                "类型": "查询问题",
                "年份": candidate_year_list,
                "SQL查询": sql_template,
                "回答模板": answer_template
            } 
        }


def generate_company_questions(templates):
    company_attributes = [
        '法定代表人',
        '注册地址',
        '办公地址',
        '股票代码',
        '证券代码',
        '企业名称',
        '网站地址',
        '外文名称',
        '电子邮箱',
        '联系电话',
        '邮政编码'
    ]
    slots_template = [
        '请提供{year_1}年{company_name}{attribute}的详细数据。',
        '请提供{year_1}年{company_name}{attribute}的具体情况。',
        '在{year_1}年，{company_name}{attribute}的详细数据是什么样的？',
        '简要介绍一下{year_1}年{company_name}{attribute}的详细情况。'
    ]
    for slot_template in slots_template:
        for attribute in company_attributes:
            templates += [slot_template.replace("{attribute}", attribute)]
    company_names = extract_all_company_name()
    special_templates = [
        '{company_name}{year_1}年的法定代表人和去年有何不同?',
        '{company_name}{year_1}年的法定代表人和上一年有变化吗?',
        '{company_name}{year_1}年的法定代表人和之前一年一样吗?',
        '{company_name}2021年的法定代表人和前年有何不同？',
        '{company_name}2021年的法定代表人和前两年有何不同？'
    ]
    year = ['2019', '2020', '2021']
    answer_template = None
    while True:
        random_number = np.random.uniform(0, 1)
        if random_number < 0.9:
            chosen_template = templates[np.random.randint(0, len(templates))]
            if "{company_name}" in chosen_template:
                company_name = company_names[np.random.randint(0, len(company_names))]
                chosen_template = chosen_template.replace("{company_name}", company_name)
            else:
                continue
            if "{year_1}" in chosen_template:
                if "{year_2}" in chosen_template:
                    year_list = sorted(np.random.choice(year, 2, replace=False))
                    flag = len(re.findall(r"(\{year\_1\}[年至-]+\{year\_2\})", chosen_template)) > 0
                    chosen_template = chosen_template.replace("{year_1}", year_list[0]).replace("{year_2}", year_list[1])
                    if flag:
                        year_list = list(map(str, list(range(int(year_list[0]), int(year_list[1])+1, 1))))
                else:
                    year_list = sorted(np.random.choice(year, 1, replace=False))
                    chosen_template = chosen_template.replace("{year_1}", year_list[0])
            else:
                continue
        else:
            chosen_template = np.random.choice(special_templates)
            if "{company_name}" in chosen_template:
                company_name = company_names[np.random.randint(0, len(company_names))]
                chosen_template = chosen_template.replace("{company_name}", company_name)
            else:
                continue
            if "{year_1}" in chosen_template:
                if "前一年" in chosen_template or "上一年" in chosen_template or "去年" in chosen_template:
                    year_list = sorted(np.random.choice(year, 1, replace=False))[0]
                    chosen_template = chosen_template.replace("{year_1}", year_list)
                    year_list = [str(int(year_list) - 1), year_list]
                else:
                    continue
            else:
                if "前年" in chosen_template:
                    year_list = ['2019', '2021']
                elif "前两年" in chosen_template:
                    year_list = ['2019', '2020', '2021']
        yield {
            "question": chosen_template,
            "info_dict": {
                "类型": "公司问题",
                "公司名称": company_name,
                "年份": year_list
            }
        }


def generate_personal_questions(templates):
    company_names = extract_all_company_name()
    year = ['2019', '2020', '2021']
    while True:
        chosen_template = templates[np.random.randint(0, len(templates))]
        if "{company_name}" in chosen_template:
            company_name = company_names[np.random.randint(0, len(company_names))]
            chosen_template = chosen_template.replace("{company_name}", company_name)
        else:
            continue
        if "{year_1}" in chosen_template:
            if "{year_2}" in chosen_template:
                year_list = sorted(np.random.choice(year, 2, replace=False))
                chosen_template = chosen_template.replace("{year_1}", year_list[0]).replace("{year_2}", year_list[1])
            else:
                year_list = sorted(np.random.choice(year, 1, replace=False))
                chosen_template = chosen_template.replace("{year_1}", year_list[0])
        else:
            continue
        yield {
            "question": chosen_template,
            "info_dict": {
                "类型": "人员问题",
                "公司名称": company_name,
                "年份": year_list
            }
        }


def generate_dataset():
    res_json, counter = category_rule_classifier()
    global company_templates, personal_templates
    company_templates = list(set(company_templates))
    personal_templates = [template for template in list(set(personal_templates)) if "董事" not in template] 
    print(json.dumps(company_templates, ensure_ascii=False, indent=4), len(company_templates))
    print(json.dumps(personal_templates, ensure_ascii=False, indent=4), len(personal_templates))
    open_generator = iter(open_question_generator())
    financial_generator = iter(financial_question_generator())
    growth_generator = iter(financial_question_generator(True))
    query_generator = iter(complex_query_generator())
    company_generator = iter(generate_company_questions(company_templates))
    personal_generator = iter(generate_personal_questions(personal_templates))
    print(counter)
    with open('finetune/table_qa/data/auto_annotated.json', 'w') as fp:
        for idx, res in enumerate(res_json):
            if res['info_dict']['类型'] == '开放问题':
                fp.write(json.dumps({"id": idx} | next(open_generator), ensure_ascii=False) + "\n")
            else:
                fp.write(json.dumps(res, ensure_ascii=False) + "\n")
        for idx in range(5000, 30000, 1):
            random_number = np.random.uniform(0, 1)
            if random_number < 0.04:
                fp.write(json.dumps({"id": idx} | next(open_generator), ensure_ascii=False) + "\n")
            elif random_number < 0.35:
                fp.write(json.dumps({"id": idx} | next(growth_generator), ensure_ascii=False) + "\n")
            elif random_number < 0.6:
                fp.write(json.dumps({"id": idx} | next(financial_generator), ensure_ascii=False) + "\n")
            elif random_number < 0.85:
                fp.write(json.dumps({"id": idx} | next(query_generator), ensure_ascii=False) + "\n")
            elif random_number < 0.93:
                fp.write(json.dumps({"id": idx} | next(personal_generator), ensure_ascii=False) + "\n")
            else:
                fp.write(json.dumps({"id": idx} | next(company_generator), ensure_ascii=False) + "\n")
    print(category_counter())
    json_lines = [json.loads(line) for line in open('finetune/table_qa/data/auto_annotated.json', 'r').readlines()]
    for line in json_lines:
        info_dict = line['info_dict']
        question = line['question']
        if info_dict['类型'] == '常识问题':
            if "2019" in question or "2020" in question or "2021" in question:
                print(question)


if __name__ == '__main__':
    # get_template()
    # random_financial_headers()
    generate_dataset()
    # next(iter(random_financial_headers()))
    # cities = iter(complex_query_generator())
    # for _ in range(100):
    #     print(json.dumps({"question": next(cities)['question']}, ensure_ascii=False))