from argparse import ArgumentParser
from tqdm import tqdm
from itertools import combinations
import os
import re
import json

from utils import *
from vector_search import build_vector_store, vector_search
from doc_tree import DocTree
from keywords import *
from formulas import *
from alias import alias_inv_dict
from query_analyze import query_analyze
from config import *
from build_prompt import *
from load_model import ask_chatglm2

from db.db_utils import query_single_klg
from db.db_schema import schema, schema_fin

import sqlite3

schema = set(schema)
db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

import warnings
warnings.filterwarnings("ignore")
    
stopwords = set([i.strip() for i in open(STOPWORDS_PATH, encoding="utf-8")])

def dt_search(dt, keyword, k=20, hop=0):
    only_excel_node = keyword not in other_text_words
    if len(keyword.split(" ")) > 1:
        only_excel_node = False
    if keyword in type1_keywords:
        klg = []
        table_name = dep_inv_map.get(keyword, keyword)
        if table_name in ("合并资产负债表", "合并利润表", "合并现金流量表"):
            klg.append("单位：元")
        elif table_name in ("员工情况"):
            klg.append("单位：人")
        
        nodes = dt.search_node(table_name)
        if len(nodes) == 0:
            return klg + [i.get_dep_str(hop=hop) for i in dt.search_leaf(keyword, only_excel_node=only_excel_node, k=k)]
        
        all_children = []
        # 其他均为模糊搜索
        if keyword in corase_search_words:
            vector_search_idx_name = dt.path
            if keyword in employee:
                all_children += nodes[-1].get_all_leaves("", only_excel_node=only_excel_node)[:k]
            else:
                for node in nodes:
                    vector_search_idx_name += "-" + str(node)
                    all_children += [i for i in node.get_all_leaves("", only_excel_node=only_excel_node) if i not in all_children]
                if len(all_children) >= 2:
                    all_children = [f"{i[0].get_dep_str(hop=hop)}" for i in vector_search(all_children, keyword, vector_search_idx_name, k=k)]
        else:
            # 财务报表精准搜索
            for node in nodes:
                all_children += [i.get_dep_str(hop=hop) for i in node.search_children(keyword)]
            all_children = all_children[:1]
            
#         print(all_children)
        
        klg += [str(i) for i in all_children]
        if keyword in corase_search_words or len(all_children) == 0:
            # 如果是模糊搜索或者上述操作无搜索结果，则补充搜索
            klg += [i.get_dep_str(hop=hop) for i in dt.search_leaf(keyword, only_excel_node=only_excel_node)]
        dedup_klg = []
        for sub_klg in klg:
            if sub_klg not in dedup_klg:
                dedup_klg.append(sub_klg)
        return dedup_klg[:k]
    
    nodes = dt.search_node(keyword)
    if len(nodes) > 0:
        all_children = []
        for node in nodes:
            all_children += [i.get_dep_str(hop=hop) for i in node.get_all_leaves(keyword, only_excel_node=only_excel_node) if i not in all_children]
        all_children = all_children[:k]
        return [str(c) for c in all_children]
    
    return [i.get_dep_str(hop=hop) for i in dt.search_leaf(keyword, only_excel_node=only_excel_node)][:k]

def get_desc_klg(pdf):
    if pdf == "":
        return ""
    try:
        _, _, comp_name, _, comp_code, _, comp_short, _, report_year, _, _ = pdf.split("_")
        return f"企业名称为{comp_name}（简称{comp_short}, 股票/证券代码{comp_code}）的年报"
    except:
        return ""
    
def solve_type1(comp_name, year, keyword, query="", **kwargs):
    if query == "":
        query = f"{comp_name}在{year}的{keyword}是？"

    pdf = get_year_doc(comp_name, year)
    if pdf == None:
        return ""
    path = get_txt_path(pdf)
    if not os.path.exists(path):
        return ""
    desc_klg = get_desc_klg(pdf)

    klg = ""
    if keyword.word in schema:
        klg = query_single_klg(cursor, "big", comp_name, year, keyword)
        if klg == "":
            return "抱歉，我没有找到您需要的数据，对于您问题的答案是不知道。"
    
    else:
        dt = DocTree(path)
        klg = dt_search(dt, str(keyword))
        klg = "\n".join(klg_cleaner(klg, year))

    prompt = build_prompt(klg, query, desc_klg)


    res = ask_chatglm2(prompt, **kwargs)
    return res

