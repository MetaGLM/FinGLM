import json
import os
import re
import torch
import pandas as pd
from transformers import AutoModel, AutoTokenizer
import tqdm
from retrieval.sparse_retrieval import BM25Retriever
from retrieval.dense_retrieval import FaissIndexer, MODEL_PATH, FAISS_FOLDER, FAISS_PATH_WITH_MODEL
from utils.compute_value import *
from utils import torch_gc, KeywordMapping, find_annual_report
from configs.model_config import *
from database.sql_db import sql_search
from utils.statistic_answer import get_statistic_answer
from utils.query_database import query_data
from utils.query_map import query_keyword_map
import random
import numpy as np

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    os.environ['PYTHONHASHSEED'] = str(seed)
    
set_seed(4396)

def chengxinzhuangkuang(annul_report,query,query_stock_name):

    MATCH_TEMPLATE_chengxinzhuangkuang_Success = """经查询，{company}在{year_time}年的控股股东、实际控制人的诚信状况如下：{context}"""

    MATCH_TEMPLATE_chengxinzhuangkuang_Fail = """经查询，{company}在{year_time}年的年报未披露控股股东、实际控制人的诚信状况的相关信息"""

    year_time= str(re.findall(r'\d{4}', query)[0])

    table_location = os.path.join(table_path,annul_report.replace('.pdf', '/诚信状况表.csv'))
    if not os.path.exists(table_location):
        return "",False
    
    table_search = pd.read_csv(table_location)
    sentence = table_search.loc[0,"情况"].strip()

    if sentence[0] == '√':
        context = ''.join(sentence.split("不适用")[1:])
        response = MATCH_TEMPLATE_chengxinzhuangkuang_Success.replace("{context}", context).replace("{year_time}", year_time).replace("{company}",query_stock_name)
    else:
        response = MATCH_TEMPLATE_chengxinzhuangkuang_Fail.replace("{year_time}", year_time).replace("{company}",query_stock_name)

    return response,True

def konggugudongshifou(annul_report,query,query_stock_name):
    MATCH_TEMPLATE_konggugudongshifou_Success = """经查询，{company}在{year_time}年的控股股东发生变更，详细情况为：{context}"""

    MATCH_TEMPLATE_konggugudongshifou_Fail = """经查询，{company}在{year_time}年的控股股东未发生变更"""

    year_time= str(re.findall(r'\d{4}', query)[0])

    table_location = os.path.join(table_path,annul_report.replace('.pdf', '/控股股东报告期内变更表.txt'))
    if not os.path.exists(table_location):
        return "",False
    
    with open(table_location,'r') as f:
        data = f.readlines()
        if data[0][0] == '√':
            context = ''
            for line in data[1:]:
                if '√' in line or '□' in line:
                    break
                context = context + line + ' '
            response = MATCH_TEMPLATE_konggugudongshifou_Success.replace("{context}", context).replace("{year_time}", year_time).replace("{company}",query_stock_name)
        elif data[0][0] == '□':
            response = MATCH_TEMPLATE_konggugudongshifou_Fail.replace("{year_time}", year_time).replace("{company}",query_stock_name)

    return response,True


def hebingbaobiaofanwei(model, tokenizer,annul_report,query,query_stock_name):

    MATCH_TEMPLATE_hebingbaobiaofanwei_Fail = """经查询，{company}在{year_time}中，公司报告期合并报表范围与上年相比无变化。"""

    year_time= str(re.findall(r'\d{4}', query)[0])

    table_location = os.path.join(table_path,annul_report.replace('.pdf', '/合并报表范围发生变化.txt'))
    if not os.path.exists(table_location):
        return "",False
    
    with open(table_location,'r') as f:
        data = f.readlines()
        if data[0][0] == '√':
            context = ''
            for line in data[1:]:
                if '√' in line or '□' in line:
                    break
                context = context + line + ' '
            prompt = PROMPT_1.replace("{question}", query).replace("{context}", context)
            response, _ = model.chat(tokenizer, prompt, history=[])
        elif data[0][0] == '□':
            response = MATCH_TEMPLATE_hebingbaobiaofanwei_Fail.replace("{year_time}", year_time).replace("{company}",query_stock_name)

    return response,True

