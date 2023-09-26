import re
import json
from method.prompt_generation import (
    get_balance_static, get_balance_sheet_prompt, get_profit_statement_prompt,
    get_cash_flow_statement_prompt, calculate_indicator, GLMPrompt
)
from method.statistics import get_statistics_answer
from method.calculate import get_calculate_keyword
from method.com_info import llm_extract_keyword
from embedding_method.doc_qa import chat
import configparser

config = configparser.ConfigParser()
config.read('./config.ini')

COMPUTE_INDEX_SET = [
    '非流动负债比率', '资产负债比率', '营业利润率', '速动比率', '流动比率', '现金比率', '净利润率',
    '毛利率', '财务费用率', '营业成本率', '管理费用率', "企业研发经费占费用",
    '投资收益占营业收入比率', '研发经费与利润比值', '三费比重', '研发经费与营业收入比值', '流动负债比率', "研发人员占职工", "硕士及以上人员占职工", "每股净资产", "每股经营现金流量", "每股收益"
]


def get_embedding_answer(question_obj):
    r = chat(question_obj)
    answer = r['result']['answer']
    return answer


def process_question(question_obj):
    glm_prompt = GLMPrompt()

    q = question_obj['question']
    q = q.replace("(", "").replace(")", "").replace(
        "（", "").replace("）", "").replace("的", "")
    question_type = question_obj['question_type']
    company = question_obj['company']
    question_obj["answer"] = ""
    stock_name, stock_info, has_stock = glm_prompt.has_stock(q)
    contains_year, year_ = glm_prompt.find_years(q)
    compute_index = False
    # 统计题
    if question_type == "com_statis":
        response_ = get_statistics_answer(question_obj['question'])
        question_obj["answer"] = str(response_)

    # 用大模型抽取com_normal的关键词
    if question_type == "com_normal":
        if len(question_obj['keywords']) == 0:
            keywords = llm_extract_keyword(question_obj)
            question_obj['keywords'] = keywords

    # 公式题（正则）
    if contains_year and has_stock and question_type not in ['com_normal', 'normal']:
        all_calculte_result = []
        for t in COMPUTE_INDEX_SET:
            if t in q:
                prompt_res = calculate_indicator(
                    year_[0], stock_name, index_name=t)
                if prompt_res is not None:
                    compute_index = True
                    all_calculte_result.append(prompt_res)
                    if '分别' not in q:
                        break

        if len(all_calculte_result) > 0:
            response_ = '\n'.join(all_calculte_result)
            question_obj["answer"] = str(response_)

    # 公式题（大模型抽取关键词）
    if contains_year and has_stock and not question_obj["answer"] and question_type == 'caculate':
        all_calculte_result = []
        calculate_keywords = get_calculate_keyword(question_obj)
        for t in calculate_keywords:
            prompt_res = calculate_indicator(
                year_[0], stock_name, index_name=t)
            if prompt_res is not None:
                compute_index = True
                all_calculte_result.append(prompt_res)
        if len(all_calculte_result) > 0:
            response_ = '\n'.join(all_calculte_result)
            question_obj["answer"] = str(response_)

    if contains_year and has_stock and not compute_index and '增长率' in q and question_type not in ['com_normal', 'normal']:
        # 大模型抽取的关键词做相似
        prompt_res = glm_prompt.handler_q_zengzhang(question_obj)
        # 直接对问题做相似
        if not prompt_res:
            mask_q = q.replace(company, "")
            statements = [
                get_profit_statement_prompt(mask_q, stock_name, year_),
                get_balance_sheet_prompt(mask_q, stock_name, year_),
                get_cash_flow_statement_prompt(mask_q, stock_name, year_),
                get_balance_static(mask_q, stock_name, year_)
            ]
            # prompt_res = [stmt for stmt in statements if len(stmt) > 5]
            # 取得分最高的一个
            prompt_res = max(statements, key=lambda x: x[1])[0]

        if prompt_res:
            compute_index = True
            # 如果返回的格式不对，则数据有问题，使用embedding的结果
            if "根据公式" not in prompt_res:
                prompt_res = ""
            response_ = prompt_res
            question_obj["answer"] = str(response_)

    if contains_year and has_stock and not compute_index and question_type not in ['com_normal', 'normal', 'calculate']:
        # 大模型抽取的关键词做相似
        response_ = glm_prompt.handler_q_new(question_obj)
        question_obj["answer"] = str(response_)

    # 如果答案为空，则使用我们的答案
    # print("\n")
    if question_obj["answer"] == "":
        # print("使用embedding的答案")
        answer = get_embedding_answer(question_obj)
        question_obj['answer'] = answer
        # print(answer.replace("\n", ""))
    elif (("-1元" in question_obj["answer"]) or ("-1.0元" in question_obj["answer"]) or ("-1.00元" in question_obj["answer"]) or ("-1人" in question_obj["answer"])):
        # print("使用embedding的答案")
        answer = get_embedding_answer(question_obj)
        question_obj['answer'] = answer
        # print(answer.replace("\n", ""))
    else:
        pass
        # print("使用数据库的的答案")
        # print(question_obj["answer"].replace("\n", ""))
    # if question_type == 'calculate' or '增长率' in question_obj["question"]:
    #     question_obj['answer'] = question_obj['answer'].replace(".0元", "元")
    # else:
    #     question_obj['answer'] = question_obj['answer'].replace(".0元", ".00元").replace(".1元", ".10元").replace(".2元", ".20元").replace(".3元", ".30元").replace(
    #         ".4元", ".40元").replace(".5元", ".50元").replace(".6元", ".60元").replace(".7元", ".70元").replace(".8元", ".80元").replace(".9元", ".90元")

    question_obj['answer'] = question_obj['answer'].replace(".0元", ".00元").replace(".1元", ".10元").replace(".2元", ".20元").replace(".3元", ".30元").replace(
        ".4元", ".40元").replace(".5元", ".50元").replace(".6元", ".60元").replace(".7元", ".70元").replace(".8元", ".80元").replace(".9元", ".90元")

    if question_type in ['com_info', 'com_statis', 'calculate']:
        pattern = r"\d+\.(?:(?<=\.)00|(?<=\.)10|(?<=\.)20|(?<=\.)30|(?<=\.)40|(?<=\.)50|(?<=\.)60|(?<=\.)70|(?<=\.)80|(?<=\.)90)元"
        re_result = re.findall(pattern, question_obj['answer'])
        for item in re_result:
            new_item = item[:-1].rstrip('0').rstrip('.')
            question_obj['answer'] = question_obj['answer'].replace(
                item, f'{item}或{new_item}元')

    print(question_obj["id"])
    print(question_obj["question"])
    print(question_obj["answer"].replace("\n", ""))

    with open(config['guanfang_data']['final_result_path'], "a", encoding="utf-8") as f:
        json.dump({k: v for k, v in question_obj.items() if k in [
                  'id', 'question', 'answer']}, f, ensure_ascii=False)
        f.write('\n')


if __name__ == '__main__':
    # questions = read_questions("./data/test_questions.jsonl")
    with open(config["question_analyse"]["keyword_question_path"], 'r') as f:
        test_questions = json.load(f)

    for idx, question_obj in enumerate(test_questions):
        process_question(question_obj)
