import json
import os
import random
import numpy as np

random.seed(2)

attr_dict = {'single_attr':[['硕士'], ['硕士及以上'], ['博士', '博士及以上'], ['研发人员'], ['技术人员'], 
                            ['职工总数', '员工总数', '员工人数', '职工总人数']],
             'multi_attr':[['硕士及以上'], ['研发人员']]}

table_attr_dict = {'single_attr':[['硕士', '硕士研究生'], ['硕士及以上', '研究生', '硕士'], ['博士', '博士及以上'], ['研发人员'], ['技术人员'], 
                            ['在职员工的数量合计', '合计']],
                    'multi_attr':[['硕士及以上', '研究生', '硕士'], ['研发人员']]}

max_count = 125

prompt = "现在给你若干个包含公司员工信息和研发信息的表格,请你根据表格的内容正确回答问题:\n"

attribute_template = {
    'single_attr': [
        {
            "question": "<company_name>在<year>年的<attribute>人员数量是多少?",
            "answer": "<company_name>在<year>年的<attribute>人员数量是<value>人。"
        },{
            "question": "请提供<company_name><year>年的<attribute>人数.",
            "answer": "<company_name><year>年的<attribute>人数是<value>人。"
        },{
            "question": "<year>年<company_name><attribute>人数是什么?",
            "answer": "<year>年<company_name><attribute>的人数是<value>人。"
        },{
            "question": "<company_name><year>年有多少<attribute>人员?",
            "answer": "<company_name><year>年的<attribute>人员有<value>人。"
        },
        {
            "question": "提供江<company_name><year>年<attribute>的员工人数，单位为人。",
            "answer": "<company_name><year>年的<attribute>人员有<value>人。"
        }
        
    ],
    'multi_attr': [
        {
            "question": "<company_name>在<year>年的<attribute>占职工人数的比例是多少？请保留2位小数。",
            "answer": "<company_name><year>年的<attribute>是<value1>人，职工人数是<value2>人，根据公式<attribute>占职工人数的比例=<attribute>/职工人数，得出结果<company_name><year>年的<attribute>占职工人数的比例是{<value1>/<value2>}。"
        },{
            "question": "<company_name>在<year>年中，<attribute>占职工人数的比例是多少，结果请保留两位小数.",
            "answer": "<company_name><year>年的<attribute>是<value1>人，职工人数是<value2>人，根据公式<attribute>占职工人数的比例=<attribute>/职工人数，得出结果<company_name><year>年的<attribute>占职工人数的比例是{<value1>/<value2>}。"
        },{
            "question": "在<year>年中，<company_name>的<attribute>占职工人数的比率是多少（保留到小数点后两位）？",
            "answer": "<company_name><year>年的<attribute>是<value1>人，职工人数是<value2>人，根据公式<attribute>占职工人数的比例=<attribute>/职工人数，得出结果<company_name><year>年的<attribute>占职工人数的比例是{<value1>/<value2>}。"
        },{
            "question": "在<year>年中，<company_name>的<attribute>占职工人数的比率是多少，保留到小数点后两位？",
            "answer": "<company_name><year>年的<attribute>是<value1>人，职工人数是<value2>人，根据公式<attribute>占职工人数的比例=<attribute>/职工人数，得出结果<company_name><year>年的<attribute>占职工人数的比例是{<value1>/<value2>}。"
        },{
            "question": "请告诉我<year>年<company_name>的年报中，<attribute>占职工人数比例保留两位小数为多少。",
            "answer": "<company_name><year>年的<attribute>是<value1>人，职工人数是<value2>人，根据公式<attribute>占职工人数的比例=<attribute>/职工人数，得出结果<company_name><year>年的<attribute>占职工人数的比例是{<value1>/<value2>}。"
        },{
            "question": "请提供<company_name><year>年的<attribute>占职工人数比例保留两位小数为多少。",
            "answer": "<company_name><year>年的<attribute>是<value1>人，职工人数是<value2>人，根据公式<attribute>占职工人数的比例=<attribute>/职工人数，得出结果<company_name><year>年的<attribute>占职工人数的比例是{<value1>/<value2>}。"
        },
    ],
    'special_template': [
        {
            "question": "<company_name>在<year>年的<attribute>人员数量是多少？",
            "answer": "<company_name>在<year>年的博士人员数量是<value1>人， 硕士人员数量是<value2>人，硕士及以上人数是{<value1>+<value2>}人。"
        },{
            "question": "请提供<company_name><year>年的<attribute>人数.",
            "answer": "<company_name><year>年的博士人员人数是<value1>人， 硕士人员人数是<value2>人，硕士及以上人数是{<value1>+<value2>}人。"
        },{
            "question": "<year>年<company_name><attribute>人数是什么?",
            "answer": "<year>年<company_name>博士的人数是<value1>人， 硕士的人数是<value2>人，硕士及以上人数是{<value1>+<value2>}人。"
        },{
            "question": "<company_name><year>年有多少<attribute>人员?",
            "answer": "<company_name><year>年的博士人员有<value1>人， 硕士人员有<value2>人，硕士及以上人员有{<value1>+<value2>}人。"
        },{
            "question": "提供江<company_name><year>年<attribute>的员工人数，单位为人。",
            "answer": "<company_name><year>年的博士人员有<value1>人， 硕士人员有<value2>人，硕士及以上人员有{<value1>+<value2>}人。"
        }
    ],
    'multi_special_template': [
        {
            "question": "<company_name>在<year>年的硕士及以上人数占职工人数的比例是多少？请保留2位小数。",
            "answer": "<company_name>在<year>年的博士人员数量是<value1>人， 硕士人员数量是<value2>人，硕士及以上人数是{<value1>+<value2>}人，职工人数是<value3>人，根据公式硕士及以上人数占职工人数的比例=(硕士人数+博士及以上人数)/职工人数，得出结果<company_name>在<year>年的硕士及以上人数占职工人数的比例是{(<value1>+<value2>)/<value3>}。"
        },{
            "question": "<company_name>在<year>年中，硕士及以上人数占职工人数的比率是多少，结果请保留两位小数.",
            "answer": "<company_name>在<year>年的博士人员数量是<value1>人， 硕士人员数量是<value2>人，硕士及以上人数是{<value1>+<value2>}人，职工人数是<value3>人，根据公式硕士及以上人数占职工人数的比例=(硕士人数+博士及以上人数)/职工人数，得出结果<company_name>在<year>年的硕士及以上人数占职工人数的比率是{(<value1>+<value2>)/<value3>}。"
        },{
            "question": "在<year>年中，<company_name>的硕士及以上人数占职工人数的比例是多少（保留到小数点后两位）？",
            "answer": "<company_name>在<year>年的博士人员数量是<value1>人， 硕士人员数量是<value2>人，硕士及以上人数是{<value1>+<value2>}人，职工人数是<value3>人，根据公式硕士及以上人数占职工人数的比例=(硕士人数+博士及以上人数)/职工人数，得出结果<company_name>在<year>年的硕士及以上人数占职工人数的比例是{(<value1>+<value2>)/<value3>}。"
        },{
            "question": "请提供<company_name><year>年的企业硕士及以上人员占职工人数比例并保留2位小数",
            "answer": "<company_name>在<year>年的博士人员数量是<value1>人， 硕士人员数量是<value2>人，硕士及以上人数是{<value1>+<value2>}人，职工人数是<value3>人，根据公式硕士及以上人数占职工人数的比例=(硕士人数+博士及以上人数)/职工人数，得出结果<company_name>在<year>年的硕士及以上人数占职工人数的比例是{(<value1>+<value2>)/<value3>}。"
        },
    ],
}


