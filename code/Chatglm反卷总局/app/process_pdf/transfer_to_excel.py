import sys
import pickle
import pandas as pd
from collections import OrderedDict

def pad_stock_codes(stock_series):
    stock_series = stock_series.astype(str).str.strip()
    stock_series_padded = stock_series.str.zfill(6)
    return stock_series_padded

def process_csv_to_excel(csv_path, excel_path, columns, sep="\001"):
    data = pd.read_csv(csv_path, sep=sep, header=None)
    data.columns = columns
    data['报告年份'] = data['报告年份'].str.replace('年', '')
    data['年份'] = data['报告年份']
    data["股票代码"] = pad_stock_codes(data["股票代码"])
    data['股票代码'] = data['股票代码'].astype(str)
    data["证券代码"] = data['股票代码']
    try:
        data["证券简称"] = data['股票简称']
    except:
        pass
    try:
        data["证券简称"] = data['股票名称']
    except:
        pass
    data = data.astype(str)
    data = data.loc[:, ~data.columns.duplicated()]
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        data.to_excel(writer, index=False)
    # result_df = pd.read_excel(excel_path)
    # data["股票代码"] = pad_stock_codes(data["股票代码"])
    # data['证券代码'] = data['股票代码']
    # data.to_excel(excel_path, index=False)

profit_columns = [
    "报告年份",
    "信息来源",
    "股票代码",
    "股票简称",
    "营业总收入",
    "营业总成本",
    "税金及附加",
    "销售费用",
    "管理费用",
    "研发费用",
    "财务费用",
    "利息支出",
    "利息收入",
    "公允价值变动收益",
    "投资收益",
    "营业利润",
    "营业外收入",
    "营业外支出",
    "利润总额",
    "所得税费用",
    "净利润",
    "其他收益",
    "综合收益总额",
    "基本每股收益",
    "稀释每股收益",
    "归属母公司所有者净利润",
    "对联营企业和合营企业的投资收益",
    "营业收入",
    "营业成本",
    "已赚保费",
    "手续费及佣金收入",
    "手续费及佣金支出",
    "退保金",
    "赔付支出净额",
    "提取保险责任准备金净额",
    "保单红利支出",
    "分保费用",
    "汇兑收益",
    "净敞口套期收益",
    "信用减值损失",
    "资产减值损失",
    "资产处置收益",
    "持续经营净利润",
    "终止经营净利润",
    "少数股东损益",
    "归属于母公司所有者的综合收益总额",
    "归属于少数股东的综合收益总额"
]
cash_columns = [
    "报告年份",
    "信息来源",
    "股票代码",
    "股票简称",
    "销售商品、提供劳务收到的现金",
    "收到的税费返还",
    "收到其他与经营活动有关的现金",
    "购买商品、接受劳务支付的现金",
    "支付给职工以及为职工支付的现金",
    "支付的各项税费",
    "支付其他与经营活动有关的现金",
    "经营活动产生的现金流量净额",
    "收回投资收到的现金",
    "取得投资收益收到的现金",
    "处置固定资产、无形资产和其他长期资产收回的现金净额",
    "处置子公司及其他营业单位收到的现金净额",
    "购建固定资产、无形资产和其他长期资产支付的现金",
    "投资支付的现金",
    "支付其他与投资活动有关的现金",
    "投资活动产生的现金流量净额",
    "吸收投资收到的现金",
    "取得借款收到的现金",
    "偿还债务支付的现金",
    "分配股利、利润或偿付利息支付的现金",
    "筹资活动产生的现金流量净额",
    "汇率变动对现金及现金等价物的影响",
    "期初现金及现金等价物余额",
    "期末现金及现金等价物余额",
    "现金的期末余额"
]
balance_columns = [
    "报告年份",
    "信息来源",
    "股票代码",
    "股票简称",
    "货币资金",
    "应收票据",
    "应收利息",
    "应收账款",
    "其他应收款",
    "预付款项",
    "存货",
    "一年内到期的非流动资产",
    "其他流动资产",
    "投资性房地产",
    "长期股权投资",
    "长期应收款",
    "固定资产",
    "在建工程",
    "无形资产",
    "商誉",
    "长期待摊费用",
    "递延所得税资产",
    "其他非流动资产",
    "短期借款",
    "应付票据",
    "应付账款",
    "预收款项",
    "应付职工薪酬",
    "应付股利",
    "应交税费",
    "应付利息",
    "其他应付款",
    "一年内到期的非流动负债",
    "其他流动负债",
    "长期借款",
    "应付债券",
    "长期应付款",
    "预计负债",
    "递延所得税负债",
    "其他非流动负债",
    "实收资本",
    "资本公积",
    "盈余公积",
    "未分配利润",
    "其他综合收益",
    "长期应付职工薪酬",
    "递延收益",
    "合同资产",
    "其他非流动金融资产",
    "应付票据及应付账款",
    "合同负债",
    "其他权益工具投资",
    "总负债",
    "总资产",
    "所有者权益合计",
    "衍生金融资产",
    "应收款项融资",
    "股本",
    "结算备付金",
    "拆出资金",
    "应收票据",
    "交易性金融资产",
    "少数股东权益",
    "负债和所有者权益",
    "应收保费",
    "应收分保账款",
    "应收分保合同准备金",
    "应收股利",
    "买入返售金融资产",
    "持有待售资产",
    "发放贷款和垫款",
    "债权投资",
    "可供出售金融资产",
    "其他债权投资",
    "持有至到期投资",
    "生产性生物资产",
    "油气资产",
    "使用权资产",
    "开发支出",
    "向中央银行借款",
    "拆入资金",
    "交易性金融负债",
    "衍生金融负债",
    "卖出回购金融资产款",
    "吸收存款及同业存放",
    "代理买卖证券款",
    "代理承销证券款",
    "应付手续费及佣金",
    "应付分保账款",
    "持有待售负债",
    "保险合同准备金",
    "优先股",
    "永续债",
    "租赁负债",
    "资本公积",
    "库存股",
    "专项储备",
    "一般风险准备",
    "少数股东权益",
    "归属于母公司所有者权益"
]
balance_static_columns = [
    "报告年份",
    "信息来源",
    "股票代码",
    "股票简称",
    "流动资产合计",
    "非流动资产合计",
    "流动负债合计",
    "非流动负债合计"
]
people_columns = [
    "报告年份",
    "信息来源",
    "股票代码",
    "股票简称",
    "职工人数",
    "研发人员",
    "研发人员比率",
    "硕士人数",
    "硕士以上人数",
    "博士人数",
    "博士以上人数",
    "生产人员",
    "销售人员",
    "技术人员",
    "财务人员",
    "行政人员"
]
basic_columns = [
    "报告年份",
    "信息来源",
    "股票代码",
    "股票简称",
    "办公地址",
    "注册地址",
    "公司邮箱",
    "法定代表人",
    "公司网址"
]

