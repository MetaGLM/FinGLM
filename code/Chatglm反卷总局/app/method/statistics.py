import re
import json
from embedding_method.doc_qa import get_chatglm_answer, m3e_model
import pandas as pd
from fuzzywuzzy import process
from copy import deepcopy
import numpy as np
import configparser

config = configparser.ConfigParser()
config.read('./config.ini')

df = pd.read_excel("./data/all_data.xlsx")
df['股票代码'] = df['股票代码'].astype(str).str.zfill(6)
df['证券代码'] = df['证券代码'].astype(str).str.zfill(6)

# 根据list筛选
valid_pdf_name = config['guanfang_data']['valid_pdf_name']

company_full_list = []
with open(valid_pdf_name, 'r', encoding='utf-8') as f:
    for line in f:
        _, company_full, _, company_short, caibao_year, _ = line.strip().split("__")
        df.loc[(df['年份'] == int(caibao_year.replace("年", ""))) & (
            df['股票简称'] == company_short), '公司全称'] = company_full
        company_full_list.append(company_short)

df = df.dropna(subset=['公司全称'])
df = df.loc[df['公司全称'].notnull()]
df = df.reset_index(drop=True)

# 关键词扩展
df['流动负债'] = df['流动负债合计']
df['流动资产'] = df['流动资产合计']
df['非流动资产'] = df['非流动资产合计']
df['非流动负债'] = df['非流动负债合计']
df['负债总额'] = df['总负债']
df['负债合计'] = df['总负债']
df['资产总计'] = df['总资产']
df['货币总额'] = df['货币资金']

# 自定义函数，用于拼接小于等于当前年份的注册地址


def concat_past_addresses(row, address_col):
    current_year = row['年份']
    stock_name = row['股票简称']
    past_addresses = df[(df['年份'] <= current_year) & (
        df['股票简称'] == stock_name)][address_col]
    past_addresses = past_addresses.dropna()
    return ', '.join(past_addresses)


df['历史注册地址'] = df.apply(concat_past_addresses, args=('注册地址',), axis=1)
df['曾经办公地址'] = df.apply(concat_past_addresses, args=('办公地址',), axis=1)

# 获取关键词的向量
keywords_list = sorted(df.columns)
keywords_embedding = m3e_model.encode(keywords_list)
keywords_embedding = keywords_embedding / \
    (keywords_embedding**2).sum(axis=1, keepdims=True)**0.5


