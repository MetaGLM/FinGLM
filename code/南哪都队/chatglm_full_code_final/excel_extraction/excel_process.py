import json
import os
from tqdm import tqdm
from collections import defaultdict
import numpy as np
import re

excels_folder = 'data/merge_excel'
output_folder = 'data/processed_excels'

key_list = ['合并资产负债表', '合并现金流量表', '合并利润表', '公司信息', '员工数量、专业构成及教育程度', '研发投入', '主要会计数据和财务指标', '股本']
process_horizontal_key_list = ['合并资产负债表', '合并现金流量表', '合并利润表']
process_vertical_key_list = ['股本']
elimination_headings = ['附注', '比例', '公司', '增减', '原因', '调整', '调整数']
title_list = ['所有者权益：', '所有者权益', '教育程度', '学历结构类别', '研发人员年龄构成', '专业构成', '研发人员学历结构', '研发人员年龄结构',
              '教育程度类别', '专业构成类别', '', '学历结构类别 学历结构人数', '备', '列）', '研发人员学历', '非流动负债：',
              '每股收益：', '-', '非流动资产：']
features_alias = {
    "研发费用": ["研发经费", "企业研发经费", '花费在研发上的费用'],
    '收回投资收到的现金': [
        '收到的投资回收现金', '收回投资所得现金', '收回投资所得的现金','收回投资所收到的现金', 
        '收回投资所获得的现金', '收回投资所得到的现金', '收回的投资所得到的现金','收回的投资所得现金', 
        '收回的投资收入', '收回的投资收到的现金', '收回的投资现金', '收到的投资收回的现金', '收回投资所得现金', '收回投资所得的现金'],
    '净利润': ['利润', '净利润总额'],
    '利息支出': ['支出的利息'],
    '归属于母公司所有者的净利润': ['归属母公司所有者净利润', '归属母公司净利润', '归属母公司所有者的净利润', '归属于母公司股东的净利润', '归属于母公司股东的净利润（净亏损以“-”号填列）'],
    '归属于母公司所有者权益合计': ['归属于母公司所有者权益（或股东权益）合计', '归属于母公司的所有者权益', '归属于母公司的所有者权益', '归属于母公司所有者权益'],
    '资产合计': ['总资产', '资产总额', '资产总计'],
    '负债合计': ['总负债'],
    '无形资产': ['无形资产价值'],
    '每股净资产': ['每股净资产价值', '每股的净资产'],
    '流动负债合计': ['流动负债', '负债总计'],
    '流动资产合计': ['流动资产'],
    '期末现金及现金等价物余额': ['现金及现金等价物余额','期末的现金及现金等价物余额', '现金及现金等价物'],
    '经营活动产生的现金流量': ['经营现金流量'],
    '应付职工薪酬': ['应付的职工薪酬', '需支付的职工薪酬', '职工薪酬'],
    '对联营企业和合营企业的投资收益': ['对其联营企业和合营企业的投资收益'],
    '税金及附加': ['营业税金及附加费用', '营业税金及附加'],
    "固定资产": ['固定资产总额'],
    '综合收益': ['综合收益总额', '综合收益总计'],
    '非流动负债合计': ['非流动负债'],
    '每股经营现金流量': ['每股的经营现金流量'],
    '每股收益': ['基本每股收益'],
    '股本': ['实收资本', '实收资本（或股本）'],
    '所有者权益合计': ['所有者权益（或股东权益）：', '所有者权益（或股东权益）合计', '股东权益合计', '所有者权益总计'],
    '负债和所有者权益总计': ['负债和所有者权益（或股东权益）总计'],
    '研发人员数量占比':['研发人员数量占公司总人数的比例（%）', '研发人员数量占比（%）'],
    '稀释每股收益':['稀释每股收益(元/股)'],
    '母公司在职员工的数量':['母公司在职员工的数量（人）', '报告期末母公司在职员工的数量（人）'],
    '主要子公司在职员工的数量':['主要子公司在职员工的数量（人）', '报告期末主要子公司在职员工的数量（人）'],
    '在职员工的数量合计': ['在职员工的数量合计（人）', '报告期末在职员工的数量合计（人）'],
    '公司网址': ['公司国际互联网网址'],
    '公司的外文名称': ['公司的外文名称（如有）', '公司的外文名称(如有)'],
    '公司的外文名称缩写': ['公司的外文名称缩写（如有）', '公司的外文名称缩写(如有)'],
    '研发人员数量': ['研发人员数量（人）', '研发人员', '公司研发人员的数量', '公司研发人员的数量（人）', '公司研发人员的数量(人)','公司研发人员数量（人）'
               '公司研发人员数量'],
    '少数股东损益': ['少数股东损益（净亏损以“-”号填列）'],
    '汇兑收益':['汇兑收益（损失以“－”号填列）', '汇兑收益（损失以“-”号填列）'],
    '办公地址的邮政编码':['公司办公地址的邮政编码'],
    '注册地址的邮政编码':['公司注册地址的邮政编码'],
    '研发投入合计':['研发投入金额（元）'],
    '研发投入占营业收入比例':['研发投入总额占营业收入比例（%）'],
    '本期资本化研发投入':['研发投入资本化的金额（元）'],
    '资本化研发投入占研发投入的比例':['研发投入资本化的比重（%）'],
    '注册地址':['公司注册地址'],
    '办公地址':['公司办公地址'],
    '母公司及主要子公司需承担费用的离退休职工人数': ['母公司及主要子公司需承担费用的离退休职工人数（人）'],
    '净敞口套期收益':['净敞口套期收益（损失以“－”号填列）', '净敞口套期收益（损失以“-”号填列）'],
    '资产处置收益':['资产处置收益（损失以“-”号填列）', '资产处置收益（损失以“－”号填列）'],
    '支付给职工以及为职工支付的现金': ['支付给职工及为职工支付的现金'],
    '提取保险责任合同准备金净额':['提取保险责任准备金净额'],
    '公司注册地址历史变更情况':['公司注册地址的历史变更情况'],
    '硕士':['硕士研究生'],
    '博士':['博士研究生', '博士及以上'],
    '本科':['大专学历', '本科学历', '大学本科', '大学本科学历'],
    '硕士及以上':['研究生及以上', '硕士及以上学历', '硕士以上', '硕士研究生及以上','研究生及以上学历', '研究生', '研究生以上'],
    '本科及以上':['本科及以上学历', '大学本科及以上', '本科及本科以上'],
    '投资收益':['投资收益（损失以“－”号填列）'],
    '净利润':['净利润（净亏损以“－”号填列）', '净利润（净亏损以“－”号填列'],
    '营业利润':['营业利润（亏损以“－”号填列）', '营业利润（亏损以“－”号填列'],
    '股票上市交易所':['股票上市证券交易所', '股票上市交易所及板块'],
    '公允价值变动收益':['公允价值变动收益（损失以“－”号填列）', '公允价值变动收益（损失以“－”号填列）', '公允价值变动收益（损失以', 
                    '公允价值变动收益（损失以“-”号填列）'],
    '归属于母公司所有者的综合收益总额':['归属于母公司所有者的综合收益'],
    '现金流量套期储备':['现金流量套期储备（现金流量套期损益的有效部分）', '现金流量套期储备(现金流量套期损益的有效部分)', '现金流量套期储备（现金流量套期损',
                      '现金流量套期储备（现金流量套期'],
    '子公司吸收少数股东投资收到的现金': ['子公司吸收少数股东投资', '子公司吸收少数股东投'],
    '其他权益工具投资公允价值变动':['其他权益工具投资公允价', '其他权益工具投资公允价值', '其他权益工具投资公允价值变', '其他权益工具投资公允','其他权益工具投资公允价值变'],
    '其他债权投资信用减值准备':['其他债权投资信用减值准', '其他债权投资信用减值', '其他债权投资信用'],
    '利润总额':['利润总额（亏损总额以“－”号填列）'],
    '每股收益':['基本每股收益（元/股）', '基本每股收益'],
    '利息收入':['其中：利息收入'],
    '利息支出':['其中：利息支出'],
    '所有者权益合计':['所有者权益总计'],
    '其他综合收益':['他综合收益'],
    '营业收入':['营业收入总额'],
    '管理费用':['一般行政管理费用']
}

