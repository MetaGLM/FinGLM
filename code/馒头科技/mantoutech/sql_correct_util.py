import company_table
import re
import prompt_util
from loguru import logger


def exc_sql(ori_question, sql, sql_cursor):
    answer = None
    exec_log = ''
    try:
        result = sql_cursor.execute(sql).fetchall()
        answer = ori_question
        rows = []
        for row in result[:50]:
            vals = []
            for val in row:
                try:
                    num = float(val)
                    vals.append('{:.2f}元{:.0f}个{:.0f}家'.format(num, num, num))
                except:
                    vals.append(val)
            rows.append(','.join(map(str, vals)))
        answer += ';'.join(rows)
    except Exception as e:
        logger.error('执行SQL[{}]错误! {}'.format(sql.replace('<>', ''), e))
        exec_log = str(e)
    return answer, exec_log



def get_field_number(sql):
    sql_words = sql.split(' ')
    fields = []
    numbers = []
    pre_word = ''
    for word in sql_words:
        if word == '' or word in ['(', ')']:
            continue
        if word.startswith('('):
            word = word[1:]
        # 只检查条件字段
        if pre_word in ['and', 'or', 'by', 'where'] and re.match(r'^[\u4E00-\u9FA5]+$', word):
            fields.append(word)
        elif pre_word in ['<', '>'] and re.match(r'^[0-9]+$', word) and len(word) > 2:
            numbers.append(word)
        pre_word = word
    return fields, numbers

def get_number_from_question(question):
    unit_dic = {'十万': 100000, '百万': 1000000, '千万': 10000000, '十亿': 1000000000, '百亿': 10000000000,
                '千亿': 100000000000, '百': 100, '千': 1000, '万': 10000, '亿': 100000000}
    num_dic = {"一": 1, "二": 2, "两": 2, "俩": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}

    numbers = re.findall('([一二三四五六七八九十两1234567890]+个?(十万|百万|千万|十亿|百亿|千亿|百|千|万|亿|))', question)
    number_list = []
    for number in numbers:
        # print(number)
        digit_num = number[0].replace('个', '')
        if len(number[1]) > 0:
            digit_num = digit_num.replace(number[1], '')
        if len(digit_num) > 0 and digit_num[-1] in ['十', '百', '千', '万']:
            print(digit_num)
            unit = digit_num[-1] + number[1]
            digit_num = digit_num[:-1]
        else:
            unit = number[1]
        # 太小的纯数字和年份不作检查
        if unit == '' and (len(digit_num) < 3 or (len(digit_num) == 4 and digit_num[:2] == '20')):
            continue
        # 纯数字，不带单位
        elif unit == '' and re.match('^[0-9]+$', digit_num):
            number_list.append(digit_num)
        # 十亿、百亿类直接是单位
        elif digit_num == '' and len(unit) == 2 and unit in unit_dic.keys():
            number_list.append(str(unit_dic.get(unit)))
        # 带单位
        elif unit in unit_dic.keys():
            digit_num = digit_num.replace(unit, '')
            if digit_num in num_dic.keys():
                digit_num = num_dic.get(digit_num)
                number_list.append(str(digit_num*unit_dic.get(unit)))
            elif re.match('^[0-9]+$', digit_num):
                number_list.append(str(int(digit_num) * unit_dic.get(unit)))
    return number_list


def get_most_like_word(word, word_lsit, model):
    mst_like_word = ''
    try:
        answer = model(prompt_util.prompt_most_like_word.format(word_lsit, word))
        logger.info('同义词查询：{}'.format(answer.replace('<>', '')))
    except Exception as e:
        logger.warning('模型查询同义词字段失败：{}'.format(str(e).replace('<>', '')))
    if '查询词语：' in answer:
        most_like_word = answer[answer.find('查询词语：')+5:]
        if most_like_word in word_lsit:
            mst_like_word = most_like_word
    return mst_like_word


def correct_sql_field(sql, question, model):
    new_sql = sql
    key_words = list(company_table.load_company_table().columns)

    fields, sql_numbers = get_field_number(sql)
    for field in fields:
        if field not in key_words:
            most_like_word = get_most_like_word(field, key_words,model)
            if len(most_like_word) > 0:
                logger.info('文本字段纠正前sql：{}'.format(new_sql))
                new_sql = new_sql.replace(field, most_like_word)
                logger.info('文本字段纠正后sql：{}'.format(new_sql))
    return new_sql


def correct_sql_number(sql, question):
    new_sql = sql
    fields, sql_numbers = get_field_number(sql)
    q_numbers = get_number_from_question(question)
    for sql_number in sql_numbers:
        if len(sql_number) > 2 and sql_number not in q_numbers and len(q_numbers) == 1:
            logger.info('文本数字纠正前sql：{}'.format(new_sql))
            new_sql = new_sql.replace(sql_number, q_numbers[0])
            logger.info('文本数字纠正后sql：{}'.format(new_sql))
    return new_sql


if __name__ == '__main__':
    sql = "select count(1), afdas from company_table where 年份 = '2020' and 公司注册地址 is not null and 归属于母公司所有者权益合计 < 50000000"
    question = '归属于母公司所有者权益合计大于500万'
    # fields, numbers = get_field_number(sql)
    # question = '我要大于五百万和大于2个亿和德国十亿和12324324并133百万第三方的十个亿'
    new_sql = correct_sql_number(sql,question)

    # num = get_number_from_question(question)
    print(new_sql)