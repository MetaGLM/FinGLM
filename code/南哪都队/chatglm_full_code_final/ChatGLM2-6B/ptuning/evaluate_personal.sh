PRE_SEQ_LEN=128
NUM_GPUS=1

torchrun --standalone --nnodes=1 --nproc-per-node=$NUM_GPUS main.py \
    --do_predict \
    --validation_file ../../finetune/table_qa/data/personal_information_augmentation_dev.json \
    --test_file ../../finetune/table_qa/data/personal_information_augmentation_dev.json \
    --overwrite_cache \
    --prompt_column prompt \
    --response_column response \
    --model_name_or_path ../../model/chatglm2-6b \
    --ptuning_checkpoint ../../model/table_qa/personal/checkpoint-1500 \
    --output_dir ../../model/table_qa/personal \
    --overwrite_output_dir \
    --max_source_length 768 \
    --max_target_length 128 \
    --per_device_eval_batch_size 32 \
    --predict_with_generate \
    --pre_seq_len $PRE_SEQ_LEN
