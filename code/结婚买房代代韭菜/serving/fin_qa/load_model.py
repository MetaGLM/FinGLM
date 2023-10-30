from .config import *
import os
import torch


def load_model_from_transformers(pre_seq_len, checkpoint_path):
    from transformers import AutoTokenizer, AutoModel, AutoConfig

    config = AutoConfig.from_pretrained(LLM_NAME, trust_remote_code=True, pre_seq_len=pre_seq_len)
    tokenizer = AutoTokenizer.from_pretrained(LLM_NAME, trust_remote_code=True)
    llm = AutoModel.from_pretrained(LLM_NAME, config=config, trust_remote_code=True, device='cuda')
    llm = llm.eval()

    if pre_seq_len != None:
        prefix_state_dict = torch.load(os.path.join(checkpoint_path, "pytorch_model.bin"))
        new_prefix_state_dict = {}
        for k, v in prefix_state_dict.items():
            if k.startswith("transformer.prefix_encoder."):
                new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
        llm.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
        llm.transformer.prefix_encoder.cuda()

    return llm, tokenizer

def ask_chatglm2_from_transformers(prompt, **kwargs):
    # print(prompt)
    res = llm.chat(tokenizer, prompt, **kwargs)[0]
    # print(res)
    return res

def reset_transformer_chatglm2(pre_seq_len, checkpoint_path):
    global llm, tokenizer
    del llm, tokenizer
    llm, tokenizer = load_model_from_transformers(pre_seq_len=pre_seq_len, checkpoint_path=checkpoint_path)

global llm, tokenizer

llm, tokenizer = load_model_from_transformers(pre_seq_len=ROUTER_PRE_SEQ_LEN, checkpoint_path=ROUTER_CHECKPOINT_PATH)
ask_chatglm2 = ask_chatglm2_from_transformers
