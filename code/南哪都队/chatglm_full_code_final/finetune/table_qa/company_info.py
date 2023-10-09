import os
import json
from pathlib import Path
from tqdm import tqdm
from collections import defaultdict
import numpy as np
from copy import deepcopy



global_same_counter = 0
global_different_counter = 0

np.random.seed(42)

prompt = "现在给你若干个包含公司基本信息的表格,请你根据表格的内容正确回答问题:\n"

# question templates

company_attribute_alias = {
    "股票简称": ["证券简称", "公司简称", "股票缩写", "公司名缩写", "公司名称缩写", "证券缩写"],
    "股票代码": ["证券代码", "代码"],
    "公司的总经理": ["总经理", "公司总经理"],
    "公司总经理": ["总经理", "公司的总经理"],
    "公司的总裁": ["总裁", "公司总裁"],
    "投资者关系联系电话": ["投资者联系电话", "投资者联系电话号码", "号码"],
    "客户服务热线": ["客户联系电话", "客户服务电话号码", "客户服务号码", "客户服务热线", "服务热线"],
    "公司注册资本": ["注册资本", "公司的注册资本"],
    "注册资本": ["公司的注册资本", "公司注册资本"],
    "英文名称": ["公司的英文名称", "外文名称", "公司的外文名称"],
    "公司的外文名称（如有）": ["公司的外文名称", "外文名称", "公司的英文名称", "英文名称"],
    "公司的外文名称": ["外文名称", "公司的英文名称", "英文名称", "公司的外文名称（如有）"],
    "变更前的股票简称（如有）": ["变更前的股票简称"],
    "变更前的股票简称": ["变更前的股票简称（如有）"],
    "变更后的股票简称（如有）": ["变更后的股票简称"],
    "变更后的股票简称": ["变更后的股票简称（如有）"],
    "公司的法定代表人": ["法定代表人", "公司法定代表人"],
    "法定代表人": ["公司的法定代表人", "公司的法定代表人"],
    "公司网址": ["公司的网址", "网站地址", "公司网站", "官方网站"],
    "公司的外文名称": ["外文名称", "公司外文名称"],
    "公司的外文名称缩写": ["外文名称缩写", "外文缩写", "公司外文名缩写", "公司外文名简称", '公司的外文名称缩写（如有）'],
    "公司的外文名称缩写（如有）": ["外文名称缩写", "外文缩写", "公司外文名缩写", "公司外文名简称", '公司的外文名称缩写（如有）'],
    "联系电话": ["电话号码", "号码", "服务热线"],
    "服务热线": ["电话号码", "联系电话"],
    "公司注册地址历史变更": ["注册地址变更"],
    "股票上市证券交易所": ["交易所", "证券交易所"],
    "注册地址的邮政编码": ["注册地邮编"],
    "注册地址": ["公司注册地址"],
    "公司注册地址历史变更情况": ["注册地址历史变更", "注册地址变更情况"],
    "办公地址": ["公司办公地址"],
    "公司的总裁": ["总裁"],
    "公司国际互联网网址": ["国际互联网网址"],
    "公司的法定代表人/董事长": ["法定代表人/董事长"],
    "公司的中文名称": ["中文名称", "公司中文名称", "企业名称", '官方注册名称'],
    "公司的中文简称": ["中文简称", "公司中文简称", "中文名缩写"],
    "办公地址的邮政编码": ["办公地邮编"],
    "主要办公地址": ["公司主要办公地址"],
    "电子信箱": ["电子邮箱", "邮箱地址", "电子邮件"],
}

global_attribute_clusters = [
    {'情况','公司注册地址历史变更情况', '公司注册地址历史变更'},
    {'公司的总经理', '法定代表人', '公司总经理', '公司的总裁', '公司的法定代表人/董事长', "公司的法定代表人"},
    {'投资者关系联系电话', '联系电话', '注册地址的邮政编码', '主要办公地址的邮政编码', '服务热线', '电子信箱', "公司国际互联网网址"},
    {'公司注册资本', '净资本', '注册资本', '公司净资本'}
]

