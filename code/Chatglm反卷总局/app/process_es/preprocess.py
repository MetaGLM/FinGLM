#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pdfplumber
import re
from collections import defaultdict
import json
import os
from tqdm import tqdm
import configparser

config = configparser.ConfigParser()
config.read('./config.ini')

input_folder = config['guanfang_data']['txt_path']
output_folder = config['process_es']['parse_title_text_path']
valid_pdf_name = config['guanfang_data']['valid_pdf_name']

valid_pdf_list = []
with open(valid_pdf_name, 'r', encoding='utf-8') as f:
    for line in f:
        valid_pdf_list.append(line.strip().strip('.pdf'))


def check_lines(page, top, buttom):
    lines = page.extract_words()[::]
    text = ''
    last_top = 0
    last_check = 0
    for l in range(len(lines)):
        each_line = lines[l]
        check_re = '(?:。|；|单位：元|单位：万元|币种：人民币|\d|报告(?:全文)?(?:（修订版）|（修订稿）|（更正后）)?)$'
        if top == '' and buttom == '':
            if abs(last_top - each_line['top']) <= 2:
                text = text + each_line['text']
            elif last_check > 0 and (page.height * 0.9 - each_line['top']) > 0 and not re.search(check_re, text):

                text = text + each_line['text']
            else:
                text = text + '\n' + each_line['text']
        elif top == '':
            if each_line['top'] > buttom:
                if abs(last_top - each_line['top']) <= 2:
                    text = text + each_line['text']
                elif last_check > 0 and (page.height * 0.85 - each_line['top']) > 0 and not re.search(check_re,
                                                                                                      text):
                    text = text + each_line['text']
                else:
                    text = text + '\n' + each_line['text']
        else:
            if each_line['top'] < top and each_line['top'] > buttom:
                if abs(last_top - each_line['top']) <= 2:
                    text = text + each_line['text']
                elif last_check > 0 and (page.height * 0.85 - each_line['top']) > 0 and not re.search(check_re,
                                                                                                      text):
                    text = text + each_line['text']
                else:
                    text = text + '\n' + each_line['text']
        last_top = each_line['top']
        last_check = each_line['x1'] - page.width * 0.85

    return text


def drop_empty_cols(data):
    # 转置数据，使得每个子列表代表一列而不是一行
    transposed_data = list(map(list, zip(*data)))
    # 过滤掉全部为空的列
    filtered_data = [col for col in transposed_data if not all(
        cell is '' for cell in col)]
    # 再次转置数据，使得每个子列表代表一行
    result = list(map(list, zip(*filtered_data)))
    return result


def change_pdf_to_txt(name):
    pdf = pdfplumber.open(name)
    last_num = 0

    all_text = {}
    allrow = 0
    for i in range(len(pdf.pages)):
        page = pdf.pages[i]
        buttom = 0
        tables = page.find_tables()
        if len(tables) >= 1:
            count = len(tables)
            for table in tables:
                if table.bbox[3] < buttom:
                    pass
                else:
                    count = count - 1
                    top = table.bbox[1]
                    text = check_lines(page, top, buttom)
                    text_list = text.split('\n')
                    for _t in range(len(text_list)):
                        all_text[allrow] = {}
                        all_text[allrow] = {'page': page.page_number, 'allrow': allrow, 'type': 'text',
                                            'inside': text_list[_t]}
                        allrow = allrow + 1

                    buttom = table.bbox[3]
                    new_table = table.extract()
                    r_count = 0

                    for r in range(len(new_table)):
                        row = new_table[r]
                        if row[0] == None:
                            r_count = r_count + 1
                            for c in range(len(row)):

                                if row[c] != None and row[c] != '' and row[c] != ' ':
                                    if new_table[r - r_count][c] == None:
                                        new_table[r - r_count][c] = row[c]
                                    else:
                                        new_table[r - r_count][c] = new_table[r -
                                                                              r_count][c] + row[c]
                                    new_table[r][c] = None
                        else:
                            r_count = 0
                    end_table = []
                    for row in new_table:
                        if row[0] != None:
                            cell_list = []
                            for cell in row:
                                if cell != None:
                                    cell = cell.replace('\n', '')
                                else:
                                    cell = ''
                                cell_list.append(cell)
                            end_table.append(cell_list)
                    end_table = drop_empty_cols(end_table)

                    for row in end_table:
                        all_text[allrow] = {'page': page.page_number, 'allrow': allrow, 'type': 'excel',
                                            'inside': str(row)}
                        # all_text[allrow] = {'page': page.page_number, 'allrow': allrow, 'type': 'excel',
                        #                     'inside': ' '.join()}
                        allrow = allrow + 1

                    if count == 0:
                        text = check_lines(page, '', buttom)
                        text_list = text.split('\n')
                        for _t in range(len(text_list)):
                            all_text[allrow] = {'page': page.page_number, 'allrow': allrow, 'type': 'text',
                                                'inside': text_list[_t]}
                            allrow = allrow + 1

        else:
            text = check_lines(page, '', '')
            text_list = text.split('\n')
            for _t in range(len(text_list)):
                all_text[allrow] = {'page': page.page_number, 'allrow': allrow, 'type': 'text',
                                    'inside': text_list[_t]}
                allrow = allrow + 1
        first_re = '[^计](?:报告(?:全文)?(?:（修订版）|（修订稿）|（更正后）)?)$'
        end_re = '^(?:\d|\\|\/|第|共|页|-|_| ){1,}'
        if last_num == 0:
            first_text = str(all_text[1]['inside'])
            end_text = str(all_text[len(all_text) - 1]['inside'])
            if re.search(first_re, first_text) and not re.search('\[', first_text):
                all_text[1]['type'] = '页眉'
                if re.search(end_re, end_text) and not re.search('\[', end_text):
                    all_text[len(all_text) - 1]['type'] = '页脚'
        else:

            first_text = str(all_text[last_num + 2]['inside'])

            end_text = str(all_text[len(all_text) - 1]['inside'])

            if re.search(first_re, first_text) and not re.search('\[', first_text):
                all_text[last_num + 2]['type'] = '页眉'
            if re.search(end_re, end_text) and not re.search('\[', end_text):
                all_text[len(all_text) - 1]['type'] = '页脚'

        last_num = len(all_text)-1
    # for key in all_text.keys():
    #     print(all_text[key])
    # pickle.dump(all_text,open('test_pdf.pkl','wb'))
    return all_text


