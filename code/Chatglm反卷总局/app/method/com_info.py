import re
import json
from embedding_method.doc_qa import get_chatglm_answer


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
    return {}


cls_history = [
    ("现在你需要帮我完成信息抽取的任务，你需要帮我抽取出句子中三元组，如果没找到对应的值，则设为空，并按照JSON的格式输出", '好的，请输入您的句子。'),
    ("<year><company>电子信箱是什么?\n\n提取上述句子中的关键词，并按照json输出。", '{"关键词":["电子信箱"]}'),
    ("根据<year>的年报数据，<company>的公允价值变动收益是多少元?\n\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["公允价值变动收益"]}'),
    ("<company>在<year>的博士及以上人员数量是多少?\n\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["博士及以上人员数量"]}'),
    ("<company><year>年销售费用和管理费用分别是多少元?\n\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["销售费用","管理费用"]}'),
    ("<company><year>的衍生金融资产和其他非流动金融资产分别是多少元？\n\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["衍生金融资产","其他非流动金融资产"]}'),
    ("<company><year>速动比率是多少?保留2位小数。\n\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["速动比率"]}'),
    ("<company>在<year>年每股的经营现金流量是多少元？\n\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["每股的经营现金流量"]}'),
    ("请具体描述一下<year><company>关键审计事项的情况。\n\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["关键审计事项"]}'),
    ("概述一下重大合同及其履行情况，针对明<company><year>的年报。\n\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["重大合同及其履行情况"]}'),
    ("根据<company><year>的年报数据，能否简要介绍公司报告期内主要供应商的详情。\n\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["主要供应商"]}'),
    ("请具体描述一下<year><company>董事、监事、高级管理人员变动情况。\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["董事、监事、高级管理人员变动情况"]}'),
    ("请告诉我<year><company>的年报中，货币资金增长率保留两位小数为多少。\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["货币资金增长率"]}'),
    ("<year><company>总负债增长率为多少？保留两位小数。\n\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["总负债增长率"]}'),
    ("<year><company>注册地址是什么？保留两位小数。\n\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["注册地址"]}'),
    ("'在保留两位小数情况下，请计算出<company><year>流动负债增长率。\n\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["流动负债增长率"]}'),
    ("'根据<year>年报数据，<company>未来发展展望情况，请做简要分析。\n\n提取上述句子中的关键词，并按照json输出。",
     '{"关键词":["未来发展展望情况"]}'),
]


def llm_extract_keyword(q):
    if q['question_type'] not in ['com_info', 'com_normal']:
        return []
    question = q['question']
    if '法定代表人' in question:
        return []
    question = question.replace('(', '').replace(
        ')', '').replace('（', '').replace('）', '')
    for y in q['match_year']:
        question = question.replace(str(y)+'年', '<year>')
        question = question.replace(str(y), '<year>')
    question = question.replace('的', '')
    if q['company'] != '':
        question = question.replace(q['company']+'公司', '<company>')
        question = question.replace(q['company'], '<company>')
    prompt = f'{question}\n\n提取上述句子中的关键词，并按照json输出。'
    llm_keywords = []
    count = 5
    while count > 0:
        try:
            answer = get_chatglm_answer(
                prompt=prompt, cls_history=cls_history, temperature=1.0)
            print(answer)
            answer = clean_response(answer)
            print(answer)
            if answer:
                llm_keywords = [k.strip('增长率') for k in answer['关键词']]
                break
            count -= 1
        except:
            pass
    return llm_keywords


