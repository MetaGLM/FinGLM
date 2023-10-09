PRE_SEQ_LEN=512
LR=2e-2
RUNNING_STEP=400
NUM_GPUS=1
CUDA_VISIBLE_DEVICES=1 torchrun --standalone --nnodes=1 --nproc-per-node=$NUM_GPUS main.py \
    --do_train \
    --train_file Fin_train/train.json \
    --validation_file Fin_train/dev.json \
    --preprocessing_num_workers 10 \
    --prompt_column question_prompt \
    --response_column query \
    --overwrite_cache \
    --model_name_or_path /home/jamepeng/git_projects/chatglm2-6b-model \
    --output_dir output/JamePeng_Ptuning_Classify/Fin-Train-chatglm2-6b-pt-$PRE_SEQ_LEN-$LR \
    --overwrite_output_dir \
    --max_source_length 512 \
    --max_target_length 128 \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --gradient_accumulation_steps 16 \
    --predict_with_generate \
    --max_steps $RUNNING_STEP \
    --logging_steps 2 \
    --save_steps $RUNNING_STEP \
    --learning_rate $LR \
    --pre_seq_len $PRE_SEQ_LEN \

