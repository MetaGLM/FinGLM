from .data_utils import extract_all_company_name, load_questions, load_extracted
import json
from snownlp.sim.bm25 import BM25
import numpy as np
import jieba
import regex as re


class EntityExtractor:
    def __init__(self) -> None:
        self.full_company_name, self.short_company_name = self.load_data()
        self.company_name_code_mapping = {**self.full_company_name, **self.short_company_name}

    def load_data(self):
        company_names = extract_all_company_name()[['full_name', 'short_name', 'stock_code']]
        full_company_name = company_names['full_name'].tolist()
        short_company_name = company_names['short_name'].tolist()
        stock_code = company_names['stock_code'].tolist()
        l = len(company_names)
        return {full_company_name[idx]:stock_code[idx] for idx in range(l)}, \
            {short_company_name[idx]:stock_code[idx] for idx in range(l)}


    def query_company_names(self, company_names):
        query_result = []
        failed_count = 0
        for company_name in company_names:
            if company_name == "无":
                query_result.append(None)
                continue
            find = False
            for full_name in self.full_company_name:
                if full_name == company_name or full_name.startswith(company_name):
                    query_result.append(self.full_company_name[full_name])
                    find = True
                    break
            if not find:
                for short_name in sorted(self.short_company_name.keys(), key=lambda k:len(k), reverse=True):
                    if short_name == company_name or company_name in short_name or short_name in company_name:
                        query_result.append(self.short_company_name[short_name])
                        find = True
                        break
            if not find:
                query_result.append(None)
                failed_count += 1
        print(f"failed:{failed_count} failed ratio: {failed_count / len(query_result)}")
        return query_result


class BM25EnityExtractor(EntityExtractor):
    def __init__(self) -> None:
        super(BM25EnityExtractor, self).__init__()
        full, short = self.load_data()
        self.vallina_corpus = [name for name in [*full, *short]]
        self.short_corpus = [jieba.lcut(name) for name in short]
        self.full_corpus = [jieba.lcut(name) for name in full]
        self.short_name_model, self.full_name_model = self.init_bm25_model()
        self.exact_extractor = EntityExtractor()

    def init_bm25_model(self):
        s_model = BM25(self.short_corpus)
        f_model = BM25(self.full_corpus)
        return s_model, f_model
    
    
    def query_company_names(self, companies, log=False):
        companies = [re.sub(r"[（）\(\)]", "", question) for question in companies]
        stock_codes = self.exact_extractor.query_company_names(companies)
        fixed_count = 0
        for idx, company_name in enumerate(companies):
            if company_name == "无":
                continue
            elif stock_codes[idx] is None:
                if "公司" in company_name:
                    engine = self.full_name_model
                    corpus = self.full_corpus
                else:
                    engine = self.short_name_model
                    corpus = self.short_corpus
                company_name = jieba.lcut(company_name)
                index = np.argsort(-np.array(engine.simall(company_name)))[0]
                if ''.join(company_name) != ''.join(corpus[index]) and log:
                    print("pred:",''.join(company_name),"\ttarget:", ''.join(corpus[index]))
                if len(set(''.join(company_name)) & set(''.join(corpus[index]))) >= 2:
                    stock_codes[idx] = self.company_name_code_mapping[''.join(corpus[index])]
                    fixed_count += 1
        print(f"fixed count:{fixed_count}")
        return stock_codes


if __name__ == '__main__':
    # json.dump(EntityExtractor().query_company_names(load_questions()), open("query_result.json", 'w'), indent=4, ensure_ascii=False)
    extracted = load_extracted(name_only=False)
    stock_codes = BM25EnityExtractor().query_company_names(load_extracted())
    with open("data/temp/extracted_with_stock_code.json", 'w') as fp:
        for info, code in zip(extracted, stock_codes):
            info['info_dict']['stock_code'] = code
            fp.write(json.dumps(info, ensure_ascii=False) + "\n")