# 读取out.csv中的'负债合计'列，找出其中为空的行，并找出'企业名称'列对应行的值
# 保存到badcase.csv中
# import csv
# keyword='货币资金'
# with open ('./out.csv','r',encoding= 'utf-8') as f:
#     reader = csv.DictReader(f)
#     with open (f'./{keyword}-badcase.csv','w',encoding='utf-8') as f1:
#         writer = csv.DictWriter(f1,fieldnames=['公司名称',keyword,'年份','table_dir','pdf_path'])
#         writer.writeheader()
#         for row in reader:
#             if row[keyword] == '':
#                 writer.writerow({'公司名称':row['公司名称'],keyword:row[keyword],'年份':row['年份'],'table_dir':row['table_dir'],'pdf_path':f"/data/chengshuang/chatglm_llm_fintech_raw_dataset/allpdf/{row['pdf_name']}.pdf"})
                
                
# 读取out.csv中的'负债合计'列，找出其中为空的行，并找出'企业名称'列对应行的值
# 保存到badcase.csv中
import csv
import os
keyword_list=['负债合计','资产总计','货币资金','营业收入','营业总成本','营业成本','营业利润','利润总额','净利润','其他流动资产','其他非流动资产','其他非流动金融资产','营业总收入','营业外收入\
','流动资产合计']
# keyword_searched = []
# file_path = os.listdir('./')
# for file_csv in file_path:
#     if 'csv' in file_csv:
#         keyword_searched.append(file_csv.split('-')[0])
for keyword in keyword_list:
    # if keyword in keyword_searched:
    #     continue
    with open ('./out.csv','r',encoding= 'utf-8') as f:
        reader = csv.DictReader(f)
        with open (f'./{keyword}-badcase.csv','w',encoding='utf-8') as f1:
            writer = csv.DictWriter(f1,fieldnames=['公司名称',keyword,'年份','table_dir','pdf_path','html_path'])
            writer.writeheader()
            for row in reader:
                if row[keyword] == '':
                    writer.writerow({'公司名称':row['公司名称'],keyword:row[keyword],'年份':row['年份'],'table_dir':row['table_dir'],'pdf_path':f"/data/chengshuang/chatglm_llm_fintech_raw_dataset/allpdf/{row['pdf_name']}.pdf",'html_path':f"/data/chengshuang/SMP2023/table_extract/html_result_new/{row['pdf_name']}.html"})