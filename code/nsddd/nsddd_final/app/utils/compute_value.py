
import pandas as pd
import csv
import re
import os

from configs.model_config import table_path


suport_table_type1 = ['合并资产负债表', '合并利润表', '合并现金流量表']
suport_table_type2 = ['公司信息表', '员工情况表', '研发人员及研发费用表']
all_cnt = 0

class_2_success_cnt = 0
class_2_fail_no_table_cnt = 0
class_2_fail_no_item_cnt = 0
class_2_fail_nan_cnt = 0
class_2_fail_unsupport_table_cnt = 0

def get_item(stock_name, table_name, item_name, year):
    '''
    table: pandas dataframe
    table_name: string
    item_name: string
    year: int
    '''
    if year == '今年':
        path = f'{table_path}/{stock_name}/{table_name}.csv'
    else:
        stock_name_end = '__'.join(stock_name.split('__')[1:-2]) + '__' + str(int(stock_name.split('__')[-2][:len('2020')])-1) + '年__年度报告'
        # 找到 table_path 下的以 stock_name_end 结尾的文件夹
        find_last_year = False
        for file_name in os.listdir(table_path):
            if file_name.endswith(stock_name_end):
                stock_name = file_name
                find_last_year = True
                break
        if not find_last_year:
            # print("未找到去年的年报：", stock_name)
            with open('result/last_year_annual_report_not_found.csv', 'a', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([stock_name, table_name, item_name, year])
            return -4
        path = f'{table_path}/{stock_name}/{table_name}.csv'
    if not os.path.exists(path):
        # print("文件不存在：", path)
        return -2
    table = pd.read_csv(path)
    if table_name in suport_table_type1:
        # 查询项目字段为item_name的行，第一列的值
        # res = table.loc[table['项目'] == item_name].iloc[:, 1]
        res = table[table.iloc[:, 0] == item_name].iloc[:, 1]
        # 判断是否查找到元素，若找不到返回-1
        item_value = res.values[0] if len(res) > 0 else -1 
        return item_value
    elif table_name in suport_table_type2:
        # 查询项目字段为item_name的行，列为year的值
        # res = table.loc[table['项目'] == item_name, '情况']
        res = table[table.iloc[:, 0] == item_name].iloc[:, 1]
        # 判断是否查找到元素，若找不到返回-1
        item_value = res.values[0] if len(res) > 0 else -1 
        return item_value
    else:
        # print("表名不支持：", table_name)
        return -3

def get_class_2_res(item_map, item_str, formula, stock_name): 
    global class_2_success_cnt, class_2_fail_no_table_cnt, class_2_fail_no_item_cnt,class_2_fail_nan_cnt, class_2_fail_unsupport_table_cnt
    '''
    item_str: string
    table_name: string
    formula: string
    stock_name: string
    now_year: int
    '''
    item_list = eval(item_str)
    full_formula = formula
    element_val=[]
    element_name=[]
    for idx, item in enumerate(item_list):
        item_name, year,table_name = item
        year = str(year)
        if year == '0':
            element_name.append([item_name,'0'])
            if item_name in item_map['key'].values:
                add_names = item_map.loc[item_map['key'] == item_name, 'values'].values[0]
                add_names = add_names.split(',')
                item_name_list = [item_name] + add_names
                for _item_name in item_name_list:
                    item_value = get_item(stock_name, table_name, _item_name, '今年')
                    if item_value != -1:
                        break
            else:
                item_value = get_item(stock_name, table_name, item_name, '今年')
            # item_value = get_item(stock_name, table_name, item_name, '今年')
        else:
            element_name.append([item_name,'1'])
            if item_name in item_map['key'].values:
                add_names = item_map.loc[item_map['key'] == item_name, 'values'].values[0]
                add_names = add_names.split(',')
                item_name_list = [item_name] + add_names
                for _item_name in item_name_list:
                    item_value = get_item(stock_name, table_name, _item_name, '去年')
                    if item_value != -1:
                        break
            else:
                item_value = get_item(stock_name, table_name, item_name, '去年')
            # item_value = get_item(stock_name, table_name, item_name, '去年')
        if isinstance(item_value, int) and item_value in [-1,-2,-3, -4]:
            path = f'{table_path}/{stock_name}/{table_name}.csv'
            if item_value == -1:
                # print("未找到项目：", item_name)
                class_2_fail_no_item_cnt += 1
                with open('result/find_item_error.csv', 'a', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([item_name, year ,path, stock_name])
                return -1,[],'',[],[]
            elif item_value == -2:
                with open('result/table_not_found.csv', 'a', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([table_name, stock_name, path])
                # print("文件不存在：", path)
                class_2_fail_no_table_cnt += 1
                return -2,[],'',[],[]
            elif item_value == -3:
                # print("表名不支持：", table_name)
                with open('result/table_unsupport.csv', 'a', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([table_name, stock_name, path])
                class_2_fail_unsupport_table_cnt += 1
                return -3,[],'',[],[]
            elif item_value == -4:
                return -4,[],'',[],[]
            
            
            # print("未找到项目：", item_name)
            # class_2_fail_no_item_cnt += 1
            # return -1,[],'',[],[]
                        
        if isinstance(item_value, str):
            item_value = item_value.replace(',', '')
        # print(item_value)
        # 判断是否是nan
        if pd.isna(item_value):
            print("项目值为nan：", item_name)
            path = f'{table_path}/{stock_name}/{table_name}.csv'
            class_2_fail_nan_cnt += 1
            with open('result/item_nan_error.csv', 'a', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([item_name, year ,path, stock_name])
            return -1,[],'',[],[]
        element_val.append(str(item_value).replace(',', '')) ## 添加了一个去,的操作 
        formula = formula.replace('{v'+str(idx)+'}', str(item_value))
        if year == '1':
            full_formula = full_formula.replace('{v'+str(idx)+'}','上年' + str(item_name))
        else:
            full_formula = full_formula.replace('{v'+str(idx)+'}', str(item_name))
    try:
        res = eval(formula)
        # 保留2位小数
        res = round(res, 4)
    except:
        res = formula
    class_2_success_cnt += 1
    # print(res, item_list, full_formula)
    return res, item_list, full_formula,element_val,element_name