import os
import sys
import json
import shutil
import pandas as pd
import sqlite3
from constant import DEBT_KEY, PROFIT_KEY, CASH_KEY 
from embeddings import find_top5

from verbaliser import make_label

def double(df, row=0, column=2):
    # if len(df.index) != 1:
        # print(df)
        # raise KeyError('df more than 1 row')
    replace_list = ['(', ')', ' ', ',']
    if isinstance(df.iloc[row, column], str):
        for item in replace_list:
            df.iloc[row, column] = df.iloc[row, column].replace(item, '')
        return float(df.iloc[row, column])
    else:
        return df.iloc[row, column]
    
def Int(str):
    return int(str.replace(',', ''))

def Float(str):
    return float(str.replace(',', ''))

def contain_table(table_name, file_paths):
    path_list = []
    for path in file_paths:
        if table_name in path:
            path_list.append(path)
    return path_list

def search_json(company_name, date, key):
    dir_name = f"data/tables/{company_name}__{date}年"
    if not os.path.exists(dir_name):
        raise KeyError(f'{dir_name} dir not exists')
    
    file_path = os.path.join(dir_name, '基本信息表.json')
    basic_info_dict = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        basic_info_dict = json.load(f)

    return basic_info_dict[key]
    
def search_table(company_name, date, key):
    dir_name = f"data/tables/{company_name}__{date}年"
    if not os.path.exists(dir_name):
        raise KeyError(f'{dir_name} dir not exists')
    
    file_paths = os.listdir(dir_name)
    file_path = []
    
    if key in (DEBT_KEY + ["非流动负债合计", "流动负债合计"]):
        file_path = contain_table('合并资产负债表', file_paths)
        if len(file_path) == 0:
            raise KeyError(f'{dir_name}/合并资产负债表.csv not exists')
    
    elif key in (PROFIT_KEY + ["联营企业和合营企业的投资收益"]):

        file_path = contain_table('合并利润表', file_paths)
        if len(file_path) == 0:
            raise KeyError(f'{dir_name}/合并利润表.csv not exists')
        
    elif key in (CASH_KEY + ["期末现金及现金等价物余额", "收回投资收到的现金"]):
        file_path = contain_table('合并现金流量表', file_paths)
        if len(file_path) == 0:
            raise KeyError(f'{dir_name}/合并现金流量表.csv not exists')
    
    df = None
    if len(file_path) == 0: return None
    elif len(file_path) == 1:
        file_path = os.path.join(dir_name, file_path[0])
        df = pd.read_csv(file_path)
    elif len(file_path) > 1:
        df = pd.read_csv(os.path.join(dir_name, file_path[0]))
        for path in file_path:
            path = os.path.join(dir_name, path)
            tmp = pd.read_csv(path)
            if len(tmp.index) > len(df.index):
                df = tmp
    
    # 清洗df 附注
    columns_to_drop = [col for col in df.columns if '附注' in col]
    df = df.drop(columns=columns_to_drop)
    
    def select_row(row):
        def align_key(key):
            return key.replace(' ', '').replace("(", "（").replace(")", "）").replace("（或股东权益）", "")
        def vague_map(key, value):
            return any(key in align_key(value) if isinstance(value, str) else False for value in row.values)
        if isinstance(key, str):
            return vague_map(key, row.values)
        elif isinstance(key, list):
            return any(vague_map(k, row.values) for k in key)
        
    result_row = df[df.apply(select_row, axis=1)]
    # df = pd.DataFrame(result_row.values, columns=list(df.columns))
    if result_row.empty:
        raise KeyError('error dataframe empty')
    return result_row


