from .base_query import base_query
from tqdm import tqdm
import json
import os
import regex as re

def verify_info_dict(info_dict):
    if isinstance(info_dict, dict):
        if '类型' in info_dict and info_dict['类型'] == "公司问题":
            if "年份" in info_dict and isinstance(info_dict['年份'], list) and len(info_dict['年份']) >= 1 and isinstance(info_dict['年份'][0], str):
                if "公司名称" in info_dict and isinstance(info_dict['公司名称'], str):
                    return True
            print("公司问题匹配错误：", info_dict)                        
    return False

def load_representers():
    result_dict = {}
    for file in os.listdir('data/final_excels'):
        _, full_name, stock_code, short_name, year, _ = file.split("__")
        data_json = json.load(open(os.path.join('data/final_excels', file), 'r', encoding='utf8'))
        for kw_tuple in data_json:
            if '公司的法定代表人' == kw_tuple[0]:
                result_dict[(stock_code, year.replace("年",""))] = kw_tuple[1]
    return result_dict


class company_info_query(base_query):
    def __init__(self, model, tokenizer, excels) -> None:
        super(company_info_query, self).__init__(model, tokenizer, excels)
        self.statistic = {
            "failed_cnt": 0
        }
        self.representers = load_representers()


    def _run_query(self, questions, retrieved_infos, batch_size=32):
        prompt = "[Round 1]\n\n问：现在给你若干个包含公司基本信息的表格,请你根据表格的内容正确回答问题:\n{}\n\n答："
        assert len(questions) == len(retrieved_infos)
        result_placeholder = [None for _ in range(len(questions))]
        batch_questions = []
        batch_data = []
        batch_indexes = []
        for idx, (question, retrieved_info) in enumerate(tqdm(zip(questions, retrieved_infos), total=len(questions), desc="公司")):
            # if retrieved_info['类型'] == '公司问题':
            if verify_info_dict(retrieved_info):
                table_text = self.get_target_table(retrieved_info)
                model_input_string = prompt.format(table_text + "\n\n" + question)
                batch_data.append(model_input_string)
                batch_indexes.append(idx)
                batch_questions.append(question)
            if len(batch_data) == batch_size or (idx == len(questions) - 1 and len(batch_data) > 0):
                batch_results = self.predict_batch(batch_data)
                for batch_result, batch_question, batch_index, model_input in zip(batch_results, batch_questions, batch_indexes, batch_data):
                    if isinstance(batch_result, str) and "法定代表人" in batch_question:
                        batch_result = batch_result.replace("一样", "相同")
                        batch_result = batch_result.replace("法人代表", "法定代表人")
                        try:
                            if len(retrieved_infos[batch_index]['年份']) >= 2:
                                lawyers = []
                                pattern = r"([\(（][^)）]*[\)）])"
                                for year in retrieved_infos[batch_index]['年份']:
                                    if (retrieved_infos[batch_index]['股票代码'], year) in self.representers:
                                        name = self.representers[(retrieved_infos[batch_index]['股票代码'], year)].replace("1", "").replace("注","").replace("先生", "").replace(" ", "").replace("【注】", "")
                                        name = name.replace("董事长", "").replace("贇", "赟")
                                        lawyers.append(re.sub(pattern, "", name))
                                flag = True
                                if len(lawyers) > 1:
                                    for lawyer in lawyers:
                                        if lawyer != lawyers[0]:
                                            flag = False
                                            break
                                    if flag and "不同" in batch_result:
                                        batch_result = batch_result.replace("不同", "相同")
                                        print(batch_result, lawyers)
                                    if not flag and "相同" in batch_result:
                                        batch_result = batch_result.replace("相同", "不同")
                                        print(batch_result, lawyers)
                        except Exception as err:
                            print(err)
                    result_placeholder[batch_index] = {
                        "id": batch_index,
                        "question": batch_question,
                        "answer": batch_result
                    }
                    if "法定代表人" in batch_question:
                        print(result_placeholder[batch_index])
                batch_data = []
                batch_indexes = []
                batch_questions = []
        return result_placeholder
    

    def predict_batch(self, batch_inputs):
        inputs = self.tokenizer(batch_inputs, return_tensors="pt", max_length=1024, truncation=True, padding=True)
        inputs = inputs.to("cuda")
        outputs = self.model.generate(**inputs, max_new_tokens=384, do_sample=True, top_p=0.7, temperature=0.95)
        response = self.tokenizer.batch_decode(outputs)
        response = [res[res.index("答：")+2:].strip() for res in response]
        return response

    
    def get_target_table(self, retrieved_info):
        stock_code = retrieved_info['股票代码']
        year_list = retrieved_info['年份']
        table_text_list = []
        for year in year_list:
            if (stock_code, year) in self.excels and '公司信息' in self.excels[(stock_code, year)]:
                table = self.excels[(stock_code, year)]                
                table_text = "\n".join([" ".join([item for item in eval(line) if item != ""]) for line in table['公司信息']])
                table_text += f"\n年份 {year}" 
                table_text_list.append(table_text)
            else:
                self.statistic['failed_cnt'] += 1
        return '\n\n'.join(table_text_list)

    @property
    def prefix_checkpoint_path(self) -> str:
        """
        实现时直接返回prefixtuning的checkpoint路径
        """
        return "model/table_qa/company_info/checkpoint-3000"


