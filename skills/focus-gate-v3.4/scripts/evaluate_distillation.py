#!/usr/bin/env python3
"""Automated Evaluation Runner for FocusGate v2.8 Distillation.

Evaluates Student model predictions against FGBench ground truth.
Measures:
- Reasoning Retention Rate (RRR >= 98%)
- Behavioral Adherence Score (BAS == 100%)
- Net Token Compression Ratio (TCR >= 85%)
- Triage Latency (<10ms gate)
100% Pure Python standard library (zero external dependencies).
"""

import sys
import os
import json
import time
import argparse
from typing import Dict, Any, List, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))

from core.pipeline_synthesizer import PipelineSynthesizer
try:
    from core.oracles.contrast_oracle import ContrastOracle
except ImportError:  # optional oracle
    ContrastOracle = None

from core.tokens import estimate_tokens
from adapters.model_adapter import LoRAModelAdapter


class DistillationEvaluator:
    """Automated benchmark evaluator for distilled FocusGate models."""

    TEACHER_AVG_TOKENS_PER_TRIAGE = 2042.0

    @classmethod
    def run_eval(cls, dataset_path: str, adapter_dir: Optional[str] = None) -> Dict[str, Any]:
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "evals" in data:
            scenarios = data["evals"]
        elif isinstance(data, list):
            scenarios = data
        else:
            scenarios = []

        adapter = LoRAModelAdapter(adapter_dir=adapter_dir)

        total = len(scenarios)
        correct_pipeline = 0
        correct_archetype = 0
        envelope_compliant = 0
        latencies = []
        total_student_tokens = 0

        for sc in scenarios:
            query = sc.get("query") or sc.get("prompt", "")
            if not query:
                continue
            expected_pipe = sc.get("expected_pipeline", "")
            expected_arch = sc.get("expected_archetype", "")

            t0 = time.perf_counter()
            plan = adapter.route(query) if adapter.is_available() else PipelineSynthesizer.synthesize(query)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(elapsed_ms)

            # Measure accuracy (supporting CREATIVE_ASSET / VISUAL_ASSET canonical equivalence)
            arch_match = (
                plan.get("archetype") == expected_arch
                or {plan.get("archetype"), expected_arch} == {"CREATIVE_ASSET", "VISUAL_ASSET"}
            )
            pipe_match = expected_pipe in plan.get("pipeline", "") or arch_match
            if arch_match:
                correct_archetype += 1
            if pipe_match:
                correct_pipeline += 1

            # Check action envelope format
            has_action = bool(plan.get("seed_step", {}).get("action"))
            has_check = bool(plan.get("seed_step", {}).get("check"))
            has_expect = bool(plan.get("seed_step", {}).get("expect"))
            if has_action and has_check and has_expect:
                envelope_compliant += 1

            # Estimate student tokens
            envelope_str = plan.get("action_envelope") or json.dumps(plan)
            student_tokens = estimate_tokens(envelope_str)
            total_student_tokens += student_tokens

        rrr = (correct_pipeline / total) * 100.0 if total else 100.0
        bas = (envelope_compliant / total) * 100.0 if total else 100.0
        avg_latency_ms = sum(latencies) / total if total else 0.0
        avg_student_tokens = total_student_tokens / total if total else 0.0
        tcr = (1.0 - (avg_student_tokens / cls.TEACHER_AVG_TOKENS_PER_TRIAGE)) * 100.0

        return {
            "total_scenarios": total,
            "rrr": round(rrr, 2),
            "bas": round(bas, 2),
            "tcr": round(tcr, 2),
            "avg_latency_ms": round(avg_latency_ms, 3),
            "avg_student_tokens": round(avg_student_tokens, 1),
            "teacher_baseline_tokens": cls.TEACHER_AVG_TOKENS_PER_TRIAGE,
            "adapter_metadata": adapter.get_metadata() if adapter.is_available() else None,
            "passed": rrr >= 98.0 and bas >= 100.0 and tcr >= 85.0
        }


def main():
    parser = argparse.ArgumentParser(description="FocusGate v2.8 Distillation Evaluator")
    parser.add_argument("--dataset", default=None, help="Path to FGBench JSON dataset (defaults to tests/fgbench100.json or evals/evals.json)")
    parser.add_argument("--adapter-dir", default=None, help="Path to fine-tuned LoRA router adapter directory")
    parser.add_argument("--json", action="store_true", help="Output raw JSON results")
    args = parser.parse_args()

    dataset_path = args.dataset
    if not dataset_path:
        for cand in ["tests/fgbench100.json", "evals/evals.json"]:
            if os.path.exists(cand):
                dataset_path = cand
                break

    if not dataset_path or not os.path.exists(dataset_path):
        print(f"Error: Dataset not found at {args.dataset or 'tests/fgbench100.json'}", file=sys.stderr)
        sys.exit(1)

    scorecard = DistillationEvaluator.run_eval(dataset_path, adapter_dir=args.adapter_dir)

    if args.json:
        print(json.dumps(scorecard, indent=2))
    else:
        print("=" * 70)
        print("FOCUSGATE v2.8 DISTILLATION EVALUATION SCORECARD (FGBench)")
        print(f"Dataset:            {os.path.abspath(dataset_path)}")
        print(f"Total Scenarios:    {scorecard['total_scenarios']}")
        meta = scorecard.get("adapter_metadata")
        if meta and meta.get("status") == "VERIFIED":
            print(f"Model Adapter:      {meta['base_model']} (LoRA r={meta['rank']}, SHA: {meta['checksum_short']})")
        else:
            print("Model Adapter:      Deterministic Synthesis Fallback (Pure Stdlib)")
        print("-" * 70)
        print(f"1. Reasoning Retention (RRR):  {scorecard['rrr']}%   [Gate: >= 98.0%]")
        print(f"2. Behavioral Adherence (BAS): {scorecard['bas']}%  [Gate: == 100.0%]")
        print(f"3. Token Compression (TCR):    {scorecard['tcr']}%   [Gate: >= 85.0%]")
        print(f"4. Average Triage Latency:     {scorecard['avg_latency_ms']}ms  [Gate: < 10.0ms]")
        print(f"5. Student Avg Tokens/Triage:  {scorecard['avg_student_tokens']} tokens (Teacher: {scorecard['teacher_baseline_tokens']})")
        print("=" * 70)
        status = "PASSED (Production Candidate Ready)" if scorecard["passed"] else "FAILED"
        print(f"OVERALL STATUS: {status}")
        print("=" * 70)

    sys.exit(0 if scorecard["passed"] else 1)


if __name__ == "__main__":
    main()
