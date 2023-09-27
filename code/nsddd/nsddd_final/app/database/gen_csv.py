import pandas as pd
import os
from tqdm import tqdm
import warnings

import sqlite3

import sys
# sys.path.append('./..')
# print(os.listdir())
from configs.model_config import keyword_path, table_path, pdf_list_path, item_map_path, database_path, sql_path
# 忽略所有的警告
warnings.filterwarnings("ignore")

# keyword_path = '/data/chengshuang/SMP2023/NSDDD/app/configs/added_keywords.csv'
# table_path = '/data/chengshuang/SMP2023/table_extract/alltable_merge' 
# pdf_list_path = '/data/chengshuang/SMP2023/B-list-pdf-name.txt'
# item_map_path = '/data/chengshuang/SMP2023/NSDDD/app/configs/item_map.csv'
# database_path = '/data/chengshuang/SMP2023/NSDDD/app/database/out.csv'
# sql_path = '/data/chengshuang/SMP2023/NSDDD/app/database/fin_data.db'




#构建中间键列表
df_kw=pd.read_csv(keyword_path)
keyword_list=df_kw['parten']


all_files_and_dirs = os.listdir(table_path)

##构建查询pdf范围列表
pdf_ls=[]
with open(pdf_list_path) as f:
    for line in f.readlines():
        line=line.rstrip()
        pdf_ls.append(line)


#构建表格键到中间键的映射
item_map_file=pd.read_csv(item_map_path)
item_map={}
for i in range(item_map_file.shape[0]):
    key=item_map_file.loc[i]['key']
    values=item_map_file.loc[i]['values']
    if pd.isnull(values):
        continue
    values_list=values.split(",")
    for value in values_list:
        item_map[value]=key



line_list=[]
for dir in tqdm(all_files_and_dirs):
    ##判断是否是目录
    dir_path=os.path.join(table_path, dir)

    if not os.path.isdir(dir_path):
        continue
    if f"{dir}.pdf" not in pdf_ls:
        continue

    all_files = os.listdir(dir_path)

    name=dir.split('__')[1]
    year=dir.split('__')[4]
    year=year[:-1]##去掉年字
    
    #normal mode
    # s1 = pd.Series([name,year],index=['公司名称','年份'])
    # s2 = pd.Series(index=keyword_list.values)
    #debug mode 
    s1 = pd.Series([dir,dir_path,name,year],index=['pdf_name','table_dir','公司名称','年份'])
    s2 = pd.Series(index=keyword_list)
    
    global_s = pd.concat([s1, s2])
    # if '2020-01-21__江苏安靠智能输电工程科技股份有限公司__300617__安靠智电__2019年__年度报告'==dir:
    #     breakpoint()
    for file in all_files:
        ##判断是否是文件
        if not os.path.isfile(os.path.join(dir_path, file)):
            continue
        ##判断是否是csv文件
        if not file.endswith('.csv'):
            continue

        df_csv=pd.read_csv(os.path.join(dir_path, file))
        
        # if file=='员工情况表_1.csv':
        #     breakpoint()
        kw_col=df_csv.columns[0]
        value_col=df_csv.columns[1]

        ##过滤掉空的行
        df_filtered=df_csv.dropna(subset=df_csv.columns)
        
        ##将表格键映射回中间键
        index_ls=df_filtered[kw_col].values
        for i,kw in  enumerate(index_ls):
            if kw in item_map.keys():
                index_ls[i]=item_map[kw]

        local_s=pd.Series(df_filtered[value_col].values,index=index_ls)

        ##去掉重复的索引
        local_s = local_s.loc[~local_s.index.duplicated(keep='first')]

        global_s.update(local_s)
        
    line_list.append(global_s)


##形成csv中间表格
df_r = pd.concat(line_list,axis=1)
df_r=df_r.T
df_r.to_csv(database_path,index=False)


df_out=pd.read_csv(database_path)
##形成数据库
# 创建SQLite数据库连接
conn = sqlite3.connect(sql_path)
# 将DataFrame写入到新的SQLite表
df_out.to_sql('fin_report', conn, if_exists='replace', index=False)
# 关闭数据库连接
conn.close()

        








