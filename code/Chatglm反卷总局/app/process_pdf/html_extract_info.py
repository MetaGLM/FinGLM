#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/8/12 13:40
# @Author  : musklin
# @Site    : 
# @File    : get_report_info.py
# @Function:

import os
import sys
import re
from bs4 import BeautifulSoup
from tqdm import tqdm
import re


def judge_caibao_title(line):
    p = re.compile(r"(第[一二三四五六七八九十]+节)|(（[一二三四五六七八九十]+）)|(\([一二三四五六七八九十]+\))|([一二三四五六七八九十]+、)|(\d+、)|(（\d+）)|(\(\d+\))")
    matches = p.findall(line)
    matched_substrings = [match for group in matches for match in group if match]
    if (matched_substrings and line.endswith('财务报表')) or (line.endswith('财务报表') and len(line) < 10):
        return True
    if matched_substrings and line.endswith('财务报告'):
        return True
    return False

def remove_title_type(line):
    pattern = re.compile(r"^(第[一二三四五六七八九十]+节|（[一二三四五六七八九十]+）|\([一二三四五六七八九十]+\)|[一二三四五六七八九十]+、|\d+、|（\d+）|\(\d+\)|\d.)")
    result = pattern.sub("", line)
    result = re.sub(r'[（(][^)）]*[)）]', '', result)
    result = result.replace('、.', '').strip()
    return result

def judge_table(tag_content):
    try:
        tag_content = tag_content.strip()
    except:
        return None
    if judge_caibao_title(tag_content):
        return 'caibao_title'
    tag_content = remove_title_type(tag_content)
    if tag_content in balance_tables_keywords:
        return 'balance'
    elif tag_content in profit_tables_keywords:
        return 'profit'
    elif tag_content in cashflow_tables_keywords:
        return 'cashflow'
    return None

