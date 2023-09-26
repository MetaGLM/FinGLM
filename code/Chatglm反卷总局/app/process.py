from process_pdf.initial_company_annual_reports import intial_company_excel
from process_keyword.question_analyse import question_analyse
from process_es.create_index import create_index
from process_es.preprocess import extra_title
from process_es.parse_three_table import gen_table_text
from process_es.initial_data_batch2 import initial_text_es
from process_es.initial_gen_table_text_batch import initial_sentence_es


if __name__ == '__main__':

    print('生成company_annual_reports_path')
    intial_company_excel()

    print('执行question分析')
    question_analyse()

    print('txt解析标题')
    extra_title()

    print('生成句子')
    gen_table_text()

    print('创建ES_index')
    create_index()

    print('推文本ES')
    initial_text_es()

    print('推生成句子ES')
    initial_sentence_es()




