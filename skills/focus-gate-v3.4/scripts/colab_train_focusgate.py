#!/usr/bin/env python3
"""FocusGate v2.8 — Autonomous Turnkey Training & Fine-Tuning Pipeline for Google Colab (T4 GPU).

Provides an end-to-end, zero-setup QLoRA training script for the FocusGate Student Router.
Trains the model to classify developer objectives into the 11 Canonical Pipelines (P1-P11),
enforce the 4-pass unlazy implementation rigor, and output the Invariant Action Envelope.

Compatible with Google Colab free-tier T4 GPU (VRAM < 2.5 GB).
"""

import os
import sys
try:
    import torch
except (ImportError, ModuleNotFoundError):
    torch = None

# =============================================================================
# Configuration & Hardware Detection
# =============================================================================

# Set to path of exported JSONL (e.g. from harvest_trajectories.py) or None to use built-in synthetic dataset
DATA_PATH = None

BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"  # Ungated, open-access, fast T4 inference (<1.5 GB VRAM in 4-bit)
OUTPUT_DIR = "./focusgate_lora_results"
ADAPTER_EXPORT_DIR = "./focusgate_v28_router_adapter"

# =============================================================================
# In-Memory FocusGate System SFT Dataset (Canonical Pipelines & Action Envelopes)
# =============================================================================

