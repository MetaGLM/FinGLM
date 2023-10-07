import re
from loguru import logger


def keep_chinese(str):
    return ''.join([c for c in str if '\u4e00' <= c <= '\u9fa5'])


def clean_row_name(name):
    return re.sub('[一二三四五六七八九十\d（）、 \n\.]', '', name)


def find_years(s):
    years = re.findall('\d{4}', s)
    return years


def find_numbers(s):
    numbers = re.findall('[-\d,\.]+', s)
    float_numbers = []
    for number in numbers:
        try:
            float_numbers.append(float(number))
        except:
            pass
            # logger.info('Invalid number {} in {}'.format(number, s))
    return float_numbers


def is_valid_number(s):
    # 0~99
    two_digits = re.findall('\d\d{0,1}', s)
    if len(two_digits) == 1 and two_digits[0] == s:
        return False
    # 7-1, 1-2
    digit_broken_digit = re.findall('\d+-\d+', s)
    if len(digit_broken_digit) == 1 and digit_broken_digit[0] == s:
        return False
    return True


def sep_numbers(line):
    pos_to_add_sep = []
    for match in re.finditer('\.\d\d +[+\-\d]{1}', line):
        pos_to_add_sep.append(match.start())
    new_line = line
    for pos in sorted(pos_to_add_sep, reverse=True):
        new_line = new_line[:pos+3] + '|' + new_line[pos+3:]
    # if new_line != line:
    #     print(line, new_line)
    return new_line


def is_header_footer(line):
    line = line.replace(' ', '')
    if re.findall('\d{4}年?年度报告', line):
        return True
    res = ['[\d]+', '[\d第页/]+']
    for pattern in res:
        matched_str = re.findall(pattern, line)
        if len(matched_str) == 1 and matched_str[0] == line:
            return True
    
    return False


def rewrite_answer(answer):
    numbers = re.findall('-?\d+.\d+元', answer)
    new_answer = answer
    for number in numbers:
        number = number.replace('元', '')
        try:
            f_num = float(number)
            if str(float(number)) != '{:.2f}'.format(float(number)):
                new_answer = new_answer.replace(number, '{:.0f}元{:.1f}元{:.2f}'.format(f_num, f_num, f_num))
        except:
            print('invalid number {}'.format(number))
    # print(new_answer)
    return new_answer


def rewrite_compute_result(answer):
    new_answer = answer
    # [\d+-/()\.=≈%元×]+
    equations = re.findall('[\d%元,\.\(\)（）+\-×/=≈]+', new_answer.replace(' ', ''))
    print(equations)
    recomputes = []
    for equation in equations:
        
            # result = eval(equation)
            # if equation == str(result):
            #     continue
            # print(equation)
        for t in re.split('[=≈]+', equation):
            t = t.replace('×', '*')
            t = t.replace('（', '(')
            t = t.replace('）', ')')
            t = t.replace(',', '')
            try:
                t_to_eval = re.sub('[%元]+', '', t)
                # print(t_to_eval)
                result = eval(t_to_eval)
                if str(result) != t_to_eval:
                    if t.endswith('%'):
                        recomputes.append('其中{}={:.2f}%'.format(t, result))
                    elif t.endswith('元'):
                        recomputes.append('其中{}={:.2f}元'.format(t, result))
                    else:
                        recomputes.append('其中{}={:.2f}%({:.2f})'.format(t, result*100, result))
            except:
                continue
    if len(recomputes) != 0:
        new_answer += '\n<green>{}</>\n'.format('\n'.join(recomputes))

    # equations = re.findall('[\d+-/()\.]+[=≈][\d+-/() \.]+%*', answer)
    # print(new_answer)
    # for equation in equations:
    #     spe = '=' if '=' in equation else '≈'
    #     left, right = equation.split(spe)
    #     print(equation)
    #     result = eval(left)
    #     new_equation = '{}={:.2f}%({:.2f})'.format(left, result*100, result)
    #     new_answer = new_answer.replace(equation, new_equation)
    #     print(equation, new_equation)

    return new_answer


def process_line(s):
    # numbers like 1,000,00 0.00
    def f(t):
        return '{}'.format(t.group().replace(' ', ''))
    s = s.strip(' ')
    space_groups = list(re.finditer(' +', s))
    for gidx in range(len(space_groups)-1):
        current_span = space_groups[gidx].span()
        next_span = space_groups[gidx+1].span()
        current_num = current_span[1] - current_span[0]
        next_num = next_span[1] - next_span[0]
        if next_num >= current_num:
            s = s[:current_span[0]] + '*'*current_num + s[current_span[1]:]
    s = s.replace('*', '')
    
    s = re.sub(' {3,}', '   ', s)
    s = re.sub('[\d,\.+-] {1,2}', f, s)
    s = re.sub('[\d\+\-%] {1,3}[\d\+\-%]', lambda t: re.sub(' {1,3}', '|', t.group()), s)
    # s = re.sub('[^\d ] [^\d ]', f, s)
    # print(s.replace(' ', '*'))
    s = re.sub('[^\d ] {1,2}', f, s)
    # print(s.replace(' ', ''))
    # print(s)
    return s


if __name__ == '__main__':
    # print((388969421.15-378737577.28)/378737577.28*100)

#     print(rewrite_compute_result('''
# （2453215434.28 - 1622278319.25）/ 1622278319.25 × 100% ≈ 79.72%
# '''))
    # print(re.sub('[×%元]+', '', '(50449943.70 - (-5146737.73)) / (-5146737.73) × 100%'))


    print(sep_numbers('预付款项|674,558,351.89435,646,053.30\n'))

    # print(is_header_footer('2020  2021  上海证券交             年度报告及其摘要的议案》、《关于 2020 年度财务决算'))

    # print(find_numbers('287571813.28元'))

    # print(is_valid_number('15-51'))

    print(re.findall('人民币.{0,3}元', '人民币百万元'))
    # rewrite_answer('北京同仁堂股份有限公司2019年的营业利润是1968133334.00元。北京同仁堂股份有限公司2019年的营业收入是13277123199.46元。公式为:营业利润率=营业利润/营业收入得出结果0.15(14.82%)')