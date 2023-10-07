PRE_SEQ_LEN=128
LR=1e-2
NUM_GPUS=4

torchrun --standalone --nnodes=1 --nproc-per-node=$NUM_GPUS main.py \
    --do_train \
    --train_file ../../finetune/table_qa/data/auto_annotated_train.json \
    --validation_file ../../finetune/table_qa/data/auto_annotated_dev.json \
    --preprocessing_num_workers 10 \
    --prompt_column prompt \
    --response_column response \
    --overwrite_cache \
    --model_name_or_path ../../model/chatglm2-6b \
    --output_dir ../../model/classifier \
    --overwrite_output_dir \
    --max_source_length 128 \
    --max_target_length 512 \
    --per_device_train_batch_size 8 \
    --per_device_eval_batch_size 32 \
    --gradient_accumulation_steps 1 \
    --predict_with_generate \
    --max_steps 4500 \
    --logging_steps 10 \
    --save_steps 150 \
    --learning_rate $LR \
    --pre_seq_len $PRE_SEQ_LEN 

