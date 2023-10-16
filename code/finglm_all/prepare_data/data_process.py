import pandas as pd

# 合并三个原始表
# 读取三个Excel文件
df1 = pd.read_excel("big_data1.xls", engine='openpyxl')
df2 = pd.read_excel("big_data2.xls", engine='openpyxl')
df3 = pd.read_excel("big_data3.xls", engine='openpyxl')
df4 = pd.read_excel('industry.xlsx', engine='openpyxl')

# 检查这三个文件中的"文件名"列是否都存在
if "文件名" not in df1.columns or "文件名" not in df2.columns or "文件名" not in df3.columns:
    raise ValueError("One of the Excel files does not have the '文件名' column.")

# 使用“文件名”列横向合并三个DataFrame
df = df1.merge(df2, on="文件名", how='inner').merge(df3, on="文件名", how='inner').merge(df4, on="文件名", how='inner')

# 保存合并后的DataFrame到新的Excel文件
df.to_excel("big_data_old.xlsx", engine='openpyxl', index=False)

# # 从Excel文件中读取数据
# df = pd.read_excel("big_data_old.xlsx", engine='openpyxl')
df['行业名称'] = ''
for row in range(len(df)):
    if df['申万行业'][row] != '其他':
        df['行业名称'][row] = str(df['申万行业'][row]).split('--')[0] + '--' + str(df['申万行业'][row]).split('--')[1]
    else:
        df['行业名称'][row] = str(df['申万行业'][row])

name_list = [
    '在建工程', '无形资产', '商誉', '其他流动资产', '其他非流动资产', '非流动资产合计', '资产总计',
    '短期借款', '应付票据', '应付账款', '应付职工薪酬', '应交税费', '长期借款', '流动负债', '非流动负债', '负债合计',
    '股本', '销售费用', '管理费用', '研发费用', '财务费用', '投资收益',
    '营业总收入', '营业收入', '营业总成本', '营业成本', '营业外收入', '营业外支出', '营业利润', '利润总额', '净利润'
]
for name in name_list:
    df[name + 'new'] = ''

new_name_list = {
    '营业成本率': {'公式': '营业成本率=营业成本/营业收入', '数值': ['营业成本', '营业收入']},
    '投资收益占营业收入比率': {'公式': '投资收益占营业收入比率=投资收益/营业收入', '数值': ['投资收益', '营业收入']},
    '管理费用率': {'公式': '管理费用率=管理费用/营业收入', '数值': ['管理费用', '营业收入']},
    '财务费用率': {'公式': '财务费用率=财务费用/营业收入', '数值': ['财务费用', '营业收入']},
    '三费比重': {'公式': '三费比重=(销售费用+管理费用+财务费用)/营业收入', '数值': ['销售费用', '管理费用', '财务费用', '营业收入']},
    '企业研发经费占费用比例': {'公式': '企业研发经费占费用比例=研发费用/(销售费用+财务费用+管理费用+研发费用)', '数值': ['研发费用', '销售费用', '财务费用', '管理费用']},
    '企业研发经费与利润比值': {'公式': '企业研发经费与利润比值=研发费用/净利润', '数值': ['研发费用', '净利润']},
    '企业研发经费与营业收入比值': {'公式': '企业研发经费与营业收入比值=研发费用/营业收入', '数值': ['研发费用', '营业收入']},
    '研发人员占职工人数比例': {'公式': '研发人员占职工人数比例=研发人员人数/职工总人数', '数值': ['研发人员人数', '职工总人数']},
    '企业硕士及以上人员占职工人数比例': {'公式': '企业硕士及以上人员占职工人数比例=(硕士员工人数 + 博士及以上的员工人数)/职工总人数', '数值': ['硕士员工人数', '博士及以上的员工人数', '职工总人数']},
    '毛利率': {'公式': '毛利率=(营业收入-营业成本)/营业收入', '数值': ['营业收入', '营业成本']},
    '营业利润率': {'公式': '营业利润率=营业利润/营业收入', '数值': ['营业利润', '营业收入']},
    '流动比率': {'公式': '流动比率=流动资产/流动负债', '数值': ['流动资产', '流动负债']},
    '速动比率': {'公式': '速动比率=(流动资产-存货)/流动负债', '数值': ['流动资产', '存货', '流动负债']},
    '资产负债比率': {'公式': '资产负债比率=总负债/资产总额', '数值': ['总负债', '资产总额']},
    '现金比率': {'公式': '现金比率=货币资金/流动负债', '数值': ['货币资金', '流动负债']},
    '非流动负债比率': {'公式': '非流动负债比率=非流动负债/总负债', '数值': ['非流动负债', '总负债']},
    '流动负债比率': {'公式': '流动负债比率=流动负债/总负债', '数值': ['流动负债', '总负债']},
    '净利润率': {'公式': '净利润率=净利润/营业收入', '数值': ['净利润', '营业收入']}}