company_info_single_attribute_template = {
    tuple(global_attribute_clusters[0]): [
        {
            "question": "请简要介绍一下<company_name><year>年<attribute>的详细内容.",
            "answer": "<attribute>如下: <value>."
        },{
            "question": "告诉我<company_name><year>年有关<attribute>.",
            "answer": "<attribute>如下: <value>."
        },{
            "question": "<company_name><year>年<attribute>怎么样?.",
            "answer": "<attribute>如下: <value>."
        },
    ],
    tuple(global_attribute_clusters[1]): [
        {
            "question": "<company_name><year>年的<attribute>是谁？",
            "answer": "<company_name><year>年的<attribute>是<value>."
        },{
            "question": "<company_name><year>年的<attribute>的名字是什么？",
            "answer": "<company_name><year>年的<attribute>的名字是<value>."
        },{
            "question": "根据所给定的表格，<year>年, <company_name>的<attribute>的名字是什么？",
            "answer": "<year>年, <company_name>的<attribute>的名字是<value>."
        },{
            "question": "请提供<year>年<company_name><attribute>的详细数据.",
            "answer": "<year>年, <company_name>的<attribute>是<value>."
        },{
            "question": "请告诉我<company_name><year>的<attribute>的具体情况",
            "answer": "<year>年, <company_name>的<attribute>是<value>." 
        }
    ],
    tuple(global_attribute_clusters[2]): [
        {
            "question": "<company_name><year>年的<attribute>是多少？",
            "answer": "<company_name><year>年的<attribute>是<value>。"
        },{
            "question": "<company_name><year>年的<attribute>是什么？",
            "answer": "<company_name><year>年的<attribute>是<value>。"
        },{
            "question": "<year>年，<company_name>的<attribute>的具体情况是什么？",
            "answer": "<year>年，<company_name><year>年的<attribute>是<value>。"
        },
        {
            "question": "告诉我<company_name><year>年的<attribute>的详细内容？",
            "answer": "<company_name><year>年的<attribute>是<value>。"
        },
    ],
    tuple(global_attribute_clusters[3]): [
        {
            "question": "<company_name><year>年的<attribute>是多少元？",
            "answer": "<company_name><year>年的<attribute>是<value>元。"
        },{
            "question": "<year>年，<company_name><attribute>的具体数值是？",
            "answer": "<year>年，<company_name>的<attribute>是<value>元。"
        },{
            "question": "根据<year>年年报，简要介绍下<company_name><attribute>的具体情况？",
            "answer": "<year>年，<company_name>的<attribute>是<value>元。"
        }
    ]
}

company_info_double_attribute_template = {
    tuple(global_attribute_clusters[0]): [],
    tuple(global_attribute_clusters[1]): [
        {
            "question": "<company_name><year>年的<attribute_1>和<attribute_2>分别是谁？",
            "answer": "<company_name><year>年的<attribute_1>和<attribute_2>分别是<value_1>和<value_2>。"
        },{
            "question": "根据所给定的表格，<year>年，<company_name>的<attribute_1>和<attribute_2>的名字分别是什么?",
            "answer": "<year>年，<company_name>的<attribute_1>和<attribute_2>的名字分别是<value_1>和<value_2>。"
        },
    ],
    tuple(global_attribute_clusters[2]): [
        {
            "question": "<company_name><year>年的<attribute_1>和<attribute_2>分别是多少？",
            "answer": "<company_name><year>年的<attribute_1>和<attribute_2>是<value_1>和<value_2>。"
        },{
            "question": "<company_name><year>年的<attribute_1>和<attribute_2>分别是什么？",
            "answer": "<company_name><year>年的<attribute_1>和<attribute_2>分别是<value_1>和<value_2>。"
        },{
            "question": "<company_name><year>年的<attribute_1>和<attribute_2>分别是什么？",
            "answer": "<company_name><year>年的<attribute_1>是<value_1>，<attribute_2>是<value_2>。"
        }
    ],
    tuple(global_attribute_clusters[3]): [
        {
            "question": "<company_name><year>年的<attribute_1>和<attribute_2>分别是多少元？",
            "answer": "<company_name><year>年的<attribute_1>和<attribute_2>分别是<value_1>元和<value_2>元。"
        },
        {
            "question": "<company_name><year>年的<attribute_1>和<attribute_2>分别是多少元？",
            "answer": "<company_name><year>年的<attribute_1>是<value_1>元，<attribute_2>是<value_2>元。"
        }
    ]
}

default_single_question_template = [
    {
        "question": "<company_name><year>年的<attribute>是什么?",
        "answer": "<company_name><year>年的<attribute>是<value>。"
    },{
        "question": "<year>年，<company_name>的<attribute>是什么?",
        "answer": "<year>年，<company_name><year>年的<attribute>是<value>。"
    },
]

default_double_question_template = [
    {
        "question": "<company_name><year>年的<attribute_1>和<attribute_2>是什么?",
        "answer": "<company_name><year>年的<attribute_1>是<value_1>，<attribute_2>是<value_2>。"
    },{
        "question": "<year>年, <company_name>的<attribute_1>和<attribute_2>分别是什么?",
        "answer": "<year>年, <company_name><year>年的<attribute_1>是<value_1>，<attribute_2>是<value_2>。"
    },
]

