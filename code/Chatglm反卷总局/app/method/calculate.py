import re
import json
from embedding_method.doc_qa import get_chatglm_answer, m3e_model
from fuzzywuzzy import process
import configparser

config = configparser.ConfigParser()
config.read('./config.ini')

COMPUTE_INDEX_SET = [
    '非流动负债比率', '资产负债比率', '营业利润率', '速动比率', '流动比率', '现金比率', '净利润率',
    '毛利率', '财务费用率', '营业成本率', '管理费用率', "企业研发经费占费用",
    '投资收益占营业收入比率', '研发经费与利润比值', '三费比重', '研发经费与营业收入比值', '流动负债比率', "研发人员占职工", "硕士及以上人员占职工", "每股净资产", "每股经营现金流量", "每股收益"
]

# # 获取关键词的向量
# keywords_list = sorted(COMPUTE_INDEX_SET)
# keywords_embedding = m3e_model.encode(keywords_list)
# keywords_embedding = keywords_embedding / \
#     (keywords_embedding**2).sum(axis=1, keepdims=True)**0.5


cls_history = [
    ("'''现在你需要帮我完成信息抽取的任务，你需要帮我抽取出句子中三元组，如果没找到对应的值，则设为空，并按照JSON的格式输出", '好的，请输入您的句子。'),
    ("'''请告诉我2019年的年报中，营业成本率保留两位小数为多少。'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2019],"关键词":["营业成本率"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''2021年的企业研发经费占费用比例保留两位小数是多少？'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2021],"关键词":["企业研发经费占费用比例"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''在保留两位小数的情况下，请计算出2020年的管理费用率'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"关键词":["管理费用率"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''在保留两位小数的情况下，请计算出2021年的流动比率'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2021],"关键词":["流动比率"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''2020年的投资收益占营业收入比率保留两位小数是多少？'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"关键词":["投资收益占营业收入比率"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''请提供2020年的毛利率并保留2位小数'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"关键词":["毛利率"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''2019年的资产负债比率保留两位小数是多少？'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2019],"关键词":["资产负债比率"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''在保留两位小数的情况下，请计算出2019年的企业研发经费与利润比值'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2019],"关键词":["企业研发经费与利润比值"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''2019年年报中提及的非流动负债比率具体是什么？'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2019],"关键词":["非流动负债比率"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''在保留两位小数的情况下，请计算出2019年的财务费用率'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2019],"关键词":["财务费用率"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''2020年的企业研发经费与营业收入比值保留两位小数是多少？'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"关键词":["企业研发经费与营业收入比值"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''在2020年的财务数据中，毛利率是多少？保留两位小数'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"关键词":["毛利率"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''请告诉我2020年的年报中，现金比率保留两位小数为多少。'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"关键词":["现金比率"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''请提供2021年的企业硕士及以上人员占职工人数比例并保留2位小数'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2021],"关键词":["企业硕士及以上人员占职工人数比例"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''请提供2020年的净利润率并保留2位小数'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"关键词":["净利润率"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''在2021年的时候，营业利润率为多少？'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2021],"关键词":["营业利润率"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''在2021年的时候，速动比率为多少？'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2021],"关键词":["速动比率"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''2019年年报中提及的三费比重具体是什么？'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2019],"关键词":["三费比重"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''在保留两位小数的情况下，请计算出浙江海正药业股份有限公司2020年的研发人员占职工人数比例'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"关键词":["研发人员占职工人数比例"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''在2021年的每股收益和每股净资产分别是多少元'''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2021],"关键词":["每股收益","每股净资产"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
]


def clean_response(response):
    response_list = response.split("\n\n")
    for ans in response_list:
        if '```json' in ans:
            res = re.findall(r'```json(.*?)```', ans, re.DOTALL)
            if len(res) and res[0]:
                ans = res[0]
        ans = ans.replace("{\"}", "{}")
        try:
            return json.loads(ans)
        except:
            pass
    return response


# 向量匹配关键词
# def find_best_match_3(word):
#     word_embedding = m3e_model.encode([word])
#     word_embedding = word_embedding / \
#         (word_embedding**2).sum(axis=1, keepdims=True)**0.5

#     dot_product = np.dot(word_embedding, keywords_embedding.T)
#     print(dot_product.max())
#     match_word = keywords_list[dot_product.argmax()]
#     return match_word


def find_best_match_new(question, mapping_list, threshold=65):
    matches = process.extract(question, mapping_list)
    best_matches = [match for match in matches if match[1] >= threshold]
    best_matches = sorted(best_matches, key=lambda x: (-x[1], -len(x[0])))
    print(best_matches)
    match_score = 0
    total_q = ""
    if len(best_matches) > 0:
        total_q = best_matches[0][0]
        match_score = best_matches[0][1]

    return total_q, match_score
    


def get_calculate_keyword(question_obj):
    company = question_obj['company']
    question = question_obj['question']
    mask_question = question.replace(company, "")

    prompt = "'''{}''''''\n提取上述句子中的年份，关键词，排序方向，排序数，筛选条件，并按照json输出。".format(mask_question)

    extract_keywords = []
    retry_count = 10
    while (retry_count):
        try:
            retry_count -= 1
            response = get_chatglm_answer(
                prompt, temperature=1, cls_history=cls_history)

            print(response)
            json_response = clean_response(response)
            print(json_response)

            if type(json_response) is dict:
                if '关键词' in json_response and type(json_response['关键词']) is list:
                    for keyword in json_response['关键词']:
                        match_keyword, _ = find_best_match_new(keyword, COMPUTE_INDEX_SET)
                        if match_keyword:
                            extract_keywords.append(match_keyword)
                    if len(extract_keywords) > 0:
                        break
        except Exception as e:
            pass
    return extract_keywords

