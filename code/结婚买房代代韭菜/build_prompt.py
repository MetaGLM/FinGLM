MAX_KLG_LENGTH = 1600

# 默认模板
def build_prompt(klg, query, desc_klg):
    return f"""【任务描述】请阅读下列参考文本，回答问题\n【问题】{query}\n【参考文本】来源:{desc_klg}\n{klg[:MAX_KLG_LENGTH]}\n【问题】{query}"""

def build_prompt_v2(query, klg, sql):
    return f"""【任务描述】你是一个问答机器人。请从数据库查询结果中找到对应问题的信息并根据信息回答问题。
    【问题】{query}\n【数据库查询结果】查询数据库获得对于问题“{query}”的答案如下：\n{klg[:MAX_KLG_LENGTH]}\n"""

def build_chatgpt_nl2sql_prompt(query, cols):
    return f"""
    你的任务是将问题转化为SQL。请注意，
    其中注册地址和办公地址都是具体的地址，如果想寻找在上海注册的公司，请使用"注册地址 like '%上海%'"这样的语句，
    "年份"字段是一个字符串，如'2019年'。
    请注意，1. 请无视掉问题中保留2位小数的要求 2.请清楚的使用as命名查询出来的数据是什么增长率。3. 请注意，增长率是指新的一年对于旧的一年，如(2021年xx-2020年xx)/2020年xx
    1. SQL语句查询的表名为: big
    2. 涉及到的列名有: {cols}

    【问题】{query}
    【SQL】"""

def build_nl2sql_prompt_type1(query, cols):
    return f"""
    你的任务是将问题转化为SQL。
    1. SQL语句查询的表名为: big
    2. 涉及到的列名有: {cols}

    【问题】{query}
    【SQL】"""

def build_nl2sql_prompt_type2(query, cols, formula):
    return f"""
    你的任务是将问题转化为SQL。
    1. SQL语句查询的表名为: big
    2. 涉及到的列名有: {cols}
    3. 涉及到的公式有: {formula}

    【问题】{query}
    【SQL】"""

def build_norm_prompt(query, res):
    return f"""根据查询结果回答问题。【查询结果】{res}【问题】{query}【回答】"""