special_question_type = {
    "股票简称变更情况": [
        {
            "question": "<year>年，<company_name>的股票简称有变动吗？",
            "answer": "<yes_or_no>，变更前股票简称为<value_1>，变更后为<value_2>。"
        }
    ],
    "法人变更情况": [
        {
            "question": "<company_name><year_1>年和<year_2>年的法人代表有变化吗",
            "yes_answer": "<company_name><year_1>年法人代表为<value_1>，<year_2>年为<value_2>，<company_name><year_1>年和<year_2>年法人代表不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value>，<year_2>年法人代表是<value>，法人代表相同。"
        },{
            "question": "<company_name><year_1>年对比<year_2>年的法人代表是否相同？",
            "yes_answer": "<company_name><year_1>年法人代表为<value_1>，<year_2>年法人代表为<value_2>，<company_name><year_1>年和<year_2>年法人代表不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value>，<year_2>年法人代表是<value>，法人代表相同。"
        },{
            "question": "<company_name><year_1>年和<year_2>年的法人代表一样吗？",
            "yes_answer": "<company_name><year_1>年法人代表为<value_1>，<year_2>年法人代表为<value_2>，<company_name><year_1>年和<year_2>年法人代表不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value>，<year_2>年的法人代表是<value>，法人代相同。"
        },{
            "question": "对比<year_1>年，<year_2>年<company_name>的法定代表人是否相同?",
            "yes_answer": "<company_name><year_1>年法人代表为<value_1>，<year_2>年法人代表为<value_2>，对比<year_1>年，<company_name><year_2>年法人代表不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value>，<year_2>年的法人代表是<value>，法人代表相同。"
        },{
            "question": "对比<year_1>年和<year_2>年，<company_name>的法定代表人是否相同?",
            "yes_answer": "<company_name><year_1>年法人代表为<value_1>，<year_2>年法人代表为<value_2>，对比<year_1>年和<year_2>年，<company_name>法人代表不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value>，<year_2>年的法人代表是<value>，对比<year_1>年和<year_2>年，<company_name>法人代表相同。"
        },{
            "question": "<company_name>对比<year_1>年和<year_2>年法定代表人是否相同?",
            "yes_answer": "<company_name><year_1>年法人代表为<value_1>，<year_2>年法人代表为<value_2>，对比<year_1>年和<year_2>年，<company_name>法人代表不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value>，<year_2>年的法人代表是<value>，<year_1>年和<year_2>年法人代表相同。"
        },{
            "question": "请问，<company_name>的法定代表人在<year_1>和<year_2>是否相同？",
            "yes_answer": "<company_name><year_1>年法人代表为<value_1>，<year_2>年法人代表为<value_2>，在<year_1>年和<year_2>年，<company_name>法人代表不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value>，<year_2>年的法人代表是<value>，<year_1>年和<year_2>年法人代表相同。"
        },{
            "question": "<company_name><year_1>年与<year_2>年的法人代表是否发生不同？",
            "yes_answer": "<company_name><year_1>年法人代表为<value_1>，<year_2>年法人代表为<value_2>，<company_name><year_1>年和<year_2>年法人代表不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value>，<year_2>年法人代表是<value>，法人代表相同。"
        }, {
            "question": "<company_name><year_1>年的法定代表人对比<year_2>年是否相同?",
            "yes_answer": "<company_name><year_1>年法人代表为<value_1>，<year_2>年法人代表为<value_2>，对比<year_1>年和<year_2>年，<company_name>法人代表不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value>，<year_2>年的法人代表是<value>，<year_1>年对比<year_2>年法人代表相同。"
        }
    ],
    "法人三年变更情况": [
        {
            "question": "2019-2021年间<company_name>的法人代表有变化吗",
            "yes_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，法人代表不同。",
            "no_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，法人代表相同。"
        },{
            "question": "<company_name>在2019年至2021年期间，法定代表人是否都是相同的？",
            "yes_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2019-2021期间法人代表不同。",
            "no_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2019-2021期间法人代表相同。",
        },{
            "question": "在2019年至2021年期间，<company_name>法定代表人是否有都是相同的情况？",
            "yes_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2019-2021期间法人代表不同。",
            "no_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2019-2021期间法人代表相同。",
        }, {
            "question": "请问在2019-2021年期间，<company_name>的法定代表人是否都是相同的情况？",
            "yes_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2019-2021期间法人代表不同。",
            "no_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2019-2021期间法人代表相同。",
        }, {
            "question": "在2019-2021年期间，<company_name>的法定代表人是否都相同？",
            "yes_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2019-2021期间法人代表不同。",
            "no_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2019-2021期间法人代表都相同。",
        }, {
            "question": "<company_name>在2019-2021年间的法定代表人是不是相同的？",
            "yes_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2019-2021期间法人代表是不同。",
            "no_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2019-2021期间法人代表是相同。",
        }, {
            "question": "<company_name>在2019-2021年期间的法定代表人是否都相同？",
            "yes_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2019-2021期间法人代表不同。",
            "no_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2019-2021期间法人代表都相同。",
        }, {
            "question": "<company_name>2021年的法定代表人和前两年相比是否都相同？",
            "yes_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2021年与前两年相比法人代表不同。",
            "no_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2021年与前两年相比法人代表都相同。",
        }, {
            "question": "<company_name>2021年的法定代表人和上两年相比是否都相同？",
            "yes_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2021年与上两年相比法人代表不同。",
            "no_answer": "<company_name>2019年的法人代表为<value_1>，2020年的法人代表为<value_2>，2021年的法人代表为<value_3>，<company_name>2021年与上两年相比法人代表都相同。",
        }
    ],
    "法人去年变化": [
        {
            "question": "<company_name><year_1>年的法定代表人与上年相比相同吗？",
            "yes_answer": "<company_name><year_1>年的法人代表是<value_1>，<year_2>年的法人代表是<value_2>，<company_name><year_1>年的法定代表人与上年相比不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value_1>，<year_2>年的法人代表是<value_2>，<company_name><year_1>年的法定代表人与上年相比相同。"
        },{
            "question": "<company_name><year_1>年的法定代表人与去年相比一样吗？",
            "yes_answer": "<company_name><year_1>年的法人代表是<value_1>，<year_2>年的法人代表是<value_2>，<company_name><year_1>年的法定代表人与去年相比不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value_1>，<year_2>年的法人代表是<value_2>，<company_name><year_1>年的法定代表人与去年相比相同。"
        },{
            "question": "<company_name><year_1>年的法定代表人与上一年相比有变化吗？",
            "yes_answer": "<company_name><year_1>年的法人代表是<value_1>，<year_2>年的法人代表是<value_2>，<company_name><year_1>年的法定代表人与去年不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value_1>，<year_2>年的法人代表是<value_2>，<company_name><year_1>年的法定代表人与去年相比相同。"
        } 
    ],
    "法人前年变化": [
        {
            "question": "<company_name><year_1>年的法定代表人与前年相比相同吗？",
            "yes_answer": "<company_name><year_1>年的法人代表是<value_1>，<year_2>年的法人代表是<value_2>，<company_name><year_1>年的法定代表人与前年相比不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value_1>，<year_2>年的法人代表是<value_2>，<company_name><year_1>年的法定代表人与前年相比相同。"
        },{
            "question": "<company_name><year_1>年的法定代表人与前年相比一样吗？",
            "yes_answer": "<company_name><year_1>年的法人代表是<value_1>，<year_2>年的法人代表是<value_2>，<company_name><year_1>年的法定代表人与前年相比不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value_1>，<year_2>年的法人代表是<value_2>，<company_name><year_1>年的法定代表人与前年相比相同。"
        },{
            "question": "<company_name><year_1>年的法定代表人与前年相比有变化吗？",
            "yes_answer": "<company_name><year_1>年的法人代表是<value_1>，<year_2>年的法人代表是<value_2>，<company_name><year_1>年的法定代表人与前年有不同。",
            "no_answer": "<company_name><year_1>年的法人代表是<value_1>，<year_2>年的法人代表是<value_2>，<company_name><year_1>年的法定代表人与前年相同。"
        } 
    ]
}

