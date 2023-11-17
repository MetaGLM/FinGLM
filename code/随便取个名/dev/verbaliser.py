import os
import sys
import json

ratio_key_dict = {
    "流动比率" : ["流动资产", "流动负债"],
    "净利润率" : ["净利润", "营业收入"],
    "资产负债比率" : ["总负债", "资产总额"],
    "现金比率" : ["货币资金", "流动负债"],
    "净利润率" : ["净利润", "营业收入"],
    "流动负债比率" : ["流动负债", "总负债"],
    "非流动负债比率" : ["非流动负债", "总负债"],
    "财务费用率" : ["财务费用", "营业收入"],
    "管理费用率" : ["管理费用", "营业收入"],
    "营业成本率" : ["营业成本", "营业收入"],
    "营业利润率" : ["营业利润", "营业收入"],
    "投资收益占营业收入比率" : ["投资收益", "营业收入"],
    "企业研发经费与营业收入比值" : ["研发费用", "营业收入"],
    "企业研发经费与利润比值" : ["研发费用", "净利润"],
    "研发人员占职工人数比例" : ["研发人员数", "职工总数"],
    "净资产收益率" : ["净利润", "净资产"],
}


def make_key_label(category, key, stat_dict, company_name, date, company_names_dict):
    if stat_dict[key] == f"没有查询到对应的信息,无法回答":
        return f"没有查询到{int(date[0])}年{company_name}对应的{key}的有关信息。"
    template = f"NOT implement"
    # special question
    if category == 0:
        pass
    
    # basic info
    elif category == 1:
        DATE = date
        date = int(date[0])
        if key == "控股股东是否发生变更":
            if stat_dict[key] == "相同":
                template = f"{company_name}在{date}年的控股股东没有变更"
            elif stat_dict[key] == "不同":
                template = f"{company_name}在{date}年的控股股东发生了变更"
                
        elif key == '法定代表人是否相同':
            ret = stat_dict[key].split('|')
            if ret[0] == '相同':
                template = f"{company_name}在{DATE[0]}年到{DATE[-1]}年的法定代表人是相同，法定代表人均是{ret[1]}。"
            elif ret[0] == '不相同':
                template = f"{company_name}在{DATE[0]}年到{DATE[-1]}年的法定代表人是不相同的。"
                for i, name in enumerate(ret[1:]):
                    template += f"在{DATE[i]}年的法定代表人是{name}。"

        elif key in ['职工总数', '技术人员数', '博士及以上', '硕士人数', '研发人员数', '销售人员数']:
            template = f"{company_name}在{date}年的{key}是{stat_dict[key]}人。"
        elif key == "面临退市":
            if stat_dict[key] == '适用':
                template = f"{company_name}在{date}年，公司有面临退市的风险。"
            elif stat_dict[key] == '不适用':
                template = f"{company_name}在{date}年。公司报告期不存在面临退市或终止上市的情况。"
            elif stat_dict[key] == '未提及':
                template = f"{company_name}在{date}年的{key}情况没有提到相关内容。"

        elif key == "处罚及整改":
            if stat_dict[key] == '适用':
                template = f"{company_name}在{date}年，公司有相关的处罚及整改的情况。"
            elif stat_dict[key] == '不适用':
                template = f"{company_name}在{date}年，公司报告期不存在处罚及整改情况。"
            elif stat_dict[key] == '未提及':
                template = f"{company_name}在{date}年的{key}情况没有提到相关内容。"

        elif key == "破产重整相关":
            if stat_dict[key] == '适用':
                template = f"{company_name}在{date}年的{key}，公司有相关的破产重整的风险。"
            elif stat_dict[key] == '不适用':
                template = f"{company_name}在{date}年的{key}。公司报告期未发生破产重整相关事项。"
            elif stat_dict[key] == '未提及':
                template = f"{company_name}在{date}年的{key}情况没有提到相关内容"

        else:
            template = f"{company_name}在{date}年的{key}是{stat_dict[key]}。"
    
    # ratio keys
    elif category == 2:
        date = int(date[0])
        if key.endswith('增长率'):
            if key == '现金及现金等价物增长率':
                _key = '期末现金及现金等价物余额'
            elif key == '流动负债增长率':
                _key = '流动负债'
            elif key == '总资产增长率':
                _key = '资产总额'
            elif key == '总负债增长率':
                _key = '总负债'
            else:
                _key = key[:-3]
                
            template = f"{company_name}在{date-1}年的{_key}为{stat_dict['去年']}元，在{date}年的{_key}为{stat_dict['今年']}元，根据公式{key}=({_key}-上年{_key})/上年{_key}，得出{company_name}在{date}年的{key}是{stat_dict[key]}。"
        
        elif key == '速动比率':
            template = f"{company_name}在{date}年的流动资产合计为{stat_dict['流动资产']}元，在{date}年的存货为{stat_dict['存货']}元，在{date}年的流动负债合计为{stat_dict['流动负债']}元，根据公式速动比率=(流动资产-存货)/流动负债，得出{company_name}在{date}年的速动比率是{stat_dict[key]}。"
            
        elif key == '毛利率':
            template = f"{company_name}在{date}年的营业收入为{stat_dict['营业收入']}元，在{date}年的营业成本为{stat_dict['营业成本']}元，根据公式毛利率=(营业收入-营业成本)/营业收入，得出{company_name}在{date}年的毛利率是{stat_dict[key]}。"
            
        elif key == '企业研发经费占费用比例':
            template = f"{company_name}在{date}年的研发费用为{stat_dict['研发费用']}元，销售费用为{stat_dict['销售费用']}元，财务费用为{stat_dict['财务费用']}元，管理费用为{stat_dict['管理费用']}元，根据公式，企业研发经费占费用比例=研发费用/(销售费用+管理费用+财务费用+研发费用)，得出结果为{date}年{company_name}的企业研发经费占费用比例是{stat_dict[key]}。"
            
        elif key == '三费比重':
            template = f"{company_name}在{date}年的销售费用为{stat_dict['销售费用']}元，管理费用为{stat_dict['管理费用']}元，财务费用为{stat_dict['财务费用']}元，营业收入为{stat_dict['营业收入']}元，根据公式，三费比重=(销售费用+管理费用+财务费用)/营业收入，得出结果为{company_name}在{date}年的三费比重是{stat_dict[key]}。"
        
        elif key == '企业硕士及以上人员占职工人数比例':
            template = f"{company_name}在{date}年的硕士人数是{stat_dict['硕士人数']}人，博士及以上人数是{stat_dict['博士及以上']}人，职工总数是{stat_dict['职工总数']}，根据公式，企业硕士及以上人员占职工人数比例=(硕士人数+博士及以上人数)/职工总数，得出结果为{company_name}在{date}年的企业硕士及以上人员占职工人数比例{stat_dict[key]}。"
            
        elif key == '比例':
            pass
        
        else:
            key1, key2 = ratio_key_dict[key]
            template = f"{company_name}在{date}年的{key1}为{stat_dict[key1]}元，在{date}年的{key2}为{stat_dict[key2]}元，根据公式{key}={key1}/{key2}，得出{company_name}在{date}的{key}是{stat_dict[key]}。"
            if key == "研发人员占职工人数比例":
                template = template.replace("元", "人")
                        
    # finacial keys
    elif category == 3:
        date = int(date[0])
        if '和' in key and key not in ['联营企业和合营企业的投资收益', '负债和所有者权益总计']:
            key1, key2 = key.split('和')[0], key.split('和')[1]
            template = f"{company_name}在{date}年的{key1}是{stat_dict[key1]}元，{key2}是{stat_dict[key2]}元。"
        elif key == "股本" or key == "实收资本":
            template = f"{company_name}在{date}年的实收资本，股本是{stat_dict[key]}元。"
        else:
            template = f"{company_name}在{date}年的{key}是{stat_dict[key]}元。"
    
    elif category == 4:
        related_info = [f"相关信息{i} : {stat_dict[key][i]}" for i in range(len(stat_dict[key]))]
        template = "\n\n".join(related_info)

    # SQL query
    elif category == 5:
        date = int(date[0])
        if len(stat_dict[key]) == 0:
            template = f"{date}年，没有上市公司满足在的{key}题目要求的。"
        else:
            template = f"在{date}年的满足{key}题目要求的上市公司有:"
            for ans in stat_dict[key]:
                
                template += f"{company_names_dict.get(ans[0], '不清楚公司名')}。"
                if len(ans) > 1:
                    if isinstance(ans[1], float):
                        round_ret = str(ans[1]) + '0' * (2 - len(str(ans[1]).split('.')[1]))
                        template += f"金额是{round_ret + '元'}。"
                    else:
                        template += f"金额是{str(ans[1]) + '元'}。"
                    

    elif stat_dict == None:
        # 无法回答的问题
        template = f'*****'

    return template

def make_label(samples):
    # according to keys
    company_names_dict = {}
    with open('data/company_names.txt', 'r', encoding='utf-8') as f:
        for line in f.readlines():
            name, short_name = line.strip().split(":")
            company_names_dict[short_name] = name

    for sample in samples:
        keys = sample['task_key']
        company_name = sample['Company_name']
        date = sample['DATE']
        
        sample['prompt'] = ""        
        if "stat_dict" not in sample: continue
        stat_dict = sample['stat_dict']

        
        if len(keys) == 1:
            template = make_key_label(sample['category'], keys[0], stat_dict, company_name, date, company_names_dict)
            sample['prompt'] += template
        else:
            sample['prompt'] = f"{company_name}在{date[0]}年的"
            for key in keys:
                template = make_key_label(sample['category'], key, stat_dict, company_name, date, company_names_dict)
                if template.startswith(f"{company_name}在{date[0]}年的"):
                    sample['prompt'] += template.replace(f"{company_name}在{date[0]}年的", "")
                else:
                    sample['prompt'] += f"{key}没有相关信息。"

        if company_names_dict.get(company_name, "None") in sample['question']:
            sample['prompt'] = sample['prompt'].replace(company_name, company_names_dict[company_name])