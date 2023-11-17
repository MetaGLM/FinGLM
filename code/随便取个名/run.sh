#! /bin/bash

#1. 将所有pdf文件转化为txt储存
# python dev/pdf2txt.py
# or 直接下载alltxt
# wget -P ./data https://sail-moe.oss-cn-hangzhou.aliyuncs.com/open_data/hackathon_chatglm_fintech/alltxt.zip & unzip alltxt.zip

echo "Good Luck!!"

#1. 解析每个alltxt中对应的txt文件，获取三大基本表 + 公司信息 + 员工信息
python preprocess_data/transfer_file.py
python preprocess_data/extract_report.py
python preprocess_data/txt_aggregate.py

#2. 建立数据库
python dev/create_table.py

#3. 对问题进行正则匹配，获取对应keyword
python dev/extract_question.py

#4.查询每个问题对应的数据表，添加到额外的问题字段`prompt`
python dev/search.py

#5. 使用chatglm进行推断
bash scripts/eval.sh

#6. [Optional] verbaliser, post-progress处理 ? 
# python dev/post_process.py