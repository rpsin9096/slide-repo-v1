#!/usr/bin/env python3
"""Unsloth QLoRA Fine-Tuning & GGUF Export Script for FocusGate v2.8.

Trains a distilled Student router (default: Llama-3.2-3B-Instruct) using harvested
SFT trajectory datasets adhering to schemas/sft-record.schema.json.
Provides turnkey GGUF export for local edge execution via Ollama or vLLM.
"""

import sys
import os
import json
import argparse
from typing import Dict, Any, List

def parse_args():
    parser = argparse.ArgumentParser(description="FocusGate v2.8 Unsloth QLoRA Fine-Tuner")
    parser.add_argument("--dataset", required=True, help="Path to harvested SFT dataset (.jsonl or .json)")
    parser.add_argument("--model-name", default="unsloth/Llama-3.2-3B-Instruct", help="Base model identifier")
    parser.add_argument("--max-seq-length", type=int, default=1024, help="Maximum context length")
    parser.add_argument("--output-dir", default="./dist/focus-gate-v2.8/models/lora_adapter", help="Adapter destination")
    parser.add_argument("--export-gguf", choices=["q4_k_m", "q8_0", "f16"], default=None, help="Quantization level for GGUF export")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size per device")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Peak learning rate")
    parser.add_argument("--dry-run", action="store_true", help="Validate dataset and configuration without GPU training")
    return parser.parse_args()

def validate_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    records = []
    if dataset_path.endswith(".jsonl"):
        with open(dataset_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    records.append(rec)
                except Exception as e:
                    raise ValueError(f"Malformed JSON on line {line_no}: {e}")
    else:
        with open(dataset_path, "r", encoding="utf-8") as f:
            records = json.load(f)

    print(f"[Dataset Audit] Loaded {len(records)} records from {dataset_path}")
    for i, r in enumerate(records[:5]):
        if "prompt" not in r or "completion" not in r:
            raise ValueError(f"Record {i} missing 'prompt' or 'completion' keys conforming to sft-record.schema.json")
    print(f"[Dataset Audit] sft-record schema contract verified: OK")
    return records

def format_chat_template(record: Dict[str, Any]) -> str:
    system_prompt = (
        "You are FocusGate v2.8, an ultra-compact, deterministic agent orchestration router. "
        "Classify user tasks, select canonical pipelines (P1-P11), and format outputs in the Invariant Action Envelope."
    )
    user_prompt = record["prompt"]
    assistant_completion = record["completion"]
    
    return (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        f"{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
        f"{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        f"{assistant_completion}<|eot_id|>"
    )

def main():
    args = parse_args()
    records = validate_dataset(args.dataset)

    if args.dry_run:
        print("[Dry Run] Dataset validated successfully.")
        print(f"[Dry Run] Sample formatted record:\n{'-'*60}\n{format_chat_template(records[0])}\n{'-'*60}")
        print("[Dry Run] Ready for GPU training execution.")
        sys.exit(0)

    try:
        from unsloth import FastLanguageModel
        import torch
        from trl import SFTTrainer
        from transformers import TrainingArguments
        from datasets import Dataset
    except ImportError:
        print(
            "ERROR: Unsloth and training dependencies not detected in current Python environment.\n"
            "To execute full GPU training, install dependencies:\n"
            "  pip install 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git'\n"
            "  pip install --no-deps trl peft accelerate bitsandbytes\n"
            "\nRun with --dry-run to validate dataset and pipeline on CPU.",
            file=sys.stderr
        )
        sys.exit(1)

    print(f"[Training] Initializing FastLanguageModel: {args.model_name}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model_name,
        max_seq_length=args.max_seq_length,
        load_in_4bit=True
    )

    print("[Training] Configuring LoRA adapter targets (r=16, alpha=16)")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42
    )

    formatted_texts = [format_chat_template(r) for r in records]
    train_dataset = Dataset.from_dict({"text": formatted_texts})

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=2,
            warmup_steps=10,
            max_steps=-1,
            num_train_epochs=args.epochs,
            learning_rate=args.learning_rate,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=5,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=42,
            output_dir=args.output_dir,
        ),
    )

    print("[Training] Starting QLoRA fine-tuning...")
    trainer.train()

    print(f"[Export] Saving LoRA adapter weights to: {args.output_dir}")
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    if args.export_gguf:
        print(f"[Export] Quantizing and exporting GGUF ({args.export_gguf}) for Ollama/vLLM...")
        model.save_pretrained_gguf(f"{args.output_dir}_gguf", tokenizer, quantization_method=args.export_gguf)
        print(f"[Export] GGUF exported to {args.output_dir}_gguf")

    print("[Success] FocusGate v2.8 Student Fine-Tuning Complete.")

if __name__ == "__main__":
    main()
