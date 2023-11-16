# encoding=UTF-8
import ast
import re
import os
import json
import multiprocessing

all_txt_path = 'data/alltxt/'

def clearexcel(list, word):
    flag = 0
    for it in list:
        if it == '':
            continue
        elif word in it:
            flag = 1
        elif flag == 1 and it != '）':
            return it
    return ''

def basic_info(filename):
#for filename in txt_list:
    #print(foldername)
    company = {'文档公司名':'','年份':'','企业名称':'', '外文名称':'-1', '证券简称':'', '证券代码':'', '法定代表人':'',
               '电子信箱':'', '办公地址':'', '注册地址': '', '公司网址':'', '营业收入':'', '净利润':'', '现金流量净额':'',
               '每股收益':'', '净资产':'','职工总数':'-1','技术人员数':'-1', '研发人员数':'-1', '销售人员数':'-1', 
               '研发人员占比':'-1', '硕士人数':'-1', '博士及以上':'-1', '实际控制人':'', '控股股东是否发生变更':'相同',
               '面临退市': '未提及', '处罚及整改' : '未提及', '破产重整相关': '未提及','控股股东、实际控制人诚信状况' : '未提及', 
                }
    company['文档公司名'] = filename.split('__')[-3]
    company['年份'] = filename.split('__')[-2]
    try:
        tmp1 = -1
        tmp2 = -1
        tmp3 = -1
        tmp4 = -1
        tmp5 = -1
        tmp_index = 0
        flag_cn_name = 0
        flag_en_name = 0
        flag_share_name = 0
        flag_share_code = 0
        flag_corporate = 0
        flag_mail = 0
        flag_work_addr = 0
        flag_regist_addr = 0
        flag_website = 0
        flag_income = 0
        flag_profit = 0
        flag_clash = 0
        flag_share = 0
        flag_assets = 0
        flag_control = 0
        flag_control_double = 0
        #### added
        flag_quit = 0
        tmp = 0
        with open(os.path.join(all_txt_path, filename), 'r') as f:
        #with open('./基本信息.txt','r', encoding='utf-8') as f:
            lines = f.readlines()
            for index, line in enumerate(lines):
                line_dict = ast.literal_eval(line)
                if len(line_dict) < 1:
                    break
                # if line_dict['page'] == 76:
                #     print(tmp1, tmp2, tmp3, tmp4, tmp5)
                #     print(line)
                # 跳过页眉与页脚
                if line_dict['type'] == '页眉' or line_dict['type'] == '页脚':
                    continue
                if '公司信息' in line_dict['inside'] or '基本情况' in line_dict['inside']:
                    tmp1 = 0
                if '联系人和联系方式' in line_dict['inside']:
                    tmp1 = -1
                if '股票简况' in line_dict['inside']:
                    tmp1 = 1
                if '主要会计数据和财务' in line_dict['inside']:
                    tmp2 = 0
                if '境内外' in line_dict['inside']:
                    tmp2 = -1
                if '控股股东情况' in line_dict['inside']:
                    tmp4 = 0
                if re.match(r'.*([^和及])实际控制人情况$',line_dict['inside']) or '公司实际控制人及其一致行动人' in line_dict['inside']:
                    if flag_control == 0:
                        tmp3 = 0
                        tmp4 = -1
                elif tmp3 >= 0 and line_dict['type'] == 'text':
                    tmp3 = tmp3 + 1
                elif tmp3 >= 10 or '董事' in line_dict['inside']:
                    tmp3 = -1
                if '重要事项' in line_dict['inside']:
                    tmp5 = 0
                if '股份变动及股东情况' in line_dict['inside']:
                    tmp5 = -1
                if line_dict['type']=='excel':
                    if tmp1 == 0:
                        if '中文' in line_dict['inside'] and flag_cn_name == 0:
                            company['企业名称'] = clearexcel(ast.literal_eval(line_dict['inside']), '中文')
                            if company['企业名称'] != '':
                                flag_cn_name = 1
                        if '外文' in line_dict['inside'] and flag_en_name == 0:
                            company['外文名称'] = clearexcel(ast.literal_eval(line_dict['inside']), '外文')
                            if company['外文名称'] != '':
                                flag_en_name = 1
                        if '股票简称' in line_dict['inside'] and flag_share_name == 0:
                            company['证券简称'] = clearexcel(ast.literal_eval(line_dict['inside']), '股票简称')
                            flag_share_name = 1
                        if '股票代码' in line_dict['inside'] and flag_share_code == 0:
                            company['证券代码'] = clearexcel(ast.literal_eval(line_dict['inside']), '股票代码')
                            flag_share_code = 1
                        if '法定代表人' in line_dict['inside'] and flag_corporate == 0:
                            company['法定代表人'] = clearexcel(ast.literal_eval(line_dict['inside']), '法定代表人')
                            flag_corporate = 1
                        if '电子信箱' in line_dict['inside'] and flag_mail == 0:
                            company['电子信箱'] = clearexcel(ast.literal_eval(line_dict['inside']), '电子信箱')
                            flag_mail = 1
                        if '办公地址' in line_dict['inside'] and flag_work_addr == 0:
                            company['办公地址'] = clearexcel(ast.literal_eval(line_dict['inside']), '办公地址')
                            flag_work_addr = 1
                        if '注册地址' in line_dict['inside'] and flag_regist_addr == 0:
                            company['注册地址'] = clearexcel(ast.literal_eval(line_dict['inside']), '注册地址')
                            flag_regist_addr = 1
                        if '网址' in line_dict['inside'] and flag_website == 0:
                            company['公司网址'] = clearexcel(ast.literal_eval(line_dict['inside']), '网址')
                            flag_website = 1
                    if tmp1 == 1:
                        if '股票简称' in line_dict['inside'] and '股票代码' in line_dict['inside'] and flag_share_name == 0 and flag_share_code == 0:
                            line_index = re.sub(r'<Page:(\d+)>',r'\1', lines[index + 1])
                            line_index_dict = ast.literal_eval(line_index)
                            if line_index_dict['type'] != 'excel':
                                tmp = -1
                                continue
                            tmp_list1 = ast.literal_eval(line_dict['inside'])
                            tmp_list2 = ast.literal_eval(line_index_dict['inside'])
                            for it_index, it1 in enumerate(tmp_list1):
                                if '股票简称' in it1 and flag_share_name == 0:
                                    company['证券简称'] = tmp_list2[it_index]
                                    flag_share_name = 1
                                if '股票代码' in it1 and flag_share_code == 0:
                                    company['证券代码'] = tmp_list2[it_index]
                                    flag_share_code = 1
                            tmp1 = -1
                    if tmp2 == 0:
                        if '营业收入' in line_dict['inside'] and flag_income == 0:
                            company['营业收入'] = clearexcel(ast.literal_eval(line_dict['inside']), '营业收入')
                            flag_income = 1
                        if '归属于上市公司股东的净' in line_dict['inside'] and (flag_profit == 0 or flag_assets == 0):
                            i = 1
                            while index + i < len(lines):
                                line_index = re.sub(r'<Page:(\d+)>',r'\1', lines[index + i])
                                line_index_dict = ast.literal_eval(line_index)
                                if line_index_dict['type'] == 'excel':
                                    break
                                i = i + 1
                            tmp_list1 = ast.literal_eval(line_dict['inside'])
                            tmp_list2 = ast.literal_eval(line_index_dict['inside'])
                            for str1 in tmp_list1:
                                if '归属于上市公司股东的净' in str1:
                                    break
                            for str2 in tmp_list2:
                                if str2 != '':
                                    break
                            str1 = str1 + str2
                            if '归属于上市公司股东的净利润' in str1 and flag_profit == 0:
                                company['净利润'] = clearexcel(ast.literal_eval(line_dict['inside']), '归属于上市公司股东的净')
                                flag_profit = 1
                            elif '归属于上市公司股东的净资产' in str1 and flag_assets == 0:
                                company['净资产'] = clearexcel(ast.literal_eval(line_dict['inside']), '归属于上市公司股东的净') ###股数？？？
                                flag_assets == 1
                        elif '经营活动产生的现金流' in line_dict['inside'] and flag_clash == 0:
                            i = 1
                            while index + i < len(lines):
                                line_index = re.sub(r'<Page:(\d+)>',r'\1', lines[index + i])
                                line_index_dict = ast.literal_eval(line_index)
                                if line_index_dict['type'] == 'excel':
                                    break
                                i = i + 1
                            tmp_list1 = ast.literal_eval(line_dict['inside'])
                            tmp_list2 = ast.literal_eval(line_index_dict['inside'])
                            for str1 in tmp_list1:
                                if '经营活动产生的现金流' in str1:
                                    break
                            for str2 in tmp_list2:
                                if str2 != '':
                                    break
                            str1 = str1 + str2
                            if '经营活动产生的现金流量净额' in str1:
                                company['现金流量净额'] = clearexcel(ast.literal_eval(line_dict['inside']), '经营活动产生的现金流')
                                flag_clash = 1
                        elif '基本每股收益' in line_dict['inside'] and flag_share == 0:
                            company['每股收益'] = clearexcel(ast.literal_eval(line_dict['inside']), '每股收益')
                            flag_share = 1
                    if tmp3 > 0:
                        if '姓名' in line_dict['inside'] or '名称' in line_dict['inside'] and flag_control == 0:
                            row = [it for it in ast.literal_eval(line_dict['inside']) if len(it)> 0]
                            if len(row) > 2 or '与实际控制人关系' in line_dict['inside'] or '与本企业关系' in line_dict['inside']: #纵表 
                                tmp_index = len([it for it in ast.literal_eval(line_dict['inside'])])
                            elif len(row) > 1:
                                company['实际控制人'] = row[1]
                                flag_control = 1
                        elif tmp_index > 0 and flag_control == 0:
                            row = [it for it in ast.literal_eval(line_dict['inside'])]
                            if len(row) == tmp_index:
                                row = [it for it in row if len(it) > 0]
                                if len(row) > 1:
                                    company['实际控制人'] = row[0]
                                    flag_control = 1
                        elif '一致行动' in line_dict['inside'] or '本人' in line_dict['inside']:
                            flag_control_double = 1
                            row = [it for it in ast.literal_eval(line_dict['inside'])]
                            if len(row) == tmp_index:
                                row = [it for it in row if len(it) > 0]
                                if len(row) > 1:
                                    company['实际控制人'] = company['实际控制人'] + '、' + row[0]
                                    flag_control = 1
                                    flag_control_double = 0
                        elif flag_control_double == 1:
                            row = [it for it in ast.literal_eval(line_dict['inside'])]
                            if len(row) == tmp_index:
                                row = [it for it in row if len(it) > 0]
                                if len(row) > 1:
                                    company['实际控制人'] = company['实际控制人'] + '、' + row[0]
                                    flag_control = 1
                                    flag_control_double = 0
                if line_dict['type'] == 'text':
                        if tmp1 == 0:
                            if '中文' in line_dict['inside'] and flag_cn_name == 0:
                                company['企业名称'] = line_dict['inside'].split('名称')[-1].split('：')[-1]
                                if company['企业名称'] != '':
                                    flag_cn_name = 1
                            if '外文' in line_dict['inside'] and flag_en_name == 0:
                                company['外文名称'] = line_dict['inside'].split('名称')[-1].split('：')[-1]
                                if company['外文名称'] != '':
                                    flag_en_name = 1
                            if '股票简称' in line_dict['inside'] and flag_share_name == 0:
                                company['证券简称'] = line_dict['inside'].split('简称')[-1].split('：')[-1]
                                flag_share_name = 1
                            if '股票代码' in line_dict['inside'] and flag_share_code == 0:
                                company['证券代码'] = line_dict['inside'].split('代码')[-1].split('：')[-1]
                                flag_share_code = 1
                            if '法定代表人' in line_dict['inside'] and flag_corporate == 0:
                                company['法定代表人'] = line_dict['inside'].split('人')[-1].split('：')[-1]
                                flag_corporate = 1
                            if ('电子信箱' in line_dict['inside'] or '电子邮箱' in line_dict['inside'])and flag_mail == 0:
                                company['电子信箱'] = line_dict['inside'].split('信箱')[-1].split('邮箱')[-1].split('：')[-1]
                                flag_mail = 1
                            if '办公地址' in line_dict['inside'] and flag_work_addr == 0:
                                company['办公地址'] = line_dict['inside'].split('地址')[-1].split('：')[-1]
                                flag_work_addr = 1
                            if '注册地址' in line_dict['inside'] and flag_regist_addr == 0:
                                company['注册地址'] = line_dict['inside'].split('地址')[-1].split('：')[-1]
                                flag_regist_addr = 1
                            if '网址' in line_dict['inside'] and flag_website == 0:
                                company['公司网址'] = line_dict['inside'].split('网址')[-1].split('：')[-1]
                                flag_website = 1
                        if tmp4 == 0:
                            if '控股股东' in line_dict['inside'] and '变更' in line_dict['inside']:
                                tmp4 = 1
                        elif tmp4 == 1:
                            if '√适用' in line_dict['inside']:
                                company['控股股东是否发生变更'] = '不同'
                                tmp4 = -1
                            elif '√不适用' in line_dict['inside']:
                                company['控股股东是否发生变更'] = '相同'
                                tmp4 = -1
                        if tmp5 == 0:
                            if ('暂停上市' in line_dict['inside'] or '终止上市' in line_dict['inside'] or '面临退市' in line_dict['inside']) and '、' in line_dict['inside'] :
                                tmp5 = 1
                            if '处罚及整改' in line_dict['inside'] and '、' in line_dict['inside'] :
                                tmp5 = 2
                            if '破产重整相关' in line_dict['inside'] and '、' in line_dict['inside'] :
                                tmp5 = 3
                            if '诚信状况' in line_dict['inside'] and '、' in line_dict['inside'] :
                                tmp5 = 4
                        if tmp5 == 1:
                            if '√适用' in line_dict['inside']:
                                company['面临退市'] = '适用'
                                tmp5 = 0
                            if '√不适用' in line_dict['inside']:
                                company['面临退市'] = '不适用'
                                tmp5 = 0
                        if tmp5 == 2:
                            if '√适用' in line_dict['inside']:
                                company['处罚及整改'] = '适用'
                                tmp5 = 0
                            if '√不适用' in line_dict['inside']:
                                company['处罚及整改'] = '不适用'
                                tmp5 = 0
                        if tmp5 == 3:
                            if '√适用' in line_dict['inside']:
                                company['破产重整相关'] = '适用'
                                tmp5 = 0
                            if '√不适用' in line_dict['inside']:
                                company['破产重整相关'] = '不适用'
                                tmp5 = 0
                        if tmp5 == 4:
                            if '√适用' in line_dict['inside']:
                                company['控股股东、实际控制人诚信状况'] = '适用'
                                tmp5 = 5
                            if '√不适用' in line_dict['inside']:
                                company['控股股东、实际控制人诚信状况'] = '不适用'
                                tmp5 = 0
                        elif tmp5 == 5:
                            company['控股股东、实际控制人诚信状况'] = line_dict['inside']
                            tmp5 = 0
                if '分季度主要财务' in line_dict['inside']:
                    tmp1 = -1
                    tmp2 = -1
                '''
                    company = {'企业名称':c_name, '外文名称':e_name, '证券简称':share, '证券代码':s_code, 
                            '法定代表人':corporation, '电子信箱':mail, '办公地址':w_addr, 
                            '注册地址': r_addr, '公司网址':website, '利润总额':income,
                            '净利润':profit_net, '现金流量净额':clash_flow, '每股收益':s_income}
                    company['每股净资产'] = assets_net 
                '''

                if '教育程度类别' in line_dict['inside']:
                    tmp = 1
                if '专业构成类别' in line_dict['inside']:
                    tmp = 2
                if line_dict['type']=='excel':
                    if tmp == 2: 
                        if '合计' in line_dict['inside']:
                            index_list = ast.literal_eval(line_dict['inside'])
                            for index in index_list:
                                if re.match("\d", index):
                                    company['职工总数'] = index
                            tmp = 0
                        elif '技术人员' in line_dict['inside']:
                            index_list = ast.literal_eval(line_dict['inside'])
                            for index in index_list:
                                if re.match("\d", index):
                                    company['技术人员数'] = index
                        elif '研发人员' in line_dict['inside']:
                            index_list = ast.literal_eval(line_dict['inside'])
                            for index in index_list:
                                if re.match("\d", index):
                                    company['研发人员数'] = index
                        elif '销售人员' in line_dict['inside']:
                            index_list = ast.literal_eval(line_dict['inside'])
                            for index in index_list:
                                if re.match("\d", index):
                                    company['销售人员数'] = index
                    if tmp == 1:
                        if '硕士' in line_dict['inside'] or '研究生' in line_dict['inside'] or '本科以上' in line_dict['inside']:
                            index_list = ast.literal_eval(line_dict['inside'])
                            for index in index_list:
                                if re.match("\d", index):
                                    company['硕士人数'] = index
                        elif '博士' in line_dict['inside']:
                            index_list = ast.literal_eval(line_dict['inside'])
                            for index in index_list:
                                if re.match("\d", index):
                                    company['博士及以上'] = index
                        elif '合计' in line_dict['inside']:
                            tmp = 0

                if company['法定代表人'] == '':
                    if '法定代表人：' in line_dict['inside']:
                        content = line_dict['inside'].split('：')
                        for index, it in enumerate(content):
                            if '法定代表人' in it:
                                company['法定代表人'] = content[index + 1].split('，')[0].strip('主管会计工作负责人')
                                break
                if company['研发人员数'] == '-1':
                    if '研发人员' in line_dict['inside'] and line_dict['type'] == 'excel':
                        company['研发人员数'] = clearexcel(ast.literal_eval(line_dict['inside']), '研发人员')
                if '研发人员' in line_dict['inside'] and '占比' in line_dict['inside'] and line_dict['type'] == 'excel':
                    company['研发人员占比'] = clearexcel(ast.literal_eval(line_dict['inside']), '占比')
                if '控股股东未发生变更' in line_dict['inside']:
                    company['控股股东是否发生变更'] = '相同'
    except IndexError as err:
        print(filename)
        print(err)
        return company
    return company
    #print(company)
    #print(company)
    

if __name__ == '__main__':
    with open('./data/basic_information.json','w') as f:
        pass

    path = all_txt_path
    count = 0
    amount = 0
    l = multiprocessing.Lock()
    pool = multiprocessing.Pool(processes=6)
    dir_list = []
    with open('data/list-pdf-name.txt', 'r', encoding='utf-8') as f:
        for line in f.readlines():
            dir_list.append(line.replace("\n", "").replace(".pdf", '.txt'))
    txt_list = [x for x in dir_list if re.match('20.*txt', x)]
    # 
    print("*" * 50)
    print("Starting extract basic information from pdf")
    for company in pool.map(basic_info, txt_list):
        amount = amount + 1
        for values in company.values():
            if values=='':
                count = count + 1
                break
        with open('./data/basic_information.json', 'a+') as file:
            json.dump(company, file, ensure_ascii=False)
            file.write('\r')
    print('%d/'%(count)+'%d'%(amount))
