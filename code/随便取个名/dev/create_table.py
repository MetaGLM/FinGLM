import sqlite3
import os
import re
import json
import csv

path = './data/tables/'

debtkey = ['公司名称', '年份', '注册地址', '负债合计', '应付职工薪酬', 
           '资产总计', '流动资产合计', '非流动资产合计', 
           '应收款项融资', '货币资金', 
            '衍生金融资产', '其他非流动金融资产',
            '流动负债合计', '非流动负债合计',
            '固定资产', '无形资产', '存货', '实收资本', '股本',
            '交易性金融资产', '应收账款', '预付款项', '应付账款', 
            '其他流动资产', '其他非流动资产', '短期借款', '长期借款',
            '在建工程', '资本公积',
            '盈余公积', '未分配利润', '递延所得税负债',
            '应收票据', '应付票据',
            '应交税费', '所有者权益合计', 
            '负债和所有者权益总计', '商誉',
            '长期应收款', '长期股权投资', '租赁负债',
            '资本支出', '资产减值损失', '债权投资',
            ]

profitkey = ['公司名称', '年份', '注册地址', '营业利润', '营业成本', '营业收入',
            '营业外支出', '营业外收入',
            '利息支出', '利息收入',
            '投资收益', '变动收益',
            '研发费用', '财务费用', 
            '销售费用', '管理费用', 
            '利润总额', '净利润', 
            '所得税费用', '综合收益总额', '税金及附加', 
            '联营企业和合营企业投资收益',
            '公允价值变动收益',
            '信用减值损失', '资产减值损失', '资产处置收益',
            '持续经营净利润', '营业总收入', '营业总成本',
            '营业外收支净额', '归属于母公司所有者权益合计',]

cashkey = ['公司名称', '年份', '注册地址', '收回投资收到现金', '现金及现金等价物余额', 
            '投资支付', '经营活动现金流入', '经营活动现金流出',
            '投资活动现金流入', '投资活动现金流出', '筹资活动现金流出',
            '筹资活动现金流入', '现金及现金等价物净增加额']

keymapping = {
    "联营企业和合营企业投资收益" : "联营企业和合营企业的投资收益",
    "收回投资收到现金" : "收回投资收到的现金",
    "现金及现金等价物余额"  : "期末现金及现金等价物余额",
    "流动负债" : "流动负债合计",
    "非流动负债" : "非流动负债合计",
    "流动资产" : "流动资产合计",
    "非流动资产" : "非流动资产合计",
}


def create_debt(foldername):
    empty_debt = [float('NaN')] * (len(debtkey))
    empty_debt[0] = foldername.split('__')[0]
    empty_debt[1] = int(foldername.split('__')[1].strip('年'))
    for filename in os.listdir(path+foldername):
        if re.match("基本信息表.json", filename):
            with open(os.path.join(path+foldername, filename), 'r',encoding='utf-8') as fd:
                json_data = json.load(fd)
                empty_debt[0] = json_data['文档公司名']
                empty_debt[1] = int(json_data['年份'].strip('年'))
                empty_debt[2] = json_data['注册地址']
        if re.match(".*合并资产负债表.*\.csv", filename):
            with open(os.path.join(path+foldername, filename), 'r',encoding='utf-8') as fd:
                sheet = csv.reader(fd)
                header = next(sheet)
                table = []
                index1 = -1
                index2 = -1
                for index,it in enumerate(header):
                    if re.match('项目', it.replace(' ','')):
                        index1 = index
                    if re.match('%d年12月31日'%(empty_debt[1]), it.replace(' ','')):
                        index2 = index
                if index1 == -1 or index2 == -1:
                    continue
                for row in sheet:
                    table.append([row[index1], row[index2]])
                for i in range(3, len(debtkey)):
                    minlength = 99
                    for item in table:
                        if debtkey[i] in item[0]:
                            if len(item[0]) < minlength:
                                if re.match("-+[^0-9]", item[1]+" ") or "－" in item[1] or '不适用' in item[1] or '/' in item[1]:
                                    empty_debt[i] = 0
                                else:
                                    tmp = item[1].replace(' ','').replace(',','').strip('(').strip(')').strip('（').strip('）')
                                    if len(tmp) < 1:
                                        empty_debt[i] = 0
                                    else:
                                        if tmp.find('.') >= 0 and len(tmp) > tmp.find('.') + 3:
                                            tmp = tmp[:tmp.find('.')+3]
                                        empty_debt[i] = float(tmp)
                                minlength = len(item[0])
    if empty_debt[0] == float('NaN'):
        print(foldername)
        return ''
    return 'INSERT INTO debt VALUES (%s)'%(str(empty_debt).strip('[').strip(']'))


