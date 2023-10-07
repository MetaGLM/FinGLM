from excel_extraction import extract_layers
from excel_extraction import from_html_extract_excel
from excel_extraction import from_json_extract_excel
from excel_extraction import count_and_merge
from excel_extraction import excel_process
from excel_extraction import company_extractor
from excel_extraction import merge_heading
import os


def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)
        

html_folder = 'data/allhtml'
txt_folder = 'data/alltxt'
html_excel_folder = 'data/html_excels'
mkdir(html_excel_folder)
dict_json_folder = 'data/dict_json'
list_json_folder = 'data/list_json'
mkdir(dict_json_folder)
mkdir(list_json_folder)
txt_excel_folder = 'data/txt_excel'
mkdir(txt_excel_folder)
merge_excel_folder = 'data/merge_excel'
mkdir(merge_excel_folder)
processed_excel_folder = 'data/processed_excels'
mkdir(processed_excel_folder)
company_folder = 'data/company_info'
final_excel_folder = 'data/final_excels'
mkdir(final_excel_folder)


if __name__ == '__main__':
    #company_extractor.main()
    #extract_layers.main(txt_folder, dict_json_folder, list_json_folder)
    #from_html_extract_excel.main(html_folder, html_excel_folder)
    from_json_extract_excel.main(dict_json_folder, txt_excel_folder)
    count_and_merge.main(html_excel_folder, txt_excel_folder, merge_excel_folder)
    excel_process.main(merge_excel_folder, processed_excel_folder)
    merge_heading.main(processed_excel_folder, company_folder, final_excel_folder)