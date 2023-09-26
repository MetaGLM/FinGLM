import glob
import json
import re
import pandas as pd
from multiprocessing import Pool

def cut_all_text(check, check_re_1, check_re_2, all_text, line_dict, text):
    if check == False and re.search(check_re_1, all_text):
        check = True
    if check == True and line_dict['type'] not in ['页眉', '页脚']:
        if not re.search(check_re_2, all_text):
            if line_dict['inside'] != '':
                text = text + line_dict['inside'] + '\n'
        else:
            check = False
    return text, check


def process_file2(file_name):
    '''
    Args:
        file_name:

    Returns:

    '''
    # print('开始 ', file_name.replace('\n', ''))
    allname = file_name.split('\\')[-1]
    date, name, stock, short_name, year, else1 = allname.split('__')
    stock2, short_name2, mail, address1, address2 = '', '', '', '', ''
    chinese_name, chinese_name2, english_name, english_name2, web, boss = '', '', '', '', '', ''
    all_person, person11, person12, person13, person14, person15 = '', '', '', '', '', ''
    person21, person22, person23, person24, person25, person26, person27 = '', '', '', '', '', '', ''
    with open(file_name, 'r',encoding='utf-8') as file:

        lines = file.readlines()
        for i in range(len(lines)):
            line = lines[i]
            line = line.replace('\n', '')
            line_dict = json.loads(line)
            try:
                if line_dict['type'] not in ['页眉', '页脚', 'text']:
                    if stock2 == '' and re.search("股票代码'|证券代码'", line_dict['inside']):
                        middle = line_dict['inside'] + '\n' + json.loads(lines[i+1].replace('\n', ''))['inside']
                        stock2_re = re.search('(?:0|6|3)\d{5}', middle)
                        if stock2_re:
                            stock2 = stock2_re.group()
                        answer_list = eval(line_dict['inside']) + eval(json.loads(lines[i+1].replace('\n', ''))['inside'])
                        for _answer in answer_list:
                            if not re.search('代码|股票|简称|交易所|A股|A 股|公司|上交所|科创版|名称', _answer) and _answer not in ['', ' ']:
                                short_name2 = _answer
                                break
                    def check_answers(answer, keywords_re, check_chinese):
                        if answer == '' and re.search(keywords_re, line_dict['inside']):
                            answer_list = eval(line_dict['inside'])
                            for _answer in answer_list:
                                keywords_re = keywords_re.replace("'", '')
                                if check_chinese == True:
                                    if not re.search(keywords_re, _answer) \
                                            and not re.search('[\u4e00-\u9fa5]', _answer) and _answer not in ['', ' ']:
                                        answer = _answer
                                        break
                                else:
                                    if not re.search(keywords_re, _answer) and _answer not in ['', ' ']:
                                        answer = _answer
                                        break
                        return answer
                    def check_person_answers(answer, all_answer, keywords_re, check_chinese):
                        if answer == '' and all_answer != '' and re.search(keywords_re, line_dict['inside']):
                            answer_list = eval(line_dict['inside'])
                            for _answer in answer_list:
                                keywords_re = keywords_re.replace("'", '')
                                if check_chinese == True:
                                    if not re.search(keywords_re, _answer) \
                                            and not re.search('[\u4e00-\u9fa5]', _answer) and _answer not in ['', ' ']:
                                        answer = _answer
                                        break
                                else:
                                    if not re.search(keywords_re, _answer) and _answer not in ['', ' ']:
                                        answer = _answer
                                        break

                        return answer
                    mail = check_answers(mail, "'电子信箱|电子信箱'", True)
                    address1 = check_answers(address1, "'注册地址|注册地址'", False)
                    address2 = check_answers(address2, "'办公地址|办公地址'", False)
                    chinese_name = check_answers(chinese_name, "'公司的中文名称|公司的中文名称'", False)
                    chinese_name2 = check_answers(chinese_name2, "'中文简称|中文简称'", False)
                    english_name = check_answers(english_name, "'公司的外文名称|公司的外文名称(?:（如有）)？'", True)
                    english_name2 = check_answers(english_name2, "'公司的外文名称缩写|公司的外文名称缩写(?:（如有）)？'", True)
                    web = check_answers(web, "'公司(?:国际互联网)?网址|公司(?:国际互联网)?网址'", True)
                    boss = check_answers(boss, "'公司的法定代表人|公司的法定代表人'", False)
                    all_person = check_answers(all_person, "'(?:报告期末)?在职员工的数量合计(?:（人）)?|(?:报告期末)?在职员工的数量合计(?:（人）)?'", True)
                    person11 = check_person_answers(person11, all_person, "'生产人员|生产人员'", True)
                    person12 = check_person_answers(person12, all_person, "'销售人员|销售人员'", True)
                    person13 = check_person_answers(person13, all_person, "'技术人员|技术人员'", True)
                    person14 = check_person_answers(person14, all_person, "'财务人员|财务人员'", True)
                    person15 = check_person_answers(person15, all_person, "'行政人员|行政人员'", True)

                    person21 = check_person_answers(person21, all_person, "本科及以上'", True)
                    person22 = check_person_answers(person22, all_person, "本科'", True)
                    person23 = check_person_answers(person23, all_person, "硕士及以上'", True)
                    person24 = check_person_answers(person24, all_person, "硕士'", True)
                    person25 = check_person_answers(person25, all_person, "博士及以上'", True)
                    person26 = check_person_answers(person26, all_person, "博士'", True)

                    person27 = check_answers(person27, "公司研发人员的数量'", True)

                    if stock2 != '' and mail != '' and address1 != '' and address2 != '' \
                            and chinese_name != '' and chinese_name2 != '' \
                            and english_name != '' and english_name2 != '' and web != '' and boss != '' \
                            and all_person != '' and person11 != '' and person12 != '' and person13 != '' \
                            and person14 != '' and person15 != ''\
                            and person21 != '' and person22 != '' and person23 != '' and person24 != ''\
                            and person25 != '' and person26 != '' and person27 != '':
                        break
            except:
                print(line_dict)
    new_row = {'文件名': allname,
               '日期': date, '公司名称': name, '股票代码': stock, '股票简称': short_name, '年份': year, '类型': '年度报告',
               '代码': stock2, '简称': short_name2, '电子信箱': mail, '注册地址': address1, '办公地址': address2,
               '中文名称': chinese_name, '中文简称': chinese_name2,
               '外文名称': english_name, '外文名称缩写': english_name2,
               '公司网址': web, '法定代表人': boss,
               '职工总数': all_person, '生产人员': person11, '销售人员': person12, '技术人员': person13,
               '财务人员': person14, '行政人员': person15,
               '本科及以上人员': person21, '本科人员': person22, '硕士及以上人员': person23, '硕士人员': person24,
               '博士及以上人员': person25, '博士人员': person26, '研发人数': person27,
               '全文': str(lines)}
    print('结束 '+file_name)
    return new_row
# 文件夹路径
folder_path = '../alltxt2'
# 获取文件夹内所有文件名称
file_names = glob.glob(folder_path + '/*')
file_names = sorted(file_names, reverse=True)
print(file_names)
results = []
# 打印文件名称

df = pd.DataFrame(columns=[
    '文件名',
    '日期', '公司名称', '股票代码', '股票简称', '年份', '类型',
    '代码', '简称', '电子信箱', '注册地址', '办公地址', '中文名称', '中文简称', '外文名称', '外文名称缩写',
    '公司网址', '法定代表人', '职工总数', '生产人员', '销售人员', '技术人员', '财务人员', '行政人员',
    '本科及以上人员', '本科人员', '硕士及以上人员', '硕士人员', '博士及以上人员', '博士人员', '研发人数',
    '全文'])


with Pool(processes=7) as pool:
    results = pool.map(process_file2, file_names)

df = pd.DataFrame(results)
df.to_excel("big_data1.xlsx", index=False)





