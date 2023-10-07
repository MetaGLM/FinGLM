PRE_SEQ_LEN=128
LR=2e-2
NUM_GPUS=1

torchrun --standalone --nnodes=1 --nproc-per-node=$NUM_GPUS main.py \
    --do_train \
    --train_file 'train_data/nl2sql_train_data.json' \
    --validation_file 'train_data/nl2sql_train_data.json' \
    --preprocessing_num_workers 10 \
    --prompt_column question \
    --response_column answer \
    --overwrite_cache \
    --model_name_or_path /tcdata/chatglm2-6b \
    --output_dir output/my-chatglm2-6b-pt-$PRE_SEQ_LEN-$LR \
    --overwrite_output_dir \
    --max_source_length 2200 \
    --max_target_length 300 \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --gradient_accumulation_steps 16 \
    --predict_with_generate \
    --max_steps 600 \
    --logging_steps 10 \
    --save_steps 100 \
    --learning_rate $LR \
    --pre_seq_len $PRE_SEQ_LEN \
    --quantization_bit 8