FOCUSGATE_TRAINING_DATA = [
    {
        "instruction": "We have an intermittent race condition in the async worker queue where jobs get dropped under load.",
        "input": "Files: worker.py, queue.py. Python 3.11, asyncio.",
        "output": """▶ NEXT ACTION: python3 -c 'from worker import JobQueue; q = JobQueue(); q.stress_test(concurrency=50)'
State: [Pipeline: Rapid Defect Resolution (Stage 1/4: Reproduce)] [Active Gate: gate-1-repro] [Queue: 1 active, 3 buffered] [Est: 15 min] [Depth: L1]

■ ACTIVE FOCUS: Formulate a deterministic reproduction oracle isolating the dropped job race condition in worker.py.
1. Inspect worker.py queue popping logic for un-awaited lock acquisition seams.
2. Execute concurrency stress test with 50 synthetic jobs to capture dropped payload signatures.
3. Lock down failing assertion before modifying queue concurrency primitives."""
    },
    {
        "instruction": "Build a modern, high-contrast dashboard component for displaying real-time cluster telemetry without generic SaaS styling.",
        "input": "Target: frontend/src/components/ClusterTelemetry.tsx with Tailwind/CSS.",
        "output": """▶ NEXT ACTION: python3 focus-gate.py --hydrate-facet frontend-design
State: [Pipeline: Bespoke Frontend Design & Implementation (Stage 1/6: Design Spec)] [Active Gate: gate-1-spec] [Queue: 1 active, 5 buffered] [Est: 15 min] [Depth: L1]

■ ACTIVE FOCUS: Establish distinctive design tokens and interface hierarchy avoiding cliche purple/terracotta palettes.
1. Extract bespoke high-contrast theme tokens into design-tokens.css (monochrome base with amber accents).
2. Scaffold ClusterTelemetry.tsx interface seam with strict props contract and accessible semantic DOM.
3. Validate safe-zone bounds and WCAG 2.1 AA relative contrast ratios via design oracles."""
    },
    {
        "instruction": "Design the domain entity model and event-sourced ledger for our customer billing subscription subsystem.",
        "input": "Architecture constraint: 100% Python standard library, zero external ORM dependencies.",
        "output": """▶ NEXT ACTION: python3 focus-gate.py --hydrate-facet codebase-design
State: [Pipeline: Modular Feature Architecture (Stage 1/3: Interface Contract)] [Active Gate: gate-1-seam] [Queue: 1 active, 2 buffered] [Est: 15 min] [Depth: L1]

■ ACTIVE FOCUS: Define immutable DomainEvent contracts and SQLite/WAL ledger storage port for subscription lifecycle.
1. Specify SubscriptionCreated, PlanUpgraded, and SubscriptionCanceled event dataclasses with ISO timestamps.
2. Implement append-only StoragePort with dual-write SQLite/WAL and JSONL audit logging.
3. Enforce optimistic locking and version sequence checking to reject out-of-order replayed deltas."""
    },
    {
        "instruction": "Audit our newly added authentication API endpoints against strict contract schemas and error suppression standards.",
        "input": "Target endpoints: POST /api/v1/auth/login, POST /api/v1/auth/refresh.",
        "output": """▶ NEXT ACTION: python3 focus-gate.py --audit-code-cliche api/auth/
State: [Pipeline: Anti-Cliché & Rigor Governance (Stage 1/2: Code Cliche Audit)] [Active Gate: gate-1-cliche] [Queue: 1 active, 1 buffered] [Est: 10 min] [Depth: L1]

■ ACTIVE FOCUS: Scan auth controllers for blanket exception masking, dummy return stubs, and schema drift.
1. Run CodeClicheOracle on api/auth/ to intercept any 'except Exception: pass' shotgun suppressions.
2. Validate JSON request/response payloads against auth.schema.json using strict jsonschema validators.
3. Enforce deterministic 401/403 status codes with explicit error reason enumerations."""
    },
    {
        "instruction": "Refactor our legacy monolithic notification dispatcher into modular, facet-driven micro-handlers.",
        "input": "Existing file: legacy_notify.py (850 lines).",
        "output": """▶ NEXT ACTION: python3 focus-gate.py --select-tool "Surgical refactoring of notification dispatcher" --target legacy_notify.py --diff-lines 45
State: [Pipeline: Refactor & Debt Remediation (Stage 1/3: Seam Isolation)] [Active Gate: gate-1-seam] [Queue: 1 active, 2 buffered] [Est: 15 min] [Depth: L1]

■ ACTIVE FOCUS: Decouple email, SMS, and webhook notification transports into isolated handler plugins behind NotificationPort.
1. Call ToolSelectionMatrix to confirm replace_file_content precondition bounds on legacy_notify.py.
2. Extract EmailNotifier and WebhookNotifier into plugins/ with uniform dispatch(msg) signatures.
3. Verify zero regression across existing unit test suites with 100% assertion parity."""
    },
    {
        "instruction": "Our system had a production deadlock during midnight batch reconciliations. Provide an immediate fix.",
        "input": "Logs show circular wait between ledger_locks and account_locks.",
        "output": """▶ NEXT ACTION: python3 focus-gate.py --synthesize-pipeline "production deadlock circular wait between ledger and account locks"
State: [Pipeline: Fast Path Hotfix (Stage 1/2: Lock Ordering Repair)] [Active Gate: gate-1-hotfix] [Queue: 1 active, 1 buffered] [Est: 10 min] [Depth: L1]

■ ACTIVE FOCUS: Impose global deterministic lock acquisition ordering across ledger and account transactions.
1. Enforce sorted multi-key acquisition sequence (always acquire account_lock before ledger_lock).
2. Add acquisition timeout with exponential backoff and jitter to prevent priority inversion.
3. Run stress concurrency harness under high simulated contention to prove zero deadlocks."""
    }
]

def format_chat_prompt(sample: dict) -> str:
    system_prompt = (
        "You are FocusGate v2.8, an ultra-compact, deterministic agent orchestration router. "
        "Classify user tasks, select canonical pipelines (P1-P11), and format outputs in the Invariant Action Envelope."
    )
    user_content = sample["instruction"]
    if sample.get("input", "").strip():
        user_content += f"\n\nContext:\n{sample['input']}"
    
    return (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{user_content}<|im_end|>\n"
        f"<|im_start|>assistant\n{sample['output']}<|im_end|>"
    )