important_tables = ['合并资产负债表', '母公司资产负债表', '合并利润表', '母公司利润表',
                    '合并现金流量表', '母公司现金流量表', '合并所有者权益变动表', '母公司所有者权益变动表']


def get_title_num_type(line):
    p1 = re.compile(r"^(第[一二三四五六七八九十]+节)")
    if line.strip() in important_tables or remove_title_type(line.strip()) in important_tables:
        return 7
    if p1.match(line) or line in ['目录','释义']:
        return 1
    p2 = re.compile(r"^(（[一二三四五六七八九十]+）)")
    if p2.match(line):
        return 2
    p3 = re.compile(r"^(\([一二三四五六七八九十]+\))")
    if p3.match(line):
        return 3
    p4 = re.compile(r"^([一二三四五六七八九十]+、)")
    if p4.match(line):
        return 8
    p5 = re.compile(r"^(\d+、)")
    if p5.match(line):
        return 4
    p6 = re.compile(r"^(（\d+）)")
    if p6.match(line):
        return 5
    p7 = re.compile(r"^(\(\d+\))")
    if p7.match(line):
        return 6
    p8 = re.compile(r"^(\d+\.)")
    if p8.match(line):
        return 9
    p9 = re.compile(r"^(\(\d+\))\.")
    if p9.match(line):
        return 10
    return -1


def remove_title_type(line):
    pattern = re.compile(
        r"^(第[一二三四五六七八九十]+节|（[一二三四五六七八九十]+）|\([一二三四五六七八九十]+\)|[一二三四五六七八九十]+、|\d+、|（\d+）|\(\d+\)|\d.|\(\d+\)\.)")
    result = pattern.sub("", line)
    result = result.replace('.','')
    return result


def get_pdf_text(filename):
    pdf_text = [eval(i.strip('\n'))
                for i in open(filename, encoding='utf-8').readlines()]
    return pdf_text


