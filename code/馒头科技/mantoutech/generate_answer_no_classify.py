import os
import json
import copy
import parse
import re
from itertools import chain
from loguru import logger
from datetime import datetime

import re_util
from config import cfg
from chatglm import ChatGLM
from file import load_total_tables
from file import load_tables_of_years
from file import add_growth_rate_in_table
from file import table_to_text
from file import load_pdf_info, load_test_questions
from recall_report_text import recall_annual_report_texts
from recall_report_names import recall_pdf_tables
# from type2 import get_question_formula, rewrite_question, get_step_questions_for_ratio
import type2, type1
import prompt_util
import question_util



def generate_answer(model):
    logger.info('Load pdf info...')
    pdf_info = load_pdf_info()
    pdf_tables = load_total_tables()

    test_questions = load_test_questions()

    answer_dir = os.path.join(cfg.DATA_PATH, 'answers')
    if not os.path.exists(answer_dir):
        os.mkdir(answer_dir)

    for question in test_questions:
        # if '增长率' not in question['question']:
        #     continue

        answer_csv = os.path.join(answer_dir, '{}.csv'.format(question['id']))
        # if os.path.exists(answer_csv):
        #     logger.info('{} exists'.format(answer_csv))
        #     continue
        logger.opt(colors=True).info('<blue>Start process question {} {}</>'.format(question['id'], question['question']))

        ori_question = re.sub('[\(\)（）]', '', question['question'])

        years = question_util.get_years_of_question(ori_question)
        mactched_pdf_names = question_util.get_match_pdf_names(ori_question, pdf_info)
        company_abbrs = question_util.get_company_name_and_abbr_code_of_question(mactched_pdf_names, pdf_info)

        answer = None

        if len(company_abbrs) > 0:
            company = company_abbrs[0][0]
            abbr= company_abbrs[0][1]
            code = company_abbrs[0][2]
            real_comp = company if company in ori_question else abbr

        # 找不到年报的部分, 年份为空且没有匹配的年报
        if len(question_util.get_years_of_question(ori_question)) != 0 and len(mactched_pdf_names) == 0:
            # continue
            if len(company_abbrs) != 0:
                logger.error('没有找到对应的年报')
                answer = '经查询，无法回答{}'.format(ori_question)
                logger.opt(colors=True).info('<magenta>{}</>'.format(answer))
            else:
                # TODO
                logger.info('Find type1-stat question')
                answer = '无法计算结果'
                logger.opt(colors=True).info('<magenta>{}</>'.format(answer))
        # elif type2.is_type2_growth_rate(ori_question):
            # continue
            # question_keywords = question_util.parse_question_keywords(model, ori_question, real_comp, years)
            # logger.info('问题关键词: {}'.format(question_keywords))
            
            # background = '请根据来源于{}(简称{})年报的数据回答问题:\n'.format(company, abbr)
            # background += '----------------------------------------\n'
            # years_to_add = []
            # for year in years:
            #     table_years = [year, str(int(year)-1)]
            #     pdf_table = load_tables_of_years(company, table_years, pdf_tables, pdf_info)
            #     matched_table_rows = recall_pdf_tables(''.join(question_keywords), table_years, pdf_table, min_match_number=3)
            #     table_text = table_to_text(real_comp, ori_question, matched_table_rows)
            #     background += table_text
            #     years_to_add.extend(table_years)
            # question_for_model = prompt_util.get_prompt_growth_rate(background, ori_question, real_comp, years_to_add)
            # logger.info(question_for_model.replace('<', ''))
            # answer = model(question_for_model)
            # answer += '\n公式为:(本年度-上年度)/上年度'
            # logger.opt(colors=True).info('<magenta>{}</>'.format(answer))

        elif type2.is_type2_formula(ori_question) or type2.is_type2_growth_rate(ori_question):
            # continue
            if len(mactched_pdf_names) == 0:
                # this should never happen
                logger.warning('没有找到对应的年报, 但是匹配到了type2')
                answer = '经查询，无法回答类型为2的问题{}'.format(ori_question)
            else:
                question_keywords = question_util.parse_question_keywords(model, ori_question, real_comp, years)
                logger.info('问题关键词: {}'.format(question_keywords))

                if type2.is_type2_growth_rate(ori_question):
                    years_of_table = []
                    for year in years:
                        years_of_table.extend([year, str(int(year)-1)])
                    pdf_table = load_tables_of_years(company, years_of_table, pdf_tables, pdf_info)
                    pdf_table = add_growth_rate_in_table(pdf_table)
                else:
                    pdf_table = load_tables_of_years(company, years, pdf_tables, pdf_info)
                
                step_questions, step_keywords, variable_names, step_years, formula, question_formula = type2.get_step_questions(
                    ori_question, ''.join(question_keywords), company, abbr, years[0])
                step_answers = []
                variable_values = []
                if len(step_questions) > 0:
                    for step_question, step_keyword, step_year in zip(step_questions, step_keywords, step_years):
                        background = '请根据来源于{}(简称{})年报的数据回答问题:\n'.format(company, abbr)
                        background += '----------------------------------------\n'
                        
                        matched_table_rows = recall_pdf_tables(step_keyword, [step_year], pdf_table, 
                            min_match_number=3, top_k=5)
                        # print(matched_table_rows)
                        if len(matched_table_rows) == 0:
                            logger.warning('无法匹配keyword {}, 尝试不设置限制'.format(step_keyword))
                            matched_table_rows = recall_pdf_tables(step_keyword, [step_year], pdf_table, 
                            min_match_number=2, top_k=None)
                            if len(matched_table_rows) == 0:
                                continue
                        
                        table_text = table_to_text(real_comp, ori_question, matched_table_rows)
                        if table_text != '':
                            background += table_text

                        question_for_model = prompt_util.get_prompt_single_question(real_comp, step_year).format(background, step_question)
                        logger.opt(colors=True).info('<cyan>{}</>'.format(question_for_model.replace('<', '')))
                        step_answer = model(question_for_model)
                        variable_value = type2.get_variable_value_from_answer(step_answer)
                        if variable_value is not None:
                            step_answers.append(step_answer)
                            variable_values.append(variable_value)
                        logger.opt(colors=True).info('<green>{}</><red>{}</>'.format(step_answer, variable_value))
                if len(step_questions) == len(variable_values):
                    for name, value in zip(variable_names, variable_values):
                        formula = formula.replace(name, value)
                    result = None
                    try:
                        result = eval(formula)
                    except:
                        logger.error('Eval formula {} failed'.format(formula))
                    if result is not None:
                        answer = ''.join(step_answers)
                        answer += question_formula
                        answer += '得出结果{:.2f}({:.2f}%)'.format(result, result*100)
                        logger.opt(colors=True).info('<magenta>{}</>'.format(answer))
            if answer is None:
                logger.warning('无法找到问题的答案')
        # type1 or type3-1
        elif len(mactched_pdf_names) != 0:
            # continue
            real_comp = company if company in ori_question else abbr
            question_keywords = question_util.parse_question_keywords(model, ori_question, real_comp, years)
            logger.info('问题关键词: {}'.format(question_keywords))
            question_related_tables = type1.get_question_related_tables(model, ori_question, company, abbr, years)            
            logger.info('问题相关表: {}'.format(question_related_tables))

            pdf_table = load_tables_of_years(company, years, pdf_tables, pdf_info)

            background = '***************{}(简称:{},股票代码:{})***************\n'.format(company, abbr, code)
            matched_table_rows = recall_pdf_tables(''.join(question_keywords), years, pdf_table, min_match_number=3)

            if len(matched_table_rows) == 0:
                for table_row in pdf_table:
                    if table_row[0] in question_related_tables:
                        matched_table_rows.append(table_row)

            table_text = table_to_text(real_comp, ori_question, matched_table_rows)

            if table_text != '':
                # continue
                background += table_text
                background += '\n' + '-'*30 + '\n'
                question_for_model = type1.get_prompt(ori_question, company, abbr, years).format(background, ori_question)
            else:
                matched_text = recall_annual_report_texts(''.join(question_keywords), mactched_pdf_names[0], None)
                for block_idx, text_block in enumerate(matched_text):
                    background += '{}信息:{}{}\n'.format('-'*15, block_idx+1, '-'*15)
                    background += text_block
                    background += '\n'
                question_for_model = prompt_util.prompt_question_tp31.format(background, ori_question)
            logger.info('Prompt length {}'.format(len(question_for_model)))
            if len(question_for_model) > 5120:
                question_for_model = question_for_model[:5120]
            logger.info(question_for_model.replace('<', ''))
            answer = model(question_for_model)
            logger.opt(colors=True).info('<magenta>{}</>'.format(answer.replace('<', '')))

        else:
            # continue
            # type3-2
            answer = model(prompt_util.prompt_question_tp32.format(ori_question))
            logger.opt(colors=True).info('<magenta>{}</>'.format(answer.replace('<', '')))

        result = copy.deepcopy(question)
        if answer is not None:
            result['answer'] = answer
        else:
            logger.error('问题无法找到类别, 无法回答')
            result['answer'] = ''
        
        with open(answer_csv, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)