def single_attribute_template():
    template_dict = defaultdict(lambda :default_single_question_template)
    for columns, v in company_info_single_attribute_template.items():
        for column in columns:
            template_dict[column] = v
    return template_dict

def double_attribute_template():
    template_dict = defaultdict(lambda :default_double_question_template)
    for columns, v in company_info_double_attribute_template.items():
        for column in columns:
            template_dict[column] = v
    return template_dict

# original dataloader

def load_json_tables():
    """
    加载较为格式化的部分表格,大概能占一半
    """
    res = defaultdict(lambda :{})
    for file in Path("data/processed_excels").rglob("*.json"):
        stock_code = os.path.basename(file).replace(".json", "").split('__')[-4]
        year = os.path.basename(file).replace(".json", "").split('__')[-2].replace("年", "")
        data_json = json.load(open(file, 'r'))
        if '公司信息' in data_json:
            valid = True
            company_basic_info = data_json['公司信息']
            info_dict = {}
            for idx in range(len(company_basic_info)):
                line_list = company_basic_info[idx]
                if idx == 0:
                    if not ('股票简称' in line_list and '股票代码' in line_list):
                        valid = False
                        break
                    else:
                        name_index, code_index = line_list.index("股票简称"), line_list.index("股票代码")
                        name = ' '.join(line_list[name_index:code_index]).replace("股票简称", "").strip()
                        code = ' '.join(line_list[code_index:]).replace("股票代码", "").strip()
                        info_dict.update({
                            "股票简称": name,
                            "股票代码": code
                        })
                elif len([col for col in line_list if col != '']) != 2:
                    valid = False
                    break
                else:
                    filtered_list = [item for item in line_list if item != '']
                    column_name = filtered_list[0]
                    column_value = filtered_list[1]
                    info_dict[column_name] = column_value
            if valid:
                res[stock_code][year] = info_dict
    return res

def load_metadata():
    res = defaultdict(lambda :{})
    for file in Path("data/processed_excels").rglob("*.json"):
        stock_code = os.path.basename(file).replace(".json", "").split('__')[-4]
        year = os.path.basename(file).replace(".json", "").split('__')[-2].replace("年", "")
        full_name = os.path.basename(file).replace(".json", "").split('__')[1]
        short_name = os.path.basename(file).replace(".json", "").split('__')[-3]
        res[stock_code][year] = {
            "full_name": full_name,
            "short_name": short_name
        }
    return res

global_table = load_json_tables()
global_stock_code_list = list(global_table.keys())
global_metadata = load_metadata()
global_single_attribute_template = single_attribute_template()
global_double_attribute_template = double_attribute_template()

# data augmentation

def augment_company_info_dict(company_info, keys_to_keep):
    for key in company_info:
        if key not in keys_to_keep and np.random.uniform(0, 1) < 0.03:
            company_info[key] = ''
    return company_info

