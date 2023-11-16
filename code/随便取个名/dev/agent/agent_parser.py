import re
import json
import sys
from langchain.llms import ChatGLM
# from langchain_experimental.pal_chain import PALChain
from pal_chain import PALChain
# from api import run_chatglm

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

def post_process(output, percent=False):
    ret = float(output)
    if percent:
        ret = '%.2f' % (100 * ret) + "%"
    else:
        ret = '%.2f' % (ret)

    return ret



class Agent_Parser:
    
    def __init__(self) -> None:
        ## 开启api
        endpoint_url = ("http://127.0.0.1:29501")
        model_path = "Helsinki-NLP/opus-mt-zh-en"
        # model_path = "model/opus-mt-zh-en"
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.translator = pipeline("translation_zh_to_en", model=self.model, tokenizer=self.tokenizer)
        self.llm = ChatGLM(
            endpoint_url=endpoint_url,
            max_token=10000,
            history=[],
            temperature=0,
            # top_p=0.9,
            model_kwargs={"sample_model_args": False},
        )

        # self.pal_chain = PALChain.from_zh_math_prompt(llm=self.llm, verbose=True)
        # adding 5 second time_out
        self.pal_chain = PALChain.from_math_prompt(llm=self.llm, verbose=True, timeout=5)

    def __init_app(self):
        pass

    def parse_ratio(self, item):
        try:
            date = int(item['DATE'][0])
            key  = item['task_key'][0]
            prompt = item['prompt'].replace(item['Company_name'], "公司").replace("元", "")

            zh_prompt = "，".join(prompt.split("，")[:-1]) + f"，请问公司在{date}的{key}是？"
            en_prompt = self.translator(zh_prompt)[0]['translation_text']
            ### 更换正则匹配
            num_pattern = re.compile(r'\d+\.?\d*')
            zh_num = num_pattern.findall(zh_prompt)
            en_num = num_pattern.findall(en_prompt)
            print("origin prompt:", zh_prompt)
            print("en_prompt", en_prompt)
            for num1, num2 in zip(en_num, zh_num):
                en_prompt = en_prompt.replace(num1, num2)
            # output = self.pal_chain.run(zh_prompt)
            output = self.pal_chain.run(en_prompt)
            
            if key in ['企业研发经费与利润比值', '企业研发经费与营业收入比值', '流动比率', '速动比率', '企业研发经费占费用比例', '企业硕士及以上人员占职工人数比例', '研发人员占职工人数比例']:
                ret = post_process(output, percent=False)
            else:
                ret = post_process(output, percent=True)
            ret = item['prompt'] + f"{item['Company_name']}在{date}的{key}是{ret}"
            return ret
        except:
            return "not found"

if __name__ == "__main__":
    parser = Agent_Parser()
    path='./data/dataset.json'
    questions = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            questions.append(json.loads(line))

    parser = Agent_Parser()
    for question in questions:
        # ratio question
        if question['category'] == 2:
            ret = parser.parse_ratio(question)
            print(ret)