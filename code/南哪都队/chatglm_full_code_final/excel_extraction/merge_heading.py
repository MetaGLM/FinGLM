import os
import json
from tqdm import tqdm
from collections import defaultdict
import re

excels_folder = 'data/processed_excels'
company_folder = 'data/company_info'
output_folder = 'data/final_excels'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

cities_dict = json.load(open('data/canonicalized_cities.json', 'r', encoding='utf-8'))
problem_location_res = json.load(open('data/problem_location_res.json', 'r', encoding='utf-8'))

title_list = ['所有者权益：', '所有者权益', '教育程度', '学历结构类别', '研发人员年龄构成', '专业构成', '研发人员学历结构', '研发人员年龄结构',
              '教育程度类别', '专业构成类别', '', '学历结构类别 学历结构人数', '项目', '备', '列）', '研发人员学历', '非流动负债：',
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
    '流动负债合计': ['流动负债', '流动负债总计'],
    '流动资产合计': ['流动资产', '流动资产合计'],
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
    '所有者权益（或股东权益）合计': ['所有者权益（或股东权益）：'],
    '负债和所有者权益总计': ['负债和所有者权益（或股东权益）总计'],
    '所有者权益':['所有者权益：'],
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

problem_json = []

def process_company_info(company):
    res = []
    for line in company:
        line = eval(line)
        line = [e for e in line if e]
        res.append(line)
    return res

def merge_head(excel):
    res = []
    for key in excel:
        if key in ['合并资产负债表', '合并现金流量表', '合并利润表']:
            temp = []
            for l in excel[key][1:]:
                if l[0] in ['研发人员学历结构', '研发人员年龄结构', '研发人员学历']:
                    break
                ele_1 = l[0]
                try:
                    l[1] = l[1].replace(' ', '')
                    ele_2 = float(l[1].replace(',', ''))
                except:
                    ele_2 = 0
                temp.append([ele_1, ele_2])
            res += temp
        #elif key in ['员工数量、专业构成及教育程度']:
        #    temp = []
        #    for line in excel[key]:
        #        temp.append([e for e in line if e != ''])
        #    res += temp
        elif key in ['公司信息']:
            temp = []
            for line in excel[key]:
                if len(line) == 2:
                    temp.append(line)
                elif len(line) == 4:
                    temp +=[line[0:2], line[2:4]]
            res += temp
    res.insert(0, ['key', 'value'])
    return res

def count_attr(folder_path):
    count_dict = defaultdict(int)
    for file in tqdm(os.listdir(folder_path)):
        excel = json.load(open(os.path.join(folder_path, file), 'r', encoding='utf-8'))
        for line in excel:
            if line:
                count_dict[line[0]] += 1
            #if line[0] == '每股收益':
            #    print(file, line)
    count_dict = {k:count_dict[k] for k in sorted(count_dict, key = lambda x:count_dict[x], reverse=True)}
    #count_dict = {k:count_dict[k] for k in sorted(count_dict.keys(), reverse=True)}
    with open('count_dict.json', 'w', encoding = 'utf-8') as f:
        json.dump(count_dict, f, indent = 4, ensure_ascii = False)
    return count_dict
    
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

def merge_attr(excel):
    pop_list = []
    for idx, line in enumerate(excel):
        if not line or line[0] in title_list:
            pop_list.append(idx)
            continue
        #if line[1] in ['', '-', '—']:
        #    line[1] = 0
        for key in features_alias:
            atrr_list = [key] + features_alias[key]
            if line[0] in atrr_list:
                excel[idx][0] = key        
    removed = 0
    for idx in pop_list:
        excel.pop(idx-removed)
        removed += 1
    return excel

def find_city(line):
    for province in cities_dict:
        for city in cities_dict[province]:
            if city+'市' in line:
                return (province, city)
    for province in cities_dict:
        for city in cities_dict[province]:
            if city in line:
                return (province, city)
    #for province in cities_dict:
    #    if province in line:
    #        return (province, None)
    else:
        return None

def add_info(excel, file):
    global problem_json
    add_table = []
    for line in excel:
        if line[0] == '注册地址':
            city_res = find_city(line[1])
            if city_res:
                add_table += [['注册省份', city_res[0]], ['注册城市', city_res[1]]]
            else:
                #print(line, file)
                #problem_json.append((file, line))
                loc_info =  problem_location_res[file]['注册地址']
                if loc_info:
                    add_table += [['注册省份', loc_info['province'][:-1]], ['注册城市', loc_info['city'][:-1]]]
        if line[0] == '办公地址':
            city_res = find_city(line[1])
            if city_res:
                add_table += [['办公省份', city_res[0]], ['办公城市', city_res[1]]]
            else:
                #print(line, file)
                #problem_json.append((file, line))
                loc_info =  problem_location_res[file]['办公地址']
                if loc_info:
                    add_table += [['办公省份', loc_info['province'][:-1]], ['办公城市', loc_info['city'][:-1]]]
    excel += add_table
    return excel

def parse_file_name(file_name):
    time, long_company_name, code, short_company_name, year, _ = file_name.split('__')
    year = year.replace('年', '')
    return long_company_name, code, short_company_name, year

def main(excels_folder, company_folder, output_folder):
    for file in tqdm(os.listdir(excels_folder)):
        excel = json.load(open(os.path.join(excels_folder, file), 'r', encoding='utf-8'))
        company = json.load(open(os.path.join(company_folder, file), 'r', encoding='utf-8'))
        company = process_company_info(company)
        excel['公司信息'] = company
        excel = merge_head(excel)
        excel = rm_prefix(excel)
        excel = merge_attr(excel)
        excel = add_info(excel, file)
        long_company_name, code, short_company_name, year = parse_file_name(file)
        excel += [['short_company_name', short_company_name], ['long_company_name', long_company_name]]
        with open(os.path.join(output_folder, file), 'w', encoding = 'utf-8') as f:
            json.dump(excel, f, indent = 4, ensure_ascii = False)

if __name__ == '__main__':
    #main(excels_folder, company_folder, output_folder)
    count_attr(output_folder)
    #with open('data/problem_location.json', 'w', encoding='utf-8') as f:
    #    json.dump(problem_json, f, indent = 4, ensure_ascii = False)