import re

from utils.query_map import query_keyword_map
from configs.model_config import STATISTIC_TEMPLATE_1, STATISTIC_TEMPLATE_2, STATISTIC_TEMPLATE_3, STATISTIC_TEMPLATE_4, STATISTIC_TEMPLATE_5

def query_to_years(query):
    # 使用正则表达式提取年份信息
    matches = re.findall(r'(\d{4})', query)
    # 将匹配到的结果转换为整数
    years = list(map(int, matches))
    for year in years:
        if year not in [2019,2020,2021]:
            # 删除不在年份范围内的年份
            years.remove(year)
    if len(years) == 1:
        years = str(years[0]) + '年'
    if len(years) == 2:
        if abs(years[0] - years[1]) == 1:
            years = str(years[0]) + '年和' + str(years[1]) + '年'
        else:
            years = str(years[0]) + '-' + str(years[1]) + '年'
    return years

def sql_to_city(sql):
    city = re.search(r"'%(.+?)%'", sql)
    if city is None:
        return '所有'
    else:
        city = city.group(1)
        city = city+'注册'
        return city
    
def query_to_num(query):
    nums = re.findall(r'(?:[一二三四五六七八九十百千万亿]+|[0-9]+)', query)
    # 去除4位年份
    nums = [num for num in nums if len(num) < 4]
    return nums


def get_statistic_answer(query, sql, sql_res):
    
    sql_res = eval(sql_res)

    keywords, raw_words = query_keyword_map.question_to_keywords_with_raw_words(query)

    year = query_to_years(query)

    city = sql_to_city(sql)
    num = query_to_num(query)
    direct = '低' if '低' in query else '高'
    answer = ''
    if len(sql_res) == 0:
        answer = '没查到'
    else:
        if '前' in query:
            res = ''
            for i in range(len(sql_res)):
                if i != len(sql_res) - 1:
                    res += '第' + str(i+1) + '是' + sql_res[i][0] + '，'
                elif len(sql_res[i]) == 1:
                    res += '第' + str(i+1) + '是' + sql_res[i][0] + '。'
                else:
                    res += '第' + str(i+1) + '是' + sql_res[i][0] + '，'

                t_str = '值为'
                if '均' in query:
                    continue
                    t_str = '平均值为'
                if len(sql_res[i]) > 1:
                    if i != len(sql_res) - 1:
                        res += t_str + str(sql_res[i][1]) + '元' + '，'
                    else:
                        res += t_str + str(sql_res[i][1]) + '元' + '。'
            
            if '均' in query:
                answer = STATISTIC_TEMPLATE_5.format(year=year, city=city, keyword=raw_words[0], num=num[0], res=res, direct=direct)
            else:
                answer = STATISTIC_TEMPLATE_1.format(year=year, city=city, keyword=raw_words[0], num=num[0], res=res, direct=direct)
            
        elif '最' in query and len(num) > 0:
            res = ''
            for i in range(len(sql_res)):
                if i != len(sql_res) - 1:
                    res += '第' + str(i+1) + '是' + sql_res[i][0] + '，'
                elif len(sql_res[i]) == 1:
                    res += '第' + str(i+1) + '是' + sql_res[i][0] + '。'
                else:
                    res += '第' + str(i+1) + '是' + sql_res[i][0] + '，'
                if len(sql_res[i]) > 1:
                    if i != len(sql_res) - 1:
                        res += '值为' + str(sql_res[i][1]) + '元' + '，'
                    else:
                        res += '值为' + str(sql_res[i][1]) + '元' + '。'
            answer = STATISTIC_TEMPLATE_2.format(year=year, city=city, keyword=raw_words[0], num=num[0], res=res, direct=direct)
        elif '第' in query:
            # ,{keyword}是{res}元
            sql_res = sql_res[0]
            stock = sql_res[0]
            res = ''
            res += stock
            
            
            if len(sql_res) > 1:
                value = sql_res[1]
                res += '，' + '值为' + str(value) + '元'
            answer = STATISTIC_TEMPLATE_4.format(year=year, city=city, keyword=raw_words[0], num=num[0], res=res, direct=direct)
        else: # 最
            sql_res = sql_res[0]
            stock = sql_res[0]
            res = ''
            res += stock
            
            if len(sql_res) > 1:
                value = sql_res[1]
                res += '，' + '值为' + str(value) + '元'
            answer = STATISTIC_TEMPLATE_3.format(year=year, city=city, keyword=raw_words[0], res=res, direct=direct)

    return answer