cls_history = [
    ("'''现在你需要帮我完成信息抽取的任务，你需要帮我抽取出句子中三元组，如果没找到对应的值，则设为空，并按照JSON的格式输出", '好的，请输入您的句子。'),
    ("'''2019年哪家公司的总负债最高。'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2019],"统计词":["总负债"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''2020年哪家公司的总负债最低。'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"统计词":["总负债"],"排序方向":"从低到高","排序数":"1","筛选条件":{}}'),
    ("'''在上海注册的上市公司中，2019年总负债最高的十家公司分别是，总负债金额是？'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2019],"统计词":["总负债"],"排序方向":"从高到低","排序数":"10","筛选条件":{"注册地点":"上海"}}'),
    ("'''在北京注册的上市公司中，2020年营业成本最低的十家公司分别是，营业成本金额是？'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"统计词":["营业成本"],"排序方向":"从低到高","排序数":"10","筛选条件":{"注册地点":"北京"}}'),
    ("'''深圳注册的上市公司中，哪家公司在2021年的营业收入最高？金额是多少？'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2021],"统计词":["营业收入"],"排序方向":"从高到低","排序数":"1","筛选条件":{"注册地点":"深圳"}}'),
    ("'''办公地点在湖南省的公司中，谁在2022年的负债最高？金额是多少？'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2022],"统计词":["负债"],"排序方向":"从高到低","排序数":"1","筛选条件":{"办公地点":"湖南省"}}'),
    ("'''注册地在广东的公司里面，2020年哪家的总负债第一'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"统计词":["总负债"],"排序方向":"从高到低","排序数":"1","筛选条件":{"注册地点":"广东"}}'),
    ("'''2019年哪家的研发人员数量最多'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2019],"统计词":["研发人员数量"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''列举出2021年技术人员数量最少的前15家企业'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2021],"统计词":["技术人员数量"],"排序方向":"从低到高","排序数":"15","筛选条件":{}}'),
    ("'''在深圳办公，在广州注册的公司里面，2020年硕士以上数量最多的公司有哪一些'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"统计词":["硕士以上数量"],"排序方向":"从高到低","排序数":"1","筛选条件":{"注册地点":"广州","办公地点":"深圳"}}'),
    ("'''2021年哪个企业的总营收是排名倒数第一的'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2021],"统计词":["总营收"],"排序方向":"从低到高","排序数":"1","筛选条件":{}}'),
    ("'''2019年哪些企业的净利润第一'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2019],"统计词":["净利润"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''找到2020年哪一家企业的负债总计在所有公司里面排行第五'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"统计词":["负债总计"],"排序方向":"从高到低","排序数":"5","筛选条件":{}}'),
    ("'''找到2019年总营收排行前8的企业'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2019],"统计词":["总营收"],"排序方向":"从高到低","排序数":"8","筛选条件":{}}'),
    ("'''2019-2021年哪些家上市公司货币总额均位列前十？'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2019,2020,2021],"统计词":["货币总额"],"排序方向":"从高到低","排序数":"10","筛选条件":{}}'),
    ("'''2020年总负债最高和营业利润最高的公司分别是？'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"统计词":["总负债","营业利润"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
    ("'''2020年其他非流动资产最高并且历史注册地址在青岛的上市公司是？金额是？'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"统计词":["其他非流动资产"],"排序方向":"从高到低","排序数":"1","筛选条件":{"历史注册地址":"青岛"}}'),
    ("'''2020年营业总收入最高的7家并且曾经在武汉注册的上市公司是？金额是？'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"统计词":["营业总收入"],"排序方向":"从高到低","排序数":"1","筛选条件":{"曾经注册地址":"武汉"}}'),
    ("'''2020年资产总金额最高并且曾经在苏州办公的上市公司是？金额是？'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2020],"统计词":["资产总金额"],"排序方向":"从高到低","排序数":"1","筛选条件":{"曾经办公地址":"苏州"}}'),
    ("'''2021年哪三家上市公司，在重庆注册，营业收入最高？金额为？'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2021],"统计词":["营业收入"],"排序方向":"从高到低","排序数":"3","筛选条件":{"注册地址":"重庆"}}'),
    ("'''2021年哪7家在南京注册的上市公司，其他非流动金融资产最高？金额是？'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2021],"统计词":["其他非流动金融资产"],"排序方向":"从高到低","排序数":"7","筛选条件":{"注册地址":"南京"}}'),
    ("'''2021年其他非流动资产最高的是哪家上市公司？'''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。",
     '{"年份":[2021],"统计词":["其他非流动资产"],"排序方向":"从高到低","排序数":"1","筛选条件":{}}'),
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
def find_best_match_3(word):
    word_embedding = m3e_model.encode([word])
    word_embedding = word_embedding / \
        (word_embedding**2).sum(axis=1, keepdims=True)**0.5

    dot_product = np.dot(word_embedding, keywords_embedding.T)
    match_word = keywords_list[dot_product.argmax()]
    return match_word


def get_statistics_answer(question):
    prompt = "'''{}''''''\n提取上述句子中的年份，统计词，排序方向，排序数，筛选条件，并按照json输出。".format(
        question)

    answer = ""
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
                if '统计词' in json_response and type(json_response['统计词']) is list:
                    for keyword in json_response['统计词']:
                        # 年份筛选
                        if '年份' in json_response and type(json_response['年份']) is list:
                            for year in json_response['年份']:
                                tmp_df = deepcopy(df)
                                match_keyword = find_best_match_3(keyword)

                                tmp_df = tmp_df[tmp_df['年份'] == int(year)]

                                # 条件删选
                                if '筛选条件' in json_response and type(json_response['筛选条件']) is dict:
                                    for key, value in json_response['筛选条件'].items():
                                        match_key = find_best_match_3(key)
                                        if match_key:
                                            tmp_df = tmp_df[tmp_df[match_key].str.contains(
                                                value, na=False)]
                                # 排除-1.0的行
                                tmp_df = tmp_df[tmp_df[match_keyword] != -1.0]
                                # 排序方向
                                sort_flag = False
                                if '排序方向' in json_response and json_response['排序方向'] in ['从低到高', '从高到低']:
                                    if json_response['排序方向'] == '从低到高':
                                        sort_flag = True
                                    if '排序数' in json_response and int(json_response['排序数']) < 0:
                                        sort_flag = not sort_flag
                                        json_response['排序数'] = - \
                                            int(json_response['排序数'])
                                    if any(word in question for word in ['倒数', '最少', '最低', '最后']):
                                        sort_flag = True
                                # 排序
                                tmp_df = tmp_df.sort_values(
                                    by=match_keyword, ascending=sort_flag)  # 按总营收从小到大排序

                                # 取topn
                                if '排序数' in json_response:
                                    result = tmp_df.head(int(json_response['排序数']))[
                                        ['公司全称', match_keyword]]
                                    result = result.reset_index(drop=True)

                                if len(result) > 0:
                                    answer += f'在{year}年，'
                                    if "第" in question and len(result) == int(json_response['排序数']):
                                        result = result.tail(2)

                                    for index, row in result.iterrows():
                                        if '人' in question:
                                            answer += f"{index+1}、{row['公司全称']}{row[match_keyword]}人；"
                                        else:
                                            if '金额' in question:
                                                answer += f"{index+1}、{row['公司全称']}{row[match_keyword]}元；"
                                            else:
                                                answer += f"{index+1}、{row['公司全称']}；"

                    if len(answer) > 0:
                        answer = question + answer
                        break
        except Exception as e:
            # print("error")
            # print(e)
            pass

    return answer

