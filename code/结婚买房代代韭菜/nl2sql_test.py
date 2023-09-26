from nl2sql.nl2sql import *
from nl2sql.chatgpt import build_chatgpt_nl2sql_dataset, chat
from query_analyze import query_type_router
from config import DB_PATH, QUESTION_PATH
from build_prompt import build_prompt_v2
import json
import sqlite3
import warnings
warnings.filterwarnings("ignore")

db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

def test(query):
    # query = "请提供天宜上佳公司2021年的流动负债增长率，保留两位小数。"
    query_analyze_result = get_query_analyze_result(query)
    sql = build_sql(query, query_analyze_result)
    print(sql)
    cols = prepare_columns_for_sql_v2(query, query_analyze_result)
    print("cols", cols)
    query = prepare_query_for_sql(query, query_analyze_result)
    print("query", )
    print(build_nl2sql_prompt(query, cols))
    # exe_sql = translate_sql(sql)
    # print(exe_sql)
    # res = cursor.execute(exe_sql).fetchall()
    # print(res)
    # print(explain_sql_result(sql, res))

if __name__ == "__main__":
    # test("在2019年的时候，国瓷材料流动负债比率为多少？")
    
    # 重点看下！！！sql = "select 应付票据 from big where 年份 in ('2021年') and 公司名称 in ('柳州两面针股份有限公司')"
    # sql = "select 法定代表人 from big where 年份 in ('2020年', '2019年') and 公司名称 in ('上海韦尔半导体股份有限公司')"
    # sql = "select 归属于母公司所有者权益合计 from big where 年份 in ('2019年') and 公司名称 in ('石药集团新诺威制药股份有限公司')"
    # added_sql = add_meta_to_sql(sql)
    # exe_sql = translate_sql(added_sql)
    # res = cursor.execute(exe_sql).fetchall()
    
    
    # klg = explain_sql_result(added_sql, res)
    # print(klg)
    #####重点看下

    # file = "normalize/query_type2.json"
    # lines = []
    # for line in open(file, encoding="utf-8"):
    #     print(line)
    #     if not line.strip():
    #         continue
    #     line = json.loads(line)
    #     prompt = prepare_type2_prompt(line["query"])
    #     line["prompt"] = prompt
    #     lines.append(line)

    # open(file, "w", encoding="utf-8").write("\n".join([json.dumps(line, ensure_ascii=False) for line in lines]))

    # 这个sql真难写
    # where 年份 between '2019年' and '2021年'
    # "select 公司名称 from (select 年份, 公司名称, row_number() over (partition by 年份 order by 货币资金 desc) as rn from big) a where rn <= 10 group by 公司名称 having count(*) == 3"

    # "select 公司名称 from (select 年份, 公司名称, row_number() over (partition by 年份 order by 负债合计 desc) as rn from big where 年份 between '2019年' and '2021年') a where rn <= 5 group by 公司名称 having count(*) == 3"

    # "select gong_si_ming_cheng from (select nian_fen, gong_si_ming_cheng, row_number() over (partition by nian_fen order by fu_zhai_he_ji desc) as rn from big where nian_fen between '2019年' and '2021年') a where rn <= 5 group by gong_si_ming_cheng having count(*) == 3"
    # a = "select 公司名称 from (select 年份, 公司名称, row_number() over (partition by 年份 order by 货币资金 desc) as rn from big where 年份 between '2019年' and '2021年') a where rn <= 10 group by 公司名称 having count(*) == 3"
    # b = add_meta_to_sql(a)
    # c = translate_sql(b)
    # print(b, c)

    query_path = "nl2sql/type12_103_clean_1280_sf.json"
    # with open("nl2sql/type1_type2_queries_data_v1.json", "w", encoding="utf-8") as f:
    import sqlite3
    db = sqlite3.connect("../db/test.db")
    cursor = db.cursor()
    for line in tqdm(open(query_path, encoding="utf-8")):
        if json.loads(line)["sql"].startswith("ERR"):
            continue
        try:
            exe_sql = translate_sql(json.loads(line)["sql"])
            cursor.execute(exe_sql)
        except:
            print(line)
            print(exe_sql)
            raise Exception
        # line = json.loads(line)
        # query = line["question"]
        # type_ = line["type"]
        # if type_ != "type2":
        #     continue
        # _, query_analyze_result = query_type_router(query)

        # prompt = prepare_prompt(query, type_, query_analyze_result)
        # sql = build_sql(query, query_analyze_result)
        # f.write(json.dumps({"prompt": prompt, "sql": sql}, ensure_ascii=False) + "\n")



