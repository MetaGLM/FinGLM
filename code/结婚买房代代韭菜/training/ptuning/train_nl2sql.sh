PRE_SEQ_LEN=256
LR=2e-2
NUM_GPUS=1

torchrun --standalone --nnodes=1 --nproc-per-node=$NUM_GPUS main.py \
    --do_train \
    --train_file data/nl2sql/train_v12.json \
    --validation_file data/nl2sql/valid_v12.json \
    --preprocessing_num_workers 10 \
    --prompt_column prompt \
    --response_column sql \
    --overwrite_cache \
    --model_name_or_path /model \
    --output_dir output/nl2sql-v32-chatglm2-6b-pt-$PRE_SEQ_LEN-$LR \
    --overwrite_output_dir \
    --max_source_length 512 \
    --max_target_length 256 \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --gradient_accumulation_steps 16 \
    --predict_with_generate \
    --max_steps 2850 \
    --logging_steps 50 \
    --save_steps 1425 \
    --learning_rate $LR \
    --pre_seq_len $PRE_SEQ_LEN \
