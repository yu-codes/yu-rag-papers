"""
TinyLlama LoRA fine-tune scaffold
=================================
用法：
    python -m rag.fine_tune \
        --train_file data/fine_tune_sample.jsonl \
        --output_dir rag/lora_adapter

輸入格式 (jsonl)：
{"prompt": "問題...", "completion": "答案..."}
"""

import argparse, os, json, torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
)

BASE_MODEL = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"  # ggml/gguf 也 OK
DEFAULT_OUT = "rag/lora_adapter"


def make_dataset(path: str):
    ds = load_dataset("json", data_files=path, split="train")

    def _format(example):
        return {
            "input_ids": tokenizer(
                f"<s>[INST] {example['prompt']} [/INST] {example['completion']}</s>",
                return_tensors="pt",
            ).input_ids[0]
        }

    ds = ds.map(_format, remove_columns=ds.column_names)
    return ds


def main(args):
    global tokenizer
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        load_in_4bit=True,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model = prepare_model_for_kbit_training(model)

    lora_cfg = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        bias="none",
        lora_dropout=0.1,
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_cfg)

    ds = make_dataset(args.train_file)

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=4,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=10,
        save_steps=200,
    )

    trainer = Trainer(model=model, args=training_args, train_dataset=ds)
    trainer.train()

    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--train_file",
        default="data/fine_tune_sample.jsonl",
        help="jsonl 訓練檔，每行 prompt/completion",
    )
    p.add_argument(
        "--output_dir",
        default=DEFAULT_OUT,
        help="LoRA adapter 輸出資料夾",
    )
    main(p.parse_args())