def canonial_judge(table):
    try:
        if len(np.array(table).shape) != 1:
            return True
    except:
        pass
    return False

def count_headings(folder):
    count_dict = {k:defaultdict(int) for k in key_list}
    for file in tqdm(os.listdir(folder)):
        excel = json.load(open(os.path.join(folder, file), 'r', encoding='utf-8'))
        for key in excel:
            if excel[key]:
                if tuple(excel[key][0]) == ('项目', '2018年12月31日', '2019年12月31日'):
                    pass
                count_dict[key][tuple(excel[key][0])] += 1
    for key in count_dict:
        count_dict[key] = {heading: count_dict[key][heading] for heading in sorted(count_dict[key], key=lambda x: count_dict[key][x], reverse=True)}
    return count_dict

def eliminate_colomns(key_list, table):
    elimination_idx = set()
    for heading in key_list:
        for i, cell in enumerate(table[0]):
            if heading in cell:
                elimination_idx.add(i)
    if elimination_idx:
        remaining_idx = sorted(list(set(range(len(table[0]))) - elimination_idx))
        table = [[row[idx] for idx in remaining_idx] for row in table]
    return table

def remove_spacebar_in_heading(table):
    #去除表头字符内空格
    for idx in range(len(table[0])):
        table[0][idx] =  table[0][idx].replace(' ', '')
    return table
       
