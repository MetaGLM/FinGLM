import json
import os
from tqdm import tqdm
import pandas as pd
    
key_list = [['合并资产负债表', '资产负债表'], ['合并现金流量表',  '现金流量表'], ['合并利润表', '利润表'], 
            ['公司信息'], ['员工数量、专业构成及教育程度', '员工情况'], ['研发投入'], ['主要会计数据和财务指标', '主要财务指标'], ['股本']]
keyword_dict = {'合并资产负债表': ['货币资金'],
                '资产负债表': ['货币资金'],
                '合并现金流量表': ['收到的现金'], 
                '现金流量表': ['收到的现金'],
                '合并利润表': ['营业收入'], 
                '利润表': ['营业收入'], 
                '公司信息': ['法定'], 
                '基本信息': ['法定'],
                '员工数量、专业构成及教育程度': ['教育程度'],
                '员工情况':['教育程度'],
                '研发投入':['研发人员'],
                '主要会计数据和财务指标': ['每股收益'],
                '主要财务指标': ['每股收益'],
                '股本':['股份总数']}

identifiers_list = ['<h>', '</h>', '<p>', '</p>']

def is_table(text):
    if text.startswith('<table'):
        return True
    return False

def extract_title(text):
    for identifier in identifiers_list:
        text = text.replace(identifier, '')
    return text
    
def heading_judge(text):
    title = extract_title(text)

def extract_keyword(text):
    for keys in key_list:
        for key in keys:
            if key in text:
                return keys[0]
    return False

def validity_judge(keyword, text):
    necessary_words = keyword_dict[keyword]
    for word in necessary_words:
        if word not in text:
            return False
    else:
        return True

def extract_cell(cell):
    for i in range(len(cell)):
        if cell[i] == '>':
            return cell[i+1:].strip()
    else:
        return '***NO_CONTENT***'
    
def extract_line(line):
    res = []
    for i in range(len(line)):
        if line[i: i+3] == '<td':
            break
    cells = line[i:].replace('\n', '').split('</td>')
    for cell in cells:
        cell = extract_cell(cell)
        if cell != '***NO_CONTENT***':
            res.append(cell)
    return res

def parse_table(text):
    res = []
    lines = text.split('</tr>')
    for line in lines:
        line = extract_line(line)
        if line:
            res.append(line)
    return res

def main(html_folder, output_folder):
    for file in tqdm(os.listdir(html_folder)):
        res = {}
        with open(os.path.join(html_folder, file), 'r', encoding='utf-8') as f:
            html_list = f.read().split('<br/>')
            keyword = False
            for idx, text in enumerate(html_list):
                if is_table(text):
                    if keyword and last_table:
                        df = parse_table(text)
                        res[keyword] += df
                    else:
                        for i in range(idx-3, idx):
                            keyword = extract_keyword(html_list[i])
                            if keyword:
                                break
                        else:
                            continue
                        if not res.get(keyword):
                            if validity_judge(keyword, text):
                                df = parse_table(text)
                                res[keyword] = df
                                last_table = True
                else:
                    last_table = False
        with open(os.path.join(output_folder, os.path.splitext(file)[0] + '.json'), 'w', encoding='utf-8') as f:
            json.dump(res, f, indent = 4, ensure_ascii = False)


if __name__ == '__main__':
    main(html_folder, output_folder)