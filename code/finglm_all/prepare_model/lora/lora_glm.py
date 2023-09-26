'''使用lora微调大模型
代码使用 PEFT（Progressive Embedding Fine-Tuning）方法和 LoRA（Low-Rank Adaptation）技术对预训练的 ChatGLM-6B 模型进行高效的微调。以下是详细的代码分块总结：

环境准备
数据准备
导入所需的库和模块
自定义函数
参数设置
加载分词器和数据集
初始化 SummaryWriter
加载和配置预训练模型
使用 Lora 设置 PEFT 微调
创建训练器
开始训练模型
关闭 SummaryWriter
保存模型
备注：PEFT（Progressive Embedding Fine-Tuning）方法，将语言模型的嵌入层进行降维处理，从而减少计算资源需求。'''

import os
import torch
import torch.nn as nn
import datasets
from dataclasses import dataclass, field
from transformers import AutoModel, AutoTokenizer
from transformers import Trainer, TrainingArguments, HfArgumentParser
from transformers.integrations import TensorBoardCallback
from transformers.trainer import TRAINING_ARGS_NAME
from torch.utils.tensorboard import SummaryWriter
from peft import get_peft_model, LoraConfig, TaskType

# 自定义一个数据类，用于解析微调参数
@dataclass
class FinetuneArguments:
    dataset_path: str = field(default="data/test")
    model_path: str = field(default="output")
    lora_rank: int = field(default=8)

# 将模型输出转换为浮点数
class CastOutputToFloat(nn.Sequential):
    def forward(self, x):
        return super().forward(x).to(torch.float32)


# 获取 attention masks 和 position ids
def get_masks_and_position_ids(
    seq, seq_len, context_length, device, gmask=False, position_encoding_2d=True
):
    mask_position = (
        seq_len - 2
    )
    attention_mask = torch.ones((1, context_length, context_length), device=device)
    attention_mask.tril_()
    attention_mask[..., : mask_position - 1] = 1
    attention_mask = (attention_mask < 0.5).bool()

    if position_encoding_2d:
        seq_length = seq_len - 1
        position_ids = torch.arange(context_length, dtype=torch.long, device=device)
        if not gmask:
            position_ids[seq_length:] = mask_position
        block_position_ids = torch.cat(
            (
                torch.zeros(seq_length, dtype=torch.long, device=device),
                torch.arange(
                    context_length - seq_length, dtype=torch.long, device=device
                )
                + 1,
            )
        )
        position_ids = torch.stack((position_ids, block_position_ids), dim=0)
    else:
        position_ids = torch.arange(context_length, dtype=torch.long, device=device)
        if not gmask:
            position_ids[context_length - 1 :] = mask_position
    return attention_mask, position_ids

# 整理输入特征以供模型使用
def data_collator(features: list) -> dict:
    len_ids = [len(feature["input_ids"]) for feature in features]
    longest = max(len_ids)
    input_ids = []
    attention_mask_list = []
    position_ids_list = []
    labels_list = []
    for ids_l, feature in sorted(zip(len_ids, features), key=lambda x: -x[0]):
        ids = feature["input_ids"]
        seq_len = feature["seq_len"]
        labels = (
            [-100] * (seq_len - 1)
            + ids[(seq_len - 1) :]
            + [-100] * (longest - ids_l)
        )
        ids = ids + [tokenizer.pad_token_id] * (longest - ids_l)
        _ids = torch.LongTensor(ids)
        attention_mask, position_ids = get_masks_and_position_ids(
            ids, seq_len, longest, _ids.device, gmask=False
        )
        labels_list.append(torch.LongTensor(labels))
        input_ids.append(_ids)
        attention_mask_list.append(attention_mask)
        position_ids_list.append(position_ids)
    input_ids = torch.stack(input_ids)
    labels = torch.stack(labels_list)
    attention_mask = torch.stack(attention_mask_list)
    position_ids = torch.stack(position_ids_list)
    return {
        "input_ids": input_ids,
        "labels": labels,
        "attention_mask": attention_mask,
        "position_ids": position_ids,
    }
# 重写原始 Trainer 类的 compute_loss 和 save_model 方法

class ModifiedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        return model(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            position_ids=inputs["position_ids"],
            labels=inputs["labels"],
        ).loss

    def save_model(self, output_dir=None, _internal_call=False):

        os.makedirs(output_dir, exist_ok=True)
        torch.save(self.args, os.path.join(output_dir, TRAINING_ARGS_NAME))
        saved_params = {
            k: v.to("cpu") for k, v in self.model.named_parameters() if v.requires_grad
        }
        torch.save(saved_params, os.path.join(output_dir, "adapter_model.bin"))

# 参数设置
training_args = TrainingArguments(
    "output",
    fp16 =True,
    gradient_accumulation_steps=1,
    per_device_train_batch_size = 2,
    learning_rate = 1e-4,
    max_steps=3000,
    logging_steps=100,
    remove_unused_columns=False,
    seed=0,
    data_seed=0,
    group_by_length=False,
    save_steps=100,
    save_total_limit=20,
)
tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm-6b", trust_remote_code=True)
dataset = datasets.load_from_disk('data/test')

writer = SummaryWriter()
model = AutoModel.from_pretrained(
    "THUDM/chatglm-6b", load_in_8bit=True, trust_remote_code=True, device_map="auto"
)

model.gradient_checkpointing_enable()
model.enable_input_require_grads()
model.is_parallelizable = True
model.model_parallel = True
model.lm_head = CastOutputToFloat(model.lm_head)
model.config.use_cache = (
    False  # silence the warnings. Please re-enable for inference!
)

peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    inference_mode=False,
    r=8,
    lora_alpha=32,
    lora_dropout=0.1,
)
model = get_peft_model(model, peft_config)

trainer = ModifiedTrainer(
    model=model,
    train_dataset=dataset,
    args=training_args,
    callbacks=[TensorBoardCallback(writer)],
    data_collator=data_collator,
)

trainer.train()
writer.close()
model.save_pretrained('output')
