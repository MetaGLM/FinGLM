import os
import json
import torch
import numpy as np
import torch.nn as nn
from typing import Any, Dict, List, Optional, Tuple, Union
from transformers.trainer import PredictionOutput

from glmtuner.extras.constants import IGNORE_INDEX
from glmtuner.extras.logging import get_logger
from glmtuner.tuner.core.trainer import PeftTrainer

logger = get_logger(__name__)


class Seq2SeqTrainerForChatGLM(PeftTrainer):
    r"""
    Inherits PeftTrainer to compute generative metrics such as BLEU and ROUGE.
    """

    def prediction_step(
        self,
        model: nn.Module,
        inputs: Dict[str, Union[torch.Tensor, Any]],
        prediction_loss_only: bool,
        ignore_keys: Optional[List[str]] = None,
    ) -> Tuple[Optional[float], Optional[torch.Tensor], Optional[torch.Tensor]]:
        r"""
        Removes the prompt part in the generated tokens.

        Subclass and override to inject custom behavior.
        """
        input_ids = inputs["input_ids"]
        loss, generated_tokens, labels = super().prediction_step(
            model, inputs, prediction_loss_only=prediction_loss_only, ignore_keys=ignore_keys
        )
        generated_tokens = generated_tokens[:, input_ids.size(-1):] if generated_tokens is not None else None
        return (loss, generated_tokens, labels)

    def save_predictions(
        self,
        predict_results: PredictionOutput
    ) -> None:
        r"""
        Saves model predictions to `output_dir`.

        A custom behavior that not contained in Seq2SeqTrainer.
        """
        if not self.is_world_process_zero():
            return

        output_prediction_file = os.path.join(self.args.output_dir, "generated_predictions.json")
        logger.info(f"Saving prediction results to {output_prediction_file}")

        preds = np.where(predict_results.predictions != IGNORE_INDEX, predict_results.predictions, self.tokenizer.pad_token_id)
        labels = np.where(predict_results.label_ids != IGNORE_INDEX, predict_results.label_ids, self.tokenizer.pad_token_id)

        decoded_preds = self.tokenizer.batch_decode(preds, skip_special_tokens=True)
        decoded_labels = self.tokenizer.batch_decode(labels, skip_special_tokens=True)

        res = []
        with open('data/list-question.json', 'r', encoding='utf-8') as f:
            for line, pred in zip(f.readlines(), decoded_preds):
                sample = json.loads(line)
                sample['answer'] = pred
                res.append(json.dumps(sample, ensure_ascii=False))
                        
        with open(output_prediction_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(res))