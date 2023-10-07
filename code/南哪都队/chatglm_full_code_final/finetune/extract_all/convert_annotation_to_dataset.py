import json
import sys
sys.path.append("finetune")
from extract.data_utils import load_questions


def load_annotations():
    result = []
    with open("annotated_with_digits.jsonl", 'r') as fp:
        lines = fp.readlines()
        for line in lines:
            result.append(json.loads(line))
    return result

def convert():
    annotations = load_annotations()
    questions = load_questions()[:len(annotations)]
    dataset = []
    for idx in range(len(annotations)):
        dataset.append({
            "prompt": f"提取以下句子的问题类型、关键词、年份、公司名称、如果需要计算返回表达式，以json形式回答:{questions[idx]}",
            "response": json.dumps(annotations[idx], ensure_ascii=False),
            "history": []
        })
    return dataset


def dump_dataset(obj, name):
    with open(f"data/temp/{name}", 'w') as fp:
        for ob in obj:
            fp.write(json.dumps(ob, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    dataset = convert()
    dump_dataset(dataset[:250], "extract_all.json")
    dump_dataset(dataset[:250], "extract_all_train.json")
    dump_dataset(dataset[250:], "extract_all_dev.json")