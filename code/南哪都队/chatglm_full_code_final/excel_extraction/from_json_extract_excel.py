import json
import os
from tqdm import tqdm
from collections import defaultdict
import re

json_folder = 'data/dict_json'
txt_excel_folder = 'data/txt_excel'

key_list = [['合并资产负债表', '资产负债表'], ['合并现金流量表',  '现金流量表'], ['合并利润表', '利润表', '合并及母公司利润表'], 
            ['公司信息'], ['员工数量、专业构成及教育程度', '员工情况'], ['研发投入'], ['主要会计数据和财务指标', '主要财务指标'], ['股本']]
keyword_dict = {'合并资产负债表': ['货币资金'],
                '资产负债表': ['货币资金'],
                '合并现金流量表': ['收到的现金'], 
                '现金流量表': ['收到的现金'],
                '合并利润表': ['营业收入', '利息收入'], 
                '利润表': ['营业收入', '利息收入'], 
                '合并及母公司利润表': ['营业收入', '利息收入'], 
                '公司信息': ['法定'], 
                '基本信息': ['法定'],
                '员工数量、专业构成及教育程度': ['教育程度'],
                '员工情况':['教育程度'],
                '研发投入':['研发人员'],
                '主要会计数据和财务指标': ['每股收益'],
                '主要财务指标': ['每股收益'],
                '股本':['股份总数']}

text_keyword_dict = {'合并资产负债表': ['货币资金'],
                    '资产负债表': ['货币资金'],
                    '合并现金流量表': ['收到的现金'], 
                    '现金流量表': ['收到的现金'],
                    '合并利润表': ['营业收入', '利息收入', '利息支出'], 
                    '利润表': ['营业收入', '利息收入', '利息支出'], 
                    '合并及母公司利润表': ['营业收入', '利息收入', '利息支出'], 
                    '公司信息': ['法定'], 
                    '基本信息': ['法定'],
                    '员工数量、专业构成及教育程度': ['教育程度'],
                    '员工情况':['教育程度'],
                    '研发投入':['研发人员'],
                    '主要会计数据和财务指标': ['每股收益'],
                    '主要财务指标': ['每股收益'],
                    '股本':['股份总数']}


def extract_excel(target, doc_list):
    flag = False
    new_table = True
    res = []
    for doc in doc_list:
        if isinstance(doc, list):
            if new_table: #新表
                if '调整' in doc or '调整' in doc[0] or '1月' in doc or '1月' in doc[0]:
                    return False
                for kw in keyword_dict[target]:
                    for row in doc:
                        if kw in row:
                            res += doc
                            break #识别出当前目标关键词，跳出本层循环
                    else:
                        continue #没识别出目标关键词，继续看下一个目标关键词
                    flag = True
                    new_table = False
                    break #识别出当前目标关键词，flag置True（允许中间出现一行text），跳出本层循环
                else:
                    continue #没识别出目标关键词，本excel无效，继续查找下一个excel
            else: #续表
                flag = True
                res += doc
        elif flag:
            flag = False #一行text上限达到，flag置False
        elif res:
            break  #如果已经有抽取结果且一行text上限达到，结束遍历       
    return res
    

def dfs(json_dict, target):
    res = []
    for key, value in json_dict.items():
        if isinstance(value, dict):
            temp = dfs(json_dict[key], target)
            if len(temp) > 0:
                res += temp
        elif target in key:
            if len(value)>0:
                excel = extract_excel(target, value)
                if excel:
                    res.append(excel)    
    return res 


def thorough_extract_excel(target, doc):
    if '调整' in doc or '调整' in doc[0] or '1月' in doc or '1月' in doc[0]:
        return False
    for kw in keyword_dict[target]:
        for row in doc:
            if kw in row:
                return doc
    return False

def thorough_dfs(json_dict, target):
    res = []
    flag = False
    temp = []
    for key, value in json_dict.items():
        if target == '利润表' and key == '二、财务报表':
            pass
        if isinstance(value, dict):
            temp = thorough_dfs(json_dict[key], target)
            if len(temp) > 0:
                res += temp
        else:
            for text in value:
                if target in text:
                    flag = True
                elif flag:
                    #temp.append(text)
                    if isinstance(text, list):
                        flag = False
                        excel = thorough_extract_excel(target, text)
                        if excel:
                            res.append(excel)
                        break
            else:
                flag = False
    return res 

def post_process(result):
    for key, value in result.items():
        len_list = [len(v[0]) for v in value]
        for v in value:
            if len(v[0]) == max(len_list):
                result[key] = v[0]
                break
    return result

def str_to_list(text_list):
    res = []
    for line in text_list:
        try:
            res.append(eval(line))
        except:
            res.append(line)
    return res

def eval_json(json_dict):
    res = {}
    for key in json_dict:
        res[key] = str_to_list(json_dict[key])
    return res

def text_extract(text, keyword):
    try: 
        first_digit_pos = re.search('[0-9]', text).span()[0]
        digit = text[first_digit_pos:]
        attr = text[:first_digit_pos]
        if keyword not in attr:
            return
        if '.' in digit:
            digits = digit.split('.')
            idx = 0
            while idx<len(digits)-1:
                digits[idx]+= '.'+digits[idx+1][:2]
                digits[idx+1] = digits[idx+1][2:]
                idx += 1
        else:
            return
        return [attr] + digits[:-1]
    except AttributeError:
        return

def text_dfs(json_dict, target):
    res = []
    flag = False
    temp = []
    for key, value in json_dict.items():
        if isinstance(value, dict):
            temp = thorough_dfs(json_dict[key], target)
            if len(temp) > 0:
                res += temp
        else:
            temp = []
            for text in value:
                if target in text:
                    flag = True
                elif flag:
                    for keyword in text_keyword_dict[target]:
                        if keyword in text:
                            if line_excel := text_extract(text, keyword):
                                temp.append(line_excel)
                    if len(temp) == len(text_keyword_dict[target]):
                        break
            if temp:
                res.append(temp)
    return res 

def main(json_folder, output_folder, start_idx = 0):
    for idx, file in tqdm(enumerate(os.listdir(json_folder))):
        if idx < start_idx:
            continue
        #if '603348' not in file or '2019年' not in file:
        #    continue
        with open(os.path.join(json_folder, file), 'r', encoding = 'utf-8') as f:
            result = defaultdict(list)
            json_dict = json.load(f)
            for keys in key_list:
                for key in keys:
                    if current_excels := dfs(json_dict, key):
                        result[keys[0]].append(current_excels)
                    if current_excels := thorough_dfs(json_dict, key):
                        result[keys[0]].append(current_excels)
                    if current_excels := text_dfs(json_dict, key):
                        result[keys[0]].append(current_excels)
                    if result.get(key):
                        break
            result = post_process(result)
            result = eval_json(result)

        with open(os.path.join(output_folder, file), 'w', encoding='utf-8') as f_out:
            json.dump(result, f_out, indent=4, ensure_ascii = False)
                
if __name__ == '__main__':
    main(json_folder, txt_excel_folder, 0) 