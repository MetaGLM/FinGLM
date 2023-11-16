# build_instruction_dataset work with usual format 
export CUDA_VISIBLE_DEVICES='0, 1'
export WANDB_LOG_MODEL=true
# export WANDB_MODE=disabled
gpu_num=$(echo $CUDA_VISIBLE_DEVICES | awk -F ',' '{print NF}')
echo $gpu_num $CUDA_VISIBLE_DEVICES

data_path=data  # dataset folder
output_path=model  # output folder
model_path='/home/lzw/.cache/huggingface/hub/models--THUDM--chatglm2-6b/snapshots/b1502f4f75c71499a3d566b14463edd62620ce9f'
peft_path=""  # 如果之前训练过，且存储了peft权重，则设置为peft权重的文件夹路径

# experiment setting


lora_rank=8
lora_trainable="query_key_value,dense,dense_h_to_4h,dense_4h_to_h"
modules_to_save="null"
lora_dropout=0.1

LR=2e-4

# torchrun \
#     --nnodes 1 \
#     --nproc_per_node $gpu_num \
#     --master_port 29500 \
python src/main.py \
    --do_train \
    --train_file $data_path/dataset.json \
    --prompt_column question \
    --response_column task_key \
    --overwrite_cache \
    --model_name_or_path $model_path \
    --output_dir $output_path \
    --overwrite_output_dir \
    --max_source_length 128 \
    --max_target_length 28 \
    --per_device_train_batch_size 8 \
    --per_device_eval_batch_size 8 \
    --gradient_accumulation_steps 4 \
    --max_steps 10000 \
    --logging_steps 100 \
    --save_steps 1000 \
    --lr_scheduler_type constant \
    --save_total_limit 3 \
    --learning_rate $LR \
    --lora_rank ${lora_rank} \
    --trainable ${lora_trainable} \
    --modules_to_save ${modules_to_save} \
    --lora_dropout ${lora_dropout}
    # --run_name  \
    # --report_to wandb
    # --lr_scheduler_type constant \
    # --do_eval \
    # --validation_file $data_path/dev.json \
    # --evaluation_strategy steps \
    # --eval_steps 500 \

    # --fp16 \
    # --deepspeed ${deepspeed_config_file} \