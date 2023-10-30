import pandas as pd
import re
from copy import deepcopy

from .config import *
from .db.db_schema import balance, income, cash


class Keyword:
    def __init__(self, word, type, formula="", is_percent=False, raw_word=""):
        self.word = word
        self.type = type
        # self.aliases = set()
        self.raw_word = raw_word if raw_word else word
        # print("#", raw_word, self.raw_word)
        self.is_percent = is_percent
        self.key_title = dep_inv_map.get(word, word)
        self.formula = formula
        self.sub = self.parse_formula(formula)

    def __str__(self):
        return self.raw_word

    def parse_formula(self, formula):
        sub = list(set([i for i in re.split("[=/()+-]", formula) if i != ""]))
        return [Keyword(i, type=1) for i in sorted(sub, key=len, reverse=True)]

    def get_sub_word_by_name(self, name):
        for word in self.sub:
            if word.word == name:
                return word
        return None

    def print_keyword(self):
        print(self.word, self.raw_word, self.formula)
        if len(self.sub) != 1:
            for word in self.sub:
                word.print_keyword()

def last_year_keyword(keyword):
    new_keyword = deepcopy(keyword)
    new_keyword.word = "上年" + new_keyword.word
    new_keyword.raw_word = "上年" + new_keyword.raw_word
    for i in range(len(new_keyword.sub)):
        word = new_keyword.sub[i]
        new_keyword.formula = new_keyword.formula.replace(word.word, "上年" + word.word)
        new_keyword.sub[i] = "上年" + word.word
    return new_keyword

titles = [i.strip() for i in open(PDF_IDX_PATH, encoding="utf-8").readlines() if i]
comps = [i.split("_")[2] for i in titles]
comps_code = [i.split("_")[4] for i in titles]
comps_short = [i.split("_")[6] for i in titles]
years = [i.split("_")[8] for i in titles]

comp_title_dict = {}
for i, comp in enumerate(comps):
    if comp not in comp_title_dict:
        comp_title_dict[comp] = []
    comp_title_dict[comp].append(titles[i])
    
short_comp_dict = {}
for name, short in zip(comps, comps_short):
    short_comp_dict[short] = name
    
comp_short_dict = {}
for name, short in zip(comps, comps_short):
    comp_short_dict[name] = short

comps = set(comps)
comps_code = set(comps_code)
comps_short = set(comps_short)
years = set(years)

# 基础信息表
base = [
    "股票简称", "证券简称",
    "股票代码", "证券代码",
    "公司名称", "企业名称",
    "公司简称", "企业简称",
    "外文名称",
    "外文简称",
    "法定代表人", "法人",
    "注册地址", "注册地址的邮政编码",
    "办公地址", "办公地址的邮政编码",
    "网址", "电子信箱",
    "传真", "联系地址"
]
# 员工情况
employee = [
    '技术人员', 
    "生产人员",
    "销售人员",
    "财务人员",
    "行政人员",
    '小学', 
    '初中', 
    '高中', 
    '专科', 
    '本科', 
    '硕士', 
    '博士', 
    '中专', 
    '职工总数',
]


# 主营业务分析
business = [
    "研发投入",
    "研发人员",
]

dep_map = {
    "公司简介": base,
    "合并资产负债表": balance,
    "合并现金流量表": cash,
    "合并利润表": income,
    "员工情况": employee,
    "主营业务分析": business
}

other_excel_words = [
    "研发人员",
    "股份总数",
]

other_text_words = [
    "重大销售合同",
    "主要销售客户",
    "主要供应商",
    "审计意见",
    "社会责任",
    "核心竞争力",
    "现金流",
    "会计师事务",
    "董事长报告书",
    "员工情况",
    "研发投入",
    "主要会计数据",
    "控股股东",
    "资产及负债状况",
    "处罚及整改",
    "仲裁事项",
    "重大环保问题",
    "重大合同"
    "破产重整",
    "重大变化"
]

other_cut_words = [
    "以上",
    "以下",
    "及以上",
    "及以下"
]

exact_search_words = cash + balance + income + other_excel_words
corase_search_words = base + employee + other_text_words + business

type1_keywords = base + cash + balance + income + employee + business + other_excel_words# + other_text_words

dep_inv_map = {}
for k, v in dep_map.items():
    for i in v:
        if i in dep_inv_map:
            print(i)
        dep_inv_map[i] = k
leng = sum([len(v) for v in dep_map.values()])
inv_leng = len(dep_inv_map)
assert leng == inv_leng, f"{leng} != {inv_leng}"

if __name__ == "__main__":
    print(len(cash + balance + income))