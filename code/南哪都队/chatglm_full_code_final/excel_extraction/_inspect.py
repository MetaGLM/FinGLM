import json
import os

classification_result = open('/extend/fintech/finetune/table_qa/data/classification.json', 'r', encoding='utf-8')
count_dict = json.load(open('/extend/fintech/count_dict.json', 'r', encoding='utf-8'))

res = []
for line in classification_result.readlines():
    line = eval(line)
    key = line.get('关键词')
    if key:
        key = key[0]
        num = count_dict.get(key)
        res.append((key, num))
res = set(res)
with open('inspect.txt', 'w', encoding='utf-8') as f:
    for l in res:
        f.write(str(l))
        f.write('\n')