# def make_submit():
#     submits = []

#     test_questions = load_test_questions()

#     answer_dir = os.path.join(cfg.DATA_PATH, 'answers')

#     for question in test_questions:
#         answer_csv = os.path.join(answer_dir, '{}.csv'.format(question['id']))
#         if os.path.exists(answer_csv):
#             with open(answer_csv, 'r', encoding='utf-8') as f:
#                 answer = json.load(f)
#                 # logger.warning(answer['answer'])
#                 # new_answer = re_util.rewrite_compute_result(answer['answer'])
#                 # logger.opt(colors=True).info(new_answer)
#                 # answer['answer'] = new_answer
#                 result = copy.deepcopy(answer)
#                 assert 'answer' in result.keys()
                
#                 new_answer = result['answer']
#                 for s in ['根据提供的信息，', '根据提供的信息']:
#                     if s in new_answer:
#                         new_answer = new_answer.replace(s, '')
#                 years = question_util.get_years_of_question(result['question'])
#                 for year in years:
#                     if year not in new_answer:
#                         new_answer += '({}年)'.format(year)

#                 if result['answer'] == '':
#                     print(result['question'])
                    
#                 if new_answer != result['answer']:
#                     # print(result['answer'])
#                     # logger.warning(new_answer)
#                     result['answer'] = new_answer
                
