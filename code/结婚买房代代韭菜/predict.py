from predict_v1 import search as search_v1
from load_model import ask_chatglm2, reset_transformer_chatglm2
from nl2sql.nl2sql import prepare_prompt, translate_sql, explain_sql_result, add_meta_to_sql, gen_rule_ans
from normalize.normalize_utils import pack_normalize_res
from config import *
from query_analyze import query_analyze, query_type_router
from tqdm import tqdm
from utils import gen_sql_res_json
import json
from argparse import ArgumentParser

from build_prompt import build_prompt_v2, build_norm_prompt
from db.db_schema import schema, schema_fin, schema_meta

import sqlite3

schema = set(schema)
db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

def nl2sql(input_path, output_path, temperature=0.1):
    with open(output_path, "w", encoding="utf-8") as f:
        for line in tqdm(open(input_path, encoding="utf-8"), desc="building_sql"):
            line = json.loads(line)
            if line["type"].startswith("type3") or line["type"].startswith("type2"):
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
                continue

            query = line["question"]
            _, query_analyze_result = query_type_router(query)
            nl2sql_prompt = prepare_prompt(query, line["type"], query_analyze_result)
            sql = ask_chatglm2(nl2sql_prompt, temperature=temperature)
            line["sql"] = sql
            line["nl2sql_prompt"] = nl2sql_prompt
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

def router(input_path, output_path, temperature=0.1):
    with open(output_path, "w", encoding="utf-8") as f:
        for line in tqdm(open(input_path, encoding="utf-8"), desc="router"):
            line = json.loads(line)
            query = line["question"]
            type_rule, _ = query_type_router(query)
            type_ = ask_chatglm2(query, temperature=temperature)
            line["type"] = type_
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

def correct_answer(gen_res, type_, res):
    try:
        if type_ == "type12":
            if "公司名称" in res:
                comps = [i for i in res["公司名称"] if i not in gen_res]
                if comps:
                    gen_res += "以及" + "和".join(comps)
            metric_keys = [i for i in res.keys() if i not in schema_meta]
            if metric_keys:
                for key in metric_keys:
                    vals = [i for i in res[key] if i not in gen_res]
                    if not vals:
                        continue
                    if key in schema_fin:
                        gen_res += "金额为：" + "、".join([i + "元" for i in vals])
                    else:
                        gen_res += "、".join(res[key])
    except:
        return gen_res
    return gen_res

def solve_type1(input_path, output_path, temperature=0.1):
    with open(output_path, "w", encoding="utf-8") as f:
        for line in tqdm(open(input_path, encoding="utf-8"), desc="normalizer"):
            line = json.loads(line)
            query = line["question"]
            type_ = line["type"]

            if line["type"].startswith("type1"):
                try:
                    sql = line.get("sql", "/")
                    added_sql = add_meta_to_sql(sql)
                    exe_sql = translate_sql(added_sql)
                    sql_res = cursor.execute(exe_sql).fetchall()

                    # 法定代表人使用规则生成答案
                    if "法定代表人" in query and len(sql_res) > 1:
                        res = pack_normalize_res(sql, gen_sql_res_json(cursor.description, sql_res), is_rule=True)
                        line["norm_prompt"] = str(res)
                        line["answer"] = gen_rule_ans(sql, res, query)
                    else:
                    # 使用模型生成答案
                        res = pack_normalize_res(sql, gen_sql_res_json(cursor.description, sql_res))
                        if len(res) == 0:
                            line["answer"] = "抱歉，没有找到你需要的数据，所以答案是不知道。"
                        else:
                            prompt = build_norm_prompt(query, res)
                            line["norm_prompt"] = prompt
                            gen_ans = ask_chatglm2(prompt, temperature=temperature)
                            line["raw_ans"] = gen_ans
                            line["answer"] = correct_answer(gen_ans, type_, res)
                except Exception as e:
                    print(added_sql)
                    print(res)
                    print("ERR: ", e)
                    line["type"] = "type3"
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

def solve_other(input_path, output_path, temperature=0.1, log_steps=1):
    i = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for line in open(input_path, encoding="utf-8"):
            line = json.loads(line)
            type_ = line["type"]
            query = line["question"]
            res = line.get("answer", "")

            if not type_.startswith("type1"):
                res = search_v1(query, temperature=0.1)
                line["answer"] = res 
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

            if i % log_steps == 0:
                print_res = res.replace("\n", "\\n")
                print(f"Q: {line['question']}\tA: {print_res}", end=";")
            i += 1

def predict(args):
    # 一共加载四次模型
    router(args.input, ROUTER_FILE_PATH) # router写到SQL_FILE_PATH里

    reset_transformer_chatglm2(pre_seq_len=NL2SQL_PRE_SEQ_LEN, checkpoint_path=NL2SQL_CHECKPOINT_PATH)
    
    nl2sql(ROUTER_FILE_PATH, SQL_FILE_PATH)

    reset_transformer_chatglm2(pre_seq_len=NORMALIZE_PRE_SEQ_LEN, checkpoint_path=NORMALIZE_CHECKPOINT_PATH)

    solve_type1(SQL_FILE_PATH, TYPE1_SOLVED_PATH)

    reset_transformer_chatglm2(pre_seq_len=None, checkpoint_path=None)

    solve_other(TYPE1_SOLVED_PATH, args.output, log_steps=args.log_steps)

if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument("-i", "--input", type=str, default=QUESTION_PATH, help="输入测试文件路径")
    ap.add_argument("-o", "--output", type=str, default=OUTPUT_PATH, help="输出文件路径")
    ap.add_argument("-t", "--temperature", type=float, default=0.1, help="温度")
    ap.add_argument("--top_p", type=float, default=0.8, help="选词的概率和")
    ap.add_argument("--log_steps", type=int, default=5000, help="打出日志的步数")

    args = ap.parse_args()
    predict(args)