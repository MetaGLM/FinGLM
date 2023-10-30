from pypinyin import lazy_pinyin
from tqdm import tqdm
import sqlite3
import re
import json
import random
import jieba

from ..build_prompt import build_nl2sql_prompt_type1, build_chatgpt_nl2sql_prompt, build_nl2sql_prompt_type2
from ..config import DB_PATH
from ..vector_search import vector_search
from ..keywords import comp_short_dict,comps,comps_short
from ..formulas import formula_dict
from ..utils import json_lines_dump,edit_distance,is_zh, is_int, is_float, find_dot, algin_float_string, year_add, lcs_sub
from ..query_analyze import query_analyze
from ..db.db_schema import TABLE_NAME, schema, schema_base, schema_fin, schema_emp, schema_meta, schema_edu


schema_fin_filtered = [i for i in schema_fin if "、" not in i]
schema_all = schema_base + schema_fin_filtered + schema_emp
schema_set = set(schema_all)
stopwords = set([i.strip() for i in open("fin_qa/resources/stopwords.txt", encoding="utf-8").readlines() if i])
stopwords_v2 = set([i.strip() for i in open("fin_qa/resources/stopwords_v2.txt", encoding="utf-8").readlines() if i])
stopwords_v2 |= stopwords

db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

BASE_IDX_NAME = "base"
FIN_IDX_NAME = "fin"
EMP_IDX_NAME = "emp"
ALL_IDX_NAME = "all"


def recall_formula(query, k=1):
    return [i[0] for i in vector_search(list(formula_dict.keys()), query, "formula", k=k)]

def query_words_filter(w):
    fil = not (len(w) > 1 and w not in stopwords_v2 and is_zh(w) and w not in comps and w not in comps_short)
    # print(w, fil)
    return fil

def recall_from_edit_distance(word, recall_n=3):
    recalls = vector_search(schema_emp+schema_base+schema_fin_filtered, word, "all", k=recall_n, rel_thres=0)
    # print(word, recalls)
    candidates = [i[0] for i in recalls][:3]
    edit_lens = [edit_distance(i, word) for i in candidates]
    return [cand for i, cand in enumerate(candidates) if edit_lens[i] != max(len(candidates[i]), len(word)) and edit_lens[i] <= 3]


def prepare_columns_for_sql_v2(query, query_analyze_result):
    '''
    准备好所需要的列
    '''
    # META
    all_cols = []
    all_cols += [i for i in schema_meta if i != "小数位数"]
    query_words = jieba.lcut(query)
    query_words = [w for w in query_words if not query_words_filter(w)]
    # print(query_words)
    
    # 来自KEYWORDS本身
    keywords = query_analyze_result.get("keywords", [])
    ques_type = ""
    for keyword in keywords:
        if keyword.type in (1, 3) and keyword.word in schema_set:
            all_cols.append(keyword.word)
        elif keyword.type == 2:
            all_cols += [i.word for i in keyword.sub if i.word in schema_set]

    all_candidates = []
    for word in query_words:
        all_candidates += recall_from_edit_distance(word)
        # print(word, recall_from_edit_distance(word))
    # print("candidates", all_candidates)
    all_cols += all_candidates

    if any([col in schema_edu for col in all_candidates]):
        all_cols += schema_edu

    all_cols_set = []
    for col in all_cols:
        if col not in all_cols_set:
            all_cols_set.append(col)
    random.shuffle(all_cols_set)
    return ",".join(all_cols_set)

def translate_sql(sql):
    reps = []
    for match in re.finditer("[\u4e00-\u9fa5]+", sql):
        # print(dir(match))
        s, e = match.span()
        # print(sql[s-1:e+1])
        if (s > 0 and sql[s-1] in ("'", "%")) or (e < len(sql) and sql[e] in ("'", "%")):
            continue
        reps.append(match.group())
    reps = sorted(list(set(reps)), key=len, reverse=True)
    for col in reps:
        py = "_".join(lazy_pinyin(col))
        sql = sql.replace(col, py)
    return sql

def build_sql(query, query_analyze_result):
    raw_comps = query_analyze_result.get("comps", [])
    years = query_analyze_result.get("years", [])
    comps = []
    comp_shorts = []
    for comp in raw_comps:
        if comp not in query and comp_short_dict[comp] in query:
            comp_shorts.append(comp_short_dict[comp])
        else:
            comps.append(comp)
    
    if "增长率" in query:
        years.append(year_add(years[0], -1))

    years_str = "年份 in (" + ", ".join([f"'{year}'" for year in years]) + ")" if years else ""
    comps_str = "公司名称 in (" + ", ".join([f"'{comp}'" for comp in comps]) + ")" if comps else ""
    comp_shorts_str = "股票简称 in (" + ", ".join([f"'{comp_short}'" for comp_short in comp_shorts]) + ")" if comp_shorts else ""

    where_cond = f"where " + " and ".join([i for i in [years_str, comps_str, comp_shorts_str] if i])
    
    keywords = query_analyze_result.get("keywords", [])
    all_selects = []
    # if years: all_selects.append("年份")
    # if comps: all_selects.append("公司名称")
    # if comp_shorts: all_selects.append("股票简称")

    if not keywords: return "lesect"

    # print("###", all_selects)
    for keyword in keywords:
        if keyword.type == 1:
            all_selects.append(keyword.word)
        elif keyword.type == 2:
            # 1. 非增长率
            if "增长率" not in query:
                for sub_word in keyword.sub:
                    all_selects.append(sub_word.word)
                if keyword.word == "博士及以上的员工人数":
                    all_selects.append("博士 as 博士及以上的员工人数")
                else:
                    all_selects.append("1.0 * " + keyword.formula + " as " + keyword.word)
            else:
                for sub_word in keyword.sub:
                    if not sub_word.word.startswith("上年"):
                        all_selects.append("年份")
                        all_selects.append(sub_word.word)
                        break

    select = "select " + ", ".join(all_selects)
    return f"""{select} from big {where_cond}"""

