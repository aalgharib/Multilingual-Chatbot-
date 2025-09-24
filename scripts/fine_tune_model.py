"""Utility script to fine-tune causal language models with Hugging Face Transformers."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
    set_seed,
)

LOGGER = logging.getLogger(__name__)
DEFAULT_DATA_PATH = Path("data/multilingual_chat_dataset.jsonl")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-name-or-path",
        default="distilgpt2",
        help="Base model to fine-tune. Any causal LM from Hugging Face Hub is supported.",
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="Path to a JSONL file with a 'text' column containing chat transcripts.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("models/fine_tuned"),
        help="Directory where the fine-tuned model and tokenizer will be saved.",
    )
    parser.add_argument("--epochs", type=float, default=3.0, help="Number of training epochs.")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size per device.")
    parser.add_argument(
        "--max-length",
        type=int,
        default=256,
        help="Maximum number of tokens per training example after tokenisation.",
    )
    parser.add_argument(
        "--eval-split",
        type=float,
        default=0.1,
        help="Fraction of the dataset reserved for evaluation. Set to 0 to disable validation.",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for dataset shuffling and training reproducibility."
    )
    return parser.parse_args()


def tokenise_dataset(dataset_path: Path, tokenizer, max_length: int, eval_split: float, seed: int):
    LOGGER.info("Loading dataset from %s", dataset_path)
    raw_dataset = load_dataset("json", data_files=str(dataset_path))
    dataset = raw_dataset["train"]

    def preprocess(batch):
        tokenised = tokenizer(
            batch["text"],
            truncation=True,
            padding="max_length",
            max_length=max_length,
        )
        tokenised["labels"] = tokenised["input_ids"].copy()
        return tokenised

    tokenised_dataset = dataset.map(preprocess, batched=True, remove_columns=dataset.column_names)

    if eval_split:
        split_dataset = tokenised_dataset.train_test_split(test_size=eval_split, seed=seed)
        return split_dataset["train"], split_dataset["test"]
    return tokenised_dataset, None


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO)
    set_seed(args.seed)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    train_dataset, eval_dataset = tokenise_dataset(
        args.dataset_path, tokenizer, args.max_length, args.eval_split, args.seed
    )

    model = AutoModelForCausalLM.from_pretrained(args.model_name_or_path)
    if getattr(model.config, "pad_token_id", None) is None:
        model.config.pad_token_id = tokenizer.pad_token_id

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        overwrite_output_dir=True,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=1,
        evaluation_strategy="steps" if eval_dataset is not None else "no",
        eval_steps=50 if eval_dataset is not None else None,
        save_steps=200,
        logging_steps=10,
        save_total_limit=2,
        warmup_steps=10,
        weight_decay=0.01,
        fp16=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    LOGGER.info("Starting fine-tuning on %s examples", len(train_dataset))
    trainer.train()

    LOGGER.info("Saving fine-tuned model to %s", args.output_dir)
    trainer.save_model()
    tokenizer.save_pretrained(args.output_dir)

    LOGGER.info("Fine-tuning completed.")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
