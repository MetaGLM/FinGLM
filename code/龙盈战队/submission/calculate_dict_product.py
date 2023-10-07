# coding: UTF-8
import os
import torch
import pandas as pd
import gc
import json
# os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import numpy as np
from tqdm import tqdm
from collections import defaultdict
import re

temp_list = []
product_dict = {}
with open('output/公式.txt','r',encoding='utf-8') as f:
    a = f.readlines()
    for i in a:
        s = i.split("|")
        product_dict[s[0]] = {}
        keyword = s[2].strip().split(",")
        product_dict[s[0]]['公式'] = s[1]
        product_dict[s[0]]['关键词'] = keyword
        if '比值' in s[0] or '比例' in s[0] or '速动比率' in s[0] or '流动比率' in s[0]:
            product_dict[s[0]]['是否百分比'] = 0
        else:
            product_dict[s[0]]['是否百分比'] = 1
        temp_list.append(s[0])
json.dump(product_dict, open(f'output/calculate_type.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(111)