def horizontal_canonialize(table, key):
    table = remove_spacebar_in_heading(table)
    if '' in table[0] and key in ['合并资产负债表', '合并现金流量表', '合并利润表']:
    #去除表头空单元格
        for cell in table[0]:
            if '项目' in cell or '资产' in cell:
                while '' in table[0]:
                    table[0].remove('')
                break
        else:
            for cell in table[0]:
                if '年' in cell:
                    table[0].insert(0, '项目')
                    table = horizontal_canonialize(table, key)
                    break
    if not canonial_judge(table):
        reset = False
        while table and len(table[0]) == 1:
            del table[0]
            reset = True
        if reset:
            table = horizontal_canonialize(table, key)
            
        table_template = [get_template(cell, key) for cell in table[0]]
        table = add_blankcell(table, table_template)
        table = remove_blankcell(table, table_template)
        if not canonial_judge(table):
            col_len = len(table[0])
            elimination_idx = set()
            for idx, row in enumerate(table):
                if len(row) != col_len:
                    elimination_idx.add(idx)
            remaining_idx = sorted(list(set(range(len(table))) - elimination_idx))
            table = [table[idx] for idx in remaining_idx]
    return table

def judge_no_num(cell):
    no_digit = False if re.match('[0-9]', cell) else True
    ch = True if re.search('[\u4e00-\u9fa5]', cell) else False
    return no_digit or ch

def get_template(cell, key):
    if key in ['合并资产负债表', '合并现金流量表', '合并利润表']:
        if re.match('项目|资产', cell):
            return '[\u4e00-\u9fa5]'
        elif re.search('年', cell):
            return '[0-9]'
        else:
            return '!!!\.'
    else:
        return ''

def judge_template(template, cell):
    if template.startswith('!!!'):
        template = template.replace('!!!', '')
        return not re.search(template, cell)
    return re.search(template, cell)

def vertical_canonialize(table, key):
    if key == '股本':
        qichu = None
        qimo = None
        find_qichu = False
        find_qimo = False
        if len(table)<=1:
            return [['期初余额', qichu], ['期末余额', qimo]]
        for cell in table[0] + table[1]:
            if '期初' in cell:
                find_qichu = True
            if '期末' in cell:
                find_qimo = True
        data_line = []
        for idx, line in enumerate(table):
            if '股份总数' in line[0]:
                if not any([re.match('[1-9]', cell) for cell in line]):
                    data_line = table[idx-1]
                else:
                    data_line = line
                break
        if data_line:
            data_line = [cell.replace(',', '') for cell in data_line if re.match('[1-9]', cell)]
        if not data_line:
            # print(1)
            return [['期初余额', qichu], ['期末余额', qimo]]
        if find_qichu:
            qichu = data_line[0].split('.')[0] + '.00'
        if find_qimo:
            qimo = data_line[-1].split('.')[0] + '.00'
        res = [['期初余额', qichu], ['期末余额', qimo]]
        return res


def add_blankcell(table, table_template):
    col_len = len(table[0])
    for idx, row in enumerate(table):
        i = 0
        while i < len(table[idx]) and len(table[idx]) < col_len:
            if table[idx][i]:
                if not judge_template(table_template[i], table[idx][i]):
                    table[idx].insert(i, '')
            i += 1
        if len(table[idx]) < col_len:
            table[idx] += [''] * (col_len - len(row))
    return table

def remove_blankcell(table, table_template):
    col_len = len(table[0])
    for idx, row in enumerate(table):
        i = 0
        while len(table[idx]) > col_len and i < len(table_template):
            if judge_template(table_template[i], table[idx][i]) and \
                not (not table[idx][i] and judge_template(table_template[i], table[idx][i+1])):
                # 条件一判断当前格子符合模板，条件二针对附注，当前格子为空且下一格也符合模板
                i += 1
            else:
                del table[idx][i]
        while len(table[idx]) > col_len and i < len(table[idx]):
            if not table[idx][i]:
                del table[idx][i]
            else:
                i += 1
    return table

def parse_file_name(file_name):
    time, long_company_name, code, short_company_name, year, _ = file_name.split('__')
    year = year.replace('年', '')
    return long_company_name, code, short_company_name, year

