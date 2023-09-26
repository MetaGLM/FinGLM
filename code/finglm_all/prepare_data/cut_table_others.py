import glob
import json
import re
import time
import pandas as pd
from multiprocessing import Pool

def process_file2(file_name):
    '''
    Args:
        file_name:

    Returns:

    '''
    allname = file_name.split('\\')[-1]
    date, name, stock, short_name, year, else1 = allname.split('__')
    cut1, cut2, cut3, cut4, cut5, cut6, cut7, cut8, cut9, cut10 = '', '', '', '', '', '', '', '', '', ''
    check_cut1, check_cut2, check_cut3, check_cut4, check_cut5, check_cut6, check_cut7, check_cut8, check_cut9, check_cut10 = False, False, False, False, False, False, False, False, False, False
    cut11, cut12, cut13, cut14, cut15, cut16, cut17, cut18, cut19, cut20 = '', '', '', '', '', '', '', '', '', ''
    check_cut11, check_cut12, check_cut13, check_cut14, check_cut15, check_cut16, check_cut17, check_cut18, check_cut19, check_cut20 = False, False, False, False, False, False, False, False, False, False
    cut21, cut22, cut23, cut24, cut25, cut26, cut27, cut28, cut29, cut30 = '', '', '', '', '', '', '', '', '', ''
    check_cut21, check_cut22, check_cut23, check_cut24, check_cut25, check_cut26, check_cut27, check_cut28, check_cut29, check_cut30 = False, False, False, False, False, False, False, False, False, False
    with open(file_name, 'r',encoding='utf-8') as file:

        lines = file.readlines()
        for i in range(len(lines)):
            line = lines[i]
            line = line.replace('\n', '')
            line_dict = json.loads(line)
            # print(line_dict)
            try:
                if line_dict['type'] not in ['页眉', '页脚']:

                    def check_answers(answer, keywords_re, keywords_stop_re, check_cut):
                        if check_cut == False and answer=='' and re.search(keywords_re, line_dict['inside']):
                            check_cut = True
                            answer = str(line_dict['inside']).replace("",'')
                        elif re.search(keywords_stop_re, line_dict['inside']) or len(answer)>=2000 \
                                or len(re.findall('是.否', answer))>=2\
                                or len(re.findall('适用.不适用', answer))>=2\
                                or len(re.findall('第(?:一|二|三|四|五|六|七|八|九|十)节', answer))>=2:
                            check_cut = False
                        elif check_cut == True:
                            answer = answer + '\n' + str(line_dict['inside']).replace("",'')
                        return answer, check_cut

                    def check_answers2(answer, keywords_re, keywords_stop_re, check_cut):
                        if check_cut == False and answer=='' and re.search(keywords_re, line_dict['inside']):
                            check_cut = True
                            answer = str(line_dict['inside']).replace("",'')
                        elif re.search(keywords_stop_re, line_dict['inside']) or len(answer)>=2000 \
                                or len(re.findall('第(?:一|二|三|四|五|六|七|八|九|十)节', answer))>=2:
                            check_cut = False
                        elif check_cut == True:
                            answer = answer + '\n' + str(line_dict['inside']).replace("",'')
                        return answer, check_cut

                    cut1, check_cut1 = check_answers(cut1, "(?:\.|、|\)|）)(?:审计意见|保留意见)$",
                                                     "(?:形成审计意见的基础|形成保留意见的基础)$", check_cut1)
                    cut2, check_cut2 = check_answers(cut2, "(?:关键审计事项)$",
                                                     "(?:其他信息)$", check_cut2)
                    cut3, check_cut3 = check_answers(cut3, "主要会计数据和财务指标",
                                                     "分季度主要财务指标", check_cut3)
                    cut4, check_cut4 = check_answers(cut4, "公司主要销售客户情况",
                                                     "公司主要供应商情况", check_cut4)
                    cut5, check_cut5 = check_answers(cut5, "公司主要供应商情况",
                                                     "研发投入|费用", check_cut5)
                    cut6, check_cut6 = check_answers2(cut6, "(?:研发投入|近三年公司研发投入金额及占营业收入的比例)$",
                                                     "现金流", check_cut6)
                    cut7, check_cut7 = check_answers(cut7, "(?:现金流)$",
                                                     "非主营业务情况", check_cut7)
                    cut8, check_cut8 = check_answers(cut8, "(?:资产及负债状况)$",
                                                     "投资状况分析", check_cut8)
                    cut9, check_cut9 = check_answers(cut9, "重大资产和股权出售",
                                                     "主要控股参股公司分析", check_cut9)
                    cut10, check_cut10 = check_answers(cut10, "主要控股参股公司分析",
                                                       "公司未来发展的展望", check_cut10)
                    cut11, check_cut11 = check_answers(cut11, "公司未来发展的展望",
                                                       "接待调研、沟通、采访等活动登记表", check_cut11)
                    cut12, check_cut12 = check_answers(cut12, "与上年度财务报告相比，合并报表范围发生变化的情况说明",
                                                       "聘任、解聘会计师事务所情况", check_cut12)
                    cut13, check_cut13 = check_answers2(cut13, "聘任、解聘会计师事务所情况",
                                                        "面临(?:暂停上市|终止上市|退市).{0,10}情况", check_cut13)
                    cut14, check_cut14 = check_answers(cut14, "面临(?:暂停上市|终止上市|退市).{0,10}情况",
                                                       "破产重整相关事项", check_cut14)
                    cut15, check_cut15 = check_answers(cut15, "破产重整相关事项",
                                                       "重大诉讼、仲裁事项", check_cut15)
                    cut16, check_cut16 = check_answers(cut16, "重大诉讼、仲裁事项",
                                                       "处罚及整改情况", check_cut16)
                    cut17, check_cut17 = check_answers(cut17, "处罚及整改情况",
                                                       "公司及其控股股东、实际控制人的诚信状况", check_cut17)
                    cut18, check_cut18 = check_answers(cut18, "公司及其控股股东、实际控制人的诚信状况",
                                                       "公司股权激励计划、员工持股计划或其他员工激励措施的实施情况", check_cut18)
                    cut19, check_cut19 = check_answers2(cut19, "重大关联交易", "重大合同及其履行情况", check_cut19)
                    cut20, check_cut20 = check_answers2(cut20, "重大合同及其履行情况", "其他重大事项的说明", check_cut20)
                    cut21, check_cut21 = check_answers(cut21, "重大环保问题|环境保护相关的情况",
                                                       "社会责任情况|重要事项|股份变动情况|其他重大事项的说明", check_cut21)
                    cut22, check_cut22 = check_answers(cut22, "社会责任情况",
                                                       "重要事项|股份变动情况|其他重大事项的说明", check_cut22)
                    cut23, check_cut23 = check_answers(cut23, "公司董事、监事、高级管理人员变动情况", "任职情况", check_cut23)
                    cut24, check_cut24 = check_answers2(cut24, "公司员工情况", "培训计划",
                                                       check_cut24)
                    cut25, check_cut25 = check_answers(cut25, "对会计师事务所本报告期“非标准审计报告”的说明",
                                                        "董事会对该事项的意见|独立董事意见|监事会意见|消除有关事项及其影响的具体措施",
                                                        check_cut25)
                    cut26, check_cut26 = check_answers(cut26, "公司控股股东情况",
                                                       "同业竞争情况|重大事项",
                                                       check_cut26)
                    cut27, check_cut27 = check_answers(cut27, "(?:\.|、|\)|）)(?:审计报告)$",
                                                       "审计报告正文|(?:\.|、|\)|）)(?:审计意见|保留意见)$",
                                                       check_cut27)
                    # 核心竞争力分析
                    # 主营业务分析
                    # 费用
                    # 股东和实际控制人情况  公司股东数量及持股情况 公司控股股东情况 公司实际控制人及其一致行动人 其他持股在10%以上的法人股东
                    # 同业竞争情况

            except:
                print(line_dict)
    new_row = {'文件名': allname,
               '日期': date, '公司名称': name, '股票代码': stock, '股票简称': short_name, '年份': year, '类型': '年度报告',
               '审计意见': cut1, '关键审计事项': cut2, '主要会计数据和财务指标': cut3,
               '主要销售客户': cut4, '主要供应商': cut5,
               '研发投入': cut6, '现金流': cut7,
               '资产及负债状况': cut8, '重大资产和股权出售': cut9, '主要控股参股公司分析': cut10, '公司未来发展的展望': cut11,
               '合并报表范围发生变化的情况说明': cut12, '聘任、解聘会计师事务所情况': cut13, '面临退市情况': cut14,
               '破产重整相关事项': cut15, '重大诉讼、仲裁事项': cut16, '处罚及整改情况': cut17,
               '公司及其控股股东、实际控制人的诚信状况': cut18, '重大关联交易': cut19, '重大合同及其履行情况': cut20,
               '重大环保问题': cut21, '社会责任情况': cut22, '公司董事、监事、高级管理人员变动情况': cut23, '公司员工情况': cut24,
               '非标准审计报告的说明': cut25, '公司控股股东情况': cut26, '审计报告': cut27,
               '全文': str(lines)}
    print('结束 '+file_name)
    return new_row
