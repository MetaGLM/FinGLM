import pandas as pd
import configparser

config = configparser.ConfigParser()
config.read('D:\\UGit\\fjzj\\app\\config.ini')

class DataQuery:

    def __init__(self):
        self.peopledata_path = config["sql_data"]['people_path']
        self.basedata_path = config["sql_data"]['baseinfo_path']
        self.balance_static_path = config["sql_data"]['balance_static_path']

        self.balance_sheet_path = config["sql_data"]['balance_sheet_path']
        self.cash_flow_statement_path = config["sql_data"]['cash_flow_statement_path']
        self.company_annual_reports_path = config["sql_data"]['company_annual_reports_path']
        self.profit_statement_path = config["sql_data"]['profit_statement_path']

        self.peopledata_df = pd.read_excel(
            self.peopledata_path, index_col=None)
        self.peopledata_df = self.peopledata_df.replace(0, -1)
        self.basedata_df = pd.read_excel(self.basedata_path, index_col=None)
        self.balance_static_df = pd.read_excel(self.balance_static_path)
        self.balance_static_df['流动负债'] = self.balance_static_df['流动负债合计']
        self.balance_static_df['流动资产'] = self.balance_static_df['流动资产合计']
        self.balance_static_df['非流动资产'] = self.balance_static_df['非流动资产合计']
        self.balance_static_df['非流动负债'] = self.balance_static_df['非流动负债合计']

        self.balance_sheet_df = pd.read_excel(
            self.balance_sheet_path, index_col=None)
        self.balance_sheet_df['负债合计'] = self.balance_sheet_df['总负债']
        self.balance_sheet_df['资产总计'] = self.balance_sheet_df['总资产']

        self.cash_flow_statement_df = pd.read_excel(
            self.cash_flow_statement_path, index_col=None)
        self.cash_flow_statement_df['证券代码'] = self.cash_flow_statement_df['股票代码']

        self.profit_statement_df = pd.read_excel(
            self.profit_statement_path, index_col=None)
        self.profit_statement_df['每股收益'] = self.profit_statement_df['基本每股收益']

        self.company_annual_reports_df = pd.read_excel(
            self.company_annual_reports_path, index_col=None, dtype={"stock_code": str})
        self.company_annual_reports_df = self.company_annual_reports_df[[
            'company_full_name', 'stock_code', 'company_short_name']].drop_duplicates()

        self.all_data = pd.read_excel("./data/all_data.xlsx")
        self.all_data['股票代码'] = self.all_data['股票代码'].astype(str).str.zfill(6)
        self.all_data['证券代码'] = self.all_data['证券代码'].astype(str).str.zfill(6)
        self.all_data['流动负债'] = self.all_data['流动负债合计']
        self.all_data['流动资产'] = self.all_data['流动资产合计']
        self.all_data['非流动资产'] = self.all_data['非流动资产合计']
        self.all_data['非流动负债'] = self.all_data['非流动负债合计']
        self.all_data['负债总额'] = self.all_data['总负债']
        self.all_data['负债合计'] = self.all_data['总负债']
        self.all_data['资产总计'] = self.all_data['总资产']
        self.all_data['货币总额'] = self.all_data['货币资金']
        self.all_data['电子信箱'] = self.all_data['公司邮箱']
        self.all_data['博士及以上人数'] = self.all_data['硕士以上人数']
        self.all_data['博士及以上人数'] = self.all_data['博士以上人数']
        self.all_data['博士'] = self.all_data['博士人数']
        self.all_data['硕士'] = self.all_data['硕士人数']
        self.all_data['职工总人数'] = self.all_data['职工人数']

    @staticmethod
    def _row_to_sentence(row):
        year = row['报告年份']
        name = row['股票简称']
        data = dq.query_company_annual_reports()
        company_full_name = data[data['company_short_name']
                                 == name]['company_full_name'].values[0]
        other_data = {k: v for k, v in row.items() if k not in [
            '报告年份', '证券代码', '证券简称']}
        details = " 。\n ".join(
            [f"{col}为{value}" for col, value in other_data.items()])
        return f"- {name}(全称:{company_full_name})的{year}年报内容:\n{details}。\n"

    def query_people_data(self, report_year, stock_name):
        data = self.peopledata_df
        data = data.loc[(data['股票简称'] == stock_name)]
        data = data.ffill().bfill()
        data.dropna(axis=0, how='any')
        data = data.loc[(data['报告年份'] == int(report_year[0]))]
        data = data.loc[:, (data != 0).any(axis=0)]

        if data.empty:
            return ''
        sentences = data.apply(self._row_to_sentence, axis=1)
        sentences = '\n -'.join(sentences)
        return sentences

    def query_basic_data(self, stock_name):
        data = self.basedata_df
        data = data.loc[data['股票简称'] == stock_name]
        data = data.ffill().bfill()
        data.dropna(axis=0, how='any')
        if data.empty:
            return ''
        sentences = data.apply(self._row_to_sentence, axis=1)
        sentences = '\n -'.join(sentences)
        return sentences

    def query_all_data(self):
        return self.all_data

    def query_balance_static_data(self):
        return self.balance_static_df

    def query_company_annual_reports(self):
        return self.company_annual_reports_df

    def query_profit_statement(self, stock_name):
        data = self.profit_statement_df.loc[self.profit_statement_df['股票简称'] == stock_name]
        return data

    def query_balance_sheet(self, stock_name):
        data = self.balance_sheet_df.loc[self.balance_sheet_df['股票简称'] == stock_name]
        return data

    def query_cash_flow_statement(self, stock_name):
        data = self.cash_flow_statement_df.loc[self.cash_flow_statement_df['股票简称'] == stock_name]
        return data

    def get_financial_data(self, year, stock_name):
        balance_data = self.balance_sheet_df.loc[(self.balance_sheet_df['股票简称'] == stock_name) & (self.balance_sheet_df['报告年份'] == int(year))]

        excel_data = self.query_balance_static_data()
        filtered_data = excel_data.loc[(excel_data['证券简称'] == stock_name) & (excel_data['年份'] == int(year))]

        profit_data = self.profit_statement_df.loc[(self.profit_statement_df['股票简称'] == stock_name) & (self.profit_statement_df['报告年份'] == int(year))]

        cash_data = self.cash_flow_statement_df.loc[(self.cash_flow_statement_df['股票简称'] == stock_name) & (self.cash_flow_statement_df['报告年份'] == int(year))]

        people_data = self.peopledata_df.loc[(self.peopledata_df['股票简称'] == stock_name) & (
            self.peopledata_df['报告年份'] == int(year)), ['研发人员', '职工人数', '硕士以上人数']]
        try:
            combined_data = {
                '总负债': balance_data['总负债'].iloc[0],
                '总资产': balance_data['总资产'].iloc[0],
                '存货': balance_data['存货'].iloc[0],
                '货币资金': balance_data['货币资金'].iloc[0],
                '流动资产合计': filtered_data['流动资产合计'].iloc[0],
                '流动负债合计': filtered_data['流动负债合计'].iloc[0],
                '非流动负债合计': filtered_data['非流动负债合计'].iloc[0],
                '净利润': profit_data['净利润'].iloc[0],
                '营业收入': profit_data['营业收入'].iloc[0],
                '营业成本': profit_data['营业成本'].iloc[0],
                '营业利润': profit_data['营业利润'].iloc[0],
                '管理费用': profit_data['管理费用'].iloc[0],
                '财务费用': profit_data['财务费用'].iloc[0],
                '研发费用': profit_data['研发费用'].iloc[0],
                '销售费用': profit_data['销售费用'].iloc[0],
                '投资收益': profit_data['投资收益'].iloc[0],

                '经营活动产生的现金流量净额': cash_data['经营活动产生的现金流量净额'].iloc[0],
                '股本': balance_data['股本'].iloc[0],
                '每股收益': profit_data['每股收益'].iloc[0],
                '研发人员': people_data['研发人员'].iloc[0],
                '职工人数': people_data['职工人数'].iloc[0],
                '硕士以上人数': people_data['硕士以上人数'].iloc[0],
            }
        except:
            combined_data = {}

        return combined_data


# 创建 DataQuery 的实例
dq = DataQuery()