def create_profit(foldername):
    empty_profit = [float('NaN')] * (len(profitkey))
    empty_profit[0] = foldername.split('__')[0]
    empty_profit[1] = int(foldername.split('__')[1].strip('年'))
    for filename in os.listdir(path+foldername):
        if re.match("基本信息表.json", filename):
            with open(os.path.join(path+foldername, filename), 'r',encoding='utf-8') as fd:
                json_data = json.load(fd)
                empty_profit[0] = json_data['文档公司名']
                empty_profit[1] = int(json_data['年份'].strip('年'))
                empty_profit[2] = json_data['注册地址']
        if re.match(".*合并利润表.*\.csv", filename):
            with open(os.path.join(path+foldername, filename), 'r',encoding='utf-8') as fd:
                sheet = csv.reader(fd)
                header = next(sheet)
                table = []
                index1 = -1
                index2 = -1
                for index,it in enumerate(header):
                    if re.match('项目', it.replace(' ','')):
                        index1 = index
                    if re.match('%d年度'%(empty_profit[1]), it.replace(' ','')):
                        index2 = index
                if index1 == -1 or index2 == -1:
                    continue
                for row in sheet:
                    table.append([row[index1], row[index2]])
                for i in range(3, len(profitkey)):
                    minlength = 99
                    for item in table:
                        if profitkey[i] in item[0] or (keymapping.get(profitkey[i], "None") in item[0]):
                            if len(item[0]) < minlength:
                                if re.match("-+[^0-9]", item[1]+" ") or "－" in item[1] or '不适用' in item[1] or '/' in item[1]:
                                    empty_profit[i] = 0
                                else:
                                    tmp = item[1].replace(' ','').replace(',','').strip('(').strip(')').strip('（').strip('）')
                                    if len(tmp) < 1:
                                        empty_profit[i] = 0
                                    else:
                                        if tmp.find('.') >= 0 and len(tmp) > tmp.find('.') + 3:
                                            tmp = tmp[:tmp.find('.')+3]
                                        empty_profit[i] = float(tmp)
                                minlength = len(item[0])
    if empty_profit[0] == float('NaN'):
        return ''
    return 'INSERT INTO profit VALUES (%s)'%(str(empty_profit).strip('[').strip(']'))


