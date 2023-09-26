import glob
import os
from tqdm import tqdm
import pandas as pd
import configparser

config = configparser.ConfigParser()
config.read('./config.ini')

OUT_PATH = config['sql_data']['company_annual_reports_path']
valid_pdf_name = config['guanfang_data']['valid_pdf_name']

valid_pdf_list = []
with open(valid_pdf_name, 'r', encoding='utf-8') as f:
    for line in f:
        valid_pdf_list.append(line.strip())

# 设置文件夹路径
folder_path = config['guanfang_data']['pdf_path']


def intial_company_excel():
    # 使用glob模块获取文件夹中所有文件的路径
    file_paths = glob.glob(os.path.join(folder_path, "*"))

    result = []
    # 循环遍历所有文件并读取内容
    for i in tqdm(range(len(file_paths))):
        file_name = file_paths[i]

        if os.path.basename(file_name) not in valid_pdf_list:
            continue

        allname = file_name.split('\\')[-1]
        date = allname.split('__')[0]
        company_name = allname.split('__')[1]
        code = allname.split('__')[2]
        company_short_name = allname.split('__')[3]
        year = allname.split('__')[4]
        report_type = allname.split('__')[-1].replace(".pdf", "")
        result.append(
            [
                date, company_name, code, company_short_name, year, report_type, allname
            ]
        )

    res_df = pd.DataFrame(result, columns=[
        'report_date', 'company_full_name', 'stock_code', 'company_short_name', 'report_year', 'report_type', 'file_name'])
    res_df.to_excel(OUT_PATH, index=False)


if __name__ == '__main__':
    intial_company_excel()