def chufajizhenggaiqingkuang(model, tokenizer,annul_report,query,query_stock_name):

    MATCH_TEMPLATE_chufajizhenggaiqingkuang_Fail = """经查询，{company}在{year_time}中，公司报告期不存在处罚及整改情况"""

    year_time= str(re.findall(r'\d{4}', query)[0])

    table_location = os.path.join(table_path,annul_report.replace('.pdf', '/处罚及整改情况.txt'))
    if not os.path.exists(table_location):
        return "",False
    
    with open(table_location,'r') as f:
        data = f.readlines()
        if data[0][0] == '√':
            context = ''
            for line in data[1:]:
                if '√' in line or '□' in line:
                    break
                context = context + line + ' '
            prompt = PROMPT_1.replace("{question}", query).replace("{context}", context)
            response, _ = model.chat(tokenizer, prompt, history=[])
        elif data[0][0] == '□':
            response = MATCH_TEMPLATE_chufajizhenggaiqingkuang_Fail.replace("{year_time}", year_time).replace("{company}",query_stock_name)

    return response,True

def pochanchongzheng(model, tokenizer,annul_report,query,query_stock_name):

    MATCH_TEMPLATE_chufajizhenggaiqingkuang_Fail = """经查询，{company}在{year_time}中，公司报告期末不存在破产重整相关事项"""

    year_time= str(re.findall(r'\d{4}', query)[0])

    table_location = os.path.join(table_path,annul_report.replace('.pdf', '/破产重整相关事项.txt'))
    if not os.path.exists(table_location):
        return "",False
    
    with open(table_location,'r') as f:
        data = f.readlines()
        if data[0][0] == '√':
            context = ''
            for line in data[1:]:
                if '√' in line or '□' in line:
                    break
                context = context + line + ' '
            prompt = PROMPT_1.replace("{question}", query).replace("{context}", context)
            response, _ = model.chat(tokenizer, prompt, history=[])
        elif data[0][0] == '□':
            response = MATCH_TEMPLATE_chufajizhenggaiqingkuang_Fail.replace("{year_time}", year_time).replace("{company}",query_stock_name)

    return response,True

def konggugudongjishijikongzhiren(model, tokenizer,annul_report,query, query_stock_name):

    PROMPT_konggugudong = """控股股东
    {s1}
    实控人
    {s2}
    其他
    {s3}
    根据上述信息，回答下面的问题
    {question}
    答案：
    """

    table_location = os.path.join(table_path,annul_report.replace('.pdf', '/控股股东及实际控制人情况表.csv'))
    if not os.path.exists(table_location):
        return "",False

    table_search = pd.read_csv(table_location)
    s1,s2,s3 = "","",""
    try:
        s1 = table_search.loc[0,"情况"].strip()
        s2 = table_search.loc[1,"情况"].strip()
        s3 = table_search.loc[2,"情况"].strip()
    except:
        print("chengshuangbiaomeiyou")
    prompt = PROMPT_konggugudong.replace("{s1}", s1).replace("{s2}", s2).replace("{s3}", s3).replace("{question}", query)
    response, _ = model.chat(tokenizer, prompt, history=[])
    print(prompt)
    return response,True

def jiepinpinren(model, tokenizer,annul_report,query,query_stock_name):

    table_location = os.path.join(table_path,annul_report.replace('.pdf', '/聘任_解聘会计师事务所.txt'))
    if not os.path.exists(table_location):
        return "",False
    context = ""
    with open(table_location,'r') as f:
        data = f.readlines()
        for line in data:
            context = context + line + ' '
        prompt = PROMPT_1.replace("{question}", query).replace("{context}", context)
        response, _ = model.chat(tokenizer, prompt, history=[])

    return response,True

