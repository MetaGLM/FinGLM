import re
from loguru import logger

# def rewrite_question(question, company, abbr):
#     question_new = question
#     if company in question:
#         question_new = question_new.replace(company, '馒头科技')
#     if abbr in question:
#         question_new = question_new.replace(abbr, '馒头科技')
#     return question_new

# def gen_question_prompt(model, question, company, abbr, years):
#     new_question = rewrite_question(question, company, abbr)
# #     prompt = '''
# # {}
# # 注意:
# # 1. 不要进行具体的回答。
# # 2. 你回答的格式为:馒头科技有限公司{}年的XXXX是未知的。
# # 3. 按照格式回答, 不要添加其他内容。
# # '''.format(new_question, years[0])
# #     prompt = '''
# # 对于文本“{}”,其中提问的关键词是什么?
# # 注意:
# # 1. 你只需要回答关键词,不要回答其他内容.
# # 2. 关键词之间用、分隔'''.format(new_question)
#     prompt = '''
# 请对问题"{}"进行分类:
# A. 查询
# B. 分析
# 你只需要回答类别对应的字母, 不要回答其他内容.
# '''.format(new_question)

#     answer = model(prompt)
#     print(answer)


def anoy_question(question, company, abbr, years):
    question_new = question
    if company in question_new:
        question_new = question_new.replace(company, 'XX公司')
    if abbr in question_new:
        question_new = question_new.replace(abbr, 'XX公司')
    for year in years:
        question_new = question_new.replace(year, 'XXXX')
    
    return question_new


# def get_question_keywords(model, question, company, abbr, years):
#     # print(company, abbr)
#     new_question = anoy_question(question, company, abbr, years)
#     prompt = '''
# 你的任务是做信息抽取, 从下面的问题中提取出最重要的几个关键词:
# {}
# 注意:
# 1. 关键词之间用'、'分隔
# 2. 关键词不要重复
# 3. 关键词数量不超过3个
# '''.format(new_question)
#     # print(prompt)
#     answer = model(prompt)
#     answer = re.split('[、,,，]', answer)
#     keywords = []
#     for keyword in answer:
#         keyword = re.sub('2020年*', '', keyword)
#         keyword = re.sub('[多是的元]', '', keyword)
#         keyword = re.sub('馒头科技', '', keyword)
#         if len(keyword) > 1:
#             keywords.append(keyword)
#     return keywords


# def get_question_keywords(model, question, pdf_info):
#     question_new = anoy_question(question, pdf_info)
#     question_new = re.sub('[?？]', '', question_new)

#     prompt_keywords = '''
# 对于文本“{}”,其中重要的关键词是什么?你只需要回答关键词,不要回答其他内容.'''.format(question_new)
#     extracted_keywords = model(prompt_keywords)

#     return extracted_keywords


def get_question_related_tables(model, question, company, abbr, years):
    question_new = anoy_question(question, company, abbr, years)
    prompt_classify_question = '''
请问“{}”是属于下面哪个类别的问题?
A: 基本信息查询, 例如证券信息、股票简称、股票代码、外文名称、法定代表人、注册地址、办公地址、公司网址、电子信箱等
B: 公司员工人数统计, 例如员工人数、员工专业、员工教育程度等
C: 财务相关, 例如金额、费用、资产、收入等
D: 以上都不是

例如:
1. XXXX的费用收入是多少元?
输出: C
2. XX公司法定代表人是谁?
输出: A
3. 请简要介绍分析XX公司的XXX情况。
输出: D
4. XX公司硕士人数是什么?
输出: B

你只需要回答编号, 不要回答其他内容.
'''.format(question_new)
    # logger.info(prompt_classify_question)
    response_classify = model(prompt_classify_question)
    # logger.info(response_classify)
    class_map = {
        'A': 'basic_info',
        'B': 'employee_info',
    }
    classes = re.findall('[A-F]+', response_classify)
    related_tables = [class_map[c] for c in classes if c in class_map]
    return related_tables


def get_prompt(question, company, abbr, years):
    comp = company if company in question else abbr
    if len(years) > 1:
        added_question = ''
        for i, year in enumerate(years):
            added_question += '{}. {}年的是?\n'.format(i+2, year)
        prompt = '''
{{}}

******************************
请回答下面的问题:
1. {{}}
{}'''.format(added_question)
        
    else:
        # if '和' in question or '分别' in question:
        #     answer_format = '{}年{}的XXXX和XXXX分别是XXXX和XXXX'.format(years[0], comp)
        # else:
        answer_format = '{}年{}的XXXX是XXXX'.format(years[0], comp)
        prompt = """
{{}}

请回答问题: {{}}
注意你的回答应该按照以下要求:
1. 你回答的格式应该是:{}。
2. 你只需要回答问题相关的内容, 不要回答无关内容。
3. 你不需要进行计算。
4. 你的回答只能来源于提供的资料。""""".format(answer_format)

    return prompt
