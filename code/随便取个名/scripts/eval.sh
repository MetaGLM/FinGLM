#!/bin/bash
echo "----------------RUNNING INFERENCE----------------"
CUDA_VISIBLE_DEVICES=2,3
gpu_num=$(echo $CUDA_VISIBLE_DEVICES | awk -F ',' '{print NF}')
echo $gpu_num $CUDA_VISIBLE_DEVICES

CUDA_VISIBLE_DEVICES=2,3 torchrun \
    --nnodes 1 \
    --nproc_per_node $gpu_num \
    --master_port 29500 \
     ./src/train_bash.py \
    --stage sft \
    --model_name_or_path THUDM/chatglm2-6b \
    --do_predict \
    --dataset SMP \
    --dataset_dir ./data \
    --output_dir output \
    --overwrite_cache \
    --max_source_length 1024 \
    --max_target_length 512 \
    --overwrite_cache true \
    --per_device_eval_batch_size 6 \
    --predict_with_generate \
    --remove_unused_columns false