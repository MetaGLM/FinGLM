#!/bin/bash
# nvidia-smi
mkdir data
ln -s /tcdata/chatglm2-6b model/chatglm2-6b
# ls model/chatglm2-6b
# ln -s /tcdata/chatglm_llm_fintech_raw_dataset data/chatglm_llm_fintech_raw_dataset
ln -s /tcdata/alltxt data/alltxt
# ln -s /tcdata/allhtml data/html
ln -s /tcdata/C-list-question.json data/C-list-question.json 
ln -s /tcdata/C-list-pdf-name.txt data/C-list-pdf-name.txt
# ls model
# cat /tcdata/C-list-pdf-name.txt | head -n 1
# cat /tcdata/C-list-pdf-name.txt | wc -l
# ln -s /tcdata/processed_excels data/processed_excels 
# ln -s /tcdata/company_info data/company_info
# python process.py
python predict.py --refresh_classification