# 文件夹路径
folder_path = '../alltxt'
# 获取文件夹内所有文件名称
file_names = glob.glob(folder_path + '/*')
file_names = sorted(file_names, reverse=True)
# file_names=file_names[:1000]
results = []
# 打印文件名称
df = pd.DataFrame(columns=[
    '文件名',
    '日期', '公司名称', '股票代码', '股票简称', '年份', '类型',
    '审计意见', '关键审计事项', '主要会计数据和财务指标',
    '主要销售客户', '主要供应商', '研发投入', '现金流', '资产及负债状况', '重大资产和股权出售',
    '主要控股参股公司分析', '公司未来发展的展望', '合并报表范围发生变化的情况说明',
    '聘任、解聘会计师事务所情况', '面临退市情况', '破产重整相关事项', '重大诉讼、仲裁事项', '处罚及整改情况',
    '公司及其控股股东、实际控制人的诚信状况', '重大关联交易', '重大合同及其履行情况',
    '重大环保问题', '社会责任情况', '公司董事、监事、高级管理人员变动情况', '公司员工情况', '非标准审计报告的说明', '公司控股股东情况',
    '审计报告',
    '全文'])


with Pool(processes=7) as pool:
    results = pool.map(process_file2, file_names)

df = pd.DataFrame(results)
time.sleep(5)
df.to_excel("big_data3.xlsx", index=False)





