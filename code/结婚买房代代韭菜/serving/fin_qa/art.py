import re

from .keywords import comp_short_dict
from .query_analyze import query_analyze
from .utils import lcs_sub


'''
人工规则拼接/修正答案
'''

def gen_rule_ans(sql, res, query):
    selects = re.findall("select(.*?)from", sql)
    if selects:
        selects = [i.strip() for i in selects[0].split(",")]
        if len(res) > 1:
            # 法定代表人题目
            if "法定代表人" in query:
                return gen_is_same_inlawer(selects, query, res)
            else:
                return gen_type12_ans(selects, query, res)
        elif len(res) == 1:
            return gen_type11_ans(selects, query, res)
    return "抱歉，没有找到您想要的数据，答案是不知道。"

def gen_is_same_inlawer(selects, query, res):
    comps, _, _ = query_analyze(query)
    if comps[0] in query:
        comp = comps[0]
    else:
        comp = comp_short_dict[comps[0]]

    final_res = f"{comp}"
    all_inlawers = []
    for year, inlawer in zip(res["年份"], res["法定代表人"]):
        all_inlawers.append(inlawer)
        final_res += f"{year}的法定代表人是{inlawer}，" if inlawer != '' else f"没有找到{year}的法定代表人，"
    
    def judge_is_same(str_list):
        lcs_str = str_list[0]
        for string in str_list[1:]:
            lcs_str = lcs_sub(lcs_str, string)
        return len(lcs_str) == min(map(len, str_list))

    if "没有找到" not in final_res:
        is_same = "相同。" if judge_is_same(all_inlawers) else "不相同, 不同。"
        final_res += f"所以答案是{is_same}"
    else:
        final_res += f"所以答案是不知道，抱歉没有找到您想要的数据。"
    return final_res

def gen_type11_ans(selects, query, res):
    return f'"{query}"的答案是：' + "、".join([i[0] for i in res.values()])

def gen_type12_ans(selects, query, res):

    final_res = f'"{query}"的答案是：'
    final_res += "、".join(res["公司名称"]) + "。"

    if len(res.keys()) > 1:
        key = [i for i in res.keys() if i != "公司名称"][0]
        final_res += "金额是：" + "、".join(res[key])
    return final_res

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