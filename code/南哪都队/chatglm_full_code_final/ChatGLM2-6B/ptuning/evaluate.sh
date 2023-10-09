PRE_SEQ_LEN=128
CHECKPOINT=adgen-chatglm2-6b-pt-128-2e-2
STEP=3000
NUM_GPUS=1

torchrun --standalone --nnodes=1 --nproc-per-node=$NUM_GPUS main.py \
    --do_predict \
    --validation_file ../../finetune/table_qa/data/auto_annotated_dev.json \
    --test_file ../../finetune/table_qa/data/auto_annotated_dev.json \
    --overwrite_cache \
    --prompt_column prompt \
    --response_column response \
    --model_name_or_path ../../model/chatglm2-6b \
    --ptuning_checkpoint ../../model/classifier/checkpoint-3900 \
    --output_dir ../../model/classifier/ \
    --overwrite_output_dir \
    --max_source_length 512 \
    --max_target_length 128 \
    --per_device_eval_batch_size 32 \
    --predict_with_generate \
    --pre_seq_len $PRE_SEQ_LEN