def process_all_csv_to_excel(csv_path_dict, excel_path, sep="\001"):
    profit_csv_path = csv_path_dict['profit']
    cashflow_csv_path = csv_path_dict['cashflow']
    balance_csv_path = csv_path_dict['balance']
    balance_static_csv_path = csv_path_dict['balance_static']
    people_csv_path = csv_path_dict['people']
    baseinfo_csv_path = csv_path_dict['baseinfo']

    profit_df = pd.read_csv(profit_csv_path, sep=sep, header=None)
    profit_df.columns = profit_columns

    cashflow_df = pd.read_csv(cashflow_csv_path, sep=sep, header=None)
    cashflow_df.columns = cash_columns
    cashflow_df = cashflow_df.drop(['股票代码','信息来源'],axis=1)

    balance_df = pd.read_csv(balance_csv_path, sep=sep, header=None)
    balance_df.columns = balance_columns
    balance_df = balance_df.drop(['股票代码','信息来源'],axis=1)
    balance_df = balance_df.loc[:, ~balance_df.columns.duplicated()]

    balance_static_df = pd.read_csv(balance_static_csv_path, sep=sep, header=None)
    balance_static_df.columns = balance_static_columns
    balance_static_df = balance_static_df.drop(['股票代码','信息来源'],axis=1)

    people_df = pd.read_csv(people_csv_path, sep=sep, header=None)
    people_df.columns = people_columns
    people_df = people_df.drop(['股票代码','信息来源'],axis=1)

    baseinfo_df = pd.read_csv(baseinfo_csv_path, sep=sep, header=None)
    baseinfo_df.columns = basic_columns
    baseinfo_df = baseinfo_df.drop(['股票代码','信息来源'],axis=1)

    merge_columns = ['报告年份','股票简称']
    all_data_df = pd.merge(profit_df,cashflow_df,on=merge_columns).merge(balance_df,on=merge_columns).merge(balance_static_df,on=merge_columns).merge(people_df,on=merge_columns).merge(baseinfo_df,on=merge_columns)
    all_data_df['报告年份'] = all_data_df['报告年份'].str.replace('年', '')
    all_data_df['年份'] = all_data_df['报告年份']
    all_data_df["股票代码"] = pad_stock_codes(all_data_df["股票代码"])
    all_data_df["证券代码"] = all_data_df['股票代码']
    all_data_df["证券简称"] = all_data_df['股票简称']
    # all_data_df['公司全称'] = all_data_df['股票简称'].apply(lambda x:com_short_mapping_full_name[x])
    # 临时改动
    baiwan = [
        '2020-03-21__招商银行股份有限公司__600036__招商银行__2019年__年度报告',
        '2020-03-28__中国神华能源股份有限公司__601088__中国神华__2019年__年度报告',
        '2020-03-28__鞍钢股份有限公司__000898__鞍钢股份__2019年__年度报告',
        '2020-03-30__中国石油化工股份有限公司__600028__中国石化__2019年__年度报告',
        '2021-03-20__招商银行股份有限公司__600036__招商银行__2020年__年度报告',
        '2021-03-26__中国人寿保险股份有限公司__601628__中国人寿__2020年__年度报告',
        '2021-03-27__中国神华能源股份有限公司__601088__中国神华__2020年__年度报告',
        '2021-03-29__中国石油化工股份有限公司__600028__中国石化__2020年__年度报告',
        '2021-03-31__鞍钢股份有限公司__000898__鞍钢股份__2020年__年度报告',
        '2022-03-19__招商银行股份有限公司__600036__招商银行__2021年__年度报告',
        '2022-03-25__中国人寿保险股份有限公司__601628__中国人寿__2021年__年度报告',
        '2022-03-26__中国神华能源股份有限公司__601088__中国神华__2021年__年度报告',
        '2022-03-28__中国石油化工股份有限公司__600028__中国石化__2021年__年度报告',
        '2022-03-31__鞍钢股份有限公司__000898__鞍钢股份__2021年__年度报告',
    ]
    for b in baiwan:
        items = b.split('__')
        year = items[-2].strip('年')
        com = items[-3]
        try:
          i = all_data_df[all_data_df['股票简称'] == com][all_data_df['年份'] == year].index[0]
        except:
          print(items)
          continue
        temp_columns = [c for c in profit_columns+balance_columns+balance_static_columns+cash_columns if c not in ["报告年份","信息来源","股票代码","股票简称"]]
        for j in temp_columns:
            old_num = all_data_df.loc[i,j]
            if old_num == -1:
                continue
            new_num = old_num * 1000000
            all_data_df.loc[i,j] = new_num
    all_data_df = all_data_df.astype(str)
    all_data_df.to_excel(excel_path, index=False)


