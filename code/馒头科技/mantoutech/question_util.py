import re
from loguru import logger

import prompt_util


def get_years_of_question(question):
    years = re.findall('\d{4}', question)

    if len(years) == 1:
        if re.search('(([上前去]的?[1一]|[上去])年|[1一]年(前|之前))', question) and '上上年' not in question:
            last_year = int(years[0]) - 1
            years.append(str(last_year))
        if re.search('((前|上上)年|[2两]年(前|之前))', question):
            last_last_year = int(years[0]) - 2
            years.append(str(last_last_year))
        if re.search('[上前去]的?[两2]年', question):
            last_year = int(years[0]) - 1
            last_last_year = int(years[0]) - 2
            years.append(str(last_year))
            years.append(str(last_last_year))

        if re.search('([后下]的?[1一]年|[1一]年(后|之后|过后))', question):
            next_year = int(years[0]) + 1
            years.append(str(next_year))
        if re.search('[2两]年(后|之后|过后)', question):
            next_next_year = int(years[0]) + 2
            years.append(str(next_next_year))
        if re.search('(后|接下来|下)的?[两2]年', question):
            next_year = int(years[0]) + 1
            next_next_year = years[0] + 2
            years.append(str(next_year))
            years.append(str(next_next_year))

    if len(years) == 2:
        if re.search('\d{4}年?[到\-至]\d{4}年?', question):
            year0 = int(years[0])
            year1 = int(years[1])
            for year in range(min(year0, year1) + 1, max(year0, year1)):
                years.append(str(year))

    return years


def get_match_company_names(question, pdf_info):
    question = re.sub('[\(\)（）]', '', question)

    matched_companys = []
    for k, v in pdf_info.items():
        company = v['company']
        abbr = v['abbr']
        if company in question:
            matched_companys.append(company)
        if abbr in question:
            matched_companys.append(abbr)
    return matched_companys


def get_match_pdf_names(question, pdf_info):
    def get_matching_substrs(a, b):
        return ''.join(set(a).intersection(b))
    
    years = get_years_of_question(question)
    match_keys = []
    for k, v in pdf_info.items():
        company = v['company']
        abbr = v['abbr']
        year = v['year'].replace('年', '').replace(' ', '')
        if company in question and year in years:
            match_keys.append(k)
        if abbr in question and year in years:
            match_keys.append(k)
    match_keys = list(set(match_keys))
    # 前面已经完全匹配了年份, 所以可以删除年份
    overlap_len = [len(get_matching_substrs(x, re.sub('\d?', '', question))) for x in match_keys]
    match_keys = sorted(zip(match_keys, overlap_len), key=lambda x: x[1], reverse=True)
    # print(match_keys)
    if len(match_keys) > 1:
        # logger.info(question)
        # 多个结果重合率完全相同
        if len(set([t[1] for t in match_keys])) == 1:
            pass
        else:
            logger.warning('匹配到多个结果{}'.format(match_keys))
            match_keys = match_keys[:1]
        # for k in match_keys:
        #     print(k[0])
    match_keys = [k[0] for k in match_keys]
    return match_keys


def get_company_name_and_abbr_code_of_question(pdf_keys, pdf_info):
    company_names = []
    for pdf_key in pdf_keys:
        company_names.append((pdf_info[pdf_key]['company'], pdf_info[pdf_key]['abbr'], pdf_info[pdf_key]['code']))
    return company_names


def parse_keyword_from_answer(anoy_question, answer):
    key_words = set()
    key_word_list = answer.split('\n')
    for key_word in key_word_list:
        key_word = key_word.replace(' ', '')
        # key_word = re.sub('年报|报告|是否', '', key_word)
        if (key_word.endswith('公司') and not key_word.endswith('股公司')) or re.search(
                r'(年报|财务报告|是否|最高|最低|相同|一样|相等|在的?时候|财务数据|详细数据|单位为|年$)', key_word):
            continue
        if key_word.startswith('关键词'):
            key_word = re.sub("关键词[1-9][:|：]", "", key_word)
            if key_word in ['金额', '单位','数据']:
                continue
            if  key_word in anoy_question and len(key_word) > 1:
                key_words.add(key_word)
    return list(key_words)


def anoy_question_xx(question, real_company, years):
    question_new = question
    question_new = question_new.replace(real_company, 'XX公司')
    for year in years:
        question_new = question_new.replace(year, 'XXXX')

    return question_new


def parse_question_keywords(model, question, real_company, years):
    question = re.sub('[\(\)（）]', '', question).replace('为？','是什么？').replace('是？','是什么？').replace('为多少','是多少')
    anoy_question = anoy_question_xx(question, real_company, years)
    anoy_question = re.sub(r'(XX公司|XXXX年|XXXX|保留两位小数|对比|相比|报告期内|哪家|上市公司|第[1234567890一二三四五六七八九十]+[高低]|最[高低](的|的前|的后)?[1234567890一二三四五六七八九十]+家)', '', anoy_question)
    if anoy_question[0] == '的':
        anoy_question = anoy_question[1:]
    answer = model(prompt_util.prompt_get_key_word.format(anoy_question))

    key_words = parse_keyword_from_answer(anoy_question, answer)
    # 无法提取，删除的再试一次
    if len(key_words) == 0:
        anoy_question = anoy_question.replace('的', '')
        answer = model(prompt_util.prompt_get_key_word.format(anoy_question))
        key_words = parse_keyword_from_answer(anoy_question, answer)
    if len(key_words) == 0:
        logger.warning('无法提取关键词')
        key_words = [anoy_question]

    return anoy_question, key_words