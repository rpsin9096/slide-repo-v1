"""Activation seed, distraction recovery and the single-item queue (moved out of the CLI script in v3.4)."""
import os

from core.aggregate import LedgerAggregate
from typing import Any
from typing import Dict
from typing import Optional


class ActivationSeed:
    """Scaffolds deterministic <=2-minute micro-actions to bypass activation paralysis."""
    @staticmethod
    def scaffold(target_dir: str = ".", task_name: str = "Atomic Task", check_cmd: str = "test -s .focusgate/SEED.md && echo SEED_PRESENT", expect_out: str = "SEED_PRESENT") -> str:
        if os.path.basename(os.path.abspath(target_dir)).startswith(".") or target_dir.endswith(".focusgate"):
            root = target_dir
        else:
            root = os.path.join(target_dir, ".focusgate")
        os.makedirs(root, exist_ok=True)
        seed_path = os.path.join(root, "GATES-SEED.md")
        content = f"""# FocusGate Seed Ledger: {task_name}
State: [Pipeline: Atomic Sprint (1/2)] [Stage: Seed Activation] [Queue: 1 active, 0 buffered] [Est: 2 min] [Depth: L1]

## 1. Activation Micro-Pledge (≤ 2 Minutes)
- [ ] seed-01: Write the first concrete step for '{task_name}' into .focusgate/SEED.md
  CHECK: {check_cmd}
{('  EXPECT: ' + expect_out + chr(10)) if expect_out else ''}"""
        with open(seed_path, "w", encoding="utf-8") as f:
            f.write(content)
        return seed_path


class DistractionRecovery:
    """Restores working memory in <3s answering What, Where, and Next Action."""
    @staticmethod
    def reorient(ledger: 'Ledger', ledger_path: str, event_store: Optional['SQLiteStorageAdapter'] = None) -> Dict[str, Any]:
        active_gate = None
        buffered_gates = []
        last_verified = None

        all_items = ledger.spikes + ledger.gates
        for item in all_items:
            if item.checked:
                last_verified = item
            elif active_gate is None:
                active_gate = item
            else:
                buffered_gates.append(item)

        stats = ledger.to_dict()["stats"]
        pct = stats.get("pct_complete", 0)
        total_checked = stats.get("gates_met", 0) + stats.get("spikes_settled", 0)
        total_items = stats.get("gates_total", 0) + stats.get("spikes_total", 0)

        bar_len = 10
        filled = int(round(bar_len * (pct / 100.0))) if total_items > 0 else 0
        progress_bar = "▓" * filled + "░" * (bar_len - filled)

        next_cmd = active_gate.check_cmd if (active_gate and active_gate.check_cmd) else "focus-gate.py --status"
        active_title = active_gate.title if active_gate else "All planned gates settled!"
        active_id = active_gate.id if active_gate else "NONE"
        last_id = last_verified.id if last_verified else "None"

        snapshot = {
            "task": ledger.title or os.path.basename(os.path.dirname(os.path.abspath(ledger_path))),
            "pct_complete": pct,
            "progress_bar": progress_bar,
            "total_met": total_checked,
            "total_items": total_items,
            "streak": total_checked,
            "last_verified_gate": last_id,
            "active_gate_id": active_id,
            "active_gate_title": active_title,
            "buffered_count": len(buffered_gates),
            "next_command": next_cmd
        }
        return snapshot


class SingleItemQueue:
    """Enforces the strict single-item active queue invariant using LedgerAggregate."""
    @staticmethod
    def evaluate(ledger: 'Ledger') -> Dict[str, Any]:
        # Must be a keyword: the first positional parameter of LedgerAggregate is
        # `workspace_root`, so `LedgerAggregate(ledger)` bound the Ledger to the
        # workspace and left `self.ledger` as None, making `get_active_gate()`
        # raise `AttributeError: 'NoneType' object has no attribute 'spikes'` and
        # crashing the documented `--queue-status` / `--queue-next` flags. Found by
        # the Loop 61 coverage tests.
        # v3.2 Loop 64: resolve the workspace root, do not inherit the cwd.
        # `os.getcwd()` here meant a run from inside .focusgate/ appended a
        # second .focusgate to its own state directory, and the nested tree
        # (14 of the 34 tracked artifacts) was the committed result.
        from core.workspace_detector import WorkspaceDetector as _WSD
        agg = LedgerAggregate(workspace_root=_WSD.resolve_root(), ledger=ledger)
        active = agg.get_active_gate()
        buffered = agg.get_frontier_buffer()
        settled = agg.get_settled_gates()
        all_items = agg._all_items()

        return {
            "active": active.to_dict() if active else None,
            "buffered": [b.to_dict() for b in buffered],
            "buffered_count": len(buffered),
            "settled_count": len(settled),
            "total": len(all_items)
        }
