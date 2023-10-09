import os
import json
from pathlib import Path
import pandas as pd


def extract_all_company_name():
    """_summary_
    从pdf名字种提取所有的公司简称、股票代码、年份等document的metadata
    Returns:
        _type_: _description_
    """
    alltxt_path = os.path.join(os.path.dirname(__file__), "../../data/alltxt")
    result = []
    for file in Path(alltxt_path).rglob("*.txt"):
        basic_info = os.path.basename(file).split("__")[:-1]
        result.append(basic_info)
    return pd.DataFrame(result, columns=["date", "full_name", "stock_code", "short_name", "year"])

def load_questions():
    """_summary_
    加载所有的问题
    """
    quests = []
    with open(os.path.join(os.path.dirname(__file__), "../../data/C-list-question.json"), 'r') as fp:
        for line in fp.readlines():
            quests.append(json.loads(line)['question'])
    return quests


class EntityExtractor:
    def __init__(self) -> None:
        self.full_company_name, self.short_company_name = self.load_data()

    def load_data(self):
        company_names = extract_all_company_name()[['full_name', 'short_name', 'stock_code']]
        full_company_name = company_names['full_name'].tolist()
        short_company_name = company_names['short_name'].tolist()
        stock_code = company_names['stock_code'].tolist()
        l = len(company_names)
        return {full_company_name[idx]:stock_code[idx] for idx in range(l)}, \
            {short_company_name[idx]:stock_code[idx] for idx in range(l)}


    def query_company_names(self, questions):
        query_result = []
        find_count = 0
        for question in questions:
            find = False
            for full_name in self.full_company_name:
                if full_name in question:
                    query_result.append(full_name)
                    find = True
                    break
            if not find:
                for short_name in self.short_company_name:
                    if short_name in question:
                        query_result.append(short_name)
                        find = True
                        break
            if not find:
                query_result.append(f"无")
            else:
                find_count += 1
        return query_result


def extract_by_rule():
    questions = load_questions()
    dataset = []
    company_names = EntityExtractor().query_company_names(questions)
    for idx, question in enumerate(questions):
        if ("2019" in question or "2020" in question or "2021" in question) and company_names[idx] == "无":
            continue
        dataset.append({
            "response": company_names[idx],
            "prompt": f"提取以下句子中的公司名称，没有则回答无: {question}",
            "history": [] 
        })
    return dataset


def classify_by_rule():
    questions = load_questions()
    dataset = []
    company_names = EntityExtractor().query_company_names(questions)
    for idx, question in enumerate(questions):
        if ("2019" in question or "2020" in question or "2021" in question) and company_names[idx] == "无":
            continue
        dataset.append({
            "response": "是" if company_names[idx] == "无" else "否",
            "prompt": f"判断以下问题是否是一个金融常识问题:{question}",
            "history": []
        })
    return dataset


if __name__ == '__main__':
    dataset = extract_by_rule()
    with open(os.path.join(os.path.dirname(__file__), "../../data/temp/entity_extraction_train.json"), 'w') as fp:
        for data in dataset[:-500]:
            fp.write(json.dumps(data, ensure_ascii=False) + "\n")
    with open(os.path.join(os.path.dirname(__file__), "../../data/temp/entity_extraction_dev.json"), 'w') as fp:
        for data in dataset[-500:]:
            fp.write(json.dumps(data, ensure_ascii=False) + "\n")
    dataset = classify_by_rule()
    with open(os.path.join(os.path.dirname(__file__), "../../data/temp/classify_train.json"), 'w') as fp:
        for data in dataset[:-500]:
            fp.write(json.dumps(data, ensure_ascii=False) + "\n")
    with open(os.path.join(os.path.dirname(__file__), "../../data/temp/classify_dev.json"), 'w') as fp:
        for data in dataset[-500:]:
            fp.write(json.dumps(data, ensure_ascii=False) + "\n")