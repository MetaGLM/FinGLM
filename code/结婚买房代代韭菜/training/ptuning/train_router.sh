PRE_SEQ_LEN=16
LR=2e-2
NUM_GPUS=1

torchrun --standalone --nnodes=1 --nproc-per-node=$NUM_GPUS main.py \
    --do_train \
    --train_file data/router/train_v4_real.json \
    --validation_file data/router/valid_v4_real.json \
    --preprocessing_num_workers 10 \
    --prompt_column query \
    --response_column type \
    --overwrite_cache \
    --model_name_or_path /model \
    --output_dir output/router-v3-chatglm2-6b-pt-$PRE_SEQ_LEN-$LR \
    --overwrite_output_dir \
    --max_source_length 128 \
    --max_target_length 16 \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --gradient_accumulation_steps 16 \
    --predict_with_generate \
    --max_steps 4800 \
    --logging_steps 200 \
    --save_steps 1200 \
    --learning_rate $LR \
    --pre_seq_len $PRE_SEQ_LEN \