def search_financial_key(key, stat_dict, company_name, date):
    if key == '每股收益':
        stat_dict['每股收益'] = Float(search_json(company_name, date, '每股收益'))
    
    elif key == '每股净资产':
        stat_dict['总股本'] = double(search_table(company_name, date, '股本'))
        stat_dict['净资产'] = Float(search_json(company_name, date, '净资产'))
        stat_dict['每股净资产'] = '%.4f' % (stat_dict['净资产'] / stat_dict['总股本'])
        
    elif key == '每股经营现金流量':
        stat_dict['总股本'] = double(search_table(company_name, date, '股本'))
        stat_dict['现金流量净额'] = Float(search_json(company_name, date, '现金流量净额'))
        stat_dict['每股经营现金流量'] = '%.3f' % (stat_dict['现金流量净额'] / stat_dict['总股本'])
        
    elif key == '负债合计':
        stat_dict[key] = search_table(company_name, date, key)
        stat_dict[key] = double(stat_dict[key], row=-1)

    elif key == '利息收入':
        stat_dict[key] = search_table(company_name, date, key)
        if len(stat_dict[key].index) > 0 and stat_dict[key].iloc[0, 0] < 10:
            stat_dict[key] = double(stat_dict[key], row=0)
        else:
            stat_dict[key] = None
    else:
        stat_dict[key] = double(search_table(company_name, date, key))

    stat_dict[key] = '%.2f' % (stat_dict[key])