excel_path = 'data/processed_excels'

def parse_file_name(file_name):
    time, long_company_name, code, short_company_name, year, _ = file_name.split('__')
    year = year.replace('年', '')
    return long_company_name, code, short_company_name, year

def process_json(path):
    excel_json = json.load(open(path, 'r', encoding = 'utf-8'))
    yg_excel = excel_json.get('员工数量、专业构成及教育程度')
    yf_excel = excel_json.get('研发投入')
    
    yg_table = None
    if yg_excel:
        yg_table = []
        for line in yg_excel:
            yg_table.append(line)

    yf_table = None
    if yf_excel:
        yf_table = []
        for line in yf_excel:
            yf_table.append(line)
         
    return yg_table, yf_table

def canonial_judge(table):
    try:
        if len(np.array(table).shape) != 1:
            return True
    except:
        pass
    return False

def find_info(table, attrs, year, mode = 'contain'):
    col_idx = -1
    for idx, ele in enumerate(table[0]):
        if year in ele:
            col_idx = idx
    if col_idx != -1 and canonial_judge(table):
        table = np.array(table)[:, [0, col_idx]]
    for idx in range(len(table)):
        key = table[idx][0]
        key = key.replace('硕士博士', '硕士及以上')
        key = key.replace('博士硕士', '硕士及以上')
        for attr in attrs:
            if mode == 'contain':
                if attr in key:
                    break
            elif mode == 'exact':
                if attr == key:
                    break
        else:
            continue
        for ele in table[idx]:
            ele = ele.replace(',', '')
            try:
                return int(ele)
            except:
                continue
    return False


