
import re
from loguru import logger
#金额单位：元，金额与元之间无空格。
# 比值、比率问题不需百分号；速动比率、流动比率也不需转化为百分比；其他情况需要。

def get_formulas():
    formulas = [
        '研发经费与利润=研发费用/净利润',
        '研发经费与营业收入=研发费用/营业收入',
        '研发人员占职工=研发人员的数量/在职员工的数量合计',
        '研发人员占总职工=研发人员的数量/在职员工的数量合计',
        '研发人员在职工=研发人员的数量/在职员工的数量合计',
        '研发人员所占=研发人员的数量/在职员工的数量合计',
        '流动比率=流动资产合计/流动负债合计',
        '速动比率=(流动资产合计-存货)/流动负债合计',
        '硕士及以上人员占职工=(硕士研究生+博士)/在职员工的数量合计',
        '硕士及以上学历的员工占职工=(硕士研究生+博士)/在职员工的数量合计',
        '硕士及以上学历人员占职工=(硕士研究生+博士)/在职员工的数量合计',
        '研发经费占费用=研发费用/(销售费用+财务费用+管理费用+研发费用)',
        '研发经费在总费用=研发费用/(销售费用+财务费用+管理费用+研发费用)',
        '研发经费占总费用=研发费用/(销售费用+财务费用+管理费用+研发费用)',
        '营业利润率=营业利润/营业收入',
        '资产负债比率=负债合计/资产总计',
        '现金比率=货币资金/流动负债合计',
        '非流动负债比率=非流动负债合计/负债合计',
        '流动负债比率=流动负债合计/负债合计',
        '流动负债的比率=流动负债合计/负债合计',
        '净资产收益率=净利润/净资产',
        '净利润率=净利润/营业收入',
        '营业成本率=营业成本/营业收入',
        '管理费用率=管理费用/营业收入',
        '财务费用率=财务费用/营业收入',
        '毛利率=(营业收入-营业成本)/营业收入',
        '三费比重=(销售费用+管理费用+财务费用)/营业收入',
        '三费（销售费用、管理费用和财务费用）占比=(销售费用+管理费用+财务费用)/营业收入',
        '投资收益占营业收入=投资收益/营业收入',
        # '净利润增长率=(净利润-上年净利润)/上年净利润',
    ]
    formulas = [t.split('=') for t in formulas]
    return formulas


def growth_formula():
    formulas = ['销售费用增长率=(销售费用-上年销售费用)/上年销售费用',
        '财务费用增长率=(财务费用-上年财务费用)/上年财务费用',
        '管理费用增长率=(管理费用-上年管理费用)/上年管理费用',
        '研发费用增长率=(研发费用-上年研发费用)/上年研发费用',
        '负债合计增长率=(负债合计-上年负债合计)上年负债合计',
        '总负债增长率=(总负债-上年总负债)/上年总负债',
        '流动负债增长率=(流动负债-上年流动负债)/上年流动负债',
        '货币资金增长率=(货币资金-上年货币资金)/上年货币资金',
        '固定资产增长率=(固定资产-上年固定资产)/上年固定资产',
        '无形资产增长率=(无形资产-上年无形资产)/上年无形资产',
        '资产总计增长率=(资产总计-上年资产总计)/上年资产总计',
        '投资收益增长率=(投资收益-上年投资收益)/上年投资收益',
        '总资产增长率=(资产总额-上年资产总额)/上年资产总额',
        '营业收入增长率=(营业收入-上年营业收入]/上年营业收入',
        '营业利润增长率=(营业利润-上年营业利润)/上年营业利润',
        '净利润增长率=(净利润-上年净利润)/上年净利润',
        '现金及现金等价物增长率=(现金及现金等价物-上年现金及现金等价物)/上年现金及现金等价物']
    formulas = [t.split('=') for t in formulas]
    return formulas


def is_type2_growth_rate(question):
    # 问题不包含年份
    if len(re.findall('\d{4}', question)) == 0:
        return False
    if '增长率' in question:
        return True
    return False


def is_type2_formula(question):
    if len(re.findall('\d{4}', question)) == 0:
        return False
    formulas = get_formulas()
    for k, v in formulas:
        if k in question:
            return True
    return False


def get_keywords_of_formula(value):
    keywords = re.split('[(+-/)]', value)
    keywords = [t for t in keywords if len(t) > 0]
    return keywords