def rename_heading(table, year):
    for cell in table[0]:
        if '调整' in cell:
            return table
    for alias in ['资产', '资金', '项目', '科目']:
        if alias in table[0][0]:
            table[0][0] = '项目'
            
    this_year = year + '年12月31日'
    last_year = str(int(year) - 1) + '年12月31日'
    find_qimo = False
    
    for idx, cell in enumerate(table[0]):
        if '2018' in cell and '2018年12月31日' not in table[0]:
            table[0][idx]  = '2018年12月31日'
        elif '2019' in cell and '2019年12月31日' not in table[0]:
            table[0][idx]  = '2019年12月31日'
        elif '2020' in cell and '2020年12月31日' not in table[0]:
            table[0][idx]  = '2020年12月31日'
        elif '2021' in cell and '2021年12月31日' not in table[0]:
            table[0][idx]  = '2021年12月31日'
        elif '期末' in cell or '本年' in cell or '本期' in cell:
            if not find_qimo:
                table[0][idx] = this_year
                find_qimo = True
            else:
                table[0][idx] = last_year
                break
        elif '上年' in cell or '期初' in cell or '年初' in cell or '上期' in cell:
            table[0][idx] = last_year
            break
    return table

def add_heading(excel):
    if excel[0][0] not in ['项目', '资产']:
        if len(excel[0]) == 3:
            excel.insert(0, ['项目', '本期', '上期'])
        if len(excel[0]) == 2:
            excel.insert(0, ['项目', '本期'])
        if len(excel[0]) == 4:
            excel.insert(0, ['项目', '附注', '本期', '上期'])
    return excel

def sep_two_colomn(table):
    if len(table[0]) % 2 == 0:
        sep = len(table[0]) // 2
        if table[0][0:sep] == table[0][sep:]:
            res = [table[0][0:sep]]
            for i in range(1, len(table)):
                res.append(table[i][0: sep])
                res.append(table[i][sep:])
            return res
    return table

def rename(table):
    pop_list = []
    for idx, line in enumerate(table):
        if not line or line[0] in title_list:
            pop_list.append(idx)
            continue
        for key in features_alias:
            atrr_list = [key] + features_alias[key]
            if line[0] in atrr_list:
                table[idx][0] = key
    removed = 0
    for idx in pop_list:
        table.pop(idx-removed)
        removed += 1   
    return table

def rm_prefix(excel):
    template = '(\([一二三四五六七八九1-9]\))|(（[一二三四五六七八九1-9]）)|([1-9].)|([一二三四五六七八九]、)|([加减]：)|(其中[:：])'
    bracket_template = '([（\(]((亏损)|(损失)|(净亏损)).*)|([\(（].*[\)）])'
    for idx, line in enumerate(excel):
        if line:
            try:
                span = re.match(template, line[0]).span()
                excel[idx][0] = excel[idx][0].replace(line[0][span[0]:span[1]], '')
                line[0] = excel[idx][0] 
            except AttributeError:
                pass
            try:
                span = re.search(bracket_template, line[0]).span()
                excel[idx][0] = excel[idx][0].replace(line[0][span[0]:span[1]], '')
            except AttributeError:
                pass
            excel[idx][0] = excel[idx][0].strip()
    return excel

def main(excels_folder, output_folder):
    for file in tqdm(os.listdir(excels_folder)):
        long_company_name, code, short_company_name, year = parse_file_name(file)
        #if '601016' not in file or '2019年' not in file:
        #    continue
        excel = json.load(open(os.path.join(excels_folder, file), 'r', encoding='utf-8'))
        for key in list(excel.keys()):
            if key in process_horizontal_key_list:
                excel[key] = horizontal_canonialize(excel[key], key)
                excel[key] = eliminate_colomns(elimination_headings, excel[key])
                excel[key] = sep_two_colomn(excel[key])
                excel[key] = [row for row in excel[key] if row]
                if excel[key]:
                    excel[key] = add_heading(excel[key])
                    excel[key] = eliminate_colomns(elimination_headings, excel[key])
                    
                    excel[key] = rename_heading(excel[key], year)
                    excel[key] = eliminate_colomns(['1月1日'], excel[key])
                    pass
                else:
                    del excel[key]
            elif key in process_vertical_key_list:
                excel[key] = vertical_canonialize(excel[key], key)
            if excel.get(key):
                excel[key] = rm_prefix(excel[key])
                excel[key] = rename(excel[key])
        with open(os.path.join(output_folder, file), 'w', encoding = 'utf-8') as f:
            json.dump(excel, f, indent = 4, ensure_ascii = False)

if __name__ == '__main__':
    #pre_count_dict = count_headings(excels_folder)
    main(excels_folder, output_folder)
    post_count_dict = count_headings(output_folder)
    pass