def gaojiguanlirenyuanbiandong(model, tokenizer,annul_report,query,query_stock_name):

    PROMPT_konggugudong = """公司董事、监事、高级管理人员变动情况如下：
    {context}
    """

    MATCH_TEMPLATE_chufajizhenggaiqingkuang_Fail = """经查询，{company}在{year_time}中，公司报告期末不存在公司董事、监事、高级管理人员变动情况"""

    year_time= str(re.findall(r'\d{4}', query)[0])

    table_location = os.path.join(table_path,annul_report.replace('.pdf', '/高级管理人员变动情况.txt'))
    if not os.path.exists(table_location):
        return "",False
    
    with open(table_location,'r') as f:
        data = f.readlines()
        if data[0] == "不适用":
            response = MATCH_TEMPLATE_chufajizhenggaiqingkuang_Fail.replace("{year_time}", year_time).replace("{company}",query_stock_name)
        else:
            context = " ".join(data[1:])
            prompt = PROMPT_konggugudong.replace("{context}", context)
            response, _ = model.chat(tokenizer, prompt, history=[])
    return response,True


def zhuyaokonggu(model, tokenizer,annul_report,query,query_stock_name):
    table_location = os.path.join(table_path,annul_report.replace('.pdf', '/主要控股参股公司分析.txt'))
    if not os.path.exists(table_location):
        return "",False
    with open(table_location,'r') as f:
        context = f.read()
        if len(context) == 0:
            return "",False
        prompt = PROMPT_1.replace("{question}", query).replace("{context}", context)
        response, _ = model.chat(tokenizer, prompt, history=[])
    return response,True

def zhongdazichan(model, tokenizer,annul_report,query,query_stock_name):
    table_location = os.path.join(table_path,annul_report.replace('.pdf', '/重大资产和股权出售.txt'))
    if not os.path.exists(table_location):
        return "",False
    with open(table_location,'r') as f:
        context = f.read()
        if len(context) == 0:
            return "",False
        prompt = PROMPT_1.replace("{question}", query).replace("{context}", context)
        response, _ = model.chat(tokenizer, prompt, history=[])
    return response,True

log_f=open("./log.txt","w")
def LOG(logs):
    log_f.write(logs+"\n")
    log_f.flush()
sql_res_map = pd.read_csv(sql_res_path)
# class4_database_gpt4 = pd.read_csv(class3_database)

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
# 读取keyword.csv
file_key_words = pd.read_csv(keyword_path, encoding='utf-8')
file_key_words.fillna(0, inplace=True)


item_map = pd.read_csv(item_map_path)

# 检索相关辅助函数
DENSEORSPARSE = "SPARSE"
if DENSEORSPARSE == "DENSE" or DENSEORSPARSE == "BOTH":
    faiss_indexer = FaissIndexer(FAISS_FOLDER,MODEL_PATH)

def dense_retrieval(file, data, keywords, top_k):
    faiss_name = os.path.join(FAISS_PATH_WITH_MODEL,file.replace('.pdf','.faiss'))
    if not os.path.exists(faiss_name):
        faiss_indexer.create_index(faiss_name,data) # 创建索引
    context = faiss_indexer.query_doc(faiss_name, [" ".join(keywords)], top_k=top_k)
    context = "\n".join([data[item[0]] for item in context[0]])
    return context

def sparse_retrieval(data, keywords, top_k):
    sparse_retriever = BM25Retriever(data)
    context = sparse_retriever.get_docs_and_scores([" ".join(keywords)], topk=top_k)
    context = "\n".join([item[0] for item in context[0]])
    return context

def sparse_retrieval_word(data, keywords, top_k):
    sparse_retriever = BM25Retriever(data)
    context = sparse_retriever.get_docs_and_scores(keywords, topk=top_k)
    result = []
    for word in context:
        result.extend([item[0] for item in word])
    return "\n".join(result)

def dense_sparse_retrieval(file, data, keywords):
    finalresult = []
    if DENSEORSPARSE == "SPARSE" or DENSEORSPARSE == "BOTH":
        sparse_result = sparse_retrieval_word(data, keywords, 4)
        finalresult.append(sparse_result)
    if DENSEORSPARSE == "DENSE" or DENSEORSPARSE == "BOTH":
        dense_result = dense_retrieval(file, data, keywords, 1)
        finalresult.append(dense_result)
    return "\n".join(finalresult)