def augment_data(company_info_by_year, stock_code, keys_to_keep=None):
    if keys_to_keep is None:
        keys_to_keep = ['年份']
    else:
        keys_to_keep += ['年份']
    data_list = []
    company_info_by_year = deepcopy(company_info_by_year)
    for year, company_info in company_info_by_year.items():
        company_info.update({
            "年份": year
        })
        data_list.append(augment_company_info_dict(company_info, keys_to_keep))
    result_without_noise = data_list
    if np.random.uniform(0, 1) > 0.95:
        noise_stock_code = np.random.choice(global_stock_code_list, 1)[0]
        if noise_stock_code != stock_code:
            year_to_choose = np.random.choice(list(global_table[noise_stock_code].keys()), 1)[0]
            noise_json_data = {"年份": year_to_choose, **global_table[noise_stock_code][year_to_choose]}
            data_list.append(augment_company_info_dict(noise_json_data, keys_to_keep))
    np.random.shuffle(data_list)
    return data_list


def random_placeholder():
    candidate_list = [' ', '  ', '\t', '   ', '\t\t', '\t ', ' \t']
    return np.random.choice(candidate_list, 1, p=[0.8, 0.06, 0.06, 0.05, 0.01, 0.01, 0.01])[0]


def random_next_line():
    return np.random.choice(['\n', random_placeholder()], 1, p=[0.95, 0.05])[0]


def random_company_name(stock_code, year):
    if np.random.uniform(0, 1) <= 0.5:
        return global_metadata[stock_code][year]['full_name']
    else:
        return global_metadata[stock_code][year]['short_name']

def random_alias(attributes):
    alias = []
    for attribute in attributes:
        if np.random.uniform(0, 1) < 0.5 and attribute in company_attribute_alias:
            alias.append(np.random.choice(company_attribute_alias[attribute], 1)[0].replace("（如有）", ""))
        else:
            alias.append(attribute)
    return alias


def cluster_attributes(attributes):
    cluster_anchors = global_attribute_clusters
    clusters = [[] for _ in range(5)]
    for attribute in attributes:
        added = False
        for idx in range(len(cluster_anchors)):
            if attribute in cluster_anchors[idx]:
                added = True
                clusters[idx].append(attribute)
                break
        if not added:
            clusters[-1].append(attribute)
    return [cluster for cluster in clusters if len(cluster) >= 2]

# serilize table
def serilize_json_data(augmented_data):
    final_result_serilization = ""
    for data_point in augmented_data:
        serilized_string = ""
        if "股票简称" in data_point and "股票代码" in data_point:
            if np.random.uniform(0, 1) < 0.95:
                serilized_string += "股票简称"+ random_placeholder() + data_point['股票简称']
                serilized_string += random_placeholder() + "股票代码" + random_placeholder() + data_point['股票代码'] + "\n"
                data_point.pop('股票简称')
                data_point.pop('股票代码')
        if np.random.uniform(0, 1) < 0.95:
            for k, v in data_point.items():
                serilized_string += k + random_placeholder() + str(v) + random_next_line()
        else:
            iter_object = list(data_point.items())
            np.random.shuffle(iter_object)
            for k, v in iter_object:
                serilized_string += k + random_placeholder() + str(v) + random_next_line()
        final_result_serilization += serilized_string + "\n"
    return final_result_serilization


# data generation
def decide_question_generator(company_info_by_year, stock_code, special=True):
    random_number = np.random.uniform(low=0, high=1)
    if random_number <= 0.2 and special:
        return decide_special_question_type(company_info_by_year=company_info_by_year, stock_code=stock_code)
    elif random_number <= 0.75:
        return generate_single_attribute_questions(company_info_by_year, stock_code)
    else:
        return generate_double_attribute_questions(company_info_by_year, stock_code)


def generate_single_attribute_questions(company_info_by_year, stock_code):
    years = list(company_info_by_year.keys())
    chosen_year = np.random.choice(years, 1)[0]
    company_info_single_year = company_info_by_year[chosen_year]
    attributes = list(company_info_single_year.keys())
    chosen_attribute = np.random.choice(attributes, 1)[0]
    invalid_answers = {
        '无', '不适用', '无变更', '-', '/', '——', '--', '报告期内无变更'
    }
    if company_info_single_year[chosen_attribute] in invalid_answers:
        return None
    template = np.random.choice(global_single_attribute_template[chosen_attribute], 1)[0]
    attribute_alias = random_alias([chosen_attribute])[0]
    company_name = random_company_name(stock_code=stock_code, year=chosen_year)
    question = template['question'].replace("<company_name>", company_name).\
            replace("<year>", chosen_year).replace("<attribute>", attribute_alias)
    augmented_data = augment_data({chosen_year: company_info_single_year}, stock_code, [chosen_attribute])
    serilized_data = serilize_json_data(augmented_data)
    answer = template['answer'].replace("<company_name>", company_name).\
            replace("<year>", chosen_year).replace("<attribute>", attribute_alias).\
            replace("<value>", company_info_single_year[chosen_attribute])
    data_point = {
        "prompt": prompt + serilized_data + question,
        "response": answer
    }
    return data_point