def solve_type2(comp_name, year, keyword, query, **kwargs):
    res = []
    extra_output = ""
    values = []
    formula = keyword.formula
    format_output = ""

    # 使得公司名称和query中的保持严格一致
    if comp_name not in query:
        comp_name = comp_short_dict[comp_name]
    
    export_dict = {}
    for word in keyword.sub:
        if word.word.startswith("上年"):
            sub_year = year_add(year, -1)            
            sub_word = Keyword(word.word[2:], type=1, raw_word=word.raw_word[2:])
        else:
            sub_year = year
            sub_word = Keyword(word.word, type=1, raw_word=word.raw_word)

        # print("DEBUG", sub_year, sub_word.word, sub_word.raw_word)
        # 尝试通过数据库先找，数据库找不到再递归调用。
        res_v = ""
        if sub_word.word in schema:
            res_v = find_res_value(query_single_klg(cursor, "big", comp_name, sub_year, sub_word), sub_word)
        else:
            type1_res = solve_type1(comp_name, sub_year, sub_word, **kwargs)
            res_v = find_res_value(type1_res, sub_word)

        if res_v == "":
            format_output += f"抱歉，没有找到{comp_name}在{sub_year}的{sub_word}。"
            continue
        
        unit = ""
        if "每股" in sub_word.word:
            unit = "元/股"
        elif sub_word.word in schema_fin:
            unit = "元"
        elif sub_word.word in schema_emp:
            unit = "人"

        if format_output:
            if sub_year in format_output:
                format_output += f"{sub_word}为{res_v}{unit}，"
            else:
                format_output += f"{sub_year}{sub_word}为{res_v}{unit}，"
        else:
            format_output += f"{comp_name}{sub_year}{sub_word}为{res_v}{unit}，"
        values.append(my_float(res_v))

        if "增长率" in keyword.word:
            export_dict[sub_year + sub_word.word] = res_v
        else:
            export_dict[word.word] = res_v

    if len(values) != len(keyword.sub):
        format_output += f"无法为您计算{year}{comp_name}的{keyword}。"
        return [], format_output

    for i, k in enumerate(keyword.sub):
        formula = formula.replace(k.word, f"{values[i]}")
    try:
        ans = eval(formula)
    except Exception as e:
        print(formula)
        ans = 1

    if ("以上" in keyword.word or "以下" in keyword.word) and "/" not in keyword.formula:
        ans = int(ans)
        export_dict[keyword.word] = ans
        format_output += f"根据公式，{keyword}={keyword.formula}，得出结果{comp_name}{year}{keyword}为{ans}人。"
        # format_output += f"计算得出{comp_name}{year}{keyword}为{ans}人。"
    else:
        ans_1 = f"{ans:.2%}"
        ans_2 = f"{ans:.2f}"

        format_output += f"根据公式，{keyword}={keyword.formula}，得出结果{comp_name}{year}{keyword}为{ans_1}或{ans_2}。"
        # format_output += f"计算得出{comp_name}{year}{keyword}为{ans_1}或{ans_2}。"
        export_dict[keyword.word] = f"{ans_1}或{ans_2}"
    # print({"sql_res": export_dict, "query": query, "answer": format_output})

    return [], format_output

def solve_type31(comp_name, year, keywords, query, hop=0, k=20, **kwargs):
    pdf = get_year_doc(comp_name, year)

    if pdf == None:
        return ask_chatglm2(query, **kwargs)
    path = get_txt_path(pdf)
    if not os.path.exists(path):
        return ask_chatglm2(query, **kwargs)
    dt = DocTree(path)

    klg = ""
    if keywords:
        nodes = dt.search_node(keywords[0].word)
        all_children = []
        for node in nodes:
            all_children += [i.get_dep_str(hop=hop) for i in node.get_all_leaves("", only_excel_node=False) if i not in all_children]
        klg = "\n".join([str(i) for i in all_children[:k]])
    
    if not klg:
        if comp_name not in query:
            comp_name = comp_short_dict[comp_name]

        dt_query = query.replace(comp_name, "公司")
        for year in years:
            dt_query = dt_query.replace(year, "")
        
        node = dt.vector_search_node(dt_query)[0][0]
        klg = "\n".join([i.get_dep_str(hop=hop) for i in node.get_all_leaves("", only_excel_node=False)][:k])

    desc_klg = get_desc_klg(pdf)
    prompt = build_prompt(klg, query, desc_klg)
    return ask_chatglm2(prompt, **kwargs)

def search(query, **kwargs):
    comp_names, years, keywords = query_analyze(query)
    # type3-2
    if (not comp_names) or (not years):
        return ask_chatglm2(query, **kwargs)

    # type1, 直接用自己的query， 减少一跳
    if len(comp_names) == 1 and len(years) == 1 and len(keywords) == 1 and keywords[0].type == 1:
        type1_res = solve_type1(comp_names[0], years[0], keywords[0], query=query, **kwargs)
        if not type1_res:
            return ask_chatglm2(query, **kwargs)
        else:
            return type1_res

    res_prompts = []
    extra_outputs = []

    for comp_name in comp_names:
        for year in years:
            if not keywords:
                return solve_type31(comp_name, year, keywords, query, **kwargs)

            for keyword in keywords:
                if keyword.type == 1:
                    res_prompts.append(solve_type1(comp_name, year, keyword, **kwargs))
                elif keyword.type == 2:
                    res, extra = solve_type2(comp_name, year, keyword, query, **kwargs)
                    res_prompts += res
                    extra_outputs.append(extra)
                elif keyword.type == 3:
                    return solve_type31(comp_name, year, keywords, query, **kwargs)

    if extra_outputs:
        return "".join(res_prompts) + "".join(extra_outputs)
    
    type1_res = ""
    if res_prompts:
        klg = "\n".join(res_prompts)
        desc_klg = []
        for comp_name in comp_names:
            for year in years:
                pdf = get_year_doc(comp_name, year)
                if pdf == None:
                    continue
                desc_klg.append(get_desc_klg(pdf))
        desc_klg = "\n".join(set(desc_klg))
        prompt = build_prompt(klg, query, desc_klg)
        type1_res = ask_chatglm2(prompt, **kwargs)

    return type1_res

def predict(args):
    i = 0
    with open(args.output, "w", encoding="utf-8") as f:
        for line in tqdm(open(args.input, encoding="utf-8")):
            
            line = json.loads(line.strip())

            ques = line["question"]
            res = search(ques, temperature=args.temperature, top_p=args.top_p)
            if i % args.log_steps == 0:
                print(f"Q: {ques}\tA: {res}\n")
            i += 1
            line["answer"] = res
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument("-i", "--input", type=str, default=QUESTION_PATH, help="输入测试文件路径")
    ap.add_argument("-o", "--output", type=str, default=OUTPUT_PATH, help="输出文件路径")
    ap.add_argument("-t", "--temperature", type=float, default=0.1, help="温度")
    ap.add_argument("--top_p", type=float, default=0.8, help="选词的概率和")
    ap.add_argument("--log_steps", type=int, default=18, help="打出日志的步数")

    args = ap.parse_args()
    predict(args)
    