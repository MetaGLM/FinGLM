from .keywords import *
from .formulas import *
from .alias import *
from .db.db_schema import schema, schema_edu

import jieba
from tqdm import tqdm

jieba.del_word("以上学历")
for word in type1_keywords + other_text_words + other_cut_words + list(formula_dict.keys()):
    jieba.add_word(word)
    
for comp in comps | comps_short:
    jieba.add_word(comp)

for k, v in alias_inv_dict.items():
    jieba.add_word(k)
    jieba.add_word(v)
    
def exact_search_query(query, query_words):
    comp_names = []
    comp_short_names = []
    years = re.findall("\d{4}年", query)
    
    qwords = jieba.cut(query)
    for qword in qwords:
        if qword in comps:
            comp_names.append(qword)
        elif qword in comps_short:
            comp_short_names.append(qword)
            
    return comp_names, comp_short_names, years

def extract_comps_and_names(query, query_words):
    # 先进行精准召回
    comp_names, comp_short_names, years = exact_search_query(query, query_words)
    # 公司名
    for short in comp_short_names:
        comp_name = short_comp_dict[short]
        if comp_name not in comp_names:
            comp_names.append(comp_name)

    return comp_names, years

def extract_keywords(query, query_words):
    keywords = []
    # print(query_words)
    for raw_word in query_words:
        word = raw_word
        # print(word, raw_word)
        if word in alias_inv_dict:
            word = alias_inv_dict[word]
        # print(word, raw_word)
        # type2
        if word in formula_dict:
            detail = formula_dict[word]
            new_keyword = Keyword(word, type=2, formula=detail["raw_formula"], is_percent=detail["is_percent"], raw_word=raw_word)
            keywords.append(new_keyword)
        # type1
        elif word in schema:
            keywords.append(Keyword(word, type=1, formula=word, raw_word=raw_word))
        # 较为泛型的 type2
        elif word in ('及以上', '及以下', '以上', '以下') and keywords[-1].word in schema_edu:
            if len(keywords) >= 1:
                edu_idx = schema_edu.index(keywords[-1].word)
                all_edus = []
                if "以上" in word:
                    all_edus += schema_edu[edu_idx + 1:]
                elif "以下" in word:
                    all_edus += schema_edu[:edu_idx]
                if "及" in word:
                    all_edus.append(keywords[-1].word)
                all_edus.sort(key=lambda x: schema_edu.index(x))
                all_edus_str = "+".join(all_edus)
                new_keyword = Keyword(f"{keywords[-1].word}{word}", type=2, formula=f"{all_edus_str}", raw_word=f"{keywords[-1].raw_word}{word}")
                keywords = keywords[:-1] + [new_keyword]
        elif word in ('比率', '比例', '比值', '比'):
            if len(keywords) >= 2:
                s = query.index(keywords[-2].raw_word)
                e = query.index(raw_word) + len(raw_word)
                new_keyword = Keyword(f"{keywords[-2].word}和{keywords[-1].word}的比", type=2, formula=f"({keywords[-2].formula})/({keywords[-1].formula})", raw_word=query[s:e], is_percent=False)
                last_2_keyword = new_keyword.get_sub_word_by_name(keywords[-2].word)
                if last_2_keyword != None: 
                    last_2_keyword.raw_word = keywords[-2].raw_word
                last_1_keyword = new_keyword.get_sub_word_by_name(keywords[-1].word)
                if last_1_keyword != None:
                    last_1_keyword.raw_word = keywords[-1].raw_word
                keywords = keywords[:-2] + [new_keyword]
        elif word in ('增长率'):
            if len(keywords) >= 1:
                s = query.index(keywords[-1].raw_word)
                e = query.index(raw_word) + len(raw_word)
                last_keyword = last_year_keyword(keywords[-1])
                new_keyword = Keyword(f"{keywords[-1].word}增长率", type=2, formula=f"({keywords[-1].formula}-{last_keyword.formula})/{last_keyword.formula}", raw_word=query[s:e], is_percent=True)
                
                last_2_keyword = new_keyword.get_sub_word_by_name(last_keyword.word)
                if last_2_keyword != None:
                    last_2_keyword.raw_word = last_keyword.raw_word
                last_1_keyword = new_keyword.get_sub_word_by_name(keywords[-1].word)
                if last_1_keyword != None:
                    last_1_keyword.raw_word = keywords[-1].raw_word
                keywords = keywords[:-1] + [new_keyword]
        elif word in other_text_words:
            keywords.append(Keyword(word, type=3))

    return keywords

