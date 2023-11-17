import glob
import pdfplumber
import re
from collections import defaultdict


class PDFProcessor:
    def __init__(self, filepath):
        self.filepath = filepath
        self.pdf = pdfplumber.open(filepath)
        self.all_text = defaultdict(dict)
        self.allrow = 0
        self.compiled_regex = {
            "check_re": re.compile(r'(?:。|；|单位：元|单位：万元|币种：人民币|\d|报告(?:全文)?(?:（修订版）|（修订稿）|（更正后）)?)$'),
            "first_re": re.compile(r'[^计](?:报告(?:全文)?(?:（修订版）|（修订稿）|（更正后）)?)$'),
            "end_re": re.compile(r'^(?:\d|\\|\/|第|共|页|-|_| ){1,}')
        }
        self.last_num = 0

    def check_lines(self, page, top, buttom):
        lines = page.extract_words()[::]
        text = ''
        last_top = 0
        last_check = 0
        for l in range(len(lines)):
            each_line = lines[l]
            check_re = '(?:。|；|单位：元|单位：万元|币种：人民币|\d|报告(?:全文)?(?:（修订版）|（修订稿）|（更正后）)?)$'
            if top == '' and buttom == '':
                if abs(last_top - each_line['top']) <= 2:
                    text = text + each_line['text']
                elif last_check > 0 and (page.height * 0.9 - each_line['top']) > 0 and not re.search(check_re, text):

                    text = text + each_line['text']
                else:
                    text = text + '\n' + each_line['text']
            elif top == '':
                if each_line['top'] > buttom:
                    if abs(last_top - each_line['top']) <= 2:
                        text = text + each_line['text']
                    elif last_check > 0 and (page.height * 0.85 - each_line['top']) > 0 and not re.search(check_re,
                                                                                                          text):
                        text = text + each_line['text']
                    else:
                        text = text + '\n' + each_line['text']
            else:
                if each_line['top'] < top and each_line['top'] > buttom:
                    if abs(last_top - each_line['top']) <= 2:
                        text = text + each_line['text']
                    elif last_check > 0 and (page.height * 0.85 - each_line['top']) > 0 and not re.search(check_re,
                                                                                                          text):
                        text = text + each_line['text']
                    else:
                        text = text + '\n' + each_line['text']
            last_top = each_line['top']
            last_check = each_line['x1'] - page.width * 0.85

        return text

    def drop_empty_cols(self, data):
        # 转置数据，使得每个子列表代表一列而不是一行
        transposed_data = list(map(list, zip(*data)))
        # 过滤掉全部为空的列
        filtered_data = [col for col in transposed_data if not all(cell is '' for cell in col)]
        # 再次转置数据，使得每个子列表代表一行
        result = list(map(list, zip(*filtered_data)))
        return result
    def extract_text_and_tables(self, page):
        buttom = 0
        tables = page.find_tables()
        if len(tables) >= 1:
            count = len(tables)
            for table in tables:
                if table.bbox[3] < buttom:
                    pass
                else:
                    count -= 1
                    top = table.bbox[1]
                    text = self.check_lines(page, top, buttom)
                    text_list = text.split('\n')
                    for _t in range(len(text_list)):
                        self.all_text[self.allrow] = {'page': page.page_number, 'allrow': self.allrow, 'type': 'text', 'inside': text_list[_t]}
                        self.allrow += 1

                    buttom = table.bbox[3]
                    new_table = table.extract()
                    r_count = 0
                    for r in range(len(new_table)):
                        row = new_table[r]
                        if row[0] is None:
                            r_count += 1
                            for c in range(len(row)):
                                if row[c] is not None and row[c] not in ['', ' ']:
                                    if new_table[r - r_count][c] is None:
                                        new_table[r - r_count][c] = row[c]
                                    else:
                                        new_table[r - r_count][c] += row[c]
                                    new_table[r][c] = None
                        else:
                            r_count = 0

                    end_table = []
                    for row in new_table:
                        if row[0] != None:
                            cell_list = []
                            for cell in row:
                                if cell != None:
                                    cell = cell.replace('\n', '')
                                else:
                                    cell = ''
                                cell_list.append(cell)
                            end_table.append(cell_list)
                    end_table = self.drop_empty_cols(end_table)
                    for row in end_table:
                        self.all_text[self.allrow] = {'page': page.page_number, 'allrow': self.allrow, 'type': 'excel', 'inside': str(row)}
                        # self.all_text[self.allrow] = {'page': page.page_number, 'allrow': self.allrow, 'type': 'excel',
                        #                               'inside': ' '.join(row)}
                        self.allrow += 1

                    if count == 0:
                        text = self.check_lines(page, '', buttom)
                        text_list = text.split('\n')
                        for _t in range(len(text_list)):
                            self.all_text[self.allrow] = {'page': page.page_number, 'allrow': self.allrow, 'type': 'text', 'inside': text_list[_t]}
                            self.allrow += 1

        else:
            text = self.check_lines(page, '', '')
            text_list = text.split('\n')
            for _t in range(len(text_list)):
                self.all_text[self.allrow] = {'page': page.page_number, 'allrow': self.allrow, 'type': 'text', 'inside': text_list[_t]}
                self.allrow += 1

        first_text = str(
            self.all_text[1]['inside'] if self.last_num == 0 else self.all_text[self.last_num + 2]['inside'])
        end_text = str(self.all_text[len(self.all_text) - 1]['inside'])

        if self.compiled_regex['first_re'].search(first_text) and not '[' in first_text:
            self.all_text[1 if self.last_num == 0 else self.last_num + 2]['type'] = '页眉'
        if self.compiled_regex['end_re'].search(end_text) and not '[' in end_text:
            self.all_text[len(self.all_text) - 1]['type'] = '页脚'

        self.last_num = len(self.all_text) - 1


    def process_pdf(self):
        for i in range(len(self.pdf.pages)):
            self.extract_text_and_tables(self.pdf.pages[i])

    def save_all_text(self, path):
        for key in self.all_text.keys():
            with open(path, 'a+', encoding='utf-8') as file:
                file.write(str(self.all_text[key]) + '\n')

def process_all_pdfs_in_folder(folder_path, save_folder_path):
    file_paths = glob.glob(f'{folder_path}/*')
    file_paths = sorted(file_paths, reverse=True)

    for file_path in file_paths:
        processor = PDFProcessor(file_path)
        processor.process_pdf()
        save_path = save_folder_path + file_path.split('/')[-1].replace('.pdf', '.txt')
        processor.save_all_text(save_path)


folder_path = 'data/allpdf'
save_folder_path = 'data/alltxt2'
process_all_pdfs_in_folder(folder_path, save_folder_path)
