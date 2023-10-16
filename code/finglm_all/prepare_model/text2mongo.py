# encoding:utf-8
import re
import pandas as pd
from pymongo import MongoClient
import sys
import cn2an
import zhipuai
sys.path.append('..')
class Text2Mongo:
    def __init__(self, db_name, uri="mongodb://localhost:27017/"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def prepare_re_dict(self, list1, list2, list3, company_list):
        re_dict = {}
        re_dict['question'] = '(?:' + '|'.join(list1) + '|' + '|'.join(list3) + '|' + '增长率|'.join(list2) + '增长率' + '|' + '|'.join(list2) +')'
        re_dict['年份'] = config['year_re']
        re_dict['文件名'] = '(?:' + '|'.join(company_list) + ')'
        return re_dict

    def prepare_dict(self, text, q_dict):
        dict1 = {}
        if q_dict['年份'] != [] and len(q_dict['年份']) == 1:
            dict1['年份'] = int(q_dict['年份'][0].replace('年', ''))

        if re.search('注册' + config['address_re'], text):
            middle = re.search('注册' + config['address_re'], text).group()
            address_list = re.findall(config['address_re2'], middle)
            if len(address_list) == 1:
                dict1['注册地址'] = {"$regex": address_list[0], "$options": "i"}
            else:
                dict1['$or'] = []
                for address in address_list:
                    middle_dict = {}
                    middle_dict['注册地址'] = {"$regex": address, "$options": "i"}
                    dict1['$or'].append(middle_dict)

        if re.search(config['address_re'] + '注册', text):
            middle = re.search(config['address_re'] + '注册', text).group()
            address_list = re.findall(config['address_re2'], middle)
            if len(address_list) == 1:
                dict1['注册地址'] = {"$regex": address_list[0], "$options": "i"}
            else:
                dict1['$or'] = []
                for address in address_list:
                    middle_dict = {}
                    middle_dict['注册地址'] = {"$regex": address, "$options": "i"}
                    dict1['$or'].append(middle_dict)

        if re.search('办公' + config['address_re'], text):
            middle = re.search('办公' + config['address_re'], text).group()
            address_list = re.findall(config['address_re2'], middle)
            if len(address_list) == 1:
                dict1['办公地址'] = {"$regex": address_list[0], "$options": "i"}
            else:
                dict1['$or'] = []
                for address in address_list:
                    middle_dict = {}
                    middle_dict['办公地址'] = {"$regex": address, "$options": "i"}
                    dict1['$or'].append(middle_dict)
        for q in q_dict['question']:
            if re.search(q + '.{0,2}(?:大于|小于)', text):
                replace_list = re.findall('(?:大于|小于)[一二三四五六七八九十](?:百|千|万|亿)', text)
                if replace_list:
                    for r in replace_list:
                        m_before = r.replace('大于', '').replace('小于', '')
                        m_after = cn2an.cn2an(m_before)
                        after = r.replace(m_before, str(m_after))
                        text = text.replace(r, after)

                dict1[q] = {}
                check_re1 = q + config['money_re1']
                check_re2 = q + config['money_re2']
                if re.search(check_re1, text):
                    middle = re.search(check_re1, text).group()
                    gt_re = re.search('大于\d(?:\d|\.){0,20}(?:百|千|万|亿){0,3}', middle).group().replace('大于', '')
                    if '亿' in gt_re:
                        gt_re = float(gt_re.replace('亿', '')) * 100000000
                    elif '千万' in gt_re:
                        gt_re = float(gt_re.replace('千万', '')) * 10000000
                    elif '百万' in gt_re:
                        gt_re = float(gt_re.replace('百万', '')) * 1000000
                    elif '万' in gt_re:
                        gt_re = float(gt_re.replace('万', '')) * 10000
                    elif '千' in gt_re:
                        gt_re = float(gt_re.replace('千', '')) * 1000
                    else:
                        gt_re = float(gt_re.replace('百', '').replace('千', '').replace('万', '').replace('亿', ''))
                    dict1[q]['$gt'] = gt_re
                if re.search(check_re2, text):
                    middle = re.search(check_re2, text).group()
                    lt_re = re.search('小于\d(?:\d|\.){0,20}(?:百|千|万|亿){0,3}', middle).group().replace('小于', '')
                    if '亿' in lt_re:
                        lt_re = float(lt_re.replace('亿', '')) * 100000000
                    elif '千万' in lt_re:
                        lt_re = float(lt_re.replace('千万', '')) * 10000000
                    elif '百万' in lt_re:
                        lt_re = float(lt_re.replace('百万', '')) * 1000000
                    elif '万' in lt_re:
                        lt_re = float(lt_re.replace('万', '')) * 10000
                    elif '千' in lt_re:
                        lt_re = float(lt_re.replace('千', '')) * 1000
                    else:
                        lt_re = float(lt_re.replace('百', '').replace('千', '').replace('万', '').replace('亿', ''))
                    dict1[q]['$lt'] = lt_re
        return dict1

    def text_to_mongo_syntax(self, text):
        zhipuai.api_key = ""
        sentence = '''改写下面的问题，使用【】''' + text
        response = zhipuai.model_api.invoke(
            model="",
            temperature=0.1,
            # top_p=0.9,
            prompt=[
                {"role": "user", "content": sentence}]

        )
        tmp = response['data']['choices'][0]['content']
        return tmp

    def prepare_mongo(self, text, re_dict):
        q_dict = {}
        mongo = ''
        for q in re_dict:
            q_dict[q] = []
            q_re = re.findall(re_dict[q].replace('*', '\*'), text)
            if q_re:
                q_dict[q] = q_re
        if q_dict['文件名']!= [] and len(q_dict['文件名'])==1 and len(q_dict['question']):
            # 查询
            dict2 = {}
            for question in q_dict['question']:
                dict2[question] = 1
            dict1 = {}
            for key in q_dict:
                if key == 'question':
                    pass
                elif key == '年份':
                    if len(q_dict['年份'])==1:
                        dict1['年份'] = int(q_dict[key][0].replace('年', ''))
                elif key == '文件名':
                    dict1['文件名'] = {"$regex": q_dict['文件名'][0], "$options": "i"}
                else:
                    dict1[key] = q_dict[key][0]
            # newtext = text_to_mongo_syntax(text)
            # mongo = newtext + '####collection.find(' + str(dict1) + ', ' + str(dict2) + ')'
            mongo = text + '####collection.find(' + str(dict1) + ', ' + str(dict2) + ')'
            mongo = mongo.replace("'re", 're').replace(".pattern'", '.pattern').replace("'", '"')



        elif q_dict['文件名'] == [] and re.search('高.{0,5}第[一二三四五六七八九十俩两仨\d]{1,2}|第[一二三四五六七八九十俩两仨\d]{1,2}高', text):
            num_re = re.search('(?:第)[一二三四五六七八九十俩两仨\d]{1,2}', text)
            if num_re:
                num_middle = num_re.group().replace('最', '').replace('前', '').replace('第', '')\
                    .replace('十九', '19').replace('十八', '18').replace('十七', '17').replace('十六', '16')\
                    .replace('十五', '15').replace('十四', '14').replace('十三', '13').replace('十二', '12')\
                    .replace('十一', '11').replace('十', '0').replace('九', '9').replace('八', '8').replace('七', '7')\
                    .replace('六', '6').replace('五', '5').replace('四', '4').replace('三', '3')\
                    .replace('二', '2').replace('一', '1').replace('俩', '2').replace('两', '2').replace('仨', '3')
                try:
                    num = int(num_middle)
                except:
                    num = 10
            dict1 = self.prepare_dict(text, q_dict)
            min_len = 100000
            mark = ''
            for q in q_dict['question']:
                check_re = re.search(q+'.*?(?:第)[一二三四五六七八九十俩两仨\d]{1,2}', text)
                if check_re:
                    check_len = len(check_re.group())
                    if check_len<min_len:
                        min_len = check_len
                        mark = q
            if mark != '':
                dict2 = [(mark, -1)]
                # newtext = text_to_mongo_syntax(text)
                # mongo = newtext + '####collection.find(' + str(dict1) + ',{\'公司名称\': 1, \'' + mark + '\': 1, \'_id\': 0}).sort(' + str(dict2)+ ').skip(' + str(num-1) +').limit(1)'
                mongo = text + '####collection.find(' + str(dict1) + ',{\'公司名称\': 1, \'' + mark + '\': 1, \'_id\': 0}).sort(' + str(dict2)+ ').skip(' + str(num-1) +').limit(1)'
                mongo = mongo.replace("'re", 're').replace(".pattern'", '.pattern').replace("'", '"')

        elif q_dict['文件名'] == [] and re.search('高.{0,5}(?:最|前)[一二三四五六七八九十俩两仨\d]{1,2}', text):
            num_re = re.search('(?:最|前)[一二三四五六七八九十俩两仨\d]{1,2}', text)
            if num_re:
                num_middle = num_re.group().replace('最', '').replace('前', '')\
                    .replace('十九', '19').replace('十八', '18').replace('十七', '17').replace('十六', '16')\
                    .replace('十五', '15').replace('十四', '14').replace('十三', '13').replace('十二', '12')\
                    .replace('十一', '11').replace('十', '0').replace('九', '9').replace('八', '8').replace('七', '7')\
                    .replace('六', '6').replace('五', '5').replace('四', '4').replace('三', '3')\
                    .replace('二', '2').replace('一', '1').replace('俩', '2').replace('两', '2').replace('仨', '3')
                try:
                    num = int(num_middle)
                except:
                    num = 10
            dict1 = self.prepare_dict(text, q_dict)
            min_len = 100000
            mark = ''
            for q in q_dict['question']:
                check_re = re.search(q+'.*?(?:最|前)[一二三四五六七八九十俩两仨\d]{1,2}', text)
                if check_re:
                    check_len = len(check_re.group())
                    if check_len<min_len:
                        min_len = check_len
                        mark = q
            if mark != '':
                dict2 = [(mark, -1)]
                # newtext = text_to_mongo_syntax(text)
                # mongo = newtext + '####collection.find(' + str(dict1) + ',{\'公司名称\': 1, \'_id\': 0}).sort(' + str(dict2)+ ').limit(' + str(num) +')'
                mongo = text + '####collection.find(' + str(dict1) + ',{\'公司名称\': 1, \'' + mark + '\': 1, \'_id\': 0}).sort(' + str(dict2)+ ').limit(' + str(num) +')'
                mongo = mongo.replace("'re", 're').replace(".pattern'", '.pattern').replace("'", '"')

        elif q_dict['文件名'] == [] and re.search('最高', text):
            num = 1
            dict1 = self.prepare_dict(text, q_dict)
            min_len = 100000
            mark = ''
            for q in q_dict['question']:
                check_re = re.search(q+'.*?(?:最高)', text)
                if check_re:
                    check_len = len(check_re.group())
                    if check_len<min_len:
                        min_len = check_len
                        mark = q
            if mark != '':
                dict2 = [(mark, -1)]
                # newtext = text_to_mongo_syntax(text)
                # mongo = newtext + '####collection.find(' + str(
                #     dict1) + ',{\'公司名称\': 1, \'' + mark + '\': 1, \'_id\': 0}).sort(' + str(
                #     dict2) + ').skip(' + str(num - 1) + ').limit(1)'
                mongo = text + '####collection.find(' + str(dict1) + ',{\'公司名称\': 1, \'' + mark + '\': 1, \'_id\': 0}).sort(' + str(
                    dict2) + ').skip(' + str(num - 1) + ').limit(1)'
                mongo = mongo.replace("'re", 're').replace(".pattern'", '.pattern').replace("'", '"')

        elif q_dict['文件名'] == [] and re.search('(?:多少|几|哪些)(?:个|家|？|\?)?', text):
            dict1 = self.prepare_dict(text, q_dict)
            # newtext = text_to_mongo_syntax(text)
            # mongo = newtext + '####collection.count_documents(' + str(dict1) + ')'
            mongo = text + '####collection.count_documents(' + str(dict1) +')'
            mongo = mongo.replace("'re", 're').replace(".pattern'", '.pattern').replace("'", '"')

        if mongo != '':
            with open('log_mongo.txt', 'a+', encoding='utf-8') as file:
                file.writelines(mongo+'\n')
        else:
            with open('log_mongo_bug.txt', 'a+', encoding='utf-8') as file2:
                file2.writelines(text+'\n')

        return mongo

# def text2vec_base(key_word_list, query):
#     embedder = SentenceModel(model_name_or_path='text2vec-base-chinese')
#     corpus_embeddings = embedder.encode(key_word_list)
#     query_embedding = embedder.encode(query)
#     hits = semantic_search(query_embedding, corpus_embeddings, top_k=3)
#     print("\n\n======================\n\n")
#     print("\nTop 5 most similar sentences in corpus:")
#     hits = hits[0]  # Get the hits for the first query
#     for hit in hits:
#         print(key_word_list[hit['corpus_id']], "(Score: {:.4f})".format(hit['score']))
#     return hits

if __name__=="__main__":
    tool = Text2Mongo("testdb")
    client = MongoClient("mongodb://localhost:27017/")
    sample = ["年份", "企业全称", "公司简称"]
    df = pd.read_excel('big_data.xlsx', engine='openpyxl')
    # 将选定的列转换为列表
    column_list = list(set(df['公司简称'].tolist()))
    long_column_list = list(set(df['企业全称'].tolist()))
    company_list = column_list + long_column_list

    basic_list = config['basic_list']
    amount_list = config['amount_list']
    list1 = config['list1']
    list2 = config['list2']
    list3 = config['list3']
    list22 = []
    for l in list2:
        list22.append(l+'增长率')
    key_word_list = list1 + list2 + list22 + list3
    address_list = [
        '北京', '上海', '广州', '无锡', '深圳', '青岛', '天津', '苏州', '杭州', '宁波', '南京', '大理', '海南']
    year_list = ['2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026']


    most_list = ['大于10万', '大于100万', '大于1000万', '小于100万', '小于1000万', '大于1000万小于2000万',
                  '大于十万', '大于一百万', '大于一千万', '小于一百万', '小于一千万', '大于一千万小于两千万',]
    num_list = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '二', '三', '四', '五', '六', '七', '八', '九', '十']
    key_word_list3 = ['办公地址', '注册地址']

    for i in range(500):
        address1 = address_list[i % 13]
        address2 = address_list[(5 + i) % 13]
        year = year_list[i % 9]
        key_word = key_word_list[i % 480]
        key_word1 = list2[i % 215]
        key_word2 = list2[(i + 20) % 215]
        short = column_list[i % 2000]
        long = long_column_list[(i+1000) % 500]
        most = most_list[i % 12]
        key_word3 = key_word_list3[i % 2]
        num = num_list[i % 19]

        query_list = [
            key_word3 + '在' + address1 + '的公司，' + year + '年' + key_word1 + most + '的公司有多少家？',
            key_word3 + '在' + address1 + '或' + address2 + '的公司，' + year + '年' + key_word2 + most + '的公司有多少家？',
            year + '年' + short + '的' + key_word + '是什么？',
            short + year + '年的' + key_word + '是什么？',
            year + '年' + long + '的' + key_word + '是什么？',
            long + year + '年的' + key_word + '是什么？',
            year + '年' + short + '的' + key_word1 + '和' + key_word2 + '分别是什么？',
            key_word3 + '在' + address1 + '的公司，' + key_word1 + year + '年最高的前' + num + '家公司是？',
            key_word3 + '在' + address1 + '或' + address2 + '的公司，' + year + '年' + key_word1 + '最高的第' + num + '家公司是？',
        ]
        for query_text in query_list:
            query_text = query_text.replace(' ', '')
            re_dict = tool.prepare_re_dict(list1, list2, list3, company_list)
            results_mongo = tool.prepare_mongo(query_text, re_dict)
            print(results_mongo)

    # query_text = '北京当升材料科技股份有限公司2018年的终止经营净利润是什么？'
    # # query_text = '2020年宁波美诺华药业股份有限公司的证券简称是什么？'
    # query_text = query_text.replace(' ', '')
    # print('query_text', query_text)
    # re_dict = tool.prepare_re_dict(list1, list2, list3, company_list)
    # print(re_dict)
    # results_mongo = tool.prepare_mongo(query_text, re_dict)
    # print('results_mongo', results_mongo)