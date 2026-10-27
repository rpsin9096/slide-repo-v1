"""FocusGate v2.9 — Prototype Spike Validator.

Inspects and validates disposable prototype HTML/Markdown artifacts against
domain invariants and decoupling constraints.

Zero external dependencies (100% Python standard library).
"""

import os
import re
from typing import Tuple, List


class SpikeValidator:
    """Inspects and validates disposable prototype artifacts."""

    @staticmethod
    def _strip_comments(code: str) -> str:
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        return code

    @classmethod
    def verify_logic_prototype(cls, html_path: str) -> Tuple[bool, List[str]]:
        errors = []
        if not os.path.exists(html_path):
            return False, [f"Artifact file not found: {html_path}"]

        with open(html_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if "<!DOCTYPE html>" not in content and "<html" not in content.lower():
            errors.append("Prototype must be a self-contained HTML document.")

        core_logic_match = re.search(r'<script[^>]*id=["\']core-logic["\'][^>]*>(.*?)</script>', content, re.DOTALL)
        if not core_logic_match:
            if "reduce(" not in content and "createStateMachine(" not in content and "DomainModule" not in content:
                errors.append("Missing isolated pure domain logic module (expected <script id=\"core-logic\"> with pure reducer or state machine).")
        else:
            raw_core_code = core_logic_match.group(1)
            clean_code = cls._strip_comments(raw_core_code)
            dom_leaks = []
            for leak in ["document.", "window.", "getElementById", "querySelector", "innerHTML", "addEventListener"]:
                if leak in clean_code:
                    dom_leaks.append(leak)
            if dom_leaks:
                errors.append(f"Pure domain module contains external DOM couplings: {', '.join(dom_leaks)}. Maintain core logic as pure, decoupled functions.")

        if "state-grid" not in content and "raw-state" not in content and "Current State" not in content:
            errors.append("Prototype must include a human-readable Current State panel.")

        if "<button" not in content:
            errors.append("Prototype must provide interactive action buttons.")

        if "scenario" not in content.lower() and "tab" not in content.lower():
            errors.append("Prototype should include guided walkthrough scenarios for tricky cases.")

        return (len(errors) == 0), errors

    @classmethod
    def verify_ui_prototype(cls, doc_path: str) -> Tuple[bool, List[str]]:
        errors = []
        if not os.path.exists(doc_path):
            return False, [f"UI prototype guide not found: {doc_path}"]
        with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if "variant" not in content.lower():
            errors.append("UI prototype spec must define multi-variant design options.")
        if "switcher" not in content.lower() and "setvariant" not in content.lower():
            errors.append("UI prototype spec must reference a floating switcher or variant parameter.")
        return (len(errors) == 0), errors
