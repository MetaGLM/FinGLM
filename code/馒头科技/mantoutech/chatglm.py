import os
from abc import ABC
from typing import Optional, List
from loguru import logger
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from transformers import (AutoConfig, AutoModel, AutoModelForCausalLM,
                          AutoTokenizer, LlamaTokenizer)
import sentencepiece

from config import cfg

if not cfg.ONLINE:
    from fastllm_pytools import llm


class ChatGLM(LLM, ABC):
    if cfg.ONLINE:
        model_name = '/tcdata/chatglm2-6b-hug'
    else:
        model_name = 'THUDM/chatglm2-6b'
    model_path = os.path.join(cfg.DATA_PATH, 'model.flm')
    # model_path = '/app/model.flm'
    # model_name = 'THUDM/chatglm2-6b-32k'
    # model_name = 'THUDM/chatglm2-6b-int4'
    tokenizer : AutoTokenizer = None
    model : AutoModel = None
    # max_token: int = 10000
    # temperature: float = 0.001
    # top_p = 0.9
    # history = []
    # history_len: int = 10

    def __init__(self, *model_args, **kwargs):
        super().__init__()

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
        if cfg.ONLINE:
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name, trust_remote_code=True).cuda().eval()
        else:
            if os.path.exists(self.model_path):
                logger.info('Load model from {}...'.format(self.model_path))
                self.model = llm.model(self.model_path)
            else:
                logger.info('Fast llm model does not exists, do convert...')
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
                hf_model = AutoModel.from_pretrained(self.model_name, trust_remote_code=True).cuda()
                self.model = llm.from_hf(hf_model, self.tokenizer, dtype='float16')
                self.model.save(self.model_path)
                logger.info('Convert to llm model ok!')

    @property
    def _llm_type(self) -> str:
        return "ChatGLM"

    @property
    def _history_len(self) -> int:
        return self.history_len

    def set_history_len(self, history_len: int = 10) -> None:
        self.history_len = history_len

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        # print(f"__call:{prompt}")
        if len(prompt) > 5120:
            print('Cut prompt len {} to 5120 as too long!'.format(len(prompt)))
            prompt = prompt[:5120]
        try:
            response, _ = self.model.chat(
                self.tokenizer,
                prompt,
                history=[],
                max_length=5120,
                top_p=1, do_sample=False,
                temperature=0.001)
        except Exception as e:
            print(e)
            response = ''
        # response = self.model.response(prompt, history=[],
            # max_length=6144, do_sample=False, top_p=1, temperature=0.001)
        # print(f"response:{response}")
        # print(f"+++++++++++++++++++++++++++++++++++")
        return response
    

if __name__ == '__main__':
    model = ChatGLM()
    print(model('你好'))