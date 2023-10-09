
LR=1e-4

MASTER_PORT=$(shuf -n 1 -i 10000-65535)

deepspeed --num_gpus=2 --master_port $MASTER_PORT main.py \
    --deepspeed deepspeed.json \
    --do_train \
    --train_file ../../data/temp/entity_extraction_train.json \
    --test_file ../../data/temp/entity_extraction_dev.json \
    --prompt_column prompt \
    --response_column response \
    --overwrite_cache \
    --model_name_or_path ../../model/chatglm2-6b \
    --output_dir ../../model/entity_extraction \
    --overwrite_output_dir \
    --max_source_length 64 \
    --max_target_length 64 \
    --per_device_train_batch_size 4 \
    --per_device_eval_batch_size 1 \
    --gradient_accumulation_steps 1 \
    --predict_with_generate \
    --max_steps 5000 \
    --logging_steps 10 \
    --save_steps 1000 \
    --learning_rate $LR \
    --fp16

