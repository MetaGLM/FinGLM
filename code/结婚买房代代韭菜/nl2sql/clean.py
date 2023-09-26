import json
import re


a = [json.loads(i) for i in open("type12_145.json", encoding="utf-8")]
b = []
for i in a:
    query = re.findall("【问题】(.+?)\n", i["prompt"])[0]
    b.append({"query": query, "sql": i["sql"], "prompt": i["prompt"]})

open("type12_145_v2.json", "w", encoding="utf-8").write("\n".join([json.dumps(i, ensure_ascii=False) for i in b]))