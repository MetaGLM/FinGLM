
# 默认模版
PROMPT_TEMPLATE = ''

######################################所有的 prompt 模版
# 基于上下文的prompt模版，查询多文档问题时的答案
PROMPT_1 = """任务：根据"已知信息"按照"回答格式"回答用户问题

已知信息：{context} 

根据上述已知信息，简洁和专业地来回答用户的问题。

问题是：{question}
答案："""


# 基于上下文的prompt模版，回答开放性问题
PROMPT_4 = """作为金融咨询分析助手，我期望你扮演一位经验丰富的企业年报分析专家，深入理解企业年报的各个内容，如财务报表、经营业绩、风险因素以及管理层的讨论与分析等；你需要擅长财务分析，理解会计原理和财务报表，包括但不限于利润表、资产负债表和现金流量表，同时对股票和债券市场也要有所了解。请以简洁专业的方式回答我关于经济和证券的问题。
问题是：{question}
答案："""

PROMPT_5 = """很抱歉，没有找到{company}在{year_time}的年报，无法提供“{query}”问题的答案。"""
PROMPT_6 = """很抱歉，没有找到该公司在{year_time}的年报，无法提供“{query}”问题的答案。"""


# class2 匹配模板
# 数值 单位元 无公式
MATCH_TEMPLATE_1 = """{stock}在{year}的{keyword}是{res}元。"""

# 数值 单位元 带公式
MATCH_TEMPLATE_2 = """根据公式{keyword}={formula}，得出{stock}在{year}的{keyword}是{res:.2f}元。"""

# 数值 单位元 每股经营现金流量
MATCH_TEMPLATE_3 = """根据公式{keyword}={formula}，得出{stock}在{year}的{keyword}是{res:.3f}元。"""

# 数值 单位元 每股净资产
MATCH_TEMPLATE_4 = """根据公式{keyword}={formula}，得出{stock}在{year}的{keyword}是{res:.4f}元。"""

# 比率
MATCH_TEMPLATE_5 = """根据公式{keyword}={formula}，得出{stock}在{year}的{keyword}是{res:.2f}。"""

# 数值 单位% 带公式
MATCH_TEMPLATE_6 = """根据公式{keyword}={formula}，得出{stock}在{year}的{keyword}是{res:.2f}%。"""

# # 文字秒速
MATCH_TEMPLATE_7 = """{stock}在{year}的{keyword}是{res}人。"""
# # 文字秒速
MATCH_TEMPLATE_8 = """{stock}在{year}的{keyword}是{res}。"""

# 字段为nan情况 这种情况交给 BM25 处理了
MATCH_TEMPLATE_9 = """很抱歉，经查询未找到足够的相关信息，无法提供{year}{stock}的{keyword}的答案。"""

### sql答案模板

# 前
STATISTIC_TEMPLATE_1 = """{year}在{city}的上市公司中,{keyword}最{direct}的前{num}家公司如下：{res}"""

# 最带数字
STATISTIC_TEMPLATE_2 = """{year}在{city}的上市公司中,{keyword}最{direct}的{num}家公司如下：{res}"""

# 最
STATISTIC_TEMPLATE_3 = """{year}在{city}的上市公司中,{keyword}最{direct}的公司是{res}。"""

# 第
STATISTIC_TEMPLATE_4 = """{year}在{city}的上市公司中,{keyword}第{num}{direct}的公司是{res}。"""

# 均
STATISTIC_TEMPLATE_5 = """{year}在{city}的上市公司中,{keyword}均位列前{num}的公司如下：{res}"""


####text to generation
PROMPT_TEXT_TO_SQL = """已知数据库中有一个表格fin_report，表格字段包含公司名称，年份，公司地址，{keyword}，请为以下问题生成 SQL 查询语句，匹配时尽量采用 LIKE。

问题是：{question}
"""
PROMPT_SQL_TO_TEXT="""
已知一个问题"{question}” 的结果为{sql_result}，请重新组织语言回答该问题
"""
###########################################################################################
### 地址文件



pdf_list_path = '/tcdata/C-list-pdf-name.txt'
pdf_all_list_path = '/app/configs/all-pdf-name.txt'


table_path = '/alltable_merge' 
knowledge_txt_path = '/own_files/alltxt_table_in_one'

keyword_path = 'configs/added_keywords.csv'
item_map_path = 'configs/item_map.csv'
item_to_parten_path = 'configs/item_to_parten.csv'

LLM_model_path = '/tcdata/chatglm2-6b-hug'

query_path = '/tcdata/C-list-question.json'
response_path = "/tmp/result.json"


database_path = 'database/out.csv'
sql_path = 'database/fin_data.db'
# sql_gpt4_path = 'configs/statistic_query_res_new.csv'

sql_res_path = 'result/sql_res.csv'
sql_chatglm_path = '/checkpoint-50_half'


# ***************************************************************
# pdf_list_path = '/data/chengshuang/SMP2023/tcdata/C-list-pdf-name.txt'
# pdf_all_list_path = 'configs/all-pdf-name.txt'


# table_path = '/data/chengshuang/SMP2023/submitnsddd/alltable_merge' 
# knowledge_txt_path = '/data/chengshuang/SMP2023/submitnsddd/own_files/alltxt_table_in_one'

# keyword_path = 'configs/added_keywords.csv'
# item_map_path = 'configs/item_map.csv'
# item_to_parten_path = 'configs/item_to_parten.csv'

# LLM_model_path = '/data/chengshuang/SMP2023/tcdata/chatglm2-6b-hug'

# query_path = '/data/chengshuang/SMP2023/tcdata/C-list-question.json'
# response_path = "result/result.json"


# database_path = 'database/out.csv'
# sql_path = 'database/fin_data.db'
# # sql_gpt4_path = 'configs/statistic_query_res_new.csv'

# sql_res_path = 'result/sql_res.csv'
# sql_chatglm_path = '/data/chengshuang/SMP2023/submitnsddd/checkpoint-50_half'