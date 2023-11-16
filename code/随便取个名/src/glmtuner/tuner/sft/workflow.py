# Inspired by: https://github.com/THUDM/ChatGLM-6B/blob/main/ptuning/main.py

from typing import Optional, List
from transformers import Seq2SeqTrainingArguments, TrainerCallback

from glmtuner.dsets import DataCollatorForChatGLM, get_dataset, preprocess_dataset, split_dataset
from glmtuner.extras.callbacks import LogCallback
from glmtuner.extras.misc import get_logits_processor
from glmtuner.hparams import ModelArguments, DataArguments, FinetuningArguments
from glmtuner.tuner.core import load_model_and_tokenizer
from glmtuner.tuner.sft.trainer import Seq2SeqTrainerForChatGLM


def run_sft(
    model_args: ModelArguments,
    data_args: DataArguments,
    training_args: Seq2SeqTrainingArguments,
    finetuning_args: FinetuningArguments,
    callbacks: Optional[List[TrainerCallback]] = [LogCallback()]
):
    dataset = get_dataset(model_args, data_args)
    model, tokenizer = load_model_and_tokenizer(model_args, finetuning_args, training_args.do_train, stage="sft")
    dataset = preprocess_dataset(dataset, tokenizer, data_args, training_args, stage="sft")
    data_collator = DataCollatorForChatGLM(
        tokenizer=tokenizer,
        model=model,
        ignore_pad_token_for_loss=(data_args.ignore_pad_token_for_loss and not training_args.predict_with_generate)
    )

    # Override the decoding parameters of Seq2SeqTrainer
    training_args.generation_max_length = training_args.generation_max_length if \
                training_args.generation_max_length is not None else data_args.max_target_length
    training_args.generation_num_beams = data_args.eval_num_beams if \
                data_args.eval_num_beams is not None else training_args.generation_num_beams

    # Initialize our Trainer
    trainer = Seq2SeqTrainerForChatGLM(
        finetuning_args=finetuning_args,
        model=model,
        args=training_args,
        tokenizer=tokenizer,
        data_collator=data_collator,
        callbacks=callbacks,
        **split_dataset(dataset, data_args.dev_ratio, training_args.do_train)
    )

    # Keyword arguments for `model.generate`
    gen_kwargs = {
        "do_sample": True,
        "top_p": data_args.top_p,
        "max_new_tokens": data_args.max_target_length + 1,
        "temperature": data_args.temperature,
        "logits_processor": get_logits_processor()
    }

    # Training
    if training_args.do_train:
        train_result = trainer.train()
        trainer.save_state()
        trainer.save_model()
       

    # Predict
    if training_args.do_predict:
        predict_results = trainer.predict(dataset, metric_key_prefix="predict", **gen_kwargs)
        trainer.save_predictions(predict_results)
