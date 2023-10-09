PRE_SEQ_LEN=256
CHECKPOINT=Fin-Train-chatglm2-6b-pt-$PRE_SEQ_LEN-2e-2
STEP=250
NUM_GPUS=1
CUDA_VISIBLE_DEVICES=1 torchrun --standalone --nnodes=1 --nproc-per-node=$NUM_GPUS main.py \
    --do_predict \
    --validation_file Fin_train/dev.json \
    --test_file Fin_train/dev.json \
    --overwrite_cache \
    --prompt_column question_prompt \
    --response_column query \
    --model_name_or_path /home/jamepeng/git_projects/chatglm2-6b-model \
    --ptuning_checkpoint ./output/JamePeng_Keywords/$CHECKPOINT/checkpoint-$STEP \
    --output_dir ./output/JamePeng_Keywords/$CHECKPOINT \
    --overwrite_output_dir \
    --max_source_length 256 \
    --max_target_length 128 \
    --per_device_eval_batch_size 1 \
    --predict_with_generate \
    --pre_seq_len $PRE_SEQ_LEN \