def get_classify_result(query):
    questions = query.split(' ')
    all_class=[file_key_words[file_key_words['parten']==question]['问题类别'].values for question in questions]
    for idx, n_class in enumerate(all_class):
        if len(n_class)==0:
            all_class[idx]=[0]
        # 判断是否为nan
        if pd.isna(all_class[idx][0]):
            all_class[idx]=[0]
    class_0=int(all_class[0][0])
    if class_0==2:
        for n_class in all_class:
            if int(n_class[0])!=2:
                class_0=int(n_class[0])
                break
    return questions, class_0

def generate_response(ids, queries, stock_full_names, query_stock_names, annul_reports):
        # id_group, query_group, document_group, document_exact_group, short_name_group, full_name_group):
    with torch.no_grad():
        tokenizer = AutoTokenizer.from_pretrained(LLM_model_path, trust_remote_code=True)
        model = AutoModel.from_pretrained(LLM_model_path, trust_remote_code=True, device=device)
        model = model.eval()

        class_2_cnt=0
        class_2_success_cnt = 0
        for id, query, stock_full_name, query_stock_name, annul_report in \
            tqdm.tqdm(zip(ids, queries, stock_full_names, query_stock_names, annul_reports), total=len(ids)):

            words = ['前', '最', '第']
            is_class_1 = annul_report ## 找到了年报
            is_class_2 = (not annul_report) and query_stock_name ## 没有年报，但是 query 中出现了公司名称，认为这是年报缺失问题，不知道
            is_class_3 = (not annul_report) and (not query_stock_name) and any(word in query for word in words) # query 中没有出现公司实体，但是出现了时间或“最”，认为这是统计问题
            is_class_4 = (not annul_report) and (not query_stock_name) and re.findall(r'2019|2020|2021', query) # 无公司 有时间, 但是不是统计问题，不知道
            is_class_5 = (not annul_report) and (not query_stock_name) ## 认为这是不需要外部信息的开放性问题

            response = '' ## 检测 response 的值判断状态转移
            # if query == ''
            if is_class_1:
                ##获取关键字
                retrieval_query, raw_words = query_keyword_map.question_to_keywords_with_raw_words(query)
                ##获取类别
                keywords, class_n = get_classify_result(retrieval_query)
                if "详情" in query:
                    class_n = 3
                print(query, keywords, class_n)
                if len(annul_report) == 1 and class_n == 2: ## 需要年报的开放性问题扔给大模型
                    answer_list = []
                    class_2_cnt += 1
                    for keyword, raw_word in zip(keywords, raw_words):
                        item_str = file_key_words[file_key_words['parten']==keyword]['需要查询指标'].values[0]
                        formula=file_key_words[file_key_words['parten']==keyword]['公式'].values[0]
                        res, item_list, full_formula, element_val,element_name = get_class_2_res(item_map, item_str, formula, annul_report[0][:-4])
                        print("res", res)
                        print(item_list, full_formula, element_val, element_name)
                        # if res == -1 or res == -2 or res == -3: ## 找不到表或者表中找不到信息，进到检索方法
                        #     continue
                        year = annul_report[0].split('__')[-2]
                        if res == -4: # -1 未找到字段 -2 表格文件不存在 -3 表格不支持 -4 去年年报不存在
                            answer = MATCH_TEMPLATE_9.format(year=year, stock=query_stock_name, keyword=raw_word)
                            answer_list.append(answer)
                            continue
                        if res == -1 or res == -2 or res == -3: ## 找不到表或者表中找不到信息，进到检索方法
                            continue
                        
                        ## 前缀信息的规则
                        foreign_name = ['外文名称','英文名称']
                        percent_words = ['率','比重']
                        ratio_words = ['比值','比例','流动比率','速动比率']
                        integer_words = ['博士','人数','总数', '硕士', '数量', '人员']

                        prefix_name=''
                        
                        for name, val in zip(element_name, element_val):
                            if name[1] == '0':
                                prefix_name = prefix_name + year + query_stock_name + name[0] + '为' + val + '元，'
                            else:
                                prefix_name = prefix_name + str(int(year[:-1])-1) + '年' + query_stock_name + name[0] + '为' + val + '元，'
                            for item in integer_words:
                                if item in query: 
                                    prefix_name.replace('元，', '人，')
                                    break

                        
                        actions = {
                            '每股经营现金流量': {'template': MATCH_TEMPLATE_3, 'precision': 3},
                            '每股净资产': {'template': MATCH_TEMPLATE_4, 'precision': 4},
                            **{word: {'template': MATCH_TEMPLATE_5, 'precision': 2} for word in ratio_words},
                            **{word: {'template': MATCH_TEMPLATE_6, 'precision': 2, 'multiplier': 100} for word in percent_words},
                            **{word: {'template': MATCH_TEMPLATE_7, 'precision': 0} for word in integer_words}
                        }
                        if isinstance(res, float) or isinstance(res, int): # 输出结果是数字
                            # Define keyword-to-action mappings

                            # Apply actions based on keywords
                            match_action = False
                            for condition, action in actions.items():
                                if condition in query:
                                    if 'multiplier' in action:
                                        res *= action['multiplier']
                                    res = round(res, action['precision'])
                                    if len(item_list) > 1: # 需要公式计算
                                        answer = prefix_name + action['template'].format(keyword=raw_word, res=res, year=year, stock=query_stock_name, formula=full_formula)
                                    else:
                                        answer = action['template'].format(keyword=raw_word, res=res, year=year, stock=query_stock_name, formula=full_formula)
                                    match_action = True
                                    break
                            if not match_action:
                                if '证券代码' in query:
                                    answer = MATCH_TEMPLATE_8.format(keyword=raw_word, res=res, year=year, stock=query_stock_name)
                                else:
                                    res = round(res, 2)
                                    if len(item_list) > 1: # 需要公式计算
                                        answer = prefix_name + MATCH_TEMPLATE_2.format(keyword=raw_word, res=res, year=year, stock=query_stock_name, formula=full_formula)
                                    else:
                                        answer = MATCH_TEMPLATE_1.format(keyword=raw_word, res=res, year=year, stock=query_stock_name)
                            answer_list.append(answer)

                        else: # 输出结果不是数字，是字符串
                            answer = MATCH_TEMPLATE_8.format(keyword=raw_word, res=res, year=year, stock=query_stock_name)
                            if any(word in keyword for word in foreign_name):
                                answer_list.append(answer)
                            else:
                                answer_list.append(answer.replace(' ', ''))
                    print(answer_list)
                    answer = ' '.join(answer_list)
                    if answer.replace(' ', '') != '':
                        response = answer
                        class_2_success_cnt += 1
                
                elif len(annul_report) == 2 or len(annul_report) == 3:
                    context = ''
                    answer_list = []
                    for keyword, raw_word in zip(keywords, raw_words):
                        info = ''
                        element_vals = []
                        for report in annul_report:
                            time = report.split('__')[-2]
                            item_str=file_key_words[file_key_words['parten']==keyword]['需要查询指标'].values[0]
                            formula=file_key_words[file_key_words['parten']==keyword]['公式'].values[0]
                            res, _, _, element_val, element_name = get_class_2_res(item_map, item_str, formula, report[:-4])
                            if res == -1 or res == -2: ## 找不到表或者表中找不到信息，进到检索方法
                                context = ''
                                break
                            # print(time, element_name, element_val)
                            info += time + element_name[0][0] + '是' + element_val[0] + '，'
                            element_vals.append(element_val[0])
                        context += info + '\n'
                        if context:
                            res = "相同。" if len(set(element_vals)) == 1 else "不相同。"
                            answer = "根据查询，" + context +  "这" + str(len(element_vals)) + "年" + str(query_stock_name) + "的" + raw_word + res
                            answer_list.append(answer)
                        
                        # 如果能通过查询方法检索到信息，则 context 已经有值，反之为空
                        else:
                            answer = MATCH_TEMPLATE_9.format(year=year, stock=query_stock_name, keyword=raw_word)
                            answer_list.append(answer)
                    answer = ' '.join(answer_list)
                    if answer.replace(' ', '') != '':
                        response = answer
                    print(query, response)

                if not response:
                    no_retrieval = False
                    if "诚信状况" in query:
                        response,success = chengxinzhuangkuang(annul_report[0],query,query_stock_name)
                        print(response,success)
                        if success:
                            no_retrieval = True

                    elif "控股股东是否" in query:
                        response,success = konggugudongshifou(annul_report[0],query,query_stock_name)
                        print(response,success)
                        if success:
                            no_retrieval = True
                            
                    elif "合并报表范围发生变化" in query:
                        response,success = hebingbaobiaofanwei(model, tokenizer,annul_report[0],query,query_stock_name)
                        print(response,success)
                        if success:
                            no_retrieval = True

                    elif "处罚及整改情况" in query:
                        response,success = chufajizhenggaiqingkuang(model, tokenizer,annul_report[0],query,query_stock_name)
                        print(response,success)
                        if success:
                            no_retrieval = True

                    elif "破产重整相关事项" in query:
                        response,success = pochanchongzheng(model, tokenizer,annul_report[0],query,query_stock_name)
                        print(response,success)
                        if success:
                            no_retrieval = True

                    elif "聘任、解聘会计师事务所" in query:
                        response,success = jiepinpinren(model, tokenizer,annul_report[0],query,query_stock_name)
                        print(response,success)
                        if success:
                            no_retrieval = True

                    elif "高级管理人员变动情况" in query:
                        response,success = gaojiguanlirenyuanbiandong(model, tokenizer,annul_report[0],query,query_stock_name)
                        print(response,success)
                        if success:
                            no_retrieval = True

                    elif "主要控股参股公司分析" in query:
                        response,success = zhuyaokonggu(model, tokenizer,annul_report[0],query,query_stock_name)
                        print(response,success)
                        if success:
                            no_retrieval = True

                    elif "重大资产和股权出售" in query:
                        response,success = zhongdazichan(model, tokenizer,annul_report[0],query,query_stock_name)
                        print(response,success)
                        if success:
                            no_retrieval = True

                    elif "控股股东及实控人" in query or "控股股东及实际控制人" in query or "控股股东和实控人" in query or "控股股东和实际控制人" in query:
                        response,success = konggugudongjishijikongzhiren(model, tokenizer,annul_report[0],query,query_stock_name)
                        print(response,success)
                        if success:
                            no_retrieval = True

                    if not no_retrieval:
                        with open(os.path.join(knowledge_txt_path, annul_report[0].replace('.pdf', '.txt')), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if len(data) == 1:
                                data = annul_report[0].replace('.pdf','').split('__')
                        context = dense_sparse_retrieval(annul_report[0], data, keywords)

                        prompt = PROMPT_1.replace("{question}", query).replace("{context}", context)
                        response, _ = model.chat(tokenizer, prompt, history=[], temperature=0.01)     

            elif is_class_2:
                year_time= str(re.findall(r'\d{4}', query)[0])
                response = PROMPT_5.replace("{query}", query).replace("{year_time}", year_time).replace("{company}",query_stock_name)

            elif is_class_3:
                LOG("这是统计问题")
                LOG("-----------------")
                LOG(query)
                ## GPT-4 测试方案
                try:
                    SQL = sql_res_map[sql_res_map['id'] == id]['sql'].values
                    if len(SQL) == 1:
                        SQL = SQL[0]
                        LOG(f"LOG:SQL:\n{SQL}")
                        #SQL语句查询结果
                        result_string=query_data(SQL)
                        LOG(f"LOG:SQL_result:\n{result_string}")

                        if result_string:#查询有结果
                            response = get_statistic_answer(query, SQL, result_string)
                            # prompt = PROMPT_SQL_TO_TEXT.replace("{question}", query).replace("{sql_result}", result_string)
                            # response,_ = model.chat(tokenizer,prompt,history=[])    
                            # ##获取关键字
                            # retrieval_query = query_keyword_map.question_to_keywords(query)
                            # ##获取类别
                            # keywords, class_n = get_classify_result(retrieval_query)
                            # get_statitic_answer(query, result_string, keywords)
                        else:#经过多查询依然没有结果
                            LOG("查询无结果")
                            response=f"很抱歉，未查询到有关{query}的结果。"
                    else:
                        result_string_list = []
                        for sql in SQL:
                            LOG(f"LOG multi :SQL:\n{sql}")
                            #SQL语句查询结果
                            result_string=query_data(sql)
                            LOG(f"LOG:SQL_result:\n{result_string}")
                            result_string_list.append(result_string)
                        result_dict = {}
                        for year_result in result_string_list:
                            year_result = eval(year_result)
                            for each_item in year_result:
                                if each_item[0] in result_dict:
                                    t = result_dict[each_item[0]]
                                    result_dict[each_item[0]] = (t[0]+1,(t[1]*t[0]+each_item[1])/(t[0]+1))
                                else:
                                    result_dict[each_item[0]] = (1,each_item[1])
                        result_dict = dict(filter(lambda x: x[1][0] == len(result_string_list), result_dict.items()))
                        if len(result_dict) == 0:
                            LOG("查询无结果")
                            response=f"很抱歉，未查询到有关{query}的结果。"
                        else:
                            result_string='[' + ",".join([",".join(("('"+str(r_tupe[0])+"'",str(round(r_tupe[1][1],2))+")")) for r_tupe in result_dict.items()]) + ']'
                            response = get_statistic_answer(query, query, result_string)
                            print(response)
                except:
                    response=f"很抱歉，未查询到有关{query}的结果。"

            elif is_class_4: # 无公司 有时间, 但是不是统计问题，不知道
                year_time= str(re.findall(r'\d{4}', query)[0])
                response = PROMPT_6.replace("{query}", query).replace("{year_time}", year_time)
            elif is_class_5:
                prompt = PROMPT_4.replace("{question}", query)
                response, _ = model.chat(tokenizer, prompt, history=[], temperature=0.01)
                
            
            with open(response_path, 'a', encoding='utf-8') as outfile:
                item ={'id': id, 'question': query, 'answer': response.replace(',', '').replace('\n', '')}
                json.dump(item, outfile, ensure_ascii=False)
                outfile.write('\n')
    torch_gc()


def main():
    with open('result/find_item_error.csv', 'w') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['item_name', 'year', 'path', 'stock_name'])
    
    with open('result/table_not_found.csv', 'w') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['table_name', 'stock_name', 'path'])

    with open('result/table_unsupport.csv', 'w') as f: 
        csv_writer = csv.writer(f)
        csv_writer.writerow(['table_name', 'stock_name', 'path'])
        
    with open('result/item_nan_error.csv', 'w') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['item_name', 'year', 'path', 'stock_name'])
        
    with open('result/class_2_result.csv', 'w') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['question', 'keywords', 'class_n'])
        
    with open('result/last_year_annual_report_not_found.csv', 'w') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['stock_name', 'table_name', 'item_name', 'year'])
    
    ids, queries, stock_full_names, query_stock_names, annul_reports = [], [], [], [], []

    with open(query_path) as reader:
        lines = reader.readlines()
        for line in tqdm.tqdm(lines, total=len(lines)):
            data = json.loads(line)
            id = data['id']
            query = data['question']
            stock_full_name, _, query_stock_name, annul_report = find_annual_report(query=query)
            ids.append(id)
            queries.append(query)
            stock_full_names.append(stock_full_name)
            query_stock_names.append(query_stock_name)
            annul_reports.append(annul_report)

    generate_response(ids, queries, stock_full_names, query_stock_names, annul_reports)
    

if __name__ == "__main__":
    main()