def extra_title():
    important_table_header = {}
    # valid_paths = json.load(open('valid_paths.json', 'r', encoding='utf-8'))
    # valid_paths = [i.strip('.json')+'.txt' for i in valid_paths]
    for foldername, subfolders, filenames in os.walk(input_folder):
        print('当前文件夹', foldername)
        for filename in tqdm(filenames):

            if filename.strip('.txt') not in valid_pdf_list:
                continue
            # if filename != '2020-04-10__欧普康视科技股份有限公司__300595__欧普康视__2019年__年度报告.txt':
            #     continue
            # if filename not in valid_paths:
            #     continue
            try:
                # allpdf
                # pdf_text = change_pdf_to_txt(os.path.join(foldername, filename))
                # pdf_text_list = [pdf_text[k] for k in pdf_text]

                # alltxt
                pdf_text_list = get_pdf_text(
                    os.path.join(foldername, filename))

                # 修补
                append_lines = []
                pattern = '|'.join(re.escape(word)
                                   for word in important_tables)
                regex = re.compile('(?:' + pattern + ')+$')
                for index, line_info in enumerate(pdf_text_list):
                    if not line_info:
                        continue
                    match = regex.search(line_info['inside'])
                    if match and '负责人' in line_info['inside']:
                        line_info['inside'] = match[0]

                # 识别出所有的标题，并且生成递归关系
                mulu_page = -1
                mulu_allrow = -1
                title_stack = []
                for index, line_info in enumerate(pdf_text_list):
                    if not line_info:
                        continue
                    text = line_info['inside']
                    if text.strip() == '目录':
                        mulu_page = line_info['page']
                        mulu_allrow = line_info['allrow']
                    title_num_type = get_title_num_type(text)
                    # 向下寻找直到找到第一个excel行则为表头
                    if title_num_type == 7:
                        temp_index = index
                        while pdf_text_list[temp_index]['type'] != 'excel' and temp_index <= (index+5):
                            temp_index += 1
                            continue
                        # 保存起来后面可以映射
                        important_table_header[index] = [pdf_text_list[ti]['inside'] for ti in range(index, temp_index + 1)
                                                         if pdf_text_list[ti]['type'] in ['text', 'excel'] and pdf_text_list[ti]['inside'].strip() != '']
                    # 找到符合标题特征的段落
                    if title_num_type != -1 and (line_info['page'] != mulu_page or line_info['allrow'] == mulu_allrow):
                        line_info['title_num_type'] = title_num_type
                    if 'title_num_type' in line_info:
                        # 往前遍历一遍看是否有同级节点，让浮标停在该位置
                        if title_stack:
                            i = len(title_stack)-1
                            while i >= 0:
                                if title_stack[i]['title_num_type'] == line_info['title_num_type']:
                                    title_stack = title_stack[:i+1]
                                    break
                                i -= 1
                        while title_stack and title_stack[-1]['title_num_type'] == line_info['title_num_type']:
                            title_stack.pop()
                        title_stack.append(line_info)
                        title_hierarchy_index = ' > '.join(
                            [str(t['allrow']) for t in title_stack])
                        pdf_text_list[index]['title_hierarchy_index'] = title_hierarchy_index
                        title_hierarchy = [remove_title_type(
                            t['inside']) for t in title_stack]
                        pdf_text_list[index]['title_hierarchy'] = title_hierarchy
                    else:
                        if title_stack:
                            title_hierarchy_index = ' > '.join(
                                [str(t['allrow']) for t in title_stack])
                            pdf_text_list[index]['title_hierarchy_index'] = title_hierarchy_index
                            title_hierarchy = [remove_title_type(
                                t['inside']) for t in title_stack]
                            pdf_text_list[index]['title_hierarchy'] = title_hierarchy
                        else:
                            pdf_text_list[index]['title_hierarchy_index'] = -1
                            pdf_text_list[index]['title_hierarchy'] = '无'

                # 根据递归关系，生成字典，key是标题名，value是对应的内容列表
                pdf_info_dict = defaultdict(list)
                exists_important_tables = []
                for line_info in pdf_text_list:
                    if 'title_hierarchy' in line_info and line_info['title_hierarchy'][-1] in important_tables:
                        exists_important_tables.append(
                            line_info['title_hierarchy'][-1])
                    if not line_info:
                        continue
                    if line_info['title_hierarchy_index'] != -1 and line_info['type'] in ['excel', 'text']:
                        new_line_info = {'title_hierarchy': line_info['title_hierarchy'],
                                         'content_type': line_info['type'],
                                         'content': line_info['inside']
                                         }
                        # 补充表头
                        try:
                            tmp = int(
                                line_info['title_hierarchy_index'].split(' > ')[-1])
                            if tmp in important_table_header and 'title_num_type' not in line_info and line_info['title_hierarchy'][-1] in important_tables:
                                new_line_info['excel_header'] = important_table_header[tmp]
                        except:
                            pass
                        pdf_info_dict[line_info['title_hierarchy_index']].append(
                            new_line_info)
                exists_important_tables = list(set(important_tables))
                try:
                    assert len(exists_important_tables) == len(
                        important_tables)
                except Exception as e:
                    # print(filename)
                    # print(exists_important_tables)
                    # print(important_tables)
                    raise e

                # 去除每个标题层级下面第一个数据,如果字符过长，则应该是正文，不进行删除
                for k in pdf_info_dict:
                    if len(pdf_info_dict[k][0]) < 50:
                        pdf_info_dict[k] = pdf_info_dict[k][1:]

                # 用自己
                with open(os.path.join(output_folder, filename.strip('.txt')+'.json'), 'w', encoding='utf-8') as f:
                    f.write(json.dumps(pdf_info_dict,
                            ensure_ascii=False, indent=4))

            except Exception as e:
                print('这个吊文件解析错误了:', filename)
                raise e


if __name__ == '__main__':
    extra_title()
