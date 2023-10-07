import os
os.environ["CUDA_VISIBLE_DEVICES"] = '1'
from peft import PeftModel
import torch
from transformers import AutoModel, AutoTokenizer, AutoConfig
model_path = "model/chatglm2-6b"
# checkpoint_path = "model/classifier/checkpoint-800"
# config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
# config.prefix_projection = False
# config.pre_seq_len = 128
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModel.from_pretrained(model_path, trust_remote_code=True)
# prefix_state_dict = torch.load(os.path.join(checkpoint_path, "pytorch_model.bin"))
# new_prefix_state_dict = {}
# for k, v in prefix_state_dict.items():
#     if k.startswith("transformer.prefix_encoder."):
#         new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
# model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
model = model.half()
model = model.cuda()


def extract_company_name(text):
    text = f"[Round 1]\n\n问：提取以下句子中的公司名称，没有则回答无: {text} \n\n答："
    return get_response(text)


def get_response(text):
    # print(text)
    inputs = tokenizer([text], return_tensors="pt", max_length=2048, truncation=True)
    inputs = inputs.to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=1024)
    outputs = outputs.tolist()[0][len(inputs['input_ids'][0]):]
    response = tokenizer.decode(outputs)
    return response


def common_conversation(message, history):
    text = ""
    idx = 0
    for idx, hist in enumerate(history):
        text += f"[Round {idx+1}]\n\n问:{hist[0]}\n\n答:{hist[1]}"
    text += f"[Round {idx+2}]\n\n问:{message}\n\n答:"
    response = get_response(text)
    history.append((message, response))
    return response


n_round = 1
message = """
样例1
问题: 根据厦门中创环保科技股份有限公司2019年的年报数据，能否简要介绍公司报告期内非标准审计报告的说明的详情。
检索内容: 董事会对最近一期“非标准审计报告”相关情况的说明：\n公司董事会认为，大华会计师事务所（特殊普通合伙）严格按照审慎性原则，为公司出具带有强调事项段的无保留意见审计报告（大华审字[2020]006885号）符合公司实际情况，公司董事会对该审计报告予以理解和认可。公司已经收回上述关联方占用资金，该事项的影响已经消除，上述事项不会对公司2019年12月31日的合并及母公司财务状况以及2019年度合并及母公司的经营成果和现金流量造成重大影响。
回答: 根据厦门中创环保科技股份有限公司2019年的年报数据，公司在非标准审计报告方面提供了以下说明的详情：\n\n公司表示，大华会计师事务所（特殊普通合伙）严格按照审慎性原则进行审计，并为公司出具了带有强调事项段的无保留意见审计报告，报告编号为大华审字[2020]006885号。\n\n公司董事会认为这份审计报告符合公司的实际情况，对该审计报告表示理解和认可。\n\n公司已经收回了上述关联方占用的资金，并且明确说明该事项的影响已经消除。此外，公司还指出上述事项不会对公司截止到2019年12月31日的合并财务状况、母公司财务状况以及2019年度合并经营成果和现金流量产生重大影响。\n\n综合来看，根据公司的年报说明，大华会计师事务所在审计报告中强调了某些事项，但公司董事会认为这些事项已经得到解决，不会对公司的财务状况和经营成果造成重大影响。因此，公司董事会对该审计报告表示理解和认可，认为该审计报告符合实际情况。这表明公司已经采取措施解决了审计报告中涉及的问题，以维护财务透明度和合规性。

样例2
问题: 请具体描述一下2021年北信源非标准审计报告的说明。
检索内容: 本公司本年度无重大经营风险，不存在与非标准审计报告相关的内容。
回答: 根据提供的检索内容，2021年北信源公司的审计报告中并没有包含与非标准审计报告相关的内容。这意味着在该年度的审计中，没有发现任何与非标准审计事项有关的问题或说明。审计报告通常用于确认财务报表的准确性和合规性，而非标准审计报告可能涉及到公司财务报表之外的特殊审计或审计事项。在这种情况下，2021年的审计报告似乎没有包含与非标准审计相关的信息。

样例3
问题: 请具体描述一下2022年青瞿公司非标准审计报告的说明。
检索内容: 本公司本年度无重大经营风险，不存在与非标准审计报告相关的内容。
回答: 根据提供的检索内容，2022年青瞿公司的审计报告中并没有包含与非标准审计报告相关的内容。这意味着在该年度的审计中，没有发现任何与非标准审计事项有关的问题或说明。审计报告通常用于确认财务报表的准确性和合规性，而非标准审计报告可能涉及到公司财务报表之外的特殊审计或审计事项。在这种情况下，2021年的审计报告似乎没有包含与非标准审计相关的信息。

现在请回答：
问题: 请问在2021年南京大学公司在非标准审计报告的说明。
检索内容: 本公司本年度无重大经营风险，不存在与非标准审计报告相关的内容。
回答：

"""
history = [
    ['我会给你一个关于某公司年报问题和一个从该公司年报里检索的内容，请模仿前两个样例，根据给出的检索内容，排除问题无关的信息回答问题。如果遇到表格，请描述表格的内容，并简要进行分析总结，而不是直接回复表格内容。你的回答里只能基于检索内容回答，不能回答任何检索内容不存在的信息。',  '好的，我明白了，我会根据您检索的内容尽力进行回答，保证答案只来源于检索结果。']
]
# message = input("问：")
while message != "-1":
    print("\n\n答:")
    response = common_conversation(message[-8096:], history)
    print(response)
    message = input(f"[Round {n_round}]\n\n问:")
    n_round += 1
