import json
import glob
import os
import re
import pandas as pd
import configparser

config = configparser.ConfigParser()
config.read('./config.ini')

# 设置文件夹路径
folder_path = config['process_es']['parse_title_text_path']
output_path = config['process_es']['gen_table_text_path']
people_path = config['sql_data']['people_path']


def gen_table_text():

    # 使用glob模块获取文件夹中所有文件的路径
    file_paths = glob.glob(os.path.join(folder_path, "*"))
    file_paths = sorted(file_paths)

    # 读取people.xlsx
    people_df = pd.read_excel(people_path)

    wrong_file = []
    wrong_file_2 = []
    for file_path in file_paths:

        year = file_path.split("__")[-2]
        jiancheng = file_path.split("__")[-3]

        with open(file_path, 'r') as f:
            data = json.load(f)

        not_text_count = 0
        text = ""
        for key, value in data.items():
            for line in value:
                title = line['title_hierarchy']
                last_title = ""
                if len(title) > 0:
                    last_title = title[-1]
                if '合并利润表' == last_title and not_text_count < 100:
                    text += line['content'] + '\n'
                else:
                    # 又遇到结果后才开始
                    if len(text) > 0:
                        not_text_count += 1

        # 匹配带逗号的数字, 并删除逗号
        pattern = re.compile(r'(?<=\d),(?=\d{3})')
        text = pattern.sub('', text)

        # 判断字符串是否是数字
        def judge_num(string):
            try:
                float(string)
                return True
            except ValueError:
                return False

        # 过滤空行
        text_list = text.split('\n')
        text_list = [x for x in text_list if len(x.strip()) > 0]
        # 找到表格
        table = []
        for line in text_list:
            if line.strip().startswith("[") and line.strip().endswith("]"):
                table.append(eval(line))

        hebing_result = []

        # 获取标题
        if len(table) > 0:
            table_title = table[0]
        # 从中间开始遍历
        for i in range(1, len(table)):
            # 如果长度不等于标题，则忽略这行
            if len(table[i]) != len(table_title):
                # 长度不相同可能是分页后附注没有值，会变成3行，补齐4行
                if (len(table_title) - len(table[i]) == 1) and ('附注' in table_title):
                    fuzhu_index = table_title.index('附注')
                    table[i] = table[i][:fuzhu_index] + \
                        [''] + table[i][fuzhu_index:]
                    # print(file_path)
                else:
                    continue
            tmp_text_list = []
            tmp_increase_list = []
            for j in range(1, len(table[i])):
                if table[0][j] == '附注':
                    continue
                # 判断是否为数字
                if judge_num(table[i][j]):
                    if (table[0][j]) == '':
                        print(file_path)
                        wrong_file_2.append(file_path)

                    gen_text = table[0][j] + table[i][0] + \
                        '为' + table[i][j] + '元。'
                    tmp_text_list.append(gen_text)

                    # 加入增长率
                    if j+1 < len(table[i]) and judge_num(table[i][j+1]):
                        increase_rate = (
                            float(table[i][j]) - float(table[i][j+1])) / (float(table[i][j+1]) + 1e-5)
                        increase_rate_percentage = "{:.2%}".format(
                            round(increase_rate, 4))
                        gen_text = table[0][j] + table[i][0] + \
                            '的增长率为' + increase_rate_percentage
                        tmp_increase_list.append(gen_text)
            tmp_text_list.extend(tmp_increase_list)

            if len(tmp_text_list) > 0:
                # 去除无用词
                for i in range(len(tmp_text_list)):
                    gen_text = tmp_text_list[i]
                    pattern = r'（(损失|亏损|净亏损).*填列）'
                    gen_text = re.sub(pattern, '', gen_text)
                    pattern = r'[\(（]?[一二三四五六七八九零十\d]+[、)）]'
                    gen_text = re.sub(pattern, "", gen_text)
                    gen_text = gen_text.replace("加：", "").replace(
                        "减：", "").replace("其中：", "")
                    tmp_text_list[i] = gen_text

                hebing_result.append('\n'.join(tmp_text_list))

        # 抽取资产负债表
        year = file_path.split("__")[-2]

        with open(file_path, 'r') as f:
            data = json.load(f)

        not_text_count = 0
        text = ""
        for key, value in data.items():
            for line in value:
                title = line['title_hierarchy']
                last_title = ""
                if len(title) > 0:
                    last_title = title[-1]
                if '合并资产负债表' == last_title and not_text_count < 100:
                    text += line['content'] + '\n'
                else:
                    # 又遇到结果后才开始
                    if len(text) > 0:
                        not_text_count += 1

        # 匹配带逗号的数字, 并删除逗号
        pattern = re.compile(r'(?<=\d),(?=\d{3})')
        text = pattern.sub('', text)

        # 判断字符串是否是数字
        def judge_num(string):
            try:
                float(string)
                return True
            except ValueError:
                return False

        # 过滤空行
        text_list = text.split('\n')
        text_list = [x for x in text_list if len(x.strip()) > 0]
        # 找到表格
        table = []
        for line in text_list:
            if line.strip().startswith("[") and line.strip().endswith("]"):
                table.append(eval(line))

        zichan_result = []

        # 获取标题
        if len(table) > 0:
            table_title = table[0]
        # 从中间开始遍历
        for i in range(1, len(table)):
            # 如果长度不等于标题，则忽略这行
            if len(table[i]) != len(table_title):
                # 长度不相同可能是分页后附注没有值，会变成3行，补齐4行
                if (len(table_title) - len(table[i]) == 1) and ('附注' in table_title):
                    fuzhu_index = table_title.index('附注')
                    table[i] = table[i][:fuzhu_index] + \
                        [''] + table[i][fuzhu_index:]
                    # print(file_path)
                else:
                    continue
            tmp_text_list = []
            tmp_increase_list = []
            for j in range(1, len(table[i])):
                if table[0][j] == '附注':
                    continue
                # 判断是否为数字
                if judge_num(table[i][j]):
                    if (table[0][j]) == '':
                        print(file_path)
                        wrong_file_2.append(file_path)

                    gen_text = table[0][j] + table[i][0] + \
                        '为' + table[i][j] + '元。'
                    tmp_text_list.append(gen_text)

                    # 加入增长率
                    if j+1 < len(table[i]) and judge_num(table[i][j+1]):
                        increase_rate = (
                            float(table[i][j]) - float(table[i][j+1])) / (float(table[i][j+1]) + 1e-5)
                        increase_rate_percentage = "{:.2%}".format(
                            round(increase_rate, 4))
                        gen_text = table[0][j] + table[i][0] + \
                            '的增长率为' + increase_rate_percentage
                        tmp_increase_list.append(gen_text)
            tmp_text_list.extend(tmp_increase_list)

            if len(tmp_text_list) > 0:
                for i in range(len(tmp_text_list)):
                    gen_text = tmp_text_list[i]
                    gen_text = gen_text.replace("加：", "").replace(
                        "减：", "").replace("其中：", "")
                    gen_text = gen_text.replace(" ", "")
                    gen_text = gen_text.replace("12月31日", "")
                    tmp_text_list[i] = gen_text
                zichan_result.append('\n'.join(tmp_text_list))

        # 抽取xxx表
        year = file_path.split("__")[-2]

        with open(file_path, 'r') as f:
            data = json.load(f)

        not_text_count = 0
        text = ""
        for key, value in data.items():
            for line in value:
                title = line['title_hierarchy']
                last_title = ""
                if len(title) > 0:
                    last_title = title[-1]
                if '合并现金流量表' == last_title and not_text_count < 100:
                    text += line['content'] + '\n'
                else:
                    # 又遇到结果后才开始
                    if len(text) > 0:
                        not_text_count += 1

        # 匹配带逗号的数字, 并删除逗号
        pattern = re.compile(r'(?<=\d),(?=\d{3})')
        text = pattern.sub('', text)

        # 判断字符串是否是数字
        def judge_num(string):
            try:
                float(string)
                return True
            except ValueError:
                return False

        # 过滤空行
        text_list = text.split('\n')
        text_list = [x for x in text_list if len(x.strip()) > 0]
        # 找到表格
        table = []
        for line in text_list:
            if line.strip().startswith("[") and line.strip().endswith("]"):
                table.append(eval(line))

        liuliang_result = []

        # 获取标题
        if len(table) > 0:
            table_title = table[0]
        # 从中间开始遍历
        for i in range(1, len(table)):
            # 如果长度不等于标题，则忽略这行
            if len(table[i]) != len(table_title):
                # 长度不相同可能是分页后附注没有值，会变成3行，补齐4行
                if (len(table_title) - len(table[i]) == 1) and ('附注' in table_title):
                    fuzhu_index = table_title.index('附注')
                    table[i] = table[i][:fuzhu_index] + \
                        [''] + table[i][fuzhu_index:]
                    # print(file_path)
                else:
                    continue
            tmp_text_list = []
            tmp_increase_list = []
            for j in range(1, len(table[i])):
                if table[0][j] == '附注':
                    continue
                # 判断是否为数字
                if judge_num(table[i][j]):
                    if (table[0][j]) == '':
                        print(file_path)
                        wrong_file_2.append(file_path)

                    gen_text = table[0][j] + table[i][0] + \
                        '为' + table[i][j] + '元。'
                    tmp_text_list.append(gen_text)

                    # 加入增长率
                    if j+1 < len(table[i]) and judge_num(table[i][j+1]):
                        increase_rate = (
                            float(table[i][j]) - float(table[i][j+1])) / (float(table[i][j+1]) + 1e-5)
                        increase_rate_percentage = "{:.2%}".format(
                            round(increase_rate, 4))
                        gen_text = table[0][j] + table[i][0] + \
                            '的增长率为' + increase_rate_percentage
                        tmp_increase_list.append(gen_text)
            tmp_text_list.extend(tmp_increase_list)

            if len(tmp_text_list) > 0:
                for i in range(len(tmp_text_list)):
                    gen_text = tmp_text_list[i]
                    gen_text = gen_text.replace("加：", "").replace(
                        "减：", "").replace("其中：", "")
                    gen_text = gen_text.replace(" ", "")
                    pattern = r'[\(（]?[一二三四五六七八九零十\d]+[、)）]'
                    gen_text = re.sub(pattern, "", gen_text)
                    gen_text = gen_text.replace("12月31日", "")
                    tmp_text_list[i] = gen_text

                liuliang_result.append('\n'.join(tmp_text_list))

        info_result = []
        company_result = []
        text = ""
        for data_list in data.values():
            if len(data_list) == 0:
                continue
            for line in data_list:
                title = line['title_hierarchy']
                if ('公司信息' in title) or ('公司基本情况' in title):
                    text += line['content'] + '\n'

        # 过滤空行
        text_list = text.split('\n')
        # text_list = [x for x in text_list if len(x.strip()) > 0]

        # 找到表格
        table = []
        for line in text_list:
            if line.strip().startswith("[") and line.strip().endswith("]"):
                table.append(eval(line))

        for i in range(len(table)):
            line = table[i]
            line = [x for x in line if x != ""]
            if len(line) == 2:
                gen_text = year + line[0] + '是' + line[1] + '。'
                gen_text = gen_text.replace("（如有）", "")
                company_result.append(gen_text)
            elif len(line) == 4:
                gen_text = year + line[0] + '是' + line[1] + \
                    '。\n' + year + line[2] + '是' + line[3] + '。'
                info_result.append(gen_text)
        tmp = []
        for i in range(len(company_result)):
            if '法定代表人' in company_result[i]:
                if len(tmp) > 0:
                    info_result.append('\n'.join(tmp))
                    tmp = []
                    info_result.append(company_result[i])
            elif '网址' in company_result[i]:
                if len(tmp) > 0:
                    info_result.append('\n'.join(tmp))
                    tmp = [company_result[i]]
            else:
                tmp.append(company_result[i])
        if len(tmp) > 0:
            info_result.append('\n'.join(tmp))

        jiben_result = []
        text = ""
        for data_list in data.values():
            if len(data_list) == 0:
                continue
            for line in data_list:
                title = line['title_hierarchy']
                if ('基本情况简介' in title):
                    text += line['content'] + '\n'

        # 过滤空行
        text_list = text.split('\n')
        # text_list = [x for x in text_list if len(x.strip()) > 0]

        # 找到表格
        table = []
        for line in text_list:
            if line.strip().startswith("[") and line.strip().endswith("]"):
                table.append(eval(line))

        for i in range(len(table)):
            line = table[i]
            line = [x for x in line if x != ""]
            if len(line) == 2:
                gen_text = year + line[0] + '是' + line[1] + '。'
                gen_text = gen_text.replace("（如有）", "")
                jiben_result.append(gen_text)
            elif len(line) == 4:
                gen_text = year + line[0] + '是' + line[1] + \
                    '。\n' + year + line[2] + '是' + line[3] + '。'
                info_result.append(gen_text)

        if len(jiben_result) > 0:
            info_result.append('\n'.join(jiben_result))

        gupiao_result = []
        text = ""
        for data_list in data.values():
            if len(data_list) == 0:
                continue
            for line in data_list:
                title = line['title_hierarchy']
                if ('公司股票简况' in title):
                    text += line['content'] + '\n'

        # 过滤空行
        text_list = text.split('\n')
        # text_list = [x for x in text_list if len(x.strip()) > 0]

        # 找到表格
        table = []
        for line in text_list:
            if line.strip().startswith("[") and line.strip().endswith("]"):
                table.append(eval(line))

        # print(table)
        for i in range(len(table)):
            if len(table[i]) > 0 and table[i][0] == '股票种类':
                break

        for j in range(i+1, len(table)):
            biaoti_list = table[i]
            gen_text_list = []
            if len(biaoti_list) == len(table[j]):
                for k in range(len(table[j])):
                    if '变更' not in biaoti_list[k]:
                        gen_text_list.append(
                            biaoti_list[k] + '为' + table[j][k])
                gen_text = year + "，".join(gen_text_list) + '。'
                gupiao_result.append(gen_text)
        if len(gupiao_result) > 0:
            info_result.append('\n'.join(gupiao_result))
        # print(table)

        text = ""
        for data_list in data.values():
            if len(data_list) == 0:
                continue
            for line in data_list:
                title = line['title_hierarchy']
                if ('员工情况' in title) or ('公司员工情况' in title):
                    text += line['content'] + '\n'

        # 匹配带逗号的数字, 并删除逗号
        pattern = re.compile(r'(?<=\d),(?=\d{3})')
        text = pattern.sub('', text)

        # 判断字符串是否是数字
        def judge_num(string):
            try:
                int(string)
                return True
            except ValueError:
                return False

        # 过滤空行
        text_list = text.split('\n')
        text_list = [x for x in text_list if len(x.strip()) > 0]
        # 找到表格
        table = []
        for line in text_list:
            if line.strip().startswith("[") and line.strip().endswith("]"):
                table.append(eval(line))

        staff_result = []
        for i in range(len(table)):
            for j in range(1, len(table[i])):
                # 判断是否为数字
                if judge_num(table[i][j]):
                    biaoti = table[i][0]
                    if len(biaoti) > 0 and biaoti != '合计' and '母公司' not in biaoti and '子公司' not in biaoti:
                        gen_text = year + table[i][0] + \
                            '的人数为' + table[i][j] + '。'
                        gen_text = gen_text.replace("（人）", "")
                        staff_result.append(gen_text)
                        break

        reyuan_result = []
        result = []
        temp = []
        for item in staff_result:
            if '人员' in item:
                if len(temp) > 0:
                    result.append('\n'.join(temp))
                    temp = []
                reyuan_result.append(item)
            else:
                temp.append(item)
        if len(temp) > 0:
            result.append('\n'.join(temp))
        if len(reyuan_result) > 0:
            result.append('\n'.join(reyuan_result))

        row = people_df.loc[(people_df['报告年份'] == int(
            year.replace("年", ""))) & (people_df['股票简称'] == jiancheng)]
        if len(row) > 0:
            gen_text_list = []
            if row.iloc[0]['职工人数'] > 0:
                gen_text_list.append(
                    year + "职工人数为" + str(row.iloc[0]['职工人数']) + '人。')
            if row.iloc[0]['研发人员'] > 0:
                gen_text_list.append(year + "研发人员数量为" +
                                     str(row.iloc[0]['研发人员']) + '人。')
            # if row.iloc[0]['研发人员比率'] > 0:
            #     gen_text_list.append(year + "研发人员比率为" +
            #                          str(row.iloc[0]['研发人员比率']) + '。')
            if row.iloc[0]['硕士以上人数'] > 0:
                gen_text_list.append(year + "硕士及以上人数为" +
                                     str(row.iloc[0]['硕士以上人数']) + '人。')
            if row.iloc[0]['博士以上人数'] > 0:
                gen_text_list.append(year + "博士及以上人数为" +
                                     str(row.iloc[0]['博士以上人数']) + '人。')
            gen_text = '\n'.join(gen_text_list)
            result.append(gen_text)

        # save
        final_hebing_result = {}
        final_hebing_result['合并利润表'] = hebing_result
        final_hebing_result['合并资产负债表'] = zichan_result
        final_hebing_result['合并现金流量表'] = liuliang_result
        final_hebing_result['公司信息'] = info_result
        final_hebing_result['员工信息表'] = result

        if (len(hebing_result) == 0) or (len(zichan_result) == 0) or (len(liuliang_result) == 0):
            wrong_file.append(file_path)

        with open(os.path.join(output_path, os.path.basename(file_path)), 'w') as f2:
            json.dump(final_hebing_result, f2, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    gen_table_text()
