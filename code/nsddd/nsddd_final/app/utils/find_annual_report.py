import re
import os
from configs.model_config import pdf_all_list_path, pdf_list_path

def find_annual_report(query):
	"""
	优先采用全名进行查找，如果有一个全名能匹配上，则选择全名(因为存在简称相同或简称包含关系)
	"""

	
	all_files = []
	with open(pdf_list_path) as f:
		for line in f.readlines():
			all_files.append(line.strip())

	all_files = sorted([name for name in all_files if name.endswith('.pdf')])

	total_all_files = []
	with open(pdf_all_list_path) as f:
		for line in f.readlines():
			total_all_files.append(line.strip())

	total_all_files = sorted([name for name in total_all_files if name.endswith('.pdf')])

	query = re.sub(r'[ \（\）()]', '', query)
	## 寻找公司名称
	stock_full_name, stock_short_name = '', '' # 认为是唯一的
	query_stock_name = '' # query中的名称
	for file_name in total_all_files: ## 两阶段名称匹配，全名匹配不上，再用简称
		_, full_name, _, short_name, _, _ = file_name.split('__')
		if full_name in query:
			stock_full_name = full_name
			stock_short_name = short_name
			query_stock_name = full_name
			break

	if not stock_full_name:
		for file_name in total_all_files:
			_, full_name, _, short_name, _, _ = file_name.split('__')
			if short_name in query and len(short_name) > len(stock_short_name):
				stock_full_name = full_name
				stock_short_name = short_name
				query_stock_name = short_name
				
	## 对年份进行筛选并整理
	pattern_continue_year = [r'\d{4}-\d{4}',r'\d{4}年-\d{4}',r'\d{4}年到\d{4}', r'\d{4}年至\d{4}', r'\d{4}到\d{4}', r'\d{4}至\d{4}']
	pattern_discrete_year = r'2019|2020|2021'
	pattern_word_year_special = r'前年'
	pattern_word_year = r'[前|头|上|去](.?)年'
	all_year = []
	# 情况 1： 跨年份
	continue_sign = False
	for continue_year_pattern in pattern_continue_year:
		if re.findall(continue_year_pattern, query):
			continue_sign = True
			continue_year = re.findall(pattern_discrete_year, query)
			start_year = eval(continue_year[0])
			end_year = eval(continue_year[1])
			for year in range(start_year, end_year+1):
				all_year.append(year)
			break
	if not continue_sign:
		if re.findall(pattern_word_year_special,query):
			wordlist = re.findall(pattern_word_year_special,query)
			continue_year = re.findall(pattern_discrete_year, query)
			end_year = eval(continue_year[0])
			all_year.append(end_year)
			all_year.append(end_year-2)
			all_year = sorted(all_year)
			
		elif re.findall(pattern_word_year,query):
			wordlist = re.findall(pattern_word_year,query)
			continue_year = re.findall(pattern_discrete_year, query)
			end_year = eval(continue_year[0])
			all_year.append(end_year)
			if wordlist[0] == "" or wordlist[0] == "1" or wordlist[0] == "一":
				all_year.append(end_year-1)
			elif wordlist[0] == "2" or wordlist[0] == "两" or wordlist[0] == "二":
				all_year.append(end_year-2)
				all_year.append(end_year-1)
			all_year = sorted(all_year)
				
		# 情况 2： 离散年份
		elif re.findall(pattern_discrete_year, query):
			all_year = [eval(year) for year in list(set(re.findall(pattern_discrete_year, query)))]
			all_year = sorted(all_year)
	

	## 整合符合公司名称和年份的年报
	annul_report = []
	if stock_full_name: ##如果公司名不存在则不需要返回年报
		for file_name in all_files: ## 两阶段名称匹配，全名匹配不上，再用简称
			_, full_name, _, short_name, year, _ = file_name.split('__')
			if full_name == stock_full_name and eval(year[:-1]) in all_year:
				annul_report.append(file_name)
	return stock_full_name, stock_short_name, query_stock_name, annul_report
