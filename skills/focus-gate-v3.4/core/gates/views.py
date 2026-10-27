"""Ledger views: the Action-First header and the lint report (moved out of the CLI script in v3.3)."""
import os
import re
import sys
import json
from typing import Any, Dict, List, Optional, Tuple

from core.gates.ledger import Ledger

_CLI_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts", "focus-gate.py")


class StateSynthesizer:
    """Synthesizes Action-First next command and persistent State header."""

    @staticmethod
    def synthesize(ledger: Ledger, cli_path: Optional[str] = None) -> Tuple[str, str, Dict[str, Any]]:
        meta: Dict[str, Any] = {
            "action_type": "none",
            "target_id": None,
            "command": "",
            "active_spikes": 0,
            "gates_met": sum(1 for g in ledger.gates if g.checked),
            "gates_total": len(ledger.gates)
        }

        unmet_spikes = [s for s in ledger.spikes if not s.checked]
        meta["active_spikes"] = len(unmet_spikes)
        if unmet_spikes:
            target_spike = unmet_spikes[0]
            meta["target_id"] = target_spike.id
            meta["action_type"] = "spike_settlement"
            cli_path = cli_path or _CLI_PATH
            if target_spike.artifact and os.path.exists(target_spike.artifact):
                line1 = f"python3 {cli_path} --verify-spike {target_spike.artifact}"
            elif target_spike.artifact:
                line1 = f"python3 {cli_path} --scaffold-spike {target_spike.branch} {target_spike.id} \"{target_spike.question or target_spike.title}\""
            else:
                line1 = f"# Settle prototype spike {target_spike.id}: {target_spike.title}"
            meta["command"] = line1
            line2 = f"State: [Step {ledger.state_meta['step_current']} of {ledger.state_meta['step_total']}] [{len(unmet_spikes)} spike(s) active] [{meta['gates_met']}/{meta['gates_total']} gates met] [Est: {ledger.state_meta['est_min']} min]"
            return line1, line2, meta

        unmet_gates = [g for g in ledger.gates if not g.checked]
        if unmet_gates:
            target_gate = unmet_gates[0]
            meta["target_id"] = target_gate.id
            meta["action_type"] = "gate_execution"
            line1 = target_gate.check_cmd if target_gate.check_cmd else f"# Execute work for {target_gate.id}: {target_gate.title}"
        else:
            meta["action_type"] = "full_verification"
            cli_path = cli_path or _CLI_PATH
            line1 = f"python3 {cli_path} --run " + ledger.filepath

        meta["command"] = line1
        line2 = f"State: [Step {ledger.state_meta['step_current']} of {ledger.state_meta['step_total']}] [{meta['gates_met']}/{meta['gates_total']} gates met] [Est: {ledger.state_meta['est_min']} min]"
        return line1, line2, meta


class FocusLinter:
    """Validates cognitive rules, ADHD limits, and verification honesty."""

    @staticmethod
    def lint(ledger: Ledger) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        if len(ledger.glossary) > 5:
            errors.append(f"Glossary has {len(ledger.glossary)} terms. Maximum allowed is 5 to protect working memory.")

        total_items = len(ledger.gates) + len(ledger.spikes)
        if total_items == 0:
            errors.append("No acceptance gates or prototype spikes found.")

        for s in ledger.spikes:
            if not s.question or not s.question.endswith('?'):
                warnings.append(f"Spike '{s.id}' QUESTION should end with '?' to state an explicit hypothesis.")
            if not s.artifact:
                warnings.append(f"Spike '{s.id}' missing ARTIFACT pointer.")

        for g in ledger.gates:
            if not g.check_cmd:
                warnings.append(f"Gate '{g.id}' has no CHECK command (manual gate).")
        # v3.2: verification honesty. Judge whether each CHECK/EXPECT could ever fail.
        from core.gates.evidence import GateIntegrity
        for g in ledger.gates + ledger.spikes:
            if not g.check_cmd:
                continue
            for f in GateIntegrity.analyze(g.check_cmd, g.expect_pattern):
                (errors if f.severity == "error" else warnings).append(f"{f.code} gate '{g.id}': {f.message}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings)
        }
