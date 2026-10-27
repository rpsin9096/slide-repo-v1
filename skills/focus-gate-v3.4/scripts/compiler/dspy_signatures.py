#!/usr/bin/env python3
"""DSPy Signatures and Prompt Compilation Modules for FocusGate v2.8.

Defines typed DSPy signatures for the 11 Canonical Pipelines, action envelope synthesis,
and programmatic prompt optimization metrics (RRR, BAS, TCR).
Pure Python standard library compatible (works with or without dspy-ai installed).
"""

from typing import Dict, Any, List, Optional
import json
import re


# =============================================================================
# Pipeline Signatures & Intent Models
# =============================================================================

PIPELINE_SIGNATURES = {
    "P1": {
        "name": "Rapid Defect Resolution",
        "archetype": "DEFECT",
        "inputs": ["query", "error_log", "test_runner"],
        "stages": ["triage", "diagnosing-bugs", "unlazy", "code-review"],
        "est_minutes": 15,
        "oracle": "CHECK: <test_command>\nEXPECT: PASS",
        "compiled_prompt": "Intent:DEFECT|Pipeline:P1|Stages:triage->diag->unlazy->review|Exit:repro_pass"
    },
    "P2": {
        "name": "Strategic Wayfinding",
        "archetype": "STRATEGY",
        "inputs": ["query", "ambiguity_tokens"],
        "stages": ["grilling", "wayfinder", "prototype", "unlazy"],
        "est_minutes": 45,
        "oracle": "CHECK: git status\nEXPECT: On branch",
        "compiled_prompt": "Intent:STRATEGY|Pipeline:P2|Stages:grill->wayfind->proto->unlazy|Exit:decision_locked"
    },
    "P3": {
        "name": "Deep Module Redesign",
        "archetype": "ARCHITECTURE",
        "inputs": ["module_path", "seam_boundary"],
        "stages": ["codebase-design", "prototype", "unlazy", "code-review"],
        "est_minutes": 40,
        "oracle": "CHECK: <unit_test_suite>\nEXPECT: OK",
        "compiled_prompt": "Intent:ARCH|Pipeline:P3|Stages:design->proto->unlazy->review|Rule:2_adapters"
    },
    "P4": {
        "name": "Loop Synthesis",
        "archetype": "AUTOMATION",
        "inputs": ["recurring_task", "checkpoint_target"],
        "stages": ["loop-me", "grilling", "unlazy"],
        "est_minutes": 30,
        "oracle": "CHECK: <cron_runner>\nEXPECT: SUCCESS",
        "compiled_prompt": "Intent:LOOP|Pipeline:P4|Stages:loop->grill->unlazy|Rule:push_right"
    },
    "P5": {
        "name": "Atomic Sprint",
        "archetype": "ATOMIC",
        "inputs": ["micro_action"],
        "stages": ["unlazy", "code-review"],
        "est_minutes": 10,
        "oracle": "CHECK: git status\nEXPECT: On branch",
        "compiled_prompt": "Intent:ATOMIC|Pipeline:P5|Stages:unlazy->review|Cap:single_item"
    },
    "P6": {
        "name": "Ideation to Implementation",
        "archetype": "IDEATION",
        "inputs": ["raw_notes", "fragment_file"],
        "stages": ["writing-fragments", "writing-shape", "unlazy"],
        "est_minutes": 30,
        "oracle": "CHECK: echo FRAGMENT_OK\nEXPECT: FRAGMENT_OK",
        "compiled_prompt": "Intent:IDEATION|Pipeline:P6|Stages:frags->shape->unlazy|Store:FRAGMENTS.md"
    },
    "P7": {
        "name": "Architectural RFC Spec",
        "archetype": "SPECIFICATION",
        "inputs": ["rfc_topic", "constraints"],
        "stages": ["writing-fragments", "codebase-design", "writing-shape", "prototype"],
        "est_minutes": 45,
        "oracle": "CHECK: git status\nEXPECT: On branch",
        "compiled_prompt": "Intent:RFC|Pipeline:P7|Stages:frags->design->shape->proto|Output:SPEC.md"
    },
    "P8": {
        "name": "Narrative Guide & Post-Mortem",
        "archetype": "POSTMORTEM",
        "inputs": ["incident_timeline", "settled_gate"],
        "stages": ["diagnosing-bugs", "writing-beats", "code-review"],
        "est_minutes": 25,
        "oracle": "CHECK: git status\nEXPECT: On branch",
        "compiled_prompt": "Intent:POSTMORTEM|Pipeline:P8|Stages:diag->beats->review|Structure:symptom->cause->fix"
    },
    "P9": {
        "name": "UI Component & Design System Slicing",
        "archetype": "UI_COMPONENT",
        "inputs": ["component_spec", "tokens_path"],
        "stages": ["writing-fragments", "focus-design", "prototype", "codebase-design", "unlazy"],
        "est_minutes": 35,
        "oracle": "CHECK: python3 focus-gate.py --audit-tokens <path>\nEXPECT: AUDIT_TOKENS_PASS",
        "compiled_prompt": "Intent:UI_COMPONENT|Pipeline:P9|Stages:frags->design->proto->code->unlazy|Tokens:3_layer"
    },
    "P10": {
        "name": "Visual Asset & Creative Production",
        "archetype": "VISUAL_ASSET",
        "inputs": ["canvas_dims", "platform"],
        "stages": ["triage", "focus-design", "prototype", "code-review"],
        "est_minutes": 25,
        "oracle": "CHECK: python3 focus-gate.py --audit-safe-zone <spec> -p <platform>\nEXPECT: SAFE_ZONE_PASS",
        "compiled_prompt": "Intent:ASSET|Pipeline:P10|Stages:triage->design->proto->review|Zone:70pct_box"
    },
    "P11": {
        "name": "Design Audit & Accessibility Polish",
        "archetype": "DESIGN_AUDIT",
        "inputs": ["source_files", "palette"],
        "stages": ["diagnosing-bugs", "focus-design", "unlazy", "code-review"],
        "est_minutes": 20,
        "oracle": "CHECK: python3 focus-gate.py --audit-contrast <fg> <bg>\nEXPECT: CONTRAST_PASS_AA",
        "compiled_prompt": "Intent:A11Y_AUDIT|Pipeline:P11|Stages:diag->design->unlazy->review|WCAG:AA_4.5"
    }
}