not_list = [
    '企业研发经费占费用比例', '企业研发经费与利润比值', '企业研发经费与营业收入比值',
    '研发人员占职工人数比例', '企业硕士及以上人员占职工人数比例', '流动比率', '速动比率']
# 新建货币资金new字段
# df['货币资金new'] = ''
for new_name in new_name_list:
    df[new_name] = ''


# 循环表格中的每一行
for index, row in df.iterrows():
    for name in name_list:
        company_name = row['格式化企业名称']
        year = int(str(row['年份']).replace('年', ''))

        # 1. 计算2020和2019的货币资金
        currency_this = df[(df['格式化企业名称'] == company_name) & (df['年份'] == year)][name].sum()
        currency_last = df[(df['格式化企业名称'] == company_name) & (df['年份'] == year-1)][name].sum()

        print(currency_this)
        print(currency_last)

        # 2. 计算2020年货币资金增长率
        if currency_last != 0:
            growth_rate_this = '('+str(currency_this)+'-'+str(currency_last)+ ')/' + str(currency_last) + ' *100=' + str((float(currency_this) - float(currency_last)) / float(currency_last) * 100) + '%'
        else:
            growth_rate_this = '由于上一年度无数值，所以增长率为空'

        # 3. 计算行业货币资金平均值
        industry_name = row['行业名称']
        industry_average_this = df[(df['年份'] == year) & (df['行业名称'] == industry_name)][name].mean()

        # 4. 计算行业货币资金排名
        industry_this_data = df[df['年份'] == year].groupby('格式化企业名称')[name].sum().reset_index()
        industry_this_data['排名'] = industry_this_data[name].rank(ascending=False)
        company_rank = industry_this_data[industry_this_data['格式化企业名称'] == company_name]['排名'].iloc[0]

        # 更新'货币资金new'字段
        df.at[index, name+'new'] = {
            str(year) + '年' + name: str(currency_this) + '元',
            str(year - 1) + '年' + name: str(currency_last) + '元',
            str(year) + '年' + name + '增长率': str(growth_rate_this),
            '行业'+name+'平均值': str(industry_average_this) + '元',
            '行业'+name+'排名': str(int(company_rank))
        }

    for new_name in new_name_list:
        company_name = row['格式化企业名称']
        year = int(str(row['年份']).replace('年', ''))
        gongshi = new_name_list[new_name]['公式'].split('=')[1]

        shuzhi_dict = {}
        for sz_name in new_name_list[new_name]['数值']:
            currency_this = str(df[(df['格式化企业名称'] == company_name) & (df['年份'] == year)][sz_name].sum())
            shuzhi_dict[sz_name] = currency_this
            gongshi = gongshi.replace(sz_name, currency_this)

        try:
            if new_name not in not_list:
                growth_rate_this = gongshi + '*100=' + str(eval(gongshi)) + '%'
            else:
                growth_rate_this = gongshi + '=' + str(eval(gongshi))

        except:
            growth_rate_this = '缺少数据，所以值为空'

        new_dict = {}
        for x in shuzhi_dict:
            new_dict[str(year) + '年' + x] = str(shuzhi_dict[x])
        new_dict['公式'] = new_name_list[new_name]['公式']
        new_dict[new_name] = growth_rate_this
        # 更新'货币资金new'字段
        df.at[index, new_name] = new_dict

        print(shuzhi_dict, )


# 保存结果
df.to_excel("big_data.xlsx", engine='openpyxl', index=False)