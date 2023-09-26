# formula schema0
formulas = [
    {'target': '博士及以上的员工人数', 'sub': ['博士'], 'raw_formula': '博士', 'is_percent': False},
    {'target': '企业研发经费与利润比值', 'sub': ['研发费用', '净利润'], 'raw_formula': '研发费用/净利润', 'is_percent': False},
    {'target': '企业研发经费与营业收入比值', 'sub': ['研发费用', '营业收入'], 'raw_formula': '研发费用/营业收入', 'is_percent': False},
    {'target': '研发人员占职工人数比例', 'sub': ['研发人员', '职工总数'], 'raw_formula': '研发人员/职工总数', 'is_percent': False},
    {'target': '研发经费与利润比值', 'sub': ['研发费用', '净利润'], 'raw_formula': '研发费用/净利润', 'is_percent': False},
    {'target': '流动比率', 'sub': ['流动资产合计', '流动负债合计'], 'raw_formula': '流动资产合计/流动负债合计', 'is_percent': False}, #变动
    {'target': '速动比率', 'sub': ['流动资产合计', '流动负债合计', '存货'], 'raw_formula': '(流动资产合计-存货)/流动负债合计', 'is_percent': False}, #变动
    {'target': '企业硕士及以上人员占职工人数比例', 'sub': ['博士', '硕士', '职工总数'], 'raw_formula': '(硕士+博士)/职工总数', 'is_percent': False},
    {'target': '企业研发经费占费用比例', 'sub': ['研发费用', '销售费用', '财务费用', '管理费用'], 'raw_formula': '研发费用/(销售费用+财务费用+管理费用+研发费用)', 'is_percent': False},       
    {'target': '企业研发经费占费用的比例', 'sub': ['研发费用', '销售费用', '财务费用', '管理费用'], 'raw_formula': '研发费用/(销售费用+财务费用+管理费用+研发费用)', 'is_percent': False},       
    {'target': '营业利润率', 'sub': ['营业利润', '营业收入'], 'raw_formula': '营业利润/营业收入', 'is_percent': True},
    {'target': '资产负债比率', 'sub': ['负债合计', '资产总计'], 'raw_formula': '负债合计/资产总计', 'is_percent': True}, #变动
    {'target': '现金比率', 'sub': ['流动负债合计', '货币资金'], 'raw_formula': '货币资金/流动负债合计', 'is_percent': True}, #变动
    {'target': '非流动负债比率', 'sub': ['非流动负债合计', '负债合计'], 'raw_formula': '非流动负债合计/负债合计', 'is_percent': True}, #变动
    {'target': '流动负债比率', 'sub': ['流动负债合计', '负债合计'], 'raw_formula': '流动负债合计/负债合计', 'is_percent': True}, #变动
    {'target': '净资产收益率', 'sub': ['所有者权益合计', '净利润'], 'raw_formula': '净利润/所有者权益合计', 'is_percent': True}, #变动
    {'target': '净利润率', 'sub': ['营业收入', '净利润'], 'raw_formula': '净利润/营业收入', 'is_percent': True}, 
    {'target': '营业成本率', 'sub': ['营业成本', '营业收入'], 'raw_formula': '营业成本/营业收入', 'is_percent': True},
    {'target': '管理费用率', 'sub': ['管理费用', '营业收入'], 'raw_formula': '管理费用/营业收入', 'is_percent': True},
    {'target': '财务费用率', 'sub': ['财务费用', '营业收入'], 'raw_formula': '财务费用/营业收入', 'is_percent': True},
    {'target': '毛利率', 'sub': ['营业收入', '营业成本'], 'raw_formula': '(营业收入-营业成本)/营业收入', 'is_percent': True},
    {'target': '三费比重', 'sub': ['销售费用', '管理费用', '财务费用', '营业收入'], 'raw_formula': '(销售费用+管理费用+财务费用)/营业收入', 'is_percent': True},
]

formula_dict = {i["target"]:i for i in formulas}