PRE_SEQ_LEN=256
LR=2e-2
NUM_GPUS=1

torchrun --standalone --nnodes=1 --nproc-per-node=$NUM_GPUS main.py \
    --do_train \
    --train_file data/normalize/train_v3_real.json \
    --validation_file data/normalize/valid_v3_real.json \
    --preprocessing_num_workers 10 \
    --prompt_column prompt \
    --response_column answer \
    --overwrite_cache \
    --model_name_or_path /model \
    --output_dir output/normalize-v2-chatglm2-6b-pt-$PRE_SEQ_LEN-$LR \
    --overwrite_output_dir \
    --max_source_length 512 \
    --max_target_length 512 \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --gradient_accumulation_steps 16 \
    --predict_with_generate \
    --max_steps 1300 \
    --logging_steps 100 \
    --save_steps 650 \
    --learning_rate $LR \
    --pre_seq_len $PRE_SEQ_LEN \

