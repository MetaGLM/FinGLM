from normalize.build_dataset import trans_type1, trans_type2
from tqdm import tqdm
import json
import random
import re

# type1 = [json.loads(i) for i in open("normalize/type1_norm_data.json", encoding="utf-8")]
# print(len(type1))
# type1 = [trans_type1(line) for line in tqdm(type1, desc="type1") if "sql_res" in line]
# print(len(type1))
# type2 = [json.loads(i) for i in open("normalize/type2_norm_data.json", encoding="utf-8")]
# print(len(type2))
# type2 = [trans_type2(line) for line in tqdm(type2, desc="type1") if "sql_res" in line]
# print(len(type2))

# all_data = type1 + type2
# # random.shuffle(all_data)
# with open("normalize/norm_data_1400.json", "w", encoding="utf-8") as f:
#     for i in all_data:
#         f.write(json.dumps(i, ensure_ascii=False) + "\n")

with open("normalize/norm_data_v2_1400.json", "w", encoding="utf-8") as f:
    for line in tqdm(open("normalize/norm_data_1400.json", encoding="utf-8")):
        line = json.loads(line)
        if not line: continue
        # print(line, type(line))
        res = re.findall("【查询结果】(.+?)【问题】", line["prompt"])[0]

        res_json = json.loads(res.replace("'", '"'))
        new_res = {}
        for r in res_json:
            for k, v in r.items():
                if k not in new_res:
                    new_res[k] = []
                new_res[k].append(v)
        line["prompt"] = line["prompt"].replace(res, str(new_res))
        f.write(json.dumps(line, ensure_ascii=False) + "\n")