def generate_double_attribute_questions(company_info_by_year, stock_code):
    years = list(company_info_by_year.keys())
    chosen_year = np.random.choice(years, 1)[0]
    company_info_single_year = company_info_by_year[chosen_year]
    attribute_clusters = cluster_attributes(list(company_info_single_year.keys()))
    chosen_cluster = attribute_clusters[np.random.randint(0, len(attribute_clusters))]
    attributes = np.random.choice(chosen_cluster, 2, replace=False).tolist()
    invalid_answers = {
        '无', '不适用', '无变更', '-', '/', '——', '--', '报告期内无变更'
    }
    if company_info_single_year[attributes[0]] in invalid_answers or company_info_single_year[attributes[1]] in invalid_answers:
        return
    candidate_templates = global_double_attribute_template[attributes[0]]
    if len(candidate_templates) == 0:
        return
    template = np.random.choice(candidate_templates, 1)[0]
    alias_attributes = random_alias(attributes)
    company_name = random_company_name(stock_code=stock_code, year=chosen_year)
    question = template['question'].replace("<company_name>", company_name).\
            replace("<year>", chosen_year).replace("<attribute_1>", alias_attributes[0]).\
            replace("<attribute_2>", alias_attributes[1])
    augmented_data = augment_data({chosen_year: company_info_single_year}, stock_code, attributes)
    serilized_data = serilize_json_data(augmented_data)
    answer = template['answer'].replace("<company_name>", company_name).\
            replace("<year>", chosen_year).replace("<attribute_1>", alias_attributes[0]).\
                replace("<value_1>", company_info_single_year[attributes[0]]).\
                replace("<attribute_2>", alias_attributes[1]).\
                replace("<value_2>", company_info_single_year[attributes[1]])
    data_point = {
        "prompt": prompt + serilized_data + question,
        "response": answer
    }
    return data_point


