# coding: UTF-8
import os
import torch
import pandas as pd
import gc
import json
from tqdm import tqdm
from collections import defaultdict
import re
import config

all_text_path = config.BASE_PATH
all_text_file = os.listdir(all_text_path)
citis = json.load(open('output/cities.json'))


pdf_list = []
with open(config.PDF_LIST, 'r',encoding='utf-8') as f:
    values = f.readlines()
    for i in values:
        pdf_list.append(i.strip())
txt_list = [i.replace(".pdf",'.txt') for i in pdf_list]
shortname_year_list = []


# output_path1 = "output/excel_资产"
# output_path2 = "output/excel_员工"
# output_path3 = "output/excel_母公司"

# for i in [output_path1,output_path2,output_path3]:
#     if not os.path.exists(i):
#         os.makedirs(i)



pattern = r'第.+财务报告\.+(\d+)'
pattern2 = r'第.+\.+(\d+)'




count = 0
no_prompt_question = []

num = 0

def is_numeric(s):
    try:
        float(s)  # 尝试将字符串转换为浮点数
        return True
    except ValueError:
        return False
#初始化
final_dict_zichan = {}
final_dict_mugongsi = {}
final_dict_base = {}

def sub_excel_data(file_name,name1,name2,name3):
    with open(file_name,'r',encoding='utf-8') as f:
        result_dict = defaultdict(list)
        address = ''
        all_content = f.readlines()
        for i, value in enumerate(all_content):
            row_dict = eval(value)
            if not row_dict:
                continue
            inside = row_dict['inside']
            page = row_dict['page']
            start_page = []
            if int(page) <= 10:
                start_page = re.findall(r'第.+节财务报告\.+(\d+)',inside)
                if start_page:
                    start_page = int(start_page[0])
                    break
            else:
                break

        if not start_page:
            start_page = 1



        mark = False
        count = 0
        for i,value in enumerate(all_content):
            row_dict = eval(value)
            if not row_dict:
                continue
            inside = row_dict['inside']
            type_text = row_dict['type']
            page = row_dict['page']
            if '注册地址' in inside and page<20:
                for city in citis:
                    if city in inside and not address:
                        address = city
            if page < start_page:
                continue


            if inside == '' or type_text=='页眉' or type_text=='页脚':
                continue



            if type_text=='text' and name1 in inside and (len(inside)<=25 or inside.find(name1)==0 or inside[-len(name1):]==name1):
                if '母公司' in name1:
                    mark = '母公司资产负债表'
                else:
                    mark = '合并资产负债表'
            elif type_text=='text' and name2 in inside and (len(inside)<=25 or inside.find(name2)==0 or inside[-len(name2):]==name2):
                if '母公司' in name2:
                    mark = '母公司利润表'
                else:
                    mark = '合并利润表'
            elif type_text=='text' and name3 in inside and (len(inside)<=25 or inside.find(name3)==0 or inside[-len(name3):]==name3):
                if '母公司' in name3:
                    mark = '母公司现金流量表'
                else:
                    mark = '合并现金流量表'
            else:
                pass

            if mark:
                count += 1
            else:
                count = 0

            #表填充完更新mark标记
            if mark:
                if count > 6 and len(result_dict[mark])==0:
                    mark = False
                elif type_text !='excel' and len(result_dict[mark])!=0:
                    mark = False
                elif type_text == 'excel':
                    result_dict[mark].append(inside)
            else:
                continue
    return result_dict,address


# #生成合并资产负债表,合并利润表,合并现金流量表
for file in tqdm(txt_list,desc='资产负债'):
    if file not in all_text_file:
        continue
    file_name = os.path.join(all_text_path,file)
    year_value = file_name.split("__")[-2][:4]
    result_dict,address = sub_excel_data(file_name,'合并资产负债表','合并利润表','合并现金流量表')
    merge_value = []
    for key,value in result_dict.items():
        merge_value.extend(value)
    if not merge_value:
        result_dict,address = sub_excel_data(file_name, '资产负债表', '利润表', '现金流量表')

    #转化为表格数据
    new_dict = defaultdict(list)
    for key,value in result_dict.items():
        delete_index = False
        for index1,i in enumerate(value):
            temp_list = []
            if index1 == 0:
                data = eval(i)
                lengh_first = len(data)
                for index2,row in enumerate(data):
                    if '附注' in row:
                        delete_index = index2
                        continue
                    year = re.findall('20(?:\d{2})', row)
                    if '年末余额' == row or "期末余额" == row:
                        row = int(year_value)
                    elif '上年年末' in row or "上期期末" in row:
                        row = int(year_value)-1

                    if year:
                        temp_list.append(int(year[0]))
                    else:
                        temp_list.append(row)
                if temp_list:
                    new_dict[key].append(temp_list)
            else:
                match = re.search("\d", i)
                if not match:
                    continue


                data = eval(i)
                for index2, row in enumerate(data):
                    # if delete_index and index2==delete_index:
                    #     row_temp = row.replace(",", "")
                    #     if not is_numeric(row_temp):
                    #         continue
                    if delete_index and index2==delete_index and len(data) == lengh_first:
                        continue
                    if index2 == 0:
                        # 正则修正特殊字符
                        match = re.search('、|：|\.|\．', row)
                        if match and match.span()[0] <= 2:
                            row = row[match.span()[0] + 1:]
                        row = re.sub("（.+）", '', row)
                        row = re.sub("\(.+\)", '', row)
                        row = row.strip()

                    temp_list.append(row)
            if temp_list and len(temp_list)>1 and index1 != 0:
                for j in temp_list[1:]:
                    j_ = j.replace(",", "")
                    if is_numeric(j_):
                        new_dict[key].append(temp_list)
                        break

    if not new_dict:
        print(file)
        num += 1
    lista = file.split("__")
    output_name = "__".join(lista[-3:-1])
    new_dict['year'] = year_value
    new_dict['name'] = file
    new_dict['address'] = address
    final_dict_zichan[output_name] = new_dict
