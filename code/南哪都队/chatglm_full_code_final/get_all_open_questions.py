import json
import whoosh
from whoosh.index import create_in
from whoosh.fields import *
import jieba.analyse as analyse
import jieba
import os



def load_all_questions():
    questions = [json.loads(line)['question'] for line in open('data/C-list-question.json', 'r').readlines()]
    classes = [json.loads(line) for line in open('finetune/table_qa/data/classification.jsonl').readlines()]
    for q, c in zip(questions, classes):
        if c['类型'] == "开放问题":
            c['问题'] = q
            print(json.dumps(c, ensure_ascii=False))


def generate_indices():
    # 构建索引
    schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)
    ix = create_in("indexdir", schema)
    writer = ix.writer()
    writer.add_document(title=u"First document", path=u"/a",content=u"This is the first document we've added!")
    writer.add_document(title=u"Second document", path=u"/b", content=u"The first second one is even more interesting!")
    writer.commit()
    # 搜索
    from whoosh.qparser import QueryParser
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema).parse("first")
        results = searcher.search(query)
        print(results[0])


def annotate_open_questions():
    json_data = [json.loads(data) for data in open('documents/open_questions.txt', 'r').readlines()]
    year_pattern = r"(2019|2020|2021)年度?"
    brackets_pattern = r'[\(（\)）]'
    
    annotate_cache = {}
    annotate_path = "documents/open_questions_annotated.txt"
    if os.path.exists(annotate_path):
        json_lines = [json.loads(line) for line in open(annotate_path, 'r').readlines()]
        for line in json_lines:
            question = line['问题']
            answer = line['关键词']
            annotate_cache[question] = answer
        progress = len(json_lines)
        mode = 'a'
    else:
        progress = 0
        mode = 'w'
    with open(annotate_path, mode) as fp:
        for json_item in json_data[progress:]:
            keywords = []
            question = json_item['问题']
            company = json_item['公司名称']
            company = re.sub(brackets_pattern, "", company)
            question = re.sub(brackets_pattern, "", question)
            question = question.replace(company, "{company}")
            question = re.sub(year_pattern, "{year}", question)
            if question in annotate_cache:
                keywords = annotate_cache[question]
            else:
                print(f"{progress}/213",question)
                keyword = input("关键词：")
                while keyword != "":
                    keywords.append(keyword)
                    keyword = input("关键词：")
                print()
                annotate_cache[question] = keywords
            fp.write(json.dumps({"问题": question, "关键词": keywords}, ensure_ascii=False) + "\n")
            fp.flush()
            progress += 1


# annotate_open_questions()
# load_all_questions()  