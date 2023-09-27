import pandas as pd
import numpy as np
from tqdm import tqdm
#构建中间键列表
keyword_file="/data/chengshuang/SMP2023/NSDDD/app/configs/added_keywords.csv"
df_kw=pd.read_csv(keyword_file)

dict_table={}
for i in range(df_kw.shape[0]):
    if df_kw.loc[i,'问题类别']==2:
        if df_kw.loc[i,'公式']=='{v0}':
            dict_table[df_kw.loc[i,'parten']]=eval(df_kw.loc[i,'需要查询指标'])[0][2]


df=pd.read_csv("out.csv")
col_kw=df.columns

# 使用isnull()方法检查每个元素是否为空
is_null = df.isnull()

# 使用where()函数获取为空元素的行号和列号
null_loc = np.where(is_null)


ctn_key=pd.Series([0]*len(col_kw),index=col_kw)
ls=[]

# 打印为空元素的行号和列号
for (row, col) in tqdm(zip(*null_loc),total=len(null_loc[0])):
    pdf_name=df.loc[row,'pdf_path']
    # breakpoint()
    pef_full_path=f"/data/chengshuang/chatglm_llm_fintech_raw_dataset/allpdf/{pdf_name}.pdf"
    table_name=dict_table[col_kw[col]]
    table_full_path=f"'/data/chengshuang/SMP2023/table_extract/alltable_merge/{pdf_name}/{table_name}.csv"
    ctn_key[col_kw[col]]=ctn_key[col_kw[col]]+1
    ls.append([pef_full_path,table_full_path,col_kw[col],ctn_key[col_kw[col]]])
df_new=pd.DataFrame(ls,columns=['pdf_file','table_path','keyword','ctn'])
df_new.to_csv('null_table.csv')
ctn_key.to_frame().to_csv('key_ctn.csv')
    