#                 # if 'answer' not in result.keys():
#                 #     result['answer'] = ''
#         else:
#             raise ValueError('{} not exists'.format(answer_csv))
#             # logger.error('{} not exists'.format(answer_csv))
#             # result = copy.deepcopy(question)
#             # result['answer'] = ''

#         submits.append(result)
    
#     with open(os.path.join(cfg.DATA_PATH, 'result_{}.json'.format(datetime.now().strftime('%Y%m%d'))),
#         'w', encoding='utf-8') as f:
#     # with open('/tmp/submits.json', 'w', encoding='utf-8') as f:
#         for submit in submits:
#             f.write(json.dumps(submit, ensure_ascii=False).encode('utf-8').decode() + '\n')

def make_submit():
    submits = []

    test_questions = load_test_questions()

    answer_dir = os.path.join(cfg.DATA_PATH, 'answers')

    for question in test_questions:
        answer_csv = os.path.join(answer_dir, '{}.csv'.format(question['id']))
        if os.path.exists(answer_csv):
            with open(answer_csv, 'r', encoding='utf-8') as f:
                answer = json.load(f)
                question = answer
        else:
            question['answer'] = ''

        submits.append(question)
    
    if cfg.ONLINE:
        save_path = '/tmp/result.json'
    else:
        save_path = os.path.join(cfg.DATA_PATH, 'result_{}.json'.format(datetime.now().strftime('%Y%m%d')))
    
    with open(save_path, 'w', encoding='utf-8') as f:
        for submit in submits:
            f.write(json.dumps(submit, ensure_ascii=False).encode('utf-8').decode() + '\n')