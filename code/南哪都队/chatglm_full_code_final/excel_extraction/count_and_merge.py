import os 
import json
from collections import defaultdict
from tqdm import tqdm

html_count = defaultdict(int)
txt_count = defaultdict(int)
total_count = defaultdict(int)

key_list = ['合并资产负债表', '合并现金流量表', '合并利润表', '公司信息', '员工数量、专业构成及教育程度', '研发投入', '主要会计数据和财务指标', '股本']
def merge(html, txt):
    for key in key_list:
        if not txt.get(key) and html.get(key):
            txt[key] = html[key]
    return txt

def main(html_folder, txt_folder, output_folder):
    for file in tqdm(os.listdir(txt_folder)):
        res = {}
        txt = json.load(open(os.path.join(txt_folder, file), 'r', encoding = 'utf-8'))
        try:
            html = json.load(open(os.path.join(html_folder, file), 'r', encoding = 'utf-8'))
            for key in key_list:
                html_bool = key in html
                txt_bool = key in txt
                html_count[key] += html_bool
                txt_count[key] += txt_bool
                total_count[key] += html_bool or txt_bool
                
            res = merge(html, txt)
        except:
            res = txt
        with open(os.path.join(output_folder, file), 'w', encoding = 'utf-8') as f:
            json.dump(res, f, indent = 4, ensure_ascii = False)
            
    print('html:', html_count)
    print('txt:', txt_count)
    print('total:', total_count)

if __name__ == '__main__':
    main(html_folder, txt_folder, output_folder)