def create_cash(foldername):
    empty_cash = [float('NaN')] * len(cashkey)
    empty_cash[0] = foldername.split('__')[0]
    empty_cash[1] = int(foldername.split('__')[1].strip('年'))
    for filename in os.listdir(path+foldername):
        if re.match("基本信息表.json", filename):
            with open(os.path.join(path+foldername, filename), 'r',encoding='utf-8') as fd:
                json_data = json.load(fd)
                empty_cash[0] = json_data['文档公司名']
                empty_cash[1] = int(json_data['年份'].strip('年'))
                empty_cash[2] = json_data['注册地址']
        if re.match(".*合并现金流量表.*\.csv", filename):
            with open(os.path.join(path+foldername, filename), 'r',encoding='utf-8') as fd:
                sheet = csv.reader(fd)
                header = next(sheet)
                table = []
                index1 = -1
                index2 = -1
                for index,it in enumerate(header):
                    if re.match('项目', it.replace(' ','')):
                        index1 = index
                    if re.match('%d年度'%(empty_cash[1]), it.replace(' ','')):
                        index2 = index
                if index1 == -1 or index2 == -1:
                    continue
                for row in sheet:
                    table.append([row[index1], row[index2]])
                for i in range(3, len(cashkey)):
                    minlength = 99
                    for item in table:
                        if cashkey[i] in item[0] or (keymapping.get(profitkey[i], "None") in item[0]):
                            if len(item[0]) < minlength:
                                if re.match("-+[^0-9]", item[1]+" ") or "－" in item[1] or '不适用' in item[1] or '/' in item[1]:
                                    empty_cash[i] = 0
                                else:
                                    tmp = item[1].replace(' ','').replace(',','').strip('(').strip(')').strip('（').strip('）')
                                    if len(tmp) < 1:
                                        empty_cash[i] = 0
                                    else:
                                        if tmp.find('.') >= 0 and len(tmp) > tmp.find('.') + 3:
                                            tmp = tmp[:tmp.find('.')+3]
                                        empty_cash[i] = float(tmp)
                                minlength = len(item[0])
    if empty_cash[0] == float('NaN'):
        return ''
    return 'INSERT INTO cash VALUES (%s)'%(str(empty_cash).strip('[').strip(']'))


def create_db():

    print("*" * 50)
    print("Staring Build DataBase")
    if os.path.exists('data/company.db'):
        os.remove('data/company.db')
    conn = sqlite3.connect('data/company.db')

    # 创建游标对象
    cursor = conn.cursor()

    # 创建表
    key_list = [f"{key} DECIMAL(20, 2) " for key in debtkey[3:]]
    create_command = ",\n".join(key_list)
    create_command = f'''CREATE TABLE IF NOT EXISTS debt
                    (公司名称 VARCHAR(10),
                    年份 INT,
                    注册地址 TEXT,
                    {create_command},
                    PRIMARY KEY (公司名称, 年份))'''
    cursor.execute(create_command)
    
    key_list = [f"{key} DECIMAL(20, 2) " for key in profitkey[3:]]
    create_command = ",\n".join(key_list) 
    create_command = f'''CREATE TABLE IF NOT EXISTS profit
                    (公司名称 VARCHAR(10),
                    年份 INT,
                    注册地址 TEXT,
                    {create_command},
                    PRIMARY KEY (公司名称, 年份))'''
    cursor.execute(create_command)

    key_list = [f"{key} DECIMAL(20, 2) " for key in cashkey[3:]]
    create_command = ",\n".join(key_list) 
    create_command = f'''CREATE TABLE IF NOT EXISTS cash
                    (公司名称 VARCHAR(10),
                    年份 INT,
                    注册地址 TEXT,
                    {create_command},
                    PRIMARY KEY (公司名称, 年份))'''

    cursor.execute(create_command)
    
    # for foldername in os.listdir(path):
    #     command = create_profit(foldername)

    with open('data/list-pdf-name.txt','r',encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            try:
                parts = line.split('__')
                foldername = parts[3] + '__' + parts[4]
                #print(parts[3] + '__' + parts[4])
                command = create_debt(foldername).replace('?', '')
                command = command.replace('nan', '?')

                if len(command) > 0:
                    params = [None] * command.count('?')
                    cursor.execute(command, params)
                
                command = create_profit(foldername).replace('?', '')
                command = command.replace('nan', '?')

                if len(command) > 0:
                    params = [None] * command.count('?')
                    cursor.execute(command, params)
                
                command = create_cash(foldername).replace('?', '')
                command = command.replace('nan', '?')

                if len(command) > 0:
                    params = [None] * command.count('?')
                    cursor.execute(command, params)
                
                conn.commit()
            except Exception as err:
                print(foldername, err)
    # test on db
    # cursor.execute("SELECT 公司名称, 年份, 货币资金 FROM debt ORDER BY 货币资金 DESC LIMIT 10")
    # rows = cursor.fetchall()
    # for row in rows:
    #     print(row)


if __name__ == "__main__":
    create_db()
