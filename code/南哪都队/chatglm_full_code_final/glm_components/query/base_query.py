from abc import abstractclassmethod
# from types import List
import torch
import os
from transformers import AutoModel, AutoConfig


class base_query:
    def __init__(self, model, tokenizer, excels) -> None:
        """
        model:GLM模型
        excels:字典，key为(stock_code,year), 值的格式见data/merged_excels
        """
        self.model = model
        self.tokenizer = tokenizer
        self.excels = excels

    
    @property
    @abstractclassmethod
    def prefix_checkpoint_path(self) -> str:
        """
        实现时直接返回prefixtuning的checkpoint路径
        """
        pass

    
    
    def run_query(self, questions, retrieved_infos, batch_size=32, **kwargs):
        """
        questions:问题字符串列表
        retrieved_infos:字典列表，格式见finetune/table_qa/data/classification.jsonl，
        多了一个字段：股票代码，方便唯一索引
        需要自己判断问题类型，如果不是这个query的目标类型，则返回list的对应位置为None
        """
        self.switch_prefix_encoder()
        if self.model is not None:
            self.model.eval()
        with torch.no_grad():
            return self._run_query(questions, retrieved_infos, batch_size, **kwargs)
    

    @abstractclassmethod
    def _run_query(self, questions, retrieved_infos, batch_size=32):
        """
        构建prompt，运行模型推理，构成batch之后再推理，不然速度太慢
        """
        pass


    def switch_prefix_encoder(self):
        if self.prefix_checkpoint_path:
            prefix_state_dict = torch.load(os.path.join(self.prefix_checkpoint_path, "pytorch_model.bin"))
            new_prefix_state_dict = {}
            for k, v in prefix_state_dict.items():
                if k.startswith("transformer.prefix_encoder."):
                    new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
            self.model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
            self.tokenizer.padding_side = 'left'
            self.model = self.model.half()
            self.model = self.model.to("cuda")
        # else:
        #     model_path = "model/chatglm2-6b"
        #     config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
        #     config.prefix_projection = False
        #     config.pre_seq_len = 128
        #     self.model = AutoModel.from_pretrained(model_path, config=config, trust_remote_code=True)
        return self.model