class Parser:

    def __init__(self) -> None:
        self.parse_fn_dict = {
        '0' : self.parse_special,
        '1' : self.parse_basic_info,
        '2' : self.parse_ratio,
        '3' : self.parse_finacial,
        '4' : self.parse_analysis,
        '5' : self.parse_sql,
    }


    def parse_finacial(self, item):
        keys = item['task_key']
        stat_dict = {}
        company_name = item['Company_name']
        date = item['DATE'][0]
        for key in keys:
            try:
                search_financial_key(key, stat_dict, company_name, date)
            except Exception as e:
                # dir not found : 没有找到XXX的信息
                # keyerror: 没有找到XXX信息
                if 'dir' not in e.__repr__():
                    print(item['question'], e)
                stat_dict[key] = '没有查询到对应的信息,无法回答'
            
        for k in stat_dict:
            stat_dict[k] = str(stat_dict[k])
        item['stat_dict'] = stat_dict
        
    def parse_basic_info(self, item):
        if len(item['task_key']) == 1:
            key = item['task_key'][0]
        else:
            print(item)
            return 
        # assert , "Ratio key got more than one argument"
        company_name, date = item['Company_name'], item['DATE'][0]
        try:
            if key == '法定代表人是否相同':
                item['DATE'] = list(map(int, item['DATE']))
                if len(item['DATE']) == 1:
                    if "上一年" in item['question'] or "上年" in item['question'] or "去年" in item['question']:
                        item['DATE'].append(item['DATE'][0]-1)
                    elif "前两年" in item['question']:
                        item['DATE'].append(item['DATE'][0]-1)
                        item['DATE'].append(item['DATE'][0]-2)
                    elif "前年" in item['question']:
                        item['DATE'].append(item['DATE'][0]-2)

                item['DATE'].sort()
                
                if f"{item['DATE'][0]}-{item['DATE'][1]}" in item['question']:
                    item['DATE'] = list(range(item['DATE'][0], item['DATE'][-1]+1))
                cur_TL = search_json(company_name, item['DATE'][0], "法定代表人")
                date = int(item['DATE'][0]) + 1
                ret_name = []
                ret = '相同'
                for date in item['DATE']:
                    TL = search_json(company_name, date, "法定代表人")
                    ret_name.append(TL)
                    if TL != cur_TL:
                        ret = '不相同'
                ret = ret + "|" + "|".join(ret_name)
            
            elif key == '企业名称':
                company_names_dict = {}
                with open('data/company_names.txt', 'r', encoding='utf-8') as f:
                    for line in f.readlines():
                        name, short_name = line.strip().split(":")
                        company_names_dict[short_name] = name
                
                if company_name in company_names_dict:
                    ret = company_names_dict[company_name]
                else:
                    ret = '没有查询到对应的信息,无法回答'
            
            elif key == '证券简称':
                ret = company_name
                
            else:
                ret = search_json(company_name, date, key)

                # 存在未提及的情况
                if ret == "未提及":
                    print(item['question'], "未提及")
                    self.parse_analysis(item)
                
            if isinstance(ret, str):
                ret = ret.replace(',', '')
            
            if ret == '-1':
                ret = '没有查询到对应的信息,无法回答'
            
        except Exception as e:
            if 'dir' not in e.__repr__():
                print(item['question'], e)
            ret = '没有查询到对应的信息,无法回答'
        
        ret = str(ret)
        item['stat_dict'] = {key: ret}
        
    def parse_ratio(self, item):
        assert len(item['task_key']) == 1, "Ratio key got more than one argument"
        key = item['task_key'][0]
        company_name, date = item['Company_name'], item['DATE'][0]
        stat_dict = {}
        try:
            if key == '流动比率':
                stat_dict['流动资产'] = double(search_table(company_name, date, '流动资产合计'))
                stat_dict['流动负债'] = double(search_table(company_name, date, '流动负债合计'))
                ret = stat_dict['流动资产'] / stat_dict['流动负债']
                
            elif key == '速动比率':
                stat_dict['流动资产'] = double(search_table(company_name, date, '流动资产合计'))
                stat_dict['存货'] = double(search_table(company_name, date, '存货'))
                stat_dict['流动负债'] = double(search_table(company_name, date, '流动负债合计'))
                ret = (stat_dict['流动资产'] - stat_dict['存货']) / stat_dict['流动负债']
                
            elif key == '现金比率':
                stat_dict['货币资金'] = double(search_table(company_name, date, '货币资金'))
                stat_dict['流动负债'] =  double(search_table(company_name, date, '流动负债合计'))
                ret = stat_dict['货币资金'] /stat_dict['流动负债']
                
            elif key == '资产负债比率':
                stat_dict['总负债'] = double(search_table(company_name, date, '负债合计'), row=2)
                stat_dict['资产总额'] = double(search_table(company_name, date, '资产总计'))
                ret = stat_dict['总负债'] / stat_dict['资产总额']
                
            elif key == '毛利率':
                stat_dict['营业收入'] = double(search_table(company_name, date, '营业收入'))
                stat_dict['营业成本'] = double(search_table(company_name, date, '营业成本'))
                ret = (stat_dict['营业收入'] - stat_dict['营业成本']) / stat_dict['营业收入']
            
            elif key == '净利润率':
                stat_dict['净利润'] = double(search_table(company_name, date, '净利润'))
                stat_dict['营业收入'] = double(search_table(company_name, date, '营业收入'))
                ret = stat_dict['净利润'] / stat_dict['营业收入']
            
            elif key == '流动负债比率':
                stat_dict['流动负债'] = double(search_table(company_name, date, '流动负债合计'))
                stat_dict['总负债'] = double(search_table(company_name, date, '负债合计'), row=2)
                ret = stat_dict['流动负债'] / stat_dict['总负债']
            
            elif key == '非流动负债比率':
                stat_dict['非流动负债'] = double(search_table(company_name, date, '非流动负债合计'))
                stat_dict['总负债'] = double(search_table(company_name, date, '负债合计'), row=2)
                ret = stat_dict['非流动负债'] / stat_dict['总负债']
                
            elif key == '企业研发经费占费用比例':
                stat_dict['销售费用'] = double(search_table(company_name, date, '销售费用'))
                stat_dict['管理费用'] = double(search_table(company_name, date, '管理费用'))
                stat_dict['财务费用'] = double(search_table(company_name, date, '财务费用'))
                stat_dict['研发费用'] = double(search_table(company_name, date, '研发费用'))
                ret = stat_dict['研发费用'] / (stat_dict['销售费用'] + stat_dict['管理费用'] + stat_dict['财务费用'] + stat_dict['研发费用']) 
                
            elif key == '三费比重':
                stat_dict['销售费用'] = double(search_table(company_name, date, '销售费用'))
                stat_dict['管理费用'] = double(search_table(company_name, date, '管理费用'))
                stat_dict['财务费用'] = double(search_table(company_name, date, '财务费用'))
                stat_dict['营业收入'] = double(search_table(company_name, date, '营业收入'))
                ret = (stat_dict['销售费用'] + stat_dict['管理费用'] + stat_dict['财务费用']) / stat_dict['营业收入']
                
            elif key == '财务费用率':
                stat_dict['财务费用'] = double(search_table(company_name, date, '财务费用'))
                stat_dict['营业收入'] = double(search_table(company_name, date, '营业收入'))
                ret =  stat_dict['财务费用'] / stat_dict['营业收入']
                
            elif key == '管理费用率':
                stat_dict['管理费用'] = double(search_table(company_name, date, '管理费用'))
                stat_dict['营业收入'] = double(search_table(company_name, date, '营业收入'))
                ret =  stat_dict['管理费用'] / stat_dict['营业收入']
            
            elif key == '营业成本率':
                stat_dict['营业收入'] = double(search_table(company_name, date, '营业收入'))
                stat_dict['营业成本'] = double(search_table(company_name, date, '营业成本'))
                ret =  stat_dict['营业成本'] / stat_dict['营业收入']
                
            elif key == '营业利润率':
                stat_dict['营业利润'] = double(search_table(company_name, date, '营业利润'))
                stat_dict['营业收入'] = double(search_table(company_name, date, '营业收入'))
                ret =  stat_dict['营业利润'] / stat_dict['营业收入']
            
            elif key == "净资产收益率":
                stat_dict['净利润'] = double(search_table(company_name, date, '净利润'))
                stat_dict['净资产'] = double(search_table(company_name, date, '净资产'))
                ret =  stat_dict['净利润'] / stat_dict['净资产']
            
            elif key.endswith('增长率'):
                if key == '现金及现金等价物增长率':
                    _key = '期末现金及现金等价物余额'
                elif key == '流动负债增长率':
                    _key = '流动负债合计'
                elif key == '总资产增长率':
                    _key = '资产总计'
                elif key == '总负债增长率':
                    _key = '负债合计'
                else:
                    _key = key[:-3]
                
                search_result = search_table(company_name, date, _key)
                stat_dict['去年'] = double(search_result, column=3) 
                stat_dict['今年'] = double(search_result) 
                ret = stat_dict['今年'] / stat_dict['去年'] - 1
                
            elif key == '投资收益占营业收入比率':
                stat_dict['投资收益'] = double(search_table(company_name, date, '投资收益'))
                stat_dict['营业收入'] = double(search_table(company_name, date, '营业收入'))
                
                ret = stat_dict['投资收益'] / stat_dict['营业收入']
                
            elif key == '企业研发经费与营业收入比值':
                stat_dict['研发费用'] = double(search_table(company_name, date, '研发费用'))
                stat_dict['营业收入'] = double(search_table(company_name, date, '营业收入'))
                
                ret = stat_dict['研发费用'] / stat_dict['营业收入']
            
            elif key == '企业研发经费与利润比值':
                stat_dict['研发费用'] = double(search_table(company_name, date, '研发费用'))
                stat_dict['净利润'] = double(search_table(company_name, date, '净利润'))
                ret = stat_dict['研发费用'] / stat_dict['净利润']
                
            elif key == '研发人员占职工人数比例':
                stat_dict['研发人员数'] = Int(search_json(company_name, date, '研发人员数'))
                stat_dict['职工总数'] = Int(search_json(company_name, date, '职工总数'))
                ret = stat_dict['研发人员数'] / stat_dict['职工总数'] if stat_dict['研发人员数'] != -1 and stat_dict['职工总数'] != -1 else -1
                if ret == -1:
                    raise KeyError()
                    # ret = '没有查询到对应的信息,无法回答'
                    
            elif key == '企业硕士及以上人员占职工人数比例':
                stat_dict['硕士人数'] = Int(search_json(company_name, date, '硕士人数'))
                stat_dict['博士及以上'] = Int(search_json(company_name, date, '博士及以上'))
                if stat_dict['博士及以上'] == -1: stat_dict['博士及以上'] = 0
                stat_dict['职工总数'] = Int(search_json(company_name, date, '职工总数'))
                ret = (stat_dict['硕士人数'] + stat_dict['博士及以上']) / stat_dict['职工总数'] if stat_dict['硕士人数'] != -1 and stat_dict['职工总数'] != -1 else -1
                if ret == -1:
                    raise KeyError()
                    # ret = '没有查询到对应的信息,无法回答'
            else:
                print(item['question'])
                ret = 0
            
            if key in ['企业研发经费与利润比值', '企业研发经费与营业收入比值', '流动比率', '速动比率', '企业研发经费占费用比例', '企业硕士及以上人员占职工人数比例', '研发人员占职工人数比例']:
                ret = '%.2f' % (ret)
            else:
                ret = '%.2f' % (ret * 100) + '%'

        except Exception as e:
            if 'dir' not in e.__repr__():
                print(item['question'], e)
            ret = '没有查询到对应的信息,无法回答'
            stat_dict[key] = ''
        
        stat_dict[key] = str(ret)
        item['stat_dict'] = stat_dict
        

    def parse_special(self, item):
        pass

    def parse_analysis(self, item):
        key = item['task_key'][0]
        item['stat_dict'] = {}
        company_name = item['Company_name']
        date = item['DATE'][0]
        full_name = ""
        with open('data/company_names.txt', 'r', encoding='utf-8') as f:
            for line in f.readlines():
                name, short_name = line.strip().split(":")
                if short_name == company_name:
                    full_name = name
                    break

        question = item['question'].replace(date+"年", "").replace(full_name, "").replace(company_name, "").replace("年报数据", '')
        # 年份一起替换了 替换公司名为公司(full name and short name)
        #
        folder_path = os.path.join(f"./data/tables/{company_name}__{date}年")
        # 先去找 analysis.json if task_key in analysis key
        if not os.path.exists(folder_path):
            item['stat_dict'][key] = "没有查询到对应的信息,无法回答"
        else:
            try:
                if key in ["情况", "分析", "原因", "简要介绍", "简要概述"]:
                    item['stat_dict'][key] = find_top5(folder_path, question)
                elif os.path.exists(tmp:=os.path.join(folder_path, 'analysis.json')):
                    with open(tmp, 'r', encoding='utf-8') as f:
                        analysis_dict = json.load(f)
                        for dict_key in analysis_dict.keys():
                            if key in dict_key or key in dict_key.replace('的', ''):
                                item['stat_dict'][key] = [" ".join(analysis_dict[dict_key])]
                    
                    # 没有检索到对应的字段
                    if key not in item['stat_dict']:
                        item['stat_dict'][key] = find_top5(folder_path, question)
                else:
                        item['stat_dict'][key] = find_top5(folder_path, question)
            except Exception as e:
                item['stat_dict'][key] = "没有查询到对应的信息,无法回答"

    def parse_sql(self, item):
        """
            输入: item 一个字典，字段包含
            {"id": int 问题id
            "question": str 问题字符串
            "DATE": List[str] 询问的年份
            "Company_name": str 公司名
            "category" : int 问题分类
            "task_key" : List[strs] 用于识别SQL关键词
            "location" : str: "None" 代表没有地址
            "rank" : 最高 -> 1，第X高 - > X，最低 -> -1
            "range" : bool，rank表示范围（T）还是第n（F）
            "require_money" : bool，需要金额（T）与否（F）
            }

            输出: item 一个字典，新增加字段包含
            "SQLquery" : 
            }
        """
        ####SELECT
        key = item['task_key'][0]
        item['SQLquery'] = "SELECT 公司名称"
        if item['require_money'] == True:
            item['SQLquery'] = item['SQLquery'] + ", " + key
        
        ####FROM
        if key in DEBT_KEY:
            item['SQLquery'] = item['SQLquery'] + " FROM debt"
        elif key in CASH_KEY:
            item['SQLquery'] = item['SQLquery'] + " FROM cash"
        else:
            item['SQLquery'] = item['SQLquery'] + " FROM profit"
        
        ####WHERE
        flag = 0
        if len(item['DATE']) > 1:
            if flag == 0:
                item['SQLquery'] = item['SQLquery'] + " WHERE"
                flag = 1
            else:
                item['SQLquery'] = item['SQLquery'] + " AND"
            item['SQLquery'] = item['SQLquery'] + " 年份 BETWEEN " + item['DATE'][0] + " AND " + item['DATE'][1]
        elif len(item['DATE']) == 1:
            if flag == 0:
                item['SQLquery'] = item['SQLquery'] + " WHERE"
                flag = 1
            else:
                item['SQLquery'] = item['SQLquery'] + " AND"
            item['SQLquery'] = item['SQLquery'] + " 年份 = " + item['DATE'][0]
        if item['location'] != "None":
            if flag == 0:
                item['SQLquery'] = item['SQLquery'] + " WHERE"
                flag = 1
            else:
                item['SQLquery'] = item['SQLquery'] + " AND"
            item['SQLquery'] = item['SQLquery'] + f" 注册地址 LIKE '%{item['location']}%'"
        
        ###ORDER BY
        item['SQLquery'] = item['SQLquery'] + " ORDER BY " + key
        if item['range'] == True:
            if item['rank'] > 0:
                item['SQLquery'] = item['SQLquery'] + " DESC NULLS LAST LIMIT " + str(item['rank']) 
            else:
                item['SQLquery'] = item['SQLquery'] + " ASC NULLS LAST LIMIT " + str(abs(item['rank'])) 
        elif abs(item['rank']) > 1:
            if item['rank'] > 0:
                item['SQLquery'] = item['SQLquery'] + " DESC NULLS LAST LIMIT 1 OFFSET " + str(item['rank'] - 1) 
            else:
                item['SQLquery'] = item['SQLquery'] + " ASC NULLS LAST LIMIT 1 OFFSET " + str(abs(item['rank']) - 1) 
        else:
            if item['rank'] > 0:
                item['SQLquery'] = item['SQLquery'] + " DESC NULLS LAST LIMIT 1"
            else:
                item['SQLquery'] = item['SQLquery'] + " ASC NULLS LAST LIMIT 1"
        

        ###
        if item['intersect'] == True:
            sql_querys = []
            single_year_query = f"SELECT 公司名称 FROM (" + item['SQLquery'].replace( f"BETWEEN {item['DATE'][0]} AND {item['DATE'][1]}", "= YEAR") + f") as ret_YEAR"
            start_year, end_year = int(item['DATE'][0]), int(item['DATE'][1])
            for cur_year in range(start_year, end_year + 1):
                sql_querys.append(single_year_query.replace("YEAR", str(cur_year)))
            item['SQLquery'] = " INTERSECT ".join(sql_querys)

        # 执行SQL
        conn = sqlite3.connect('data/company.db')
        cursor = conn.cursor()
        try:
            cursor.execute(item['SQLquery'])
            sql_ret = cursor.fetchall()
            item['stat_dict'] = {}
            item['stat_dict'][key] = sql_ret
        except Exception as e:
            print(item["question"], e)
            sql_ret = ""

        item['stat_dict'] = {key: sql_ret}

    def parse_question(self, item):
        parse_fn = self.parse_fn_dict[str(item['category'])]
        parse_fn(item)


def parse_question(path='./data/parse_question.json'):
    questions = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            questions.append(json.loads(line))
    
    parser = Parser()
    datasets = [] 
    for question in questions:
        # parse_fn = parser.parse_fn_dict[str(question['category'])]
        company_name = question['Company_name']
        year = question['DATE']
        parser.parse_question(question)

    make_label(questions)
    
    for question in questions:
        if question['prompt'] != '':
            datasets.append({
                "question" : question['question'],
                "prompt" : f"{question['prompt'][:5000]}",
                "target" : f"{question['prompt'][:5000]}",
                "category" : question['category'],
            })
        else:
            datasets.append({
                "question" : question['question'],
                "prompt" : f"简洁和专业的来回答用户的问题，如果无法从中得到答案，可以乱编或改写提问句子回复。无法根据以上信息回答问题",
                "target" : "无法根据以上信息回答问题",
                "category" : question['category'],
            })
            
        
    with open('data/dataset.json', 'w') as file:
        for question in questions:
            file.write(json.dumps(question, ensure_ascii=False) + '\n')
    
    with open('data/smp2023/dataset.json', 'w') as file:
        json.dump(datasets, file, ensure_ascii=False)

# puts into language model dataset

if __name__ == '__main__':
    parse_question()