json.dump(final_dict_zichan, open(f'output/zichan.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(num)



# #生成母公司资产负债表,母公司利润表,母公司现金流量表
#生成计算需要用到的数据
for file in tqdm(txt_list,desc='母公司资产负债'):
    if file not in all_text_file:
        continue
    file_name = os.path.join(all_text_path,file)
    year_value = file_name.split("__")[-2][:4]
    result_dict,address = sub_excel_data(file_name,'母公司资产负债表','母公司利润表','母公司现金流量表')

    # 转化为表格数据
    new_dict = defaultdict(list)
    for key, value in result_dict.items():
        delete_index = False
        for index1, i in enumerate(value):
            temp_list = []
            if index1 == 0:
                data = eval(i)
                lengh_first = len(data)
                for index2, row in enumerate(data):
                    if '附注' in row:
                        delete_index = index2
                        continue
                    year = re.findall('20(?:\d{2})', row)
                    if '年末余额' == row or "期末余额" == row:
                        row = int(year_value)
                    elif '上年年末' in row or "上期期末" in row:
                        row = int(year_value) - 1

                    if year:
                        temp_list.append(int(year[0]))
                    else:
                        temp_list.append(row)
                if temp_list:
                    new_dict[key].append(temp_list)
            else:
                match = re.search("\d", i)
                if not match:
                    continue

                data = eval(i)
                for index2, row in enumerate(data):
                    # if delete_index and index2==delete_index:
                    #     row_temp = row.replace(",", "")
                    #     if not is_numeric(row_temp):
                    #         continue
                    if delete_index and index2 == delete_index and len(data) == lengh_first:
                        continue
                    if index2 == 0:
                        # 正则修正特殊字符
                        match = re.search('、|：|\.|\．', row)
                        if match and match.span()[0] <= 2:
                            row = row[match.span()[0] + 1:]
                        row = re.sub("（.+）", '', row)
                        row = re.sub("\(.+\)", '', row)
                        row = row.strip()

                    temp_list.append(row)
            if temp_list and len(temp_list) > 1 and index1 != 0:
                for j in temp_list[1:]:
                    j_ = j.replace(",", "")
                    if is_numeric(j_):
                        new_dict[key].append(temp_list)
                        break

    if not new_dict:
        print(file)
        num += 1
    lista = file.split("__")
    output_name = "__".join(lista[-3:-1])
    new_dict['year'] = year_value
    new_dict['name'] = file
    new_dict['address'] = address
    final_dict_mugongsi[output_name] = new_dict
json.dump(final_dict_mugongsi, open(f'output/mugongsi.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(num)



#生成基本信息数据、包括公司基本信息及员工情况
for file in tqdm(txt_list,desc='公司基本信息'):
    file_name = os.path.join(all_text_path,file)
    with open(file_name,'r',encoding='utf-8') as f:
        result_dict = defaultdict(list)
        all_content = f.readlines()
        mark = False
        for i,value in enumerate(all_content):
            row_dict = eval(value)
            if not row_dict:
                continue
            inside = row_dict['inside']
            type_text = row_dict['type']
            page = row_dict['page']

            n = 1
            while True:
                if i+n < len(all_content):
                    post_row_dict = eval(all_content[i+n])
                    n += 1
                    if not post_row_dict:
                        continue
                    post_type_text = post_row_dict['type']
                    post_inside = post_row_dict['inside']
                    if post_type_text != '页眉' and post_type_text != '页脚':
                        break
                else:
                    break

            if inside == '' or type_text=='页眉' or type_text=='页脚':
                continue

            if i < len(all_content)-1:
                post_row_dict = eval(all_content[i+1])
                if not post_row_dict:
                    continue
                post_type_text = post_row_dict['type']


            if type_text=='text' and ('公司信息' in inside or '公司基本情况' in inside):
                mark = '公司信息'
            elif type_text=='text' and '公司股票简况' in inside and page<=15:
                mark = '公司股票简况'
            elif type_text=='text' and '基本情况简介' in inside:
                mark = '基本情况简介'
            elif type_text=='text' and '员工情况' in inside:
                mark = '员工情况'
            elif type_text=='text' and '员工数量' in inside:
                mark = '员工数量'

            elif type_text=='excel' and '研发人员' not in result_dict:
                a = eval(inside)
                if len(a)>1 and '研发人员' in a[0]:
                    for j in range(1,20):
                        type_temp_forward = eval(all_content[i-j])['type']
                        if type_temp_forward != 'excel':
                            start_index = i-j
                            break
                    for j in range(1,20):
                        type_temp_post = eval(all_content[i+j])['type']
                        if type_temp_post != 'excel':
                            end_index = i+j
                            break
                    for z in all_content[start_index+1:end_index]:
                        temp_inside = eval(z)['inside']
                        result_dict['研发人员'].append(temp_inside)
            else:
                pass

            #表填充完更新mark标记
            if mark:
                if post_type_text != 'excel' and type_text == 'text' and post_inside[:2] != '单位':
                    mark = False
                elif type_text !='excel' and len(result_dict[mark])!=0:
                    mark = False
                elif type_text == 'excel':
                    result_dict[mark].append(inside)
            else:
                continue



        #转化为表格数据
        new_dict = defaultdict(list)
        new_dict['硕士'] = 0
        new_dict['博士'] = 0
        new_dict['研发'] = 0
        new_dict['职工总数'] = 1
        new_dict['法定代表人'] = ''

        for key,value in result_dict.items():
            if key == '公司股票简况':
                if len(value)>=2:
                    data1 = eval(value[-2])
                    data2 = eval(value[-1])
                    if len(data1) == len(data2):
                        for a,b in zip(data1,data2):
                            if a == '股票简称':
                                a = '证券简称'
                            if a == '股票代码':
                                a = '证券代码'
                            new_dict[key].append((a,b))
                continue

            for index1,i in enumerate(value):
                temp_list = []
                _temp_list = []
                data = eval(i)
                for index2,row in enumerate(data):
                    if row == '':
                        continue
                    _temp_list.append(row)
                if 2<=len(_temp_list)<=3:
                    temp_list.append((_temp_list[0],_temp_list[1]))
                elif len(_temp_list)== 4:
                    temp_list.append((_temp_list[0],_temp_list[1]))
                    temp_list.append((_temp_list[2], _temp_list[3]))
                else:
                    continue

                for i in temp_list:
                    title = i[0]
                    content = i[1]
                    if re.search("20\d{2}", title) and re.search("20\d{2}", content):
                        continue
                    if '法定代表人' in title:
                        new_dict['法定代表人'] = content

                    if key == '员工情况' or key == '员工数量':
                        content = content.replace(",", '')
                        if re.search("\d", content):
                            if title == '合计':
                                title = '职工总数'
                                if bool(re.match(r'^\d+$', content)):
                                    new_dict['职工总数'] = int(content)

                            if '母公司' in title or '子公司' in title:
                                break

                            if '硕士' in title:
                                title = '硕士人员'
                                if bool(re.match(r'^\d+$', content)):
                                    new_dict['硕士'] = int(content)
                            elif '博士' in title:
                                title = '博士人员'
                                if bool(re.match(r'^\d+$', content)):
                                    new_dict['博士'] = int(content)
                            elif '研究生' in title:
                                title = '硕士人员'
                                if bool(re.match(r'^\d+$', content)):
                                    new_dict['硕士'] = int(content)



                    if key == '员工情况' or key == '员工数量' or key =='研发人员':
                        content = content.replace(",", '')
                        if re.search("\d", content):
                            if '研发人员' in title and ('占比' not in title and '比例' not in title):
                                title = '研发人员'
                                if bool(re.match(r'^\d+$', content)):
                                    new_dict['研发'] = int(content)
                            title = title.replace('人员',"")
                            new_dict[key].append((title,content))
                        break

                    if '股票简称'== title:
                        title = '证券简称'
                    if '股票代码'== title:
                        title = '证券代码'
                    # _title = re.sub("（.+）", '', _title)
                    # _title = _title.strip()
                    new_dict[key].append((title,content))

        for key,value in new_dict.items():
            if isinstance(value,list):
                new_dict[key] = sorted(set(value), key=value.index)

        if not new_dict:
            print(file)
            num += 1
        lista = file.split("__")
        output_name = "__".join(lista[-3:-1])
        final_dict_base[output_name] = new_dict
json.dump(final_dict_base, open(f'output/base.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

