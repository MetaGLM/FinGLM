from .base_query import base_query
from tqdm import tqdm
import re


def verify_info_dict(info_dict):
    if isinstance(info_dict, dict):
        if '类型' in info_dict and info_dict['类型'] == "人员问题":
            if "年份" in info_dict and isinstance(info_dict['年份'], list) and len(info_dict['年份']) >= 1 and isinstance(info_dict['年份'][0], str):
                if "公司名称" in info_dict and isinstance(info_dict['公司名称'], str):
                    return True
            print("人员问题匹配错误：", info_dict)
    return False


class personal_query(base_query):
    def __init__(self, model, tokenizer, excels) -> None:
        super(personal_query, self).__init__(model, tokenizer, excels)
        self.statistic = {
            "failed_cnt": 0
        }

    def _run_query(self, questions, retrieved_infos, batch_size=32):
        prompt = "[Round 1]\n\n问：现在给你若干个包含公司员工信息和研发信息的表格,请你根据表格的内容正确回答问题:\n{}\n\n答："
        assert len(questions) == len(retrieved_infos)
        result_placeholder = [None for _ in range(len(questions))]
        batch_questions = []
        batch_data = []
        batch_indexes = []
        for idx, (question, retrieved_info) in enumerate(tqdm(zip(questions, retrieved_infos), total=len(questions), desc="人员")):
            # if retrieved_info['类型'] == '人员问题':
            if verify_info_dict(retrieved_info):
                table_text = self.get_target_table(retrieved_info)
                model_input_string = prompt.format(table_text + "\n\n" + question)
                batch_data.append(model_input_string)
                batch_indexes.append(idx)
                batch_questions.append(question)
            if len(batch_data) == batch_size or (idx == len(questions) - 1 and len(batch_data) > 0):
                batch_results = self.predict_batch(batch_data)
                for batch_result, batch_question, batch_index, model_input in zip(batch_results, batch_questions, batch_indexes, batch_data):
                    batch_result = batch_result.replace("硕士及以上人数/职工总数","(硕士人数 + 博士及以上人数)/职工总数").replace("硕士及以上人员/职工总数","(硕士人数 + 博士及以上人数)/职工总数").replace("硕士及以上人数/职工人数", "(硕士人数 + 博士及以上人数)/职工总数")
                    batch_result = batch_result.replace("研发人员占职工人数的比例=研发人员/职工人数", "研发人员占职工人数比例=研发人员数/职工总数") 
                    result_placeholder[batch_index] = {
                        "id": batch_index,
                        "question": batch_question,
                        "answer": batch_result
                    }
                    if "公式" in batch_result:
                        print(batch_question, batch_result)
                    # print(model_input)
                    # print(batch_result)
                batch_data = []
                batch_indexes = []
                batch_questions = []
        return result_placeholder
    

    def predict_batch(self, batch_inputs):
        inputs = self.tokenizer(batch_inputs, return_tensors="pt", max_length=2048, truncation=True, padding=True)
        inputs = inputs.to("cuda")
        outputs = self.model.generate(**inputs, max_new_tokens=256, do_sample=True, top_p=0.7, temperature=0.95)
        response = self.tokenizer.batch_decode(outputs)
        response = [res[res.index("答：")+2:].strip() for res in response]
        # response = [res.strip() for res in response]
        
        # 正则匹配 大括号中的内容{}，懒惰模式
        pattern = re.compile(r'\{.*?\}')
        for idx, res in enumerate(response):
            matchs = pattern.findall(res)
            for cur_match in matchs:
                # cur_match = matchs[-1]
                try:
                    value = list(eval(cur_match))[0]
                    if isinstance(value, float):
                        cur_match_res = f"{value :.2f}"
                    else:
                        cur_match_res = str(value)
                    res = res.replace(cur_match, cur_match_res)
                except:
                    continue
            response[idx] = res
        return response

    
    def get_target_table(self, retrieved_info):
        def get_table(excel_json):
            yg_excel = excel_json.get('员工数量、专业构成及教育程度')
            yf_excel = excel_json.get('研发投入')
            
            yg_table = []
            if yg_excel:
                yg_table = []
                for line in yg_excel:
                    yg_table.append(line)
                    
            yf_table = []
            if yf_excel:
                yf_table = []
                for line in yf_excel:
                    yf_table.append(line)
                    
            return yg_table, yf_table
        
        stock_code = retrieved_info['股票代码']
        year_list = retrieved_info['年份']
        company_name = retrieved_info['公司名称']
        
        table_str = ""
        for year in year_list:
            if (stock_code, year) in self.excels:
                yg_table, yf_table = get_table(self.excels[(stock_code, year)])
                table_str = f"{year}年{company_name}员工数量、专业构成及教育程度表：" + '\n'.join(' '.join(table) for table in yg_table) + "\n\n" + f"{year}年{company_name}研发投入表：" + '\n'.join(' '.join(table) for table in yf_table)
            else:
                self.statistic['failed_cnt'] += 1
        return table_str

    @property
    def prefix_checkpoint_path(self) -> str:
        """
        实现时直接返回prefixtuning的checkpoint路径
        """
        return "model/table_qa/personal/checkpoint-1500"


if __name__ == '__main__':
    import json
    import os
    def load_excels():
        excel_path = "data/chatglm_llm_fintech_raw_dataset/excels"
        def preprocess_excels(excel):
            return excel

        def load_merged_excels():
            excel_mapping = {}
            for file in os.listdir(excel_path):
                filename = os.path.basename(file)
                _, full_name, stock_code, short_name, year, _ = filename.split("__")
                year = year.replace("年", "")
                excel_mapping[(stock_code, year)] = preprocess_excels(json.load(open(os.path.join(excel_path, file), 'r')))
            return excel_mapping

        excel_mapping = load_merged_excels()
       
        return excel_mapping
    
    def load_extracted():
        return [json.loads(line) for line in open('finetune/table_qa/data/classification.jsonl', 'r', encoding='utf8').readlines()]
    
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
        with open(os.path.join(os.path.dirname(__file__), "../../data/C-list-question.json"), 'r') as fp:
            for line in fp.readlines():
                quests.append(json.loads(line)['question'])
        return quests
    
    from transformers import AutoConfig, AutoTokenizer, AutoModel
    model_path = "model/chatglm2-6b"
    
    config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
    config.prefix_projection = False
    config.pre_seq_len = 128
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_path, config=config, trust_remote_code=True)
    
    excels = load_excels()
    query = personal_query(model, tokenizer, excels)
    questions = load_questions()
    retrieved_infos = set_stock_code(load_extracted())
    
    answers = query.run_query(questions, retrieved_infos)
    for answer in answers:
        if answer is not None:
            print(json.dumps(answer, ensure_ascii=False, indent=4) + "\n")
    print(query.statistic)