def decide_special_question_type(company_info_by_year, stock_code):
    without_change_answers = {
        '无', '不适用', '无变更', '-', '/', '——', '--', '报告期内无变更'
    }
    def brief_name_change(company_info_by_year):
        company_info_single_year = list(company_info_by_year.values())[0]
        year = list(company_info_by_year.keys())[0]
        if "变更前的股票简称（如有）" in company_info_single_year:
            prev_attribute_name = "变更前的股票简称（如有）"
        elif "变更前的股票简称" in company_info_single_year:
            prev_attribute_name = "变更前的股票简称"
        else:
            prev_attribute_name = None
        if "变更后的股票简称（如有）" in company_info_single_year:
            post_attribute_name = "变更后的股票简称（如有）"
        elif "变更后的股票简称" in company_info_single_year:
            post_attribute_name = "变更后的股票简称"
        else:
            post_attribute_name = None
        # TODO: 这里的问题:根本没有变更前的股票简称这一个key
        if prev_attribute_name is not None and post_attribute_name is not None:
            if company_info_single_year[prev_attribute_name] in without_change_answers \
                or company_info_single_year[post_attribute_name] in without_change_answers:
                yes_or_no = False
            else:
                yes_or_no = True
            template = np.random.choice(special_question_type['股票简称变更情况'], 1)[0]
            if yes_or_no:
                answer = template['answer'].replace("<yes_or_no>", "存在变更").\
                    replace("<value_1>", company_info_single_year[prev_attribute_name]).\
                    replace("<value_2>", company_info_single_year[post_attribute_name])
            else:
                answer = "股票简称不存在变更"
            # TODO: HERE
            question = template['question'].replace("<company_name>", random_company_name(stock_code, year)).replace("<year>", year)
            augmented_data = augment_data(company_info_by_year, stock_code, keys_to_keep=[prev_attribute_name, post_attribute_name])
            serilized_data = serilize_json_data(augmented_data)
            data_point = {
                "prompt": prompt + serilized_data + question,
                "response": answer
            } 
            return data_point
        else:
            return None
    global global_same_counter, global_different_counter
    def generate_law_representer_questions(company_info_by_year, stock_code):
        global global_same_counter, global_different_counter
        rand_number = np.random.uniform(0, 1)
        if  rand_number <= 0.5 and len(company_info_by_year) == 3:
            keys = list(company_info_by_year.keys())                
            assert "2019" in keys and "2020" in keys and "2021" in keys, "年份错误"
            valid = True
            law_representers = []
            keys = sorted(keys)
            for key in keys:
                if "公司的法定代表人" in company_info_by_year[key]:
                    law_representers.append(company_info_by_year[key]['公司的法定代表人'].replace(" ","").replace("（代）","").replace("（暂代）",""))
                elif "法定代表人" in company_info_by_year[key]:
                    law_representers.append(company_info_by_year[key]['法定代表人'].replace(" ","").replace("（代）","").replace("（暂代）",""))
                elif "法人代表" in company_info_by_year[key]:
                    law_representers.append(company_info_by_year[key]['法人代表'].replace(" ","").replace("（代）","").replace("（暂代）",""))
                else:
                    valid = False
                    break
            if valid:
                template = np.random.choice(special_question_type['法人三年变更情况'], 1)[0]
                company_name = random_company_name(stock_code, '2021')
                question = template['question'].replace("<company_name>", company_name)
                agumented_data = augment_data(company_info_by_year, stock_code, keys_to_keep=["公司的法定代表人", "法定代表人", "法人代表"])
                serilized_data = serilize_json_data(agumented_data)
                # company_name = random_company_name(stock_code, '20')
                yes_or_no = law_representers[0] == law_representers[1] and law_representers[1] == law_representers[2]
                if yes_or_no:
                    if global_different_counter * 1.2 < global_same_counter:
                        return decide_question_generator(company_info_by_year, stock_code, special=False)
                    global_same_counter += 1
                    answer = template['no_answer'].replace("<value_1>", law_representers[0])\
                        .replace("<value_2>", law_representers[1])\
                        .replace("<value_3>", law_representers[2])\
                        .replace("<company_name>", company_name)
                else:
                    global_different_counter += 1
                    answer = template['yes_answer'].replace("<value_1>", law_representers[0])\
                        .replace("<value_2>", law_representers[1])\
                        .replace("<value_3>", law_representers[2])\
                        .replace("<company_name>", company_name)
                data_point = {
                    "prompt": prompt + serilized_data + question,
                    "response": answer
                }
                return data_point
            else:
                return decide_question_generator(company_info_by_year, stock_code, special=False)
        elif rand_number <= 0.7:
            keys = list(company_info_by_year.keys())
            if len(keys) >= 2:
                keys = np.random.choice(keys, 2, replace=False)
                keys = sorted(keys)
                valid = True
                law_representers = []
                for key in keys:
                    if "公司的法定代表人" in company_info_by_year[key]:
                        law_representers.append(company_info_by_year[key]['公司的法定代表人'].replace("（代）","").replace("（暂代）",""))
                    elif "法定代表人" in company_info_by_year[key]:
                        law_representers.append(company_info_by_year[key]['法定代表人'].replace("（代）","").replace("（暂代）",""))
                    elif "法人代表" in company_info_by_year[key]:
                        law_representers.append(company_info_by_year[key]['法人代表'].replace(" ","").replace("（代）","").replace("（暂代）",""))
                    else:
                        valid = False
                        break
                if valid:
                    template = np.random.choice(special_question_type['法人变更情况'], 1)[0]
                    company_name = random_company_name(stock_code, keys[-1])
                    question = template['question'].replace("<company_name>", company_name)\
                        .replace("<year_1>", keys[0]).replace("<year_2>", keys[1])
                    agumented_data = augment_data({k:company_info_by_year[k] for k in keys}, stock_code, keys_to_keep=["公司的法定代表人", "法定代表人", "法人代表"])
                    serilized_data = serilize_json_data(agumented_data)
                    yes_or_no = law_representers[0] == law_representers[1]
                    if yes_or_no:
                        if global_different_counter * 1.2 < global_same_counter:
                            return decide_question_generator(company_info_by_year, stock_code, special=False)
                        global_same_counter += 1
                        answer = template['no_answer']\
                            .replace("<year_1>", keys[0])\
                            .replace("<year_2>", keys[1])\
                            .replace("<company_name>", company_name)\
                            .replace("<value>", law_representers[0])
                        # answer = "法定代表人没有发生变更，{}{}年和{}年的法定代表人均为{}".format(company_name, keys[0], keys[1], law_representers[0])
                    else:
                        global_different_counter += 1
                        answer = template['yes_answer'].replace("<yes_or_no>", "法定代表人发生了变化")\
                            .replace("<value_1>", law_representers[0])\
                            .replace("<value_2>", law_representers[1])\
                            .replace("<year_1>", keys[0])\
                            .replace("<year_2>", keys[1])\
                            .replace("<company_name>", company_name)
                    data_point = {
                        "prompt": prompt + serilized_data + question,
                        "response": answer
                    }
                    # print(data_point['prompt'])
                    # print()
                    # print(data_point['response'])
                    # print()
                    return data_point
            else:
                return decide_question_generator(company_info_by_year, stock_code, special=False)
        elif rand_number <= 0.95:
            keys = list(company_info_by_year.keys())
            keys = sorted(keys)
            if "2019" in keys and "2021" in keys:
                valid = True
                law_representers = []
                for key in ['2019', '2021']:
                    if "公司的法定代表人" in company_info_by_year[key]:
                        law_representers.append(company_info_by_year[key]['公司的法定代表人'].replace("（代）","").replace("（暂代）",""))
                    elif "法定代表人" in company_info_by_year[key]:
                        law_representers.append(company_info_by_year[key]['法定代表人'].replace("（代）","").replace("（暂代）",""))
                    elif "法人代表" in company_info_by_year[key]:
                        law_representers.append(company_info_by_year[key]['法人代表'].replace(" ","").replace("（代）","").replace("（暂代）",""))
                    else:
                        valid = False
                        break
                if valid:
                    template = np.random.choice(special_question_type['法人前年变化'], 1)[0]
                    company_name = random_company_name(stock_code, keys[-1])
                    question = template['question'].replace("<company_name>", company_name)\
                        .replace("<year_1>", '2021')
                    agumented_data = augment_data({k:company_info_by_year[k] for k in ['2019', '2021']}, stock_code, keys_to_keep=["公司的法定代表人", "法定代表人", "法人代表"])
                    serilized_data = serilize_json_data(agumented_data)
                    yes_or_no = law_representers[0] == law_representers[1]
                    if yes_or_no:
                        if global_different_counter * 1.2 < global_same_counter:
                            return decide_question_generator(company_info_by_year, stock_code, special=False)
                        global_same_counter += 1
                        answer = template['no_answer']\
                            .replace("<year_1>", '2021')\
                            .replace("<year_2>", '2019')\
                            .replace("<company_name>", company_name)\
                            .replace("<value_1>", law_representers[1])\
                            .replace("<value_2>", law_representers[0])
                    else:
                        global_different_counter += 1
                        answer = template['yes_answer'].replace("<yes_or_no>", "法定代表人发生了变化")\
                            .replace("<value_1>", law_representers[1])\
                            .replace("<value_2>", law_representers[0])\
                            .replace("<year_1>", '2021')\
                            .replace("<year_2>", '2019')\
                            .replace("<company_name>", company_name)
                    data_point = {
                            "prompt": prompt + serilized_data + question,
                            "response": answer
                    }
                    # print(data_point['prompt'])
                    # print()
                    # print(data_point['response'])
                    # print()
                    return data_point
            else:
                return decide_question_generator(company_info_by_year, stock_code, special=False)
        else:
            keys = list(company_info_by_year.keys())
            keys = sorted(keys)
            if len(keys) >= 2 and (('2019' in keys and '2020' in keys) or ('2020' in keys and '2021' in keys)):
                if len(keys) == 3:
                    year = np.random.choice([2020, 2021], 1)[0]
                    last_year, year = str(year - 1), str(year)
                else:
                    last_year, year = sorted(keys)
                valid = True
                law_representers = []
                for key in [last_year, year]:
                    if "公司的法定代表人" in company_info_by_year[key]:
                        law_representers.append(company_info_by_year[key]['公司的法定代表人'].replace("（代）","").replace("（暂代）",""))
                    elif "法定代表人" in company_info_by_year[key]:
                        law_representers.append(company_info_by_year[key]['法定代表人'].replace("（代）","").replace("（暂代）",""))
                    elif "法人代表" in company_info_by_year[key]:
                        law_representers.append(company_info_by_year[key]['法人代表'].replace(" ","").replace("（代）","").replace("（暂代）",""))
                    else:
                        valid = False
                        break
                if valid:
                    template = np.random.choice(special_question_type['法人去年变化'], 1)[0]
                    company_name = random_company_name(stock_code, keys[-1])
                    question = template['question'].replace("<company_name>", company_name)\
                        .replace("<year_1>", year)
                    agumented_data = augment_data({k:company_info_by_year[k] for k in [last_year, year]}, stock_code, keys_to_keep=["公司的法定代表人", "法定代表人", "法人代表"])
                    serilized_data = serilize_json_data(agumented_data)
                    yes_or_no = law_representers[0] == law_representers[1]
                    if yes_or_no:
                        if global_different_counter * 1.2 < global_same_counter:
                            return decide_question_generator(company_info_by_year, stock_code, special=False)
                        global_same_counter += 1
                        answer = template['no_answer']\
                            .replace("<year_1>", year)\
                            .replace("<year_2>", last_year)\
                            .replace("<company_name>", company_name)\
                            .replace("<value_1>", law_representers[1])\
                            .replace("<value_2>", law_representers[0])
                    else:
                        global_different_counter += 1
                        answer = template['yes_answer'].replace("<yes_or_no>", "法定代表人发生了变化")\
                            .replace("<value_1>", law_representers[1])\
                            .replace("<value_2>", law_representers[0])\
                            .replace("<year_1>", year)\
                            .replace("<year_2>", last_year)\
                            .replace("<company_name>", company_name)
                    data_point = {
                        "prompt": prompt + serilized_data + question,
                        "response": answer
                    }
                    # print(data_point['prompt'])
                    # print()
                    # print(data_point['response'])
                    # print()
                    return data_point
            else:
                return decide_question_generator(company_info_by_year, stock_code, special=False)
    
    if len(company_info_by_year) == 1:
        return brief_name_change(company_info_by_year)
    else:
        # 这类信息很少, 优先生成这种
        for company_info_single_year in company_info_by_year:
            data_point = brief_name_change({company_info_single_year: company_info_by_year[company_info_single_year]})
            if data_point is not None:
                return data_point
        law_representer_data_point = generate_law_representer_questions(company_info_by_year, stock_code)
        if law_representer_data_point is not None:
            return law_representer_data_point
        else:
            return decide_question_generator(company_info_by_year, stock_code, special=False)


def main():
    company_pool = list(global_table)
    company_chosen = np.random.choice(company_pool, 10000)
    with open(os.path.join(os.path.dirname(__file__),'./data/company_info.json'), 'w') as fp:
        for company in company_chosen:
            question = decide_question_generator(global_table[company], company)
            if question is not None:
                fp.write(json.dumps(question, ensure_ascii=False) + "\n") 


if __name__ == '__main__':
    main()