def prepare_query_for_sql(query, query_analyze_result):
    comps = keywords = query_analyze_result.get("comps", [])
    for comp in comps:
        if comp in query:
            query = query.replace(comp, f"公司名称为{comp}的公司")
        elif comp_short_dict[comp] in query:
            comp_short = comp_short_dict[comp]
            query = query.replace(comp_short, f"股票简称为{comp_short}的公司")
    return query

def build_nl2sql_dataset(input_path, output_path, train_n=1000, test_n=100):
    samples = []
    for line in tqdm(open(input_path, encoding="utf-8")):
        if not line:
            continue 
        query = json.loads(line)["question"]

        query_analyze_result = get_query_analyze_result(query)
        sql = build_sql(query, query_analyze_result)
        prompt = prepare_prompt(query, query_analyze_result)

        exe_sql = translate_sql(sql)
        try:
            res = cursor.execute(exe_sql).fetchall()
            if len(res) > 0:
                sample = {"prompt": prompt, "sql": sql}
                # print(sample)
                samples.append(sample)
        except Exception as e:
            # print(e, exe_sql)
            continue
    print("len_samples", len(samples))
    random.shuffle(samples)
    json_lines_dump(samples, output_path + "_all.json")
    json_lines_dump(samples[:train_n], output_path + "_train.json")
    json_lines_dump(samples[train_n:train_n+test_n], output_path + "_test.json")

def process_select(select):
    if "as" in select:
        return select.split("as")[-1].strip("1.0 *").strip()
    return select.strip("1.0 *").strip()

def add_meta_to_sql(sql, meta=["小数位数", "年份", "公司名称", "股票简称", "股票代码"]):
    if "增长率" in sql: return sql
    if "group by" in sql: return sql
    selects = re.findall("select(.*?)from", sql)[:1]
    # print(selects[0])
    if selects == "":
        return "ERR SQL"
    select_formula = [select.split(" as ")[0].strip() for select in selects[0].split(",") if " as " in select]
    # print(select_formula)
    subs = [] if not select_formula else list(set([i.strip() for i in re.split("[=/()+-]", select_formula[0].strip("1.0 * ")) if i.strip() != ""]))
    # print(subs)
    subs_str = ",".join(subs)
    to_be_added = [i for i in meta if i not in selects[0]]
    new_selects = " " + ", ".join(to_be_added + subs + selects) + " "

    from_pos = sql.find("from") + 4
    return f"select{new_selects}from" + sql[from_pos:]

def explain_sql_result(sql, res, query):
    selects = re.findall("select(.*?)from", sql)
    if not selects:
        return ""

    if len(res) > 1 and "法定代表人" in query:
        return gen_is_same_inlawer(selects[0], query, res)

    selects = [process_select(select) for select in selects[0].split(",")]

    lines_ans = []
    for i, line in enumerate(res):
        line_ans = f"{i+1}. " if len(res) > 1 else ""
        selects_dic = {k: v for k, v in zip(selects, line)}
        dot_bits = selects_dic.get("小数位数", '2')
        line_ans += f"{selects_dic.get('公司名称', '')}"
        if '年份' in selects_dic:
            line_ans += f"在{selects_dic['年份']}"
        for s, v in zip(selects, line):
            if s in ("公司名称", "年份", "小数位数"):
                continue
            
            unit = '' if s not in schema_fin else '元'
            unit = unit if s not in schema_emp else '人'

            if isinstance(v, float):
                v = algin_float_string(v, dot_bits)
            
            line_ans += f'{s}为{v}{unit}，'
        if line_ans.endswith("，"): line_ans = line_ans[:-1]
        line_ans = line_ans + "。"
        lines_ans.append(line_ans)
    return "".join(lines_ans[:10]) 

def prepare_nl2sql_prompt(query, query_type, query_analyze_result):
    cols = prepare_columns_for_sql_v2(query, query_analyze_result)
    query = prepare_query_for_sql(query, query_analyze_result)
    
    if query_type == "type2" and "增长率" not in query:
        formula_name = recall_formula(query)[0]
        formula = formula_dict[formula_name]
        cols = set(cols.split(",") + formula['sub'])
        cols = ",".join(cols)
        return build_nl2sql_prompt_type2(query, cols, f"{formula_name}={formula['raw_formula']}")
    
    return build_nl2sql_prompt_type1(query, cols)

if __name__ == "__main__":
    build_nl2sql_dataset(QUESTION_PATH, "nl2sql")