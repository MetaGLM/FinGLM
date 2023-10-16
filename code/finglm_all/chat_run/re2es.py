# encoding:utf-8
import re
import pandas as pd
from pymongo import MongoClient
from elasticsearch import Elasticsearch
import json
import zhipuai
import sys
import cn2an
sys.path.append('..')


with open('config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)

class Text2ES:
    def __init__(self, host="localhost", port=9200):
        self.es = Elasticsearch([{'host': host, 'port': port}])


    def query_collection(self, collection_name, body):
        response = es.search(index="collection_name", body=body)
        answer = response['hits']['total']['value']
        return answer

    def prepare_re_dict(self, list1, list2, list3, company_list):
        re_dict = {}
        re_dict['question'] = '(?:' + '|'.join(list1) + '|' + '|'.join(list3) + '|' + '增长率|'.join(list2) + '增长率' + '|' + '|'.join(list2) +')'
        re_dict['年份'] = config['year_re']
        re_dict['文件名'] = '(?:' + '|'.join(company_list) + ')'
        return re_dict

    def prepare_dict(self, text, q_dict):
        dict1 = {}
        if q_dict['年份'] != [] and len(q_dict['年份']) == 1:
            dict1['年份'] = {"term": {"年份": int(q_dict['年份'][0].replace('年', ''))}}

        if re.search('注册' + config['address_re'], text):
            middle = re.search('注册' + config['address_re'], text).group()
            address_list = re.findall(config['address_re2'], middle)
            if len(address_list) == 1:
                dict1['注册地址'] = {"term": {"注册地址.keyword": address_list[0]}}
            else:
                dict1['注册地址'] = {"regexp": {"注册地址.keyword":'|'.join(address_list)}}

        if re.search(config['address_re'] + '注册', text):
            middle = re.search(config['address_re'] + '注册', text).group()
            address_list = re.findall(config['address_re2'], middle)
            if len(address_list) == 1:
                dict1['注册地址'] = {"term": {"注册地址.keyword": address_list[0]}}
            else:
                dict1['注册地址'] = {"regexp": {"注册地址.keyword":'|'.join(address_list)}}

        if re.search('办公' + config['address_re'], text):
            middle = re.search('办公' + config['address_re'], text).group()
            address_list = re.findall(config['address_re2'], middle)
            if len(address_list) == 1:
                dict1['办公地址'] = {"term": {"办公地址.keyword": address_list[0]}}
            else:
                dict1['办公地址'] = {"regexp": {"办公地址.keyword":'|'.join(address_list)}}
        for q in q_dict['question']:
            if re.search(q + '.{0,2}(?:大于|小于)', text):
                replace_list = re.findall('(?:大于|小于)[一二三四五六七八九十](?:百|千|万|亿)', text)
                if replace_list:
                    for r in replace_list:
                        m_before = r.replace('大于', '').replace('小于', '')
                        m_after = cn2an.cn2an(m_before)
                        after = r.replace(m_before, str(m_after))
                        text = text.replace(r, after)

                dict1[q] = {"range": {q: {}}}
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
                    dict1[q]['range'][q]['gt'] = gt_re

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
                    dict1[q]['range'][q]['lt'] = lt_re
        return dict1

    def prepare_es(self, text, re_dict):
        q_dict = {}
        es = ''
        for q in re_dict:
            q_dict[q] = []
            q_re = re.findall(re_dict[q].replace('*', '\*'), text.replace('(', '').replace(')', ''))
            if q_re:
                q_dict[q] = q_re
        if q_dict['文件名']!= [] and len(q_dict['文件名'])==1 and len(q_dict['question']):
            # 查询
            list2 = []
            for question in q_dict['question']:
                list2.append(question)
            list1 = []
            for key in q_dict:
                if key == 'question':
                    pass
                elif key == '年份':
                    if len(q_dict['年份'])==1:
                        list1.append({"term": {"年份": int(q_dict[key][0].replace('年', ''))}})
                elif key == '文件名':
                    list1.append({"term": {"文件名.keyword": q_dict['文件名'][0]}})
                else:
                    list1.append({"term": {key: q_dict[key][0]}})
            body = {}
            body['query']={}
            body['query']['bool']= {}
            body['query']['bool']['must'] = list1
            body['_source'] = list2
            es = text + '####' + str(body)
            response = es.search(index="test", body=body)
            answer = response['hits']['hits'][0]['_source']



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
            list1 = []
            for key in dict1:
                list1.append(dict1[key])
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
                dict2 = {mark: {"order": "order"}}
            body = {}
            body['query']={}
            body['query']['bool']= {}
            body['query']['bool']['must'] = list1
            body['_source'] = ['公司名称']
            body['sort'] = [dict2]
            body['size'] = num
            es = text + '####' + str(body)
            response = es.search(index="test", body=body)
            answer = response['hits']['hits'][0]['_source']

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
            list1 = []
            for key in dict1:
                list1.append(dict1[key])
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
                dict2 = {mark: {"order": "order"}}

            body = {}
            body['query']={}
            body['query']['bool']= {}
            body['query']['bool']['must'] = list1
            body['_source'] = ['公司名称']
            body['sort'] = [dict2]
            body['size'] = num
            es = text + '####' + str(body)
            response = es.search(index="test", body=body)
            answer = response['hits']['hits'][0]['_source']
        elif q_dict['文件名'] == [] and re.search('最高', text):
            dict1 = self.prepare_dict(text, q_dict)
            list1 = []
            for key in dict1:
                list1.append(dict1[key])
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
                dict2 = {mark: {"order": "order"}}
            body = {}
            body['query']={}
            body['query']['bool']= {}
            body['query']['bool']['must'] = list1
            body['_source'] = ['公司名称']
            body['sort'] = [dict2]
            body['size'] = 1
            es = text + '####' + str(body)
            response = es.search(index="test", body=body)
            answer = response['hits']['hits'][0]['_source']

        elif q_dict['文件名'] == [] and re.search('(?:多少|几|哪些)(?:个|家|？|\?)?', text):
            dict1 = self.prepare_dict(text, q_dict)
            list1 = []
            for key in dict1:
                list1.append(dict1[key])
            body = {}
            body['query']={}
            body['query']['bool']= {}
            body['query']['bool']['must'] = list1
            body['size'] = 0
            es = text + '####' + str(body)
            response = es.search(index="test", body=body)
            answer = response['hits']['total']

        return es, answer


def text_to_answer_syntax(self, answer, text):
    zhipuai.api_key = ""
    sentence = '已知问题为：' + str(text) + '''\nmongo查询的结果为：''' + answer + '\n根据上面的问题及答案整合成一段话。'
    response = zhipuai.model_api.invoke(
        model="chatglm_6b",
        temperature=0.1,
        # top_p=0.9,
        prompt=[
            {"role": "user", "content": sentence}]
    )
    tmp = response['data']['choices'][0]['content']
    return tmp

if __name__=="__main__":
    tool = Text2ES("testdb")
    es = Elasticsearch(["http://localhost:9200/"])
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

    # query_text = '百达精工2019年的电子信箱是多少？'
    # query_text = '2019年货币资金第3高的公司是？'
    # query_text = '2019年货币资金最高的公司是？'
    # query_text = '在杭州注册的所有上市公司中，2020年负债合计大于5亿的有多少家？'
    # query_text = '在北京注册的上市公司中，2020年负债合计大于五亿的有多少家？'
    with open('data/C-list-question.json', 'r', encoding='utf-8') as file:
        questions = [json.loads(line.strip())['question'] for line in file]

    for question in questions:
        query_text = question.replace(' ', '').replace('总额', '合计').replace('总金额', '合计').replace('总计', '合计')\
            .replace('总负债', '负债合计').replace('总资产', '资产合计')\
            .replace('总人数', '总数').replace('货币合计', '货币资金')\
            .replace('硕士员工人数', '硕士人员')
        re_dict = tool.prepare_re_dict(list1, list2, list3, company_list)
        results_es, results_es_answer = tool.prepare_es(query_text, re_dict)
        if results_es == '' and not re.search('2019|2020|2021', query_text):
            # 直接走chatglm2-6b
            print('question1', query_text, results_es)
        elif results_es == '':
            # 需要优化部分
            print('question2', query_text, results_es)
        else:
            print('question3', query_text, results_es)

        answer = tool.text_to_answer_syntax(results_es_answer, query_text)
