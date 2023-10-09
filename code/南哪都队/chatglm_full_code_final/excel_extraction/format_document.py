import os
import json
from tqdm import tqdm
from multiprocess import Pool
import numpy as np

txt_folder = 'data/alltxt'
json_folder = 'data/report_json'
if not os.path.exists(json_folder):
    os.makedirs(json_folder)

big_capital = [ '零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十', '二十一', '二十二', '二十三', '二十四', '二十五', '二十六', '二十七', '二十八', '二十九', '三十']
small_capital = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91']
big_letter = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
small_letter = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
circle_digits = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩']

big_capital_brackets = ['（_）'.replace('_', num) for num in big_capital]
big_capital_brackets += ['(_)'.replace('_', num) for num in big_capital]
big_capital_brackets += ['(_）'.replace('_', num) for num in big_capital]
big_capital_brackets += ['（_)'.replace('_', num) for num in big_capital]
small_capital_brackets = ['（_）'.replace('_', num) for num in small_capital]
small_capital_brackets += ['(_)'.replace('_', num) for num in small_capital]
small_capital_brackets += ['(_）'.replace('_', num) for num in small_capital]
small_capital_brackets += ['（_)'.replace('_', num) for num in small_capital]
small_capital_half_brackets = ['_）'.replace('_', num) for num in small_capital]
small_capital_half_brackets += ['_)'.replace('_', num) for num in small_capital]
big_capital_A = [num + '、' for num in big_capital]
big_capital_B = [num + '.' for num in big_capital]
small_capital_A = [num + '、' for num in small_capital]
small_capital_B = [num + '.' for num in small_capital]
big_letter = [letter + '.' for letter in big_letter]
big_letter_brackets = ['（_）'.replace('_', letter) for letter in big_letter]
big_letter_brackets += ['(_)'.replace('_', letter) for letter in big_letter]
big_letter_brackets += ['(_）'.replace('_', letter) for letter in big_letter]
big_letter_brackets += ['（_)'.replace('_', letter) for letter in big_letter]
small_letter = [letter + '.' for letter in small_letter]
small_letter_brackets = ['（_）'.replace('_', letter) for letter in small_letter]
small_letter_brackets += ['(_)'.replace('_', letter) for letter in small_letter]
small_letter_brackets += ['(_）'.replace('_', letter) for letter in small_letter]
small_letter_brackets += ['（_)'.replace('_', letter) for letter in small_letter]

def remove(line):
    if not line:
        return True
    if not line['inside']:
        return True
    if line['type'] in ['页眉', '页脚', '页脚']:
        return True
    return False

def get_category(line):
    content = line['inside']
    title = content[:content.find('...')]
    for i in range(len(content)):
        if content[-(i+1)] == '.':
            break
    page = content[-i:]
    return title, page

def add_hierarchy(result, title_stack):
    if len(title_stack) == 1:
        result[title_stack[0]] = {}
    else:
        add_hierarchy(result[title_stack[0]], title_stack[1:])

def add_doc(result, title_stack, doc):
    if len(title_stack) == 1:
        result[title_stack[0]] = doc
    else:
        add_doc(result[title_stack[0]], title_stack[1:], doc)

def main(index):
    for idx, file in enumerate(os.listdir(txt_folder)):
        if idx != index:
            continue
        found_category = False
        end_category = False
        is_excel = False
        result = {}
        current_doc = []
        current_excel = []
        category = []
        hierarchy_stack = []
        title_stack = []
        for line in open(os.path.join(txt_folder, file), 'rb').readlines():
            try:
                current_line = eval(line.rstrip())
            except:
                continue
            if not current_line:
                break
            if remove(current_line):
                continue
            if not end_category:
                if not found_category:
                    if current_line['inside'] == '目录':
                        found_category = True
                elif end_category == False:
                    if '...' in current_line['inside']:
                        title, page = get_category(current_line)
                        category.append(title)
                    else:
                        end_category = True
                continue
                        
            def match_index(line):
                if line['inside'] in category:
                    return 'A'
                for idx in big_capital_A:
                    if line['inside'].startswith(idx):
                        return 'B'
                for idx in big_capital_B:
                    if line['inside'].startswith(idx):
                        return 'C'
                for idx in big_capital_brackets:
                    if line['inside'].startswith(idx):
                        return 'D'
                for idx in small_capital_A:
                    if line['inside'].startswith(idx):
                        return 'E'
                for idx in small_capital_B:
                    if line['inside'].startswith(idx):
                        try:
                            if line['inside'][len(idx)] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '%', '（', '(']:
                                return False
                        except:
                            pass
                        return 'F'
                for idx in small_capital_brackets:
                    if line['inside'].startswith(idx):
                        return 'G'
                for idx in small_capital_half_brackets:
                    if line['inside'].startswith(idx):
                        return 'H'
                for idx in big_letter:
                    if line['inside'].startswith(idx):
                        return 'I'
                for idx in big_letter_brackets:
                    if line['inside'].startswith(idx):
                        return 'J'
                for idx in small_letter:
                    if line['inside'].startswith(idx):
                        return 'K'
                for idx in small_letter_brackets:
                    if line['inside'].startswith(idx):
                        return 'L'
                for idx in circle_digits:
                    if line['inside'].startswith(idx):
                        return 'M'
                return False
            
            if current_line['type'] == 'text' and is_excel:
                is_excel = False
                current_doc.append(current_excel)
                current_excel = []
                
            hierarchy = match_index(current_line)
            if hierarchy:
                if hierarchy in hierarchy_stack:
                    add_doc(result, title_stack, current_doc)
                    while hierarchy in hierarchy_stack:
                        hierarchy_stack.pop()
                        title_stack.pop()
                hierarchy_stack.append(hierarchy)
                title_stack.append(current_line['inside'])
                add_hierarchy(result, title_stack)
                current_doc = []
            else:
                if not result:
                    continue
                if current_line['type'] == 'text':
                    current_doc.append(current_line['inside'])
                elif current_line['type'] == 'excel':
                    is_excel = True
                    current_excel.append(current_line['inside'])
        try:     
            add_doc(result, title_stack, current_doc)
        except:
            pass
        with open(os.path.join(json_folder, os.path.splitext(file)[0]+'.json'), 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii = False)


if __name__ == '__main__':
    num_processes = 8
    num_tasks = len(os.listdir(txt_folder))
    params = [i for i in range(num_tasks)]
    with Pool(num_processes) as p:
        res = list(tqdm(p.imap(main, params), total=len(params)))
    p.close()
    p.join()