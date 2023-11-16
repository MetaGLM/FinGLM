from glmtuner.tuner import get_train_args, run_sft


def main():
    model_args, data_args, training_args, finetuning_args, general_args = get_train_args()

    import torch
    print(torch.cuda.get_device_name())
    if general_args.stage == "sft":
        run_sft(model_args, data_args, training_args, finetuning_args)

def _mp_fn(index):
    # For xla_spawn (TPUs)
    main()


if __name__ == "__main__":
    main()