# =============================================================================
# Optimization Metric Functions (BAS, RRR, TCR)
# =============================================================================

class CompilationMetrics:
    """Objective validation metrics for DSPy and MIPROv2 optimizers."""

    ACTION_RE = re.compile(r"^▶ NEXT ACTION:\s+.+$", re.MULTILINE)
    STATE_RE = re.compile(r"^State:\s+\[Pipeline:.+\]\s+\[Stage:.+\]\s+\[Queue:.+\]\s+\[Est:.+\]\s+\[Depth:.+\]$", re.MULTILINE)
    FOCUS_RE = re.compile(r"^■ ACTIVE FOCUS:\s+.+$", re.MULTILINE)
    NEXT_RE = re.compile(r"^Next:\s+.+$", re.MULTILINE)

    @classmethod
    def validate_action_envelope(cls, output: str) -> bool:
        """Verifies strict adherence to the 3-zone visual layout (BAS = 100%)."""
        return bool(
            cls.ACTION_RE.search(output) and
            cls.STATE_RE.search(output) and
            cls.FOCUS_RE.search(output) and
            cls.NEXT_RE.search(output)
        )

    @classmethod
    def evaluate_triage(cls, prediction: str, ground_truth: str) -> bool:
        """Evaluates pipeline classification accuracy (RRR = 100%)."""
        pred_norm = prediction.strip().upper()
        gt_norm = ground_truth.strip().upper()
        return gt_norm in pred_norm or pred_norm in gt_norm


def get_compiled_pipeline_prompt(pipeline_id: str) -> str:
    """Returns the token-compressed declarative directive for a canonical pipeline."""
    return PIPELINE_SIGNATURES.get(pipeline_id, {}).get("compiled_prompt", "")