if __name__ == '__main__':
    import json
    import os
    def load_excels():
        def preprocess_excels(excel):
            return excel

        def load_merged_excels():
            excel_mapping = {}
            for file in os.listdir('data/merged_excels'):
                filename = os.path.basename(file)
                _, full_name, stock_code, short_name, year, _ = filename.split("__")
                year = year.replace("年", "")
                excel_mapping[(stock_code, year)] = preprocess_excels(json.load(open(os.path.join('data/merged_excels', file), 'r')))
            return excel_mapping

        def load_company_infos():
            company_mapping = {}
            for file in os.listdir('data/company_info'):
                filename = os.path.basename(file)
                _, full_name, stock_code, short_name, year, _ = filename.split("__")
                year = year.replace("年", "")
                company_mapping[(stock_code, year)] = json.load(open(os.path.join('data/company_info',file), 'r'))
            return company_mapping

        excel_mapping = load_merged_excels()
        company_infos = load_company_infos()
        for k in excel_mapping:
            excel_mapping[k]['公司信息'] = company_infos[k]
        # for k,v in sorted(Counter(header_list).items(), key=lambda x:x[1], reverse=True):
        #     print(f"{k}:\t{v}")
        return excel_mapping
    
    def load_extracted():
        result = [json.loads(line) for line in open('finetune/table_qa/data/classification.jsonl', 'r', encoding='utf8').readlines()]
        for idx, res in enumerate(result):
            if isinstance(res, list):
                result[idx] = {
                    "类型": "未知"
                }
        return result
    
    def extract_company_names(extracted_info):
        res = []
        for line in extracted_info:
            if '公司名称' in line:
                res.append(line['公司名称'])
            else:
                res.append('')
        return res


    def query_stock_code(companies):
        import sys 
        sys.path.append("glm_components")
        from query_company import BM25EnityExtractor
        extractor = BM25EnityExtractor()
        return extractor.query_company_names(companies)
    
    def set_stock_code(company_infos):
        company_names = extract_company_names(company_infos)
        stock_codes = query_stock_code(company_names)
        for company_info, stock_code in zip(company_infos, stock_codes):
            if '公司名称' in company_info:
                company_info['股票代码'] = stock_code
        return company_infos
    def load_questions():
        """_summary_
        加载所有的问题
        """
        quests = []
        with open(os.path.join(os.path.dirname(__file__), "../../data/C-list-question.jsonl"), 'r') as fp:
            for line in fp.readlines():
                quests.append(json.loads(line)['question'])
        return quests
    from transformers import AutoConfig, AutoTokenizer, AutoModel
    model_path = "model/chatglm2-6b"
    checkpoint_path = "model/classifier/checkpoint-400"
    config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
    config.prefix_projection = False
    config.pre_seq_len = 128
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_path, config=config, trust_remote_code=True)
    excels = load_excels()
    query = company_info_query(model, tokenizer, excels)
    answers = query.run_query(load_questions(), set_stock_code(load_extracted()))
    for answer in answers:
        if answer is not None and "法定代表人" in answer['question']:
            print(json.dumps(answer, ensure_ascii=False, indent=4) + "\n")
    print(query.statistic)