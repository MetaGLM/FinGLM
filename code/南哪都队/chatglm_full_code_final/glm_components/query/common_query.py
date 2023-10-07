from .base_query import base_query
from transformers import AutoConfig, AutoModel
from tqdm import tqdm
from .document_retrieval.commonsense_retrieval import retrieve
import json

class common_query(base_query):
    def __init__(self, model, tokenizer, excels):
        super(common_query, self).__init__(model, tokenizer, excels)
    
    def switch_prefix_encoder(self):
        model_path = "model/chatglm2-6b"
        self.model = AutoModel.from_pretrained(model_path, trust_remote_code=True).half()
        self.model = self.model.to("cuda")
        return self.model
    
    def _run_query(self, questions, retrieved_infos, batch_size=1):
        """
        构建prompt，运行模型推理，构成batch之后再推理，不然速度太慢
        """
        prompt = "[Round 1]\n\n问：以下是一个财务报表编制相关的问题，请你尽可能详细且准确地回答下面的问题:{}\n\n答："
        assert len(questions) == len(retrieved_infos)
        result_placeholder = [None for _ in range(len(questions))]
        batch_questions = []
        batch_data = []
        batch_indexes = []
        for idx, (question, retrieved_info) in enumerate(tqdm(zip(questions, retrieved_infos), total=len(questions), desc="常识")):
            if isinstance(retrieved_info, dict) and '类型' in retrieved_info and retrieved_info['类型'] == '常识问题':
                # document = retrieve(question)
                model_input_string = prompt.format(question)
                batch_data.append(model_input_string)
                batch_indexes.append(idx)
                batch_questions.append(question)
            if len(batch_data) == batch_size or  (idx == len(questions) - 1 and len(batch_data) > 0):
                batch_results = self.predict_batch(batch_data)
                for batch_result, batch_question, batch_index in zip(batch_results, batch_questions, batch_indexes):
                    result_placeholder[batch_index] = {
                        "id": batch_index,
                        "question": batch_question,
                        "answer": batch_result
                    }
                    # print(json.dumps(result_placeholder[batch_index] | {'document': document}, ensure_ascii=False, indent=4))
                batch_data = []
                batch_indexes = []
                batch_questions = []
        return result_placeholder
    
    def predict_batch(self, batch_inputs):
        inputs = self.tokenizer(batch_inputs, return_tensors="pt", max_length=8096, truncation=True, padding=True)
        inputs = inputs.to("cuda")
        outputs = self.model.generate(**inputs, max_new_tokens=2048, do_sample=True, temperature=0.95)
        response = self.tokenizer.batch_decode(outputs)
        response = [res[res.index("答：")+2:].strip() for res in response]
        return response


    def prefix_checkpoint_path(self) -> str:
        """
        实现时直接返回prefixtuning的checkpoint路径
        """
        return None