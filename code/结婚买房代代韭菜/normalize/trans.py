import json


a = open("chatgpt_answer_type1.json", encoding="utf-8").readlines()
b = open("chatgpt_query_type1.json", encoding="utf-8").readlines()
with open("normalize_type1_data.json", "w", encoding="utf-8") as f:
    for i, j in zip(a,b):
        i = json.loads(i)
        j = json.loads(j)
        i.update(j)
        f.write(json.dumps(i, ensure_ascii=False) + "\n")
# with open("ans_type31.json", "w", encoding="utf-8") as f:
#     for i in open("../nl2sql/type31_75.json", encoding="utf-8"):
#         line = json.loads(i)
#         query = line["query"].strip()

#         if query in b:
#             f.write(json.dumps({"query": query, "answer": b[query]}, ensure_ascii=False) + "\n")

# with open("ans_type32.json", "w", encoding="utf-8") as f:
#     for i in open("../nl2sql/type32_80.json", encoding="utf-8"):
#         line = json.loads(i)
#         query = line["query"].strip()

#         if query in b:
#             f.write(json.dumps({"query": query, "answer": b[query]}, ensure_ascii=False) + "\n")

# with open("chatgpt_answer_type2.json", "w", encoding="utf-8") as f:
#     for i in open("../normalize/query_type2.json", encoding="utf-8"):
#         line = json.loads(i)
#         query = line["query"].strip()

#         if query in b:
#             f.write(json.dumps({"query": query, "answer": b[query]}, ensure_ascii=False) + "\n")