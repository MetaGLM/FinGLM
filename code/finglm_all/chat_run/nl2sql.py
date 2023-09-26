# - **输入问题**。
# - **Prompt 准备**：根据问题，使用正则、相似度(m3e、text2vec等)、向量或树检索等方式生成对应的 prompt。
# - **生成查询语句**：根据 GPU 使用率，选择模型、API 或正则方式生成查询语句。
# - **查询数据库**：返回查询结果。
# - **答案生成**：利用问题和查询结果，使用 API 或原始 glm2-6b 模型生成答案。
import json
import re
import sys
import zhipuai
from text2vec import SentenceModel, cos_sim, semantic_search
from transformers import AutoModel
import torch
from transformers import AutoTokenizer
from peft import PeftModel

# Constants
COLUMNS = [
    '证券代码', '证券简称', '电子信箱', '注册地址', '办公地址', '企业名称', '外文名称', '外文名称缩写', '公司网址',
    '法定代表人', '研发人员人数', '职工总人数', '销售人员人数', '技术人员人数', '硕士员工人数', '博士及以上的员工人数',
    '货币资金', '应收款项融资', '存货', '其他非流动金融资产', '固定资产', '无形资产', '资产总额', '应付职工薪酬', '负债合计',
    '交易性金融资产', '应收票据', '应收账款', '流动资产', '在建工程', '商誉', '其他流动资产', '其他非流动资产', '非流动资产',
    '短期借款', '应付票据', '应付账款', '应交税费', '长期借款', '流动负债', '非流动负债', '股本', '营业总收入', '营业收入',
    '营业总成本', '营业成本', '销售费用', '管理费用', '研发费用', '财务费用', '投资收益', '营业外收入', '营业外支出',
    '营业利润', '利润总额', '净利润', '审计意见', '关键审计事项', '主要会计数据和财务指标', '主要销售客户', '主要供应商',
    '研发投入', '现金流', '资产及负债状况', '重大资产和股权出售', '主要控股参股公司分析', '公司未来发展的展望',
    '合并报表范围发生变化的情况说明', '聘任、解聘会计师事务所情况', '面临退市情况', '破产重整相关事项', '重大诉讼、仲裁事项',
    '处罚及整改情况', '公司及其控股股东、实际控制人的诚信状况', '重大关联交易', '重大合同及其履行情况', '重大环保问题',
    '社会责任情况', '公司董事、监事、高级管理人员变动情况', '公司员工情况', '非标准审计报告的说明', '公司控股股东情况',
    '申万行业', '行业名称', '营业成本率', '投资收益占营业收入比率', '管理费用率', '财务费用率', '三费比重', '企业研发经费占费用比例',
    '企业研发经费与利润比值', '企业研发经费与营业收入比值', '研发人员占职工人数比例', '企业硕士及以上人员占职工人数比例',
    '毛利率', '营业利润率', '流动比率', '速动比率', '资产负债比率', '现金比率', '非流动负债比率', '流动负债比率', '净利润率'
]
COLUMNS_REGEX = '(?:' + '|'.join(COLUMNS) + ')'
DEFAULT_COLUMNS = ['文件名', '年份', '企业名称']

def get_embedder(model_path):
    return SentenceModel(model_name_or_path=model_path)

def get_similar_columns(embedder, question, existing_matches):
    corpus_embeddings = embedder.encode(COLUMNS)
    query_embedding = embedder.encode(question)
    hits = semantic_search(query_embedding, corpus_embeddings, top_k=5)
    print("\n\n======================")
    print('Question:', question)
    # print("\nTop 5 most similar sentences in corpus:")
    hits = hits[0]  # Get the hits for the first query
    for hit in hits:
        column_name = COLUMNS[hit['corpus_id']]
        print(column_name, "(Score: {:.4f})".format(hit['score']))
        if hit['score'] > 0.8 and column_name not in existing_matches:
            existing_matches.append(column_name)
    print("\n\n======================")

    return existing_matches

def process_question(question):
    question = question.replace('总额', '合计')
    matches = re.findall(COLUMNS_REGEX, question)

    # Load the model only once to optimize for performance
    # m3e-base text2vec-base-chinese 等
    embedder = get_embedder('model/emb/m3e-base')
    matches = get_similar_columns(embedder, question, matches)

    return DEFAULT_COLUMNS + matches


def text_to_sql_syntax(sample, text):
    zhipuai.api_key = ""
    sentence = str(sample) + '''
    示例：
    某公司2023年的注册地址是什么？
    回答：【SELECT 注册地址 FROM test WHERE 公司全称 REGEXP '某公司' AND year = '2023';】

    仿照上面的示例，完成下面问题的sql语句书写。问题：''' + text
    response = zhipuai.model_api.invoke(
        model="chatglm_6b",
        temperature=0.1,
        # top_p=0.9,
        prompt=[
            {"role": "user", "content": sentence}]

    )
    tmp = response['data']['choices'][0]['content']
    chekc_tmp = re.search('(?:SELECT|select).*?;', tmp)
    if chekc_tmp:
        tmp = chekc_tmp.group()
    return tmp

def text_to_mongo_syntax(sample, text):
    zhipuai.api_key = ""
    sentence = str(sample) + '''
    示例：
    X公司2023年的注册地址是什么？
    回答：【collection.find({"年份": "2023年", "公司全称": {"$regex": "X公司", "$options": "i"}}, {"注册地址": 1})】

    仿照上面的示例，完成下面问题的【mongo语句】书写。问题：''' + text
    response = zhipuai.model_api.invoke(
        model="chatglm_6b",
        temperature=0.1,
        # top_p=0.9,
        prompt=[
            {"role": "user", "content": sentence}]

    )
    tmp = response['data']['choices'][0]['content']
    chekc_tmp = re.search('\(.*?\}\)', tmp)
    if chekc_tmp:
        tmp = chekc_tmp.group()
    tmp = tmp.replace(' ', '').replace('\\"', '"')
    return tmp


def main():
    with open('data/C-list-question.json', 'r', encoding='utf-8') as file:
        questions = [json.loads(line.strip())['question'] for line in file]
    with torch.no_grad():
        for question in questions:
            answer_columns = process_question(question)
            prompt_cols = '已知问题为：【' + question + '】\n已知需要的列名为：【' + '、'.join(answer_columns) + '】\n'
            print('Answer columns:', answer_columns)
            print('Prompt cols:', prompt_cols)
            model = AutoModel.from_pretrained("THUDM/chatglm2-6b", trust_remote_code=True, device_map='auto')
            tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm2-6b", trust_remote_code=True)
            model = PeftModel.from_pretrained(model, "./output/")
            input_ids = tokenizer.encode(prompt_cols, return_tensors='pt')
            out = model.generate(
                input_ids=input_ids,
                max_length=500,
                temperature=0
            )
            answer = tokenizer.decode(out[0])
            print(answer)

if __name__ == "__main__":
    main()



