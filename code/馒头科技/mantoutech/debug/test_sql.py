import os

GPU_ID = 1
os.environ['CUDA_VISIBLE_DEVICES'] = str(GPU_ID)

from datetime import datetime
from loguru import logger
import re
import json
from xpinyin import Pinyin

from collections import Counter

from config import cfg
from file import download_data
from chatglm import ChatGLM

from company_table import load_company_table
from company_table import load_cn_en_key_map


key_map = load_cn_en_key_map()

question = '2019年哪家公司的负债总额最高?'

# 在上海注册的上市公司中, 2019年负债总额最高的十家公司是?

matched_keys = ['公司全称', '年份']
for cn_key in key_map.keys():
    if len(set(cn_key).intersection(set(question.replace('公司', '')))) > 1:
        matched_keys.append(cn_key)

print(matched_keys)
prompt = '''
已知数据库表CompInfo包含以下列:
股票简称、股票代码、公司的中文名称、公司的中文简称、负债总额、年份、注册地址



请问"2019年哪家公司的负债总额最高?"的输出是?
'''

print(prompt)
model = ChatGLM()
print(model(prompt))

# prompt = '''
# There is a SQL table named CompInfo, which has the following columns:
# {}
# You need to write a SQL query to answer the following question:
# Which company has the highest lending total in 2019?
# '''.format('|'.join([key_map[cn_key] for cn_key in matched_keys]))

# print(prompt)
# print(model(prompt))

# 例如：
# 1. 请问2019年有哪些公司?
# SQL: SELECT Company_Name FROM CompInfo WHERE Year_Yearly=2019
# 2. 中国平安2019的合同负债是多少?
# SQL: SELECT Contract_Liability FROM CompInfo WHERE Company_Name='中国平安' AND Year_Yearly=2019
# 3. 2019年全部公司的合同负债总和是多少？
# SQL: SELECT SUM(Contract_Liability) FROM CompInfo WHERE Year_Yearly=2019
# prompt = '''
# 已知MySQL表的信息如下：
# 表名: CompInfo
# 列名: {}
# 列的含义如下: 
# {}

# 你需要做一个自然语言到SQL语句的转换任务.

# 注意:
# 1. 你不能自己生成表中以外的列名
# 2. 你生成的SQL语句中的列名只能属于【{}】
# 3. 应该保证SQL语句的语法正确
# 4. 只需要给出SQL语句， 不要输出除SQL语句以外的其他内容
# 5. 你可以生成多条SQL语句

# 需要转换的文本是: "{}"
# '''.format(
#     '、'.join([key_map[cn_key] for cn_key in matched_keys]),
#     '\n'.join('{}表示{}'.format(key_map[cn_key], cn_key) for cn_key in matched_keys),
#     '、'.join([key_map[cn_key] for cn_key in matched_keys]),
#     question
# )
# print(prompt)

# print(model(prompt))

    # cols = []
    # for table_name, year, row_name, row_value in table:
    #     try:
    #         eval(row_value)
    #         cls = 'float'
    #     except:
    #         cls = 'text'
    #     row_name = re.sub('[（）]', '', row_name)
    #     pinyin = p.get_pinyin(row_name).replace('-', '')
    #     # rows += '{} {},\n'.format(row_name, cls.upper())
    #     cols.append(row_name)
    # print(cols)

    # prompt = prompt.format('、'.join(cols))
    # print(prompt)

    # logger.warning(model(prompt))

    # break