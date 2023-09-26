#!/bin/bash

# 这里可以放入代码运行命令

# nvidia-smi

export LC_ALL=C.UTF-8
export PATH=$PATH:/usr/local/go/bin 

# echo "pdf2excel"
# bash process_data.sh

# 启动ES
systemctl start elasticsearch

echo "process start..."
python3 process.py

# 停止ES
systemctl stop elasticsearch

echo "predict start..."
python3 predict.py