def get_step_questions(question, keywords, real_comp, year):
    new_question = question
    step_questions = []
    question_keywords = []
    variable_names = []
    step_years = []
    formula = None
    question_formula = None

    if '增长率' in question:
        # word_map = {
        #     '现金及现金等价物': '期末现金及现金等价物余额',
        #     '总负债': '负债合计',
        #     '总资产': '资产总计',
        #     '流动负债': '流动负债合计'
        # }
        # for k, v in word_map.items():
        #     if k in new_question and v not in new_question:
        #         new_question = new_question.replace(k, v)
        if keywords == '增长率':
            keywords = new_question
        question_keywords = [keywords.replace('增长率', '')] * 2 + [keywords]
        variable_names = ['A', 'B', 'C']
        formula = '(A-B)/B'
        question_formula = '根据公式，=(-上年)/上年'
        for formula_key, formula_value in growth_formula():
            if formula_key in new_question.replace('的', ''):
                question_formula = '根据公式，{}={},'.format(formula_key, formula_value)
        step_years = [year, str(int(year)-1), year]
        step_questions.append(new_question.replace('增长率', ''))
        step_questions.append(new_question.replace('增长率', '').replace(year, str(int(year)-1)))
        step_questions.append(new_question)
    else:
        formulas = get_formulas()
        for k, v in formulas:
            if k in new_question:
                variable_names = get_keywords_of_formula(v)
                formula = v
                for name in variable_names:
                    if '人数' in question or '数量' in question or '人员' in question:
                        step_questions.append('{}年{}{}有多少人?如果已知信息没有提供, 你应该回答为0人。'.format(year, real_comp, name))
                    else:
                        step_questions.append('{}年{}的{}是多少元?'.format(year, real_comp, name))
                    
                    question_keywords.append(name)
                    step_years.append(year)
                question_formula = '根据公式，{}={}'.format(k, v)
                break
    return step_questions, question_keywords, variable_names, step_years, formula, question_formula


def get_question_formula_prompt(question):
    prompt = None
    if '增长率' in question:
        prompt = '问题"{}"中的计算公式是什么?请按照"(XXXX-上年度的XXXX)/上年度的XXXX"的格式写出, 你只需给出公式,不要回答其他内容.'.format(question)
    else:
        formulas = get_formulas()
        for k, v in formulas:
            if k in question:
                prompt = '问题"{}"中的计算公式是什么? 你只需给出公式,不要回答其他内容.'.format(question)
                break
    return prompt


def get_variable_value_from_answer(answer):
    numbers = re.findall(r'[+\-\d\.]*', answer)
    numbers = [t for t in numbers if t not in ['2018', '2019', '2020', '2021', '2022']]
    numbers = sorted(numbers, key=lambda x: len(x), reverse=True)
    if len(numbers) >= 1:
        return numbers[0]
    else:
        return None


# def rewrite_question(question):
#     new_question = question
#     if '增长率' in question:
#         if '现金及现金等价物' in question:
#             new_question = new_question.replace('现金及现金等价物', '期末现金及现金等价物余额')
#         if '总负债' in question:
#             new_question = new_question.replace('总负债', '负债合计')
#         if '总资产' in question:
#             new_question = new_question.replace('总资产', '资产总计')
#         new_question += '其中增长率=(本年度-上年度)/上年度, 按照公式计算并列出具体的计算步骤。'
#         new_question += '\n2. 问题1当中本年度和上年度的值分别是多少元?'
#     formulas = get_formulas()
#     for k, v in formulas:
#         if k in question:
#             new_question += '其中{}={}, 按照公式计算并列出具体的计算步骤。\n'.format(k, v)
#             # new_question += '2. 如何将文本"{}"替换为上述文本中的数值?'.format(v)
#             keywords = get_keywords_of_formula(v)
#             for i, keyword in enumerate(keywords):
#                 new_question += '{}. 从提供的信息中可以得知，该年度{}是多少元？\n'.format(i+2, keyword)
#     return new_question


def get_question_formula(question):
    formulas = get_formulas()
    formula = None
    for k, v in formulas:
        if k in question:
            formula = '{}={}'.format(k, v)
    return formula



# #                 prompt = '''
# # 你的任务是模仿下面的问答来进行回答, 例如:
# # 问:"2021年神雾节能股份有限公司的营业收入增长率是多少？保留两位小数。" 答:营业收入增长率。
# # 问:"2021年商业城现金及现金等价物增长率是多少?保留2位小数。" 答:现金及现金等价物增长率。
# # 问:"南红文化集团股份有限公司在2021年的固定资产增长率是多少？请保留2位小数" 答:固定资产增长率。
# # 问:"请问，海正药业在2021年的现金及现金等价物增长率是多少？请保留两位小数。" 答:现金及现金等价物增长率。
# # 问:"2021年神雾节能股份有限公司的营业收入增长率是多少？保留两位小数。" 答:营业收入增长率。
# # 注意你必须按照上面的方式进行回答, 不要添加其他内容。
# # 问: "{}"
# # '''.format(ori_question, company, year)
#                 prompt = '''
# {}
# 注意:
# 1. 你不需要进行计算或者查询。
# 2. 你回答的格式为:{}{}的XXX是88.66%。
# 3. 按照格式回答, 不要添加其他内容。"
# '''.format(ori_question, company, year)
#                 answer = model(prompt)
#                 print(answer)
#                 # logger.opt(colors=True).info('<green>{}</>'.format(answer))


if __name__ == '__main__':
    print(get_keywords_of_formula('(净利润-上年净利润)/上年净利润'))