def query_analyze(query):
    query = re.sub("[(（）)]", "", query)
    query = query.replace("每股的", "每股")
    query_words = jieba.lcut(query)
    comp_names, years = extract_comps_and_names(query, query_words)
    keywords = extract_keywords(query, query_words)
    return comp_names, years, keywords

def get_query_analyze_result(query):
    comp_names, years, raw_keywords = query_analyze(query)
    query_analyze_result = {
        "comps": comp_names,
        "years": years,
        "keywords": raw_keywords 
    }
    return query_analyze_result

def query_type_router(query):
    query_analyze_result = get_query_analyze_result(query)

    ''' 2^3 = 8
        comps years keywords
        y y y type11/type2
        y y n type31
        y n y type12
        y n n x - type12 很可能是因为关键词为隐性的
        n y y type12
        n y n x - type12 很可能是因为关键词为隐性的
        n n y type32
        n n n x - type32

        keypoint: keyword detection
    '''
    keywords = [i for i in raw_keywords if i.type != 3]
    if comp_names and years and keywords:
        if any([keyword.type == 2 for keyword in keywords]):
            return "type2", query_analyze_result
        else:
            return "type11", query_analyze_result
    elif comp_names and years and not keywords:
        return "type31", query_analyze_result
    elif (comp_names and not years and keywords) or (not comp_names and years and keywords) \
      or (comp_names and not years and not keywords) or (not comp_names and years and not keywords):
        return "type12", query_analyze_result
    elif not comp_names and not years:
        return "type32", query_analyze_result
    return "type32", query_analyze_result

    


if __name__ == "__main__":
    # 生成nl2sql type11数据集 得代码
    import json

    import json
    import random
    all_comps = list(comps) + list(comps_short)
    all_years = ["2019年", "2020年", "2021年"]
    with open("random_gen_type11_type2_data.json", "w", encoding="utf-8") as f:
        for line in open("type_extra_data.json", encoding="utf-8"):
            line = json.loads(line)
            query = re.findall("【问题】(.+?)\n", line["prompt"])[0]
            raw_comp = re.findall("公司名称为(.+?)的公司", query)
            if raw_comp:
                query = query.replace(f"公司名称为{raw_comp[0]}的公司", raw_comp[0])
            raw_comp_short = re.findall("股票简称为(.+?)的公司", query)
            if raw_comp_short:
                query = query.replace(f"股票简称为{raw_comp_short[0]}的公司", raw_comp_short[0])
            comp_names, years, keywords = query_analyze(query)

            comp = comp_names[0]
            comp = comp if comp in comp_names else comp_short_dict[comp]
            year = random.choice(years)
            keyword = random.choice(keywords)

            random_comp = random.choice(all_comps)
            random_year = random.choice(all_years)
            random_keyword = random.choice(schema)

            if random_keyword in alias_dict:
                random_keyword = random.choice(alias_dict[random_keyword] + [random_keyword])

            new_query = query.replace(comp, random_comp).replace(year, random_year).replace(keyword.raw_word, random_keyword)
            f.write(json.dumps({"query": new_query, "type": "type11"}, ensure_ascii=False) + "\n")

            # dump type2
            random_comp = random.choice(all_comps)
            random_year = random.choice(all_years)
            random_keyword = random.choice(schema)

            if random_keyword in alias_dict:
                random_keyword = random.choice(alias_dict[random_keyword] + [random_keyword])
            random_keyword = random_keyword + "增长率"

            new_query = query.replace(comp, random_comp).replace(year, random_year).replace(keyword.raw_word, random_keyword)
            f.write(json.dumps({"query": new_query, "type": "type2"}, ensure_ascii=False) + "\n")