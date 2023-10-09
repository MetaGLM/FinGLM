import os
import json
from tqdm import tqdm

dict_json_folder = 'data/dict_json'
list_json_folder = 'data/list_json'
txt_folder = 'data/alltxt'

def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)
mkdir(dict_json_folder)
mkdir(list_json_folder)

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
    if '.' in content:
        title = content[:content.find('...')]
    elif '……' in content:
        title = content[:content.find('……')]
    for i in range(len(content)):
        if content[-(i+1)] == '.':
            break
    page = content[-i:]
    return title, page

def find_dict_idx(mixed_list):
    for idx, e in enumerate(mixed_list):
        if isinstance(e, dict):
            return idx
    else:
        mixed_list.append({})
        return -1

def add_hierarchy(result, title_stack):
    if len(title_stack) == 1:
        idx = find_dict_idx(result)
        result[idx][title_stack[0]] = []
    else:
        if isinstance(result, dict):
            add_hierarchy(result[title_stack[0]], title_stack[1:])
        else:
            idx = find_dict_idx(result)
            add_hierarchy(result[idx][title_stack[0]], title_stack[1:])

def add_doc(result, title_stack, doc):
    if len(title_stack) == 1:
        idx = find_dict_idx(result)
        result[idx][title_stack[0]] += doc
    else:
        if isinstance(result, dict):
            add_doc(result[title_stack[0]], title_stack[1:], doc)
        else:
            idx = find_dict_idx(result)
            add_doc(result[idx][title_stack[0]], title_stack[1:], doc)

def valid_check(line):
    content = line['inside']
    if len(content) < 10 and '不适用' in content:
        return False
    return True

def json_to_pure_json(input, output, idx, exception_dict, exception_idx, initial_key = None):
    temp = []
    find_dict = False
            
    for idx, e in enumerate(input):
        if isinstance(e, dict):
            find_dict = True
            for k in e:
                if initial_key:
                    if not output.get(initial_key):
                        output[initial_key] = {}
                    json_to_pure_json(input[idx][k], output[initial_key], idx, exception_dict, exception_idx, k)
                else:
                    json_to_pure_json(input[idx][k], output, idx, exception_dict, exception_idx, k)
        else:
            temp.append(e)
    for e in temp:
        if find_dict:
            exception_dict['exception_{}'.format(exception_idx)] = e
            exception_idx += 1
        else:
            output[initial_key] = temp
    return exception_idx

def match_index(line, category = []):
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
            
def main(txt_folder, dict_json_folder, list_json_folder, start_idx=0):
    def process_file(idx, file):
        if idx < start_idx:
            return
        found_category = False
        end_category = False
        is_excel = False
        result = []
        current_doc = []
        current_excel = []
        category = []
        hierarchy_stack = []
        title_stack = []
        #exception_idx = 0
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
                    if '...' in current_line['inside'] or '…' in current_line['inside']:
                        title, page = get_category(current_line)
                        if title:
                            category.append(title)
                    elif category:
                        end_category = True
                continue
            
            if current_line['type'] == 'text' and is_excel:
                is_excel = False
                current_doc.append(current_excel)
                current_excel = []
            
            #if current_line['allrow'] == 1512:
            #    pass
            
            hierarchy = match_index(current_line, category)
            if not valid_check(current_line):
                continue
            if hierarchy:
                if hierarchy in hierarchy_stack:
                    add_doc(result, title_stack, current_doc)
                    while hierarchy in hierarchy_stack:
                        hierarchy_stack.pop()
                        title_stack.pop()
                elif len(current_doc) > 1:
                    add_doc(result, title_stack, current_doc)
                    #result['exception_{}'.format(exception_idx)] = current_doc
                    #exception_idx += 1
                if not hierarchy_stack and hierarchy != 'A':
                    continue
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
            if result:  
               add_doc(result, title_stack, current_doc)
        except:
            pass
        
        if not end_category or not result:
            is_excel = False
            result = []
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
                
                if current_line['type'] == 'text' and is_excel:
                    is_excel = False
                    current_doc.append(current_excel)
                    current_excel = []
                
                #if current_line['allrow'] == 1512:
                #    pass
                
                hierarchy = match_index(current_line)
                if not valid_check(current_line):
                    continue
                if hierarchy:
                    if hierarchy in hierarchy_stack:
                        add_doc(result, title_stack, current_doc)
                        while hierarchy in hierarchy_stack:
                            hierarchy_stack.pop()
                            title_stack.pop()
                    elif len(current_doc) > 1:
                        add_doc(result, title_stack, current_doc)
                        #result['exception_{}'.format(exception_idx)] = current_doc
                        #exception_idx += 1
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
        
        excel_json = {}
        exception_dict = {}
        json_to_pure_json(result, excel_json, idx, exception_dict, 0, initial_key = None)
        excel_json.update(exception_dict)
        with open(os.path.join(dict_json_folder, os.path.splitext(file)[0]+'.json'), 'w', encoding='utf-8') as f:
            json.dump(excel_json, f, indent=4, ensure_ascii = False)
        with open(os.path.join(list_json_folder, os.path.splitext(file)[0]+'.json'), 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii = False)
    #'''
    from multiprocess import Pool
    pool = Pool(8)
    async_results = []
    for idx, file in enumerate(os.listdir(txt_folder)):
        async_results.append(pool.apply_async(process_file, (idx, file)))
    for res in tqdm(async_results):
        res.get()
    pool.close()
    pool.join()
    '''
    for idx, file in enumerate(os.listdir(txt_folder)):
        if '300623' not in file or '2020年' not in file:
            continue
        process_file(idx, file)
    '''
    
    
if __name__ == '__main__':
    result = main(txt_folder, dict_json_folder, list_json_folder)
    pass