def main():
    print("=" * 80)
    print("FOCUSGATE v2.8 — AUTONOMOUS STUDENT ROUTER FINE-TUNING PIPELINE")
    print("=" * 80)

    # 1. Hardware Check
    device = "cuda" if torch.cuda.is_available() else "cpu"
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    print(f"[Hardware] Device: {device.upper()} | Name: {gpu_name}")
    if device != "cuda":
        print("[Warning] CUDA not detected. For fast training, ensure Colab GPU runtime (T4) is active.")

    # 2. Dataset Loading
    from datasets import Dataset, load_dataset
    if DATA_PATH and os.path.exists(DATA_PATH):
        print(f"[Dataset] Loading exported FocusGate trajectories from: {DATA_PATH}")
        ext = DATA_PATH.split(".")[-1]
        raw_ds = load_dataset(ext if ext in ("json", "csv") else "json", data_files=DATA_PATH)["train"]
    else:
        print(f"[Dataset] Initializing canonical FocusGate SFT dataset ({len(FOCUSGATE_TRAINING_DATA)} examples)")
        raw_ds = Dataset.from_list(FOCUSGATE_TRAINING_DATA)

    formatted_ds = raw_ds.map(lambda x: {"text": format_chat_prompt(x)})
    print(f"[Dataset] Prepared {len(formatted_ds)} training sequences.")

    # 3. Model & Tokenizer
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TrainingArguments
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True
    )

    print(f"[Model] Loading quantized base router: {BASE_MODEL_ID}")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        quantization_config=bnb_config if device == "cuda" else None,
        device_map="auto" if device == "cuda" else None,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        trust_remote_code=True
    )

    if device == "cuda":
        model = prepare_model_for_kbit_training(model)

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, peft_config)
    trainable, total = model.get_nb_trainable_parameters()
    print(f"[LoRA] Trainable Parameters: {trainable:,} / {total:,} ({100 * trainable / total:.2f}%)")

    # 4. Training Arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=2,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        logging_steps=1,
        optim="paged_adamw_8bit" if device == "cuda" else "adamw_torch",
        fp16=(device == "cuda"),
        bf16=False,
        max_grad_norm=0.3,
        save_strategy="no",
        report_to="none"
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=formatted_ds,
        dataset_text_field="text",
        max_seq_length=512,
        tokenizer=tokenizer,
        args=training_args,
        packing=False
    )

    print("[Training] Executing FocusGate Student Router fine-tuning...")
    train_res = trainer.train()
    print(f"[Training] Finished. Loss: {train_res.training_loss:.4f} in {train_res.metrics['train_runtime']:.1f}s")

    # 5. Export Adapters
    model.save_pretrained(ADAPTER_EXPORT_DIR)
    tokenizer.save_pretrained(ADAPTER_EXPORT_DIR)
    print(f"[Export] Saved FocusGate LoRA adapters to: {ADAPTER_EXPORT_DIR}")

    # 6. Verification Inference
    test_task = "We need to build a distributed telemetry ingress pipeline for our microservices with JSON schema validation."
    test_prompt = (
        f"<|im_start|>system\n"
        f"You are FocusGate v2.8, an ultra-compact, deterministic agent orchestration router. "
        f"Classify user tasks, select canonical pipelines (P1-P11), and format outputs in the Invariant Action Envelope.<|im_end|>\n"
        f"<|im_start|>user\n{test_task}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )

    model.eval()
    inp = tokenizer(test_prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(
            **inp,
            max_new_tokens=160,
            do_sample=False,
            temperature=0.0,
            pad_token_id=tokenizer.eos_token_id
        )
    pred = tokenizer.decode(out[0][inp.input_ids.shape[1]:], skip_special_tokens=True)

    print("\n" + "=" * 80)
    print("FOCUSGATE POST-TRAINING INFERENCE VERIFICATION")
    print("=" * 80)
    print(f"Developer Query:\n  {test_task}\n")
    print(f"Fine-Tuned FocusGate Action Envelope:\n{pred.strip()}")
    print("=" * 80)

if __name__ == "__main__":
    main()
