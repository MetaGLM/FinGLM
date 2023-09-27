#!/bin/bash

# 这里可以放入代码运行命令
echo "program start..."
# cd database
# cd database
python3 query_sql.py

python3 -m database.gen_csv

python3 main.py
# python3 demo.py
echo "program end..."