if __name__ == '__main__':
    # combine_data_path = 'E:\\combine_data\\'
    combine_data_path = sys.argv[1]
    process_csv_to_excel(combine_data_path+'profit.csv', combine_data_path+'profit_statement.xlsx', profit_columns)
    process_csv_to_excel(combine_data_path+'cashflow.csv', combine_data_path+'cash_flow_statement.xlsx', cash_columns)
    process_csv_to_excel(combine_data_path+'balance.csv', combine_data_path+'balance_sheet.xlsx', balance_columns)
    process_csv_to_excel(combine_data_path+'balance_static.csv', combine_data_path+'balance_static.xlsx', balance_static_columns)
    process_csv_to_excel(combine_data_path+'people.csv', combine_data_path+'people.xlsx', people_columns)
    process_csv_to_excel(combine_data_path+'baseinfo.csv', combine_data_path+'baseinfo.xlsx', basic_columns)
    csv_path_dict = {'profit':combine_data_path+'profit.csv',
                     'cashflow':combine_data_path+'cashflow.csv',
                     'balance':combine_data_path+'balance.csv',
                     'balance_static':combine_data_path+'balance_static.csv',
                     'people':combine_data_path+'people.csv',
                     'baseinfo':combine_data_path+'baseinfo.csv',
                     }
    # com_short_mapping_full_name = pickle.load(open(combine_data_path+'com_short_mapping_full_name.pkl','rb'))
    process_all_csv_to_excel(csv_path_dict, combine_data_path+'all_data.xlsx', sep="\001")
