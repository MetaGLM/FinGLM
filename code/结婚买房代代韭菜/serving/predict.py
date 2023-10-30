from tqdm import tqdm
import json
from argparse import ArgumentParser
import sqlite3

from fin_qa.load_model import ask_chatglm2, reset_transformer_chatglm2
from fin_qa.nl2sql.nl2sql import prepare_nl2sql_prompt, translate_sql, explain_sql_result, add_meta_to_sql
from fin_qa.normalize.normalize_utils import pack_sql_res, pack_normalize_res
from fin_qa.config import *
from fin_qa.query_analyze import get_query_analyze_result
from fin_qa.utils import gen_sql_res_json
from fin_qa.build_prompt import build_prompt_v2, build_norm_prompt
from fin_qa.art import gen_rule_ans, correct_answer
from fin_qa.db.db_schema import schema, schema_fin, schema_meta

from predict_v1 import search as search_v1


schema = set(schema)
db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

def nl2sql(args, input_path, output_path):
    '''
    nl2sql model call
        - prompt: query & db columns
        - response: sql
    '''
    with open(output_path, "w", encoding="utf-8") as f:
        for line in tqdm(open(input_path, encoding="utf-8"), desc="building_sql"):
            line = json.loads(line)
            # 如果使用全模型模式，type2也走nl2sql
            if line["type"].startswith("type1") or (args.mode == "all_model" and line["type"].startswith("type2")):
                query = line["question"]
                query_analyze_result = get_query_analyze_result(query)
                nl2sql_prompt = prepare_nl2sql_prompt(query, line["type"], query_analyze_result)
                sql = ask_chatglm2(nl2sql_prompt, temperature=args.temperature)
                line["sql"] = sql
                line["nl2sql_prompt"] = nl2sql_prompt
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
            # 其余的先不动
            else:
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
                continue

def router(args, output_path):
    '''
    router model call
        - prompt: query
        - response: type
    '''
    input_path = args.input
    with open(output_path, "w", encoding="utf-8") as f:
        for line in tqdm(open(input_path, encoding="utf-8"), desc="router"):
            line = json.loads(line)
            query = line["question"]
            type_ = ask_chatglm2(query, temperature=args.temperature)
            line["type"] = type_
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

def normalize(args, input_path, output_path):
    '''
    normalize model call
        - prompt: sql result & query
        - response: answer
    '''
    with open(output_path, "w", encoding="utf-8") as f:
        for line in tqdm(open(input_path, encoding="utf-8"), desc="normalizer"):
            line = json.loads(line)
            query = line["question"]
            type_ = line["type"]
            query_analyze_result = get_query_analyze_result(query)

            if type_.startswith("type3"):
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
                continue
            if type_.startswith("type2") and args.mode != "all_model":
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
                continue

            try:
                sql = line.get("sql", "/")
                exe_sql = translate_sql(sql)
                sql_res = cursor.execute(exe_sql).fetchall()

                if args.mode == "listC_final":
                    # 法定代表人使用规则生成答案
                    res = pack_normalize_res(type_, sql, gen_sql_res_json(cursor.description, sql_res))
                    if "法定代表人" in query and len(sql_res) > 1:
                        
                        line["norm_prompt"] = str(res)
                        line["answer"] = gen_rule_ans(sql, res, query)
                    else:
                    # 使用模型生成答案
                        if len(res) == 0:
                            line["answer"] = "抱歉，没有找到你需要的数据，所以答案是不知道。"
                        else:
                            prompt = build_norm_prompt(query, res)
                            line["norm_prompt"] = prompt
                            gen_ans = ask_chatglm2(prompt, temperature=args.temperature)
                            line["raw_ans"] = gen_ans
                            line["answer"] = correct_answer(gen_ans, type_, res)
                elif args.mode == "all_model":
                    res = pack_sql_res(sql, query, query_analyze_result, type_, sql_res)
                    if len(res) == 0:
                        line["answer"] = "抱歉，没有找到你需要的数据，所以答案是不知道。"
                    else:
                        prompt = build_norm_prompt(query, res)
                        line["norm_prompt"] = prompt
                        gen_ans = ask_chatglm2(prompt, temperature=args.temperature)
                        line["answer"] = gen_ans
            except Exception as e:
                print(query)
                print(sql_res)
                print("ERR: ", e)
                line["type"] = "type3"
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

def solve_type3(args, input_path):
    '''
    no-tune model call
        - prompt: query (& klg from doc_tree)
        - response: answer
    '''
    output_path = args.output
    i = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for line in tqdm(open(input_path, encoding="utf-8"), desc="no-tune"):
            line = json.loads(line)
            type_ = line["type"]
            query = line["question"]
            res = line.get("answer", "")

            if not type_.startswith("type1"):
                res = search_v1(query, temperature=args.temperature)
                line["answer"] = res 
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

            if i % args.log_steps == 0:
                print_res = res.replace("\n", "\\n")
                print(f"Q: {line['question']}\tA: {print_res}", end=";")
            i += 1

def predict(args):
    # 一共加载四次模型

    # 1. 路由问题类型
    router(args, ROUTER_FILE_PATH)

    # 2. 对部分问题作nl2sql
    reset_transformer_chatglm2(pre_seq_len=NL2SQL_PRE_SEQ_LEN, checkpoint_path=NL2SQL_CHECKPOINT_PATH)
    nl2sql(args, ROUTER_FILE_PATH, SQL_FILE_PATH)

    # 3. 对于使用sql进行查询的结果进行回答问题
    reset_transformer_chatglm2(pre_seq_len=NORMALIZE_PRE_SEQ_LEN, checkpoint_path=NORMALIZE_CHECKPOINT_PATH)
    normalize(args, SQL_FILE_PATH, NORM_SOLVED_PATH)

    # 4. 解决非sql查询问题
    reset_transformer_chatglm2(pre_seq_len=None, checkpoint_path=None)
    solve_type3(args, NORM_SOLVED_PATH)

if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument("-i", "--input", type=str, default=QUESTION_PATH, help="输入测试文件路径")
    ap.add_argument("-o", "--output", type=str, default=OUTPUT_PATH, help="输出文件路径")
    ap.add_argument("-t", "--temperature", type=float, default=0.1, help="温度")
    ap.add_argument("--top_p", type=float, default=0.8, help="选词的概率和")
    ap.add_argument("--log_steps", type=int, default=5000, help="打出日志的步数")
    ap.add_argument("--mode", type=str, default="listC_final", help="运行模式，默认和C榜提交完全一致，可以选择完全模型的模式 all_model")

    args = ap.parse_args()
    predict(args)