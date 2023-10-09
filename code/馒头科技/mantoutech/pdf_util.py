import os
import json
import shutil
import tempfile
import pdfplumber
import camelot
import re
import numpy as np
from loguru import logger
from multiprocessing import Pool
# from langchain.document_loaders import UnstructuredPDFLoader
# from langchain.document_loaders import PDFPlumberLoader
# from langchain.document_loaders import TextLoader
# from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
# from langchain.schema import Document
# from langchain.embeddings.huggingface import HuggingFaceEmbeddings
# from langchain.vectorstores import FAISS

from config import cfg
# from chinese_text_splitter import ChineseTextSplitter
# from pdf2txt import PDFProcessor


class PdfExtractor(object):

    def __init__(self, path) -> None:
        self.path = path

    def extract_pure_content_and_save(self, save_path, use_xpdf=True):
        try:
            pdf = pdfplumber.open(self.path)
        except Exception as e:
            print(e)
            return

        if not use_xpdf:
            with open(save_path, 'w', encoding='utf-8') as f:
                for page in pdf.pages:
                    text = page.extract_text()
                    line = {
                        'page': page.page_number,
                        'text': text
                    }
                    # print(text)
                    f.write(json.dumps(line, ensure_ascii=True) + '\n')
        else:
            os.chdir(cfg.XPDF_PATH)
            cmd = './pdftotext -table -enc UTF-8 "{}" "{}"'.format(
                    self.path, save_path)
            os.system(cmd)
            with open(save_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                pages = '\n'.join(lines).split('\x0c')
                
            if len(pdf.pages) != len(pages) - 1:
                logger.error('{} {} does not match for {}'.format(len(pdf.pages), len(pages), self.path))
            with open(save_path, 'w', encoding='utf-8') as f:
                for idx, page in enumerate(pages):
                    lines = page.split('\n')
                    lines = [line for line in lines if len(line.strip()) > 0]
                    page_block = {
                        'page': idx+1,
                        'text': '\n'.join(lines)
                    }
                    f.write(json.dumps(page_block, ensure_ascii=False) + '\n')
        pdf.close()

    def extract_table_of_pages(self, page_ids: list):
        '''
            this method is slow
        '''
        if True:
            with tempfile.TemporaryDirectory() as temp_dir:
                if not self.path.endswith('.pdf'):
                    temp_path = os.path.join(temp_dir, '{}.pdf'.format(os.path.basename(self.path)))
                    shutil.copy(self.path, temp_path)
                else:
                    temp_path = self.path
                try:
                    tables = camelot.read_pdf(temp_path,
                        strip_text='\n',
                        pages=','.join(map(str, page_ids)),
                        line_tol=6,
                        line_scale=60)
                except IndexError:
                    tables = []
                
                # check chaos tables
                num_chaos = 0
                for table in tables:
                    for _, row in table.df.iterrows():
                        for v in row.values:
                            point_num = list(v).count('.')
                            num_chaos = max(point_num, num_chaos)
                # print(num_chaos, '--')

                if len(tables) == 0 or num_chaos > 5:
                    tables = camelot.read_pdf(temp_path,
                        pages=','.join(map(str, page_ids)),
                        flavor='stream', edge_tol=100)
                if False:
                    for table in tables:
                        print(table.page)
                        import matplotlib.pyplot as plt
                        camelot.plot(table, kind='grid').show()
                        plt.show()
                        for _, row in table.df.iterrows():
                            print(row.values)
        else:
            
            # def cidToChar(cidx):
            #     return chr(int(re.findall()[0]) + 29)
            tables = camelot.read_pdf(self.path,
                    strip_text='\n',
                    pages=','.join(map(str, page_ids)),
                    line_scale=60, copy_text=['v', 'h'])
            # tables.export(r'C:\Users\CHENZHAOCAI\Downloads\\foo.csv', f='csv', 
            #               compress=False)
            # tables = camelot.read_pdf(self.path, flavor='stream',
            #     pages=','.join(map(str, page_ids)), edge_tol=100)
            print(tables)
            for table in tables:
                print(table.df.to_string())
                print(table._bbox)
            # import matplotlib.pyplot as plt
            # camelot.plot(tables[0], kind='text')
            # plt.show()
        return tables

    def extract_table_of_pages_pdfplumber(self, page_ids: list):
        pdf = pdfplumber.open(self.path)
        
        tables = []
        for i, page in enumerate(pdf.pages):
            if page.page_number not in page_ids:
                continue

            page = page.filter(self.keep_visible_lines)
            
            edges = self.curves_to_edges(page.curves + page.edges)
            if len(edges) > 0:
                table_settings = {
                    "vertical_strategy": "explicit",
                    "horizontal_strategy": "explicit",
                    "explicit_vertical_lines": self.curves_to_edges(page.curves + page.edges),
                    "explicit_horizontal_lines": self.curves_to_edges(page.curves + page.edges),
                    "intersection_y_tolerance": 3,
                    'snap_tolerance': 3,
                }
            else:
                table_settings = {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    'snap_tolerance': 3,
                }
            
            # Get the bounding boxes of the tables on the page.
            plumber_tables = page.find_tables(table_settings=table_settings)
            # camelot_tables = []
            
            # for table in plumber_tables:
            #     x0, top, x1, bottom = table.bbox
            #     print(table.bbox, page.height)
            #     area = ','.join(map(str, [x0, page.height-bottom, x1, page.height-top]))
            #     print(area)
            #     tables_in_bbox = camelot.read_pdf(pdf_path, pages=str(i),
            #         table_regions=[area], strip_text=' \n')
            #     print(len(tables_in_bbox))
            #     # assert len(tables_in_bbox) == 1
            #     for ctab in tables_in_bbox:
            #         camelot_tables.append({
            #             'x0': x0, 'top': top, 'x1': x1, 'bottom': bottom,
            #             'text': ctab.df.to_string()})

            # table_bboxes = [table.bbox for table in plumber_tables]

            # Get the text lines on the page without tables.
            # lines = page.filter(lambda obj : self.not_within_bboxes(obj, table_bboxes))\
            #     .extract_text_lines()

            # page_objs = lines + plumber_tables
            # page_objs = sorted(page_objs, key=lambda obj: self.get_top(obj))
            
            # docs.extend([self.get_text(t) for t in page_objs])
            tables.extend([self.get_text(t) for t in plumber_tables])

        for table in tables:
            print(table)

        return tables
        

    @staticmethod
    def keep_visible_lines(obj):
        """
        If the object is a ``rect`` type, keep it only if the lines are visible.

        A visible line is the one having ``non_stroking_color`` not null.
        """
        if obj['object_type'] == 'rect':
            if obj['non_stroking_color'] is None:
                return False
            if obj['width'] < 1 and obj['height'] < 1:
                return False
            # return obj['width'] >= 1 and obj['height'] >= 1 and obj['non_stroking_color'] is not None
        if obj['object_type'] == 'char':
            return obj['stroking_color'] is not None and obj['non_stroking_color'] is not None
        return True
    
    @staticmethod
    def curves_to_edges(cs):
        """See https://github.com/jsvine/pdfplumber/issues/127"""
        edges = []
        for c in cs:
            edges += pdfplumber.utils.rect_to_edges(c)
        return edges
    
    @staticmethod
    def not_within_bboxes(obj, bboxes):
        """Check if the object is in any of the table's bbox."""
        def obj_in_bbox(_bbox):
            """See https://github.com/jsvine/pdfplumber/blob/stable/pdfplumber/table.py#L404"""
            v_mid = (obj["top"] + obj["bottom"]) / 2
            h_mid = (obj["x0"] + obj["x1"]) / 2
            x0, top, x1, bottom = _bbox
            return (h_mid >= x0) and (h_mid < x1) and (v_mid >= top) and (v_mid < bottom)
        return not any(obj_in_bbox(__bbox) for __bbox in bboxes)
    
    @staticmethod
    def get_top(obj):
        if isinstance(obj, pdfplumber.table.Table):
            return obj.bbox[1]
        if isinstance(obj, dict):
            return obj['top']
    
    @staticmethod
    def get_text(obj):
        if isinstance(obj, pdfplumber.table.Table):
            table_text = obj.extract()
            table_text = [[t if t is not None else 'NULL' for t in row] for row in table_text]
            table_text = [[t.replace('\n', '').replace(' ', '') for t in row] for row in table_text]
            table_text = [[t if t!='' else 'NULL' for t in row] for row in table_text]
            text = '\n'
            if len(table_text) == 0:
                return text
            num_cols = len(table_text[0])
            seps = ['---' for _ in range(num_cols)]
            if len(table_text) > 1:
                table_text.insert(1, seps)
            for row in table_text:
                text += '| {} |\n'.format(' | '.join(row))
            text += '\n'
            return text
        if isinstance(obj, dict):
            text = obj['text'].replace(' ', '').replace('\n', '')
            if len(text) == 0:
                return ''
            else:
                return text + '\n'