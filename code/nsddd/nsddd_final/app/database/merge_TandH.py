import pandas as pd

text_df=pd.read_csv("/data/chengshuang/chatglm_llm_fintech_raw_dataset/alltable_v8_clean/2022-04-18__博敏电子股份有限公司__603936__博敏电子__2021年__年度报告/合并资产负债表_1.csv")
html_df=pd.read_csv("/data/chengshuang/SMP2023/table_extract/alltable_merge/2022-04-18__博敏电子股份有限公司__603936__博敏电子__2021年__年度报告/合并资产负债表.csv")


##填充
# text_s=Series(index=text_df['项目'].values,index=text_df['项目'].values)

##找到空的行
nan_html_df = html_df[html_df.isnull().any(axis=1)]
html_kw_col=nan_html_df.columns[0]
html_value_col=nan_html_df.columns[1]


for i in range(text_df.shape[0]):
    kw_col=text_df.columns[0]
    value_col=text_df.columns[1]
     
    kw=text_df.loc[i,kw_col]
    value=text_df.loc[i,value_col]
    if kw in nan_html_df[html_kw_col].values:
        ##在里面
        index=nan_html_df[nan_html_df[html_kw_col]==kw].index
        html_df.loc[index,html_value_col]

##


 
html_keys=html_df[html_kw_col].values
text_keys=text_df[text_df.columns[0]].values
add_keys = [item for item in text_keys if item not in html_keys]

for key in add_keys:
    line=text_df[text_df[text_df.columns[0]]==key]
    html_df.append(line,ignore_index=True)
    breakpoint()

print("ss")