def solve_single_question(year, attrs, table):
    bs_num = 0  #仅在硕士及以上时统计
    if attrs[0] == '硕士':
        num = find_info(table, attrs, year, mode = 'exact')
    elif '硕士及以上' in attrs:
        bs_num = find_info(table, ['博士'], year)
        if not bs_num:
            bs_num = 0
        num = bs_num + find_info(table, attrs, year)
    else:
        num = find_info(table, attrs, year)
    return num, bs_num

def main():
    excel_files = os.listdir(excel_path)
    result = []
    for attr_type in attr_dict:
        for idx, key_words in enumerate(attr_dict[attr_type]):
            count = 0
            while count < max_count:
                data = {}
                file = random.choice(excel_files)
                long_company_name, code, short_company_name, year = parse_file_name(file)
                company_name = random.choice([long_company_name, short_company_name])
                attribute = random.choice(key_words)
                
                yg_table, yf_table = process_json(os.path.join(excel_path, file))
                
                if not isinstance(yg_table, list) or not isinstance(yf_table, list):
                    continue
                
                if attr_type == 'single_attr':
                    if '研发人员' not in key_words:
                        table = yg_table
                    else:
                        table = yf_table
                    answer, bs_num = solve_single_question(year, table_attr_dict['single_attr'][idx], table)
                    if not answer:
                        continue
                    
                    if bs_num == 0:
                        value = answer
                        qa_pair = str(random.choice(attribute_template['single_attr']))
                        qa_pair = qa_pair.replace('<company_name>', company_name)
                        qa_pair = qa_pair.replace('<year>', year)
                        qa_pair = qa_pair.replace('<attribute>', attribute)
                        qa_pair = qa_pair.replace('<value>', str(value))
                    else:
                        value1 = bs_num
                        value2 = answer - bs_num
                        qa_pair = str(random.choice(attribute_template['special_template']))
                        qa_pair = qa_pair.replace('<company_name>', company_name)
                        qa_pair = qa_pair.replace('<year>', year)
                        qa_pair = qa_pair.replace('<attribute>', attribute)
                        qa_pair = qa_pair.replace('<value1>', str(value1))
                        qa_pair = qa_pair.replace('<value2>', str(value2))
                elif attr_type == 'multi_attr':
                    if '硕士及以上' in key_words:
                        numerator, bs_num = solve_single_question(year, table_attr_dict['multi_attr'][idx], yg_table)
                        ss_num = numerator - bs_num
                    else:
                        numerator, bs_num = solve_single_question(year, table_attr_dict['multi_attr'][idx], yf_table)
                    total, _ = solve_single_question(year, ['在职员工的数量合计', '合计'], yg_table)
                    if not numerator or not total:
                        continue
                    #answer = str(round(numerator/total, 2))
                    #if len(answer.split('.')[-1]) == 1:
                    #    answer += '0'
                    
                    if bs_num == 0:
                        value1 = numerator
                        value2 = total
                        qa_pair = str(random.choice(attribute_template['multi_attr']))
                        qa_pair = qa_pair.replace('<company_name>', company_name)
                        qa_pair = qa_pair.replace('<year>', year)
                        qa_pair = qa_pair.replace('<attribute>', attribute)
                        qa_pair = qa_pair.replace('<value1>', str(value1))
                        qa_pair = qa_pair.replace('<value2>', str(value2))
                    else:
                        value1 = bs_num
                        value2 = ss_num
                        value3 = total
                        qa_pair = str(random.choice(attribute_template['multi_special_template']))
                        qa_pair = qa_pair.replace('<company_name>', company_name)
                        qa_pair = qa_pair.replace('<year>', year)
                        #qa_pair = qa_pair.replace('<attribute>', attribute)
                        qa_pair = qa_pair.replace('<value1>', str(value1))
                        qa_pair = qa_pair.replace('<value2>', str(value2))
                        qa_pair = qa_pair.replace('<value3>', str(value3))
                        
                qa_pair = eval(qa_pair)
                data['prompt'] = prompt + '\n{}年{}员工数量、专业构成及教育程度表：'.format(year, company_name) + '\n'.join(' '.join(table) for table in yg_table) + \
                    '\n\n{}年{}研发投入表：'.format(year, company_name)  + '\n'.join(' '.join(table) for table in yf_table) + '\n\n' + qa_pair['question']
                data['response'] = qa_pair['answer']
                if len(data['prompt']) > 768:
                    continue
                count += 1
                result.append(data)
                print(count)
    random.shuffle(result)
    
    max_len = max([len(problem["response"]) for problem in result])
    output_file = open('finetune/table_qa/data/personal_information_augmentation_dev.json', 'w', encoding = 'utf-8') 
    for res in result:
        json.dump(res, output_file, ensure_ascii = False)
        output_file.write('\n')
    output_file.close()
    #with open('val.json', 'w', encoding = 'utf-8') as f:
    #    json.dump(result, f, indent = 4, ensure_ascii = False)

if __name__ == '__main__':
    main()