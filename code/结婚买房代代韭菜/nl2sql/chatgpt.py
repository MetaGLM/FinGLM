import openai
import time
import json
from tqdm import tqdm
from nl2sql.nl2sql import *


openai.api_key = "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"

def chat(prompt):
    resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
    return resp.choices[0].message.content

def get_result_from_chatgpt(prompt, retry=3, sleep=3):
    for i in range(retry):
        try:
            return chat(prompt).lower()
        except Exception as e:
            print(e, "get from chatgpt err, sleeping")
            time.sleep(sleep)
        
    return None

def build_chatgpt_nl2sql_dataset(input_path, output_path, train_n=1000, test_n=100):
    samples = []
    for line in tqdm(open(input_path, encoding="utf-8")):
        if not line:
            continue 
        query = json.loads(line)["question"]

        if "硕士及以上" in query or "博士及以上" in query:
            edu = random.choice(schema_edu)
            m = random.choice(["以上", "以下", "及以上", "及以下"])
            query = re.sub("硕士及以上|博士及以上", edu + m, query)
            print(query)

        query_analyze_result = get_query_analyze_result(query)
        cols = prepare_columns_for_sql_v2(query, query_analyze_result)
        query = prepare_query_for_sql(query, query_analyze_result)
        prompt = build_nl2sql_prompt(query, cols)

        # sql = get_result_from_chatgpt(prompt)
        # if sql == None:
        #     break
        # elif sql == "该问题无法转化为sql。":
        #     sample = {"prompt": prompt, "sql": sql}
        #     continue

        # exe_sql = translate_sql(sql)
        # try:
        #     res = cursor.execute(exe_sql).fetchall()
        #     if len(res) > 0:
        sample = prompt
        samples.append(prompt)
        #         # print(sample)
        #         samples.append(sample)
        # except Exception as e:
        #     # print(e, exe_sql)
        #     continue
    
    # print("len_samples", len(samples))
    # random.shuffle(samples)
    # json_lines_dump(samples, output_path + "_all.json")
    # json_lines_dump(samples[:train_n], output_path + "_train.json")
    # json_lines_dump(samples[train_n:train_n+test_n], output_path + "_test.json")


if __name__ == "__main__":
    prompt = """
    你的任务是将问题转化为SQL。
    备注：其中注册地址和办公地址都是具体的地址，如果想寻找在上海注册的公司，请使用"注册地址 like '%上海%'"这样的语句，"年份"字段是一个字符串，如'2019年'。
    如果问题需求是xxxx率则使用百分比返回，否则使用小数返回，均保留两位小数，如果根据已有列无法进行查询，请返回"该问题无法转化为sql。"
    1. SQL语句查询的表名为: big
    2. 涉及到的列名有: 公司名称,股票代码,股票简称,年份

    【问题】能否根据2020年金宇生物技术股份有限公司的年报，给我简要介绍一下报告期内公司的社会责任工作情况？
    【SQL】"""

    print(chat(prompt))