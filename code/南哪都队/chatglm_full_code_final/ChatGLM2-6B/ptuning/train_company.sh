PRE_SEQ_LEN=128
LR=1e-2
NUM_GPUS=1

torchrun --standalone --nnodes=1 --nproc-per-node=$NUM_GPUS main.py \
    --do_train \
    --train_file /home/zy/other/fintech/finetune/table_qa/data/company_info_train.json \
    --validation_file /home/zy/other/fintech/finetune/table_qa/data/company_info_train.json \
    --preprocessing_num_workers 10 \
    --prompt_column prompt \
    --response_column response \
    --overwrite_cache \
    --model_name_or_path ../../model/chatglm2-6b \
    --output_dir ../../model/table_qa/company_info \
    --overwrite_output_dir \
    --max_source_length 512 \
    --max_target_length 128 \
    --per_device_train_batch_size 32 \
    --per_device_eval_batch_size 64 \
    --gradient_accumulation_steps 1 \
    --predict_with_generate \
    --max_steps 1500 \
    --logging_steps 4 \
    --save_steps 50 \
    --learning_rate $LR \
    --pre_seq_len $PRE_SEQ_LEN 