# 打开文件并读取内容
def read_html(filePath: str):
    # print(filePath)
    with open(filePath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 创建一个BeautifulSoup对象
    soup = BeautifulSoup(content, 'html.parser')

    balance = []
    profit = []
    cashflow = []
    # 遍历所有的标签
    # 状态1，进入财务报表
    # 状态2：找到合并资产负债表
    # 状态3：退出合并资产负债表，找寻合并利润表
    # 状态4：找到合并利润表
    # 状态5：退出合并利润表，找寻合并现金流量表
    # 状态6：找到合并现金流量表
    conditionFlag = 0
    for tag in soup.children:
        if tag.name:
            # if len(tag.contents)>0 and tag.contents[0] == '二、财务报表':
            #     print(1)
            if len(tag.contents) == 1:
                # 修补
                match = important_tables_regex.search(tag.contents[0])
                if match and '负责人' in tag.contents[0] and tag.contents[0].endswith(match[0]):
                    tag.contents[0] = match[0]
            # if len(tag.contents) >= 1:
            #     print(tag.contents)
            if conditionFlag == 0:
                if tag.name in ["h","p"] and len(tag.contents) >= 1 and judge_table(tag.contents[0])=='caibao_title' and len(tag.contents[0])<=40:
                    conditionFlag = 1
            elif conditionFlag == 1:
                if len(tag.contents) >= 1 and judge_table(tag.contents[0]) == 'balance':
                    conditionFlag = 2
            elif conditionFlag == 2:
                if tag.name == "table":
                    trs = tag.children
                    for tr in trs:
                        if tr.name:
                            tds = tr.children
                            td_list = []
                            for td in tds:
                                if td.name:
                                    td_list.append(td)
                            if len(td_list) == 2:
                                balance.append((td_list[0].contents[0].replace('\n', ''),
                                                td_list[1].contents[0].replace('\n', '')))
                            elif len(td_list) == 3:
                                balance.append((td_list[0].contents[0].replace('\n', ''),
                                                td_list[1].contents[0].replace('\n', '')))
                            elif len(td_list) == 4:
                                balance.append((td_list[0].contents[0].replace('\n', ''),
                                                td_list[2].contents[0].replace('\n', '')))
                            elif len(td_list) == 5:
                                balance.append((td_list[0].contents[0].replace('\n', ''),
                                                td_list[2].contents[0].replace('\n', '')))
                            elif len(td_list) == 6:
                                balance.append((td_list[0].contents[0].replace('\n', ''),
                                                td_list[2].contents[0].replace('\n', '')))
                elif tag.name != "table" and len(tag.contents) >= 1 and '母公司资产负债表' in tag.contents[0]:
                    conditionFlag = 3
                elif tag.name != "table" and len(tag.contents) >= 1 and judge_table(tag.contents[0]) == 'profit':
                    conditionFlag = 4
            elif conditionFlag == 3:
                if tag.name != "table" and len(tag.contents) >= 1 and judge_table(tag.contents[0]) == 'profit':
                    conditionFlag = 4
            elif conditionFlag == 4:
                if tag.name == "table":
                    trs = tag.children
                    for tr in trs:
                        if tr.name:
                            tds = tr.children
                            td_list = []
                            for td in tds:
                                if td.name:
                                    td_list.append(td)
                            if len(td_list) == 2:
                                profit.append((td_list[0].contents[0].replace('\n', ''),
                                               td_list[1].contents[0].replace('\n', '')))
                            elif len(td_list) == 3:
                                profit.append((td_list[0].contents[0].replace('\n', ''),
                                               td_list[1].contents[0].replace('\n', '')))
                            elif len(td_list) == 4:
                                profit.append((td_list[0].contents[0].replace('\n', ''),
                                               td_list[2].contents[0].replace('\n', '')))
                            elif len(td_list) == 5:
                                profit.append((td_list[0].contents[0].replace('\n', ''),
                                               td_list[2].contents[0].replace('\n', '')))
                            elif len(td_list) == 6:
                                profit.append((td_list[0].contents[0].replace('\n', ''),
                                               td_list[2].contents[0].replace('\n', '')))
                elif tag.name != "table" and len(tag.contents) >= 1 and '母公司利润表' in tag.contents[0]:
                    conditionFlag = 5
                elif tag.name != "table" and len(tag.contents) >= 1 and judge_table(tag.contents[0]) == 'cashflow':
                    conditionFlag = 6
            elif conditionFlag == 5:
                if tag.name != "table" and len(tag.contents) >= 1 and judge_table(tag.contents[0]) == 'cashflow':
                    conditionFlag = 6
            elif conditionFlag == 6:
                if tag.name == "table":
                    trs = tag.children
                    for tr in trs:
                        if tr.name:
                            tds = tr.children
                            td_list = []
                            for td in tds:
                                if td.name:
                                    td_list.append(td)
                            if len(td_list) == 2:
                                cashflow.append((td_list[0].contents[0].replace('\n', ''),
                                                 td_list[1].contents[0].replace('\n', '')))
                            elif len(td_list) == 3:
                                cashflow.append((td_list[0].contents[0].replace('\n', ''),
                                                 td_list[1].contents[0].replace('\n', '')))
                            elif len(td_list) == 4:
                                cashflow.append((td_list[0].contents[0].replace('\n', ''),
                                                 td_list[2].contents[0].replace('\n', '')))
                            elif len(td_list) == 5:
                                cashflow.append((td_list[0].contents[0].replace('\n', ''),
                                                 td_list[2].contents[0].replace('\n', '')))
                            elif len(td_list) == 6:
                                cashflow.append((td_list[0].contents[0].replace('\n', ''),
                                                 td_list[2].contents[0].replace('\n', '')))
                elif tag.name != "table" and len(tag.contents) >= 1 and '母公司现金流量表' in tag.contents[0]:
                    conditionFlag = 7
                    break
                elif tag.name != "table" and len(tag.contents) >= 1 and '合并所有者权益变动表' in tag.contents[0]:
                    conditionFlag = 8
                    break
    return balance, profit, cashflow





if __name__ == '__main__':
    # html_path = 'E:\\allpdf_html\\'
    # # 输出的文件位置
    # out_dir = "E:\\html抽取三表19到21\\"

    list_file = sys.argv[1]
    html_path = sys.argv[2]
    out_dir = sys.argv[3]
    process_num = int(sys.argv[4])
    process_id = int(sys.argv[5])

    balance_tables_keywords = ['合并资产负债表', '资产负债表', '合并及母公司资产负债表', '合并及银行资产负债表']
    profit_tables_keywords = ['合并利润表', '利润表', '合并及母公司利润表', '合并及银行利润表']
    cashflow_tables_keywords = ['合并现金流量表', '现金流量表', '合并及母公司现金流量表', '合并及银行现金流量表']
    important_tables = balance_tables_keywords + profit_tables_keywords + cashflow_tables_keywords
    important_tables.sort(key=len, reverse=True)
    important_tables_regex = re.compile('(?:' + '|'.join(important_tables) + ')+$')

    html_names = []
    for line in open(list_file,'r',encoding='utf-8').readlines():
        line = line.strip().replace(".pdf","")
        html_names.append(line)

    for index,name in tqdm(enumerate(html_names)):
        if index % process_num != process_id:
            continue
        # if name != '2021-04-28__深圳市科陆电子科技股份有限公司__002121__科陆电子__2020年__年度报告':
        #     continue
        print(index, name)
        file_path = os.path.join(html_path, name) + ".html"
        if not os.path.exists(file_path):
            continue
        balance,profit,cashflow = read_html(os.path.join(html_path,name)+".html")

        with open(out_dir+name+".txt_balance.txt", 'w', encoding='utf-8') as f:
            for t in balance:
                try:
                    f.write(t[0]+'\001'+t[1]+'\n')
                except:
                    continue
        with open(out_dir+name+".txt_profit.txt", 'w', encoding='utf-8') as f:

            for t in profit:
                try:
                    f.write(t[0]+'\001'+t[1]+'\n')
                except:
                    continue
        with open(out_dir+name+".txt_cashflow.txt", 'w', encoding='utf-8') as f:
            for t in cashflow:
                try:
                    f.write(t[0]+'\001'+t[1]+'\n')
                except:
                    continue