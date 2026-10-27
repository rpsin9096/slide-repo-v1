"""FocusGate v2.9 — Deep Module AST parser for FocusGate Task Ledgers.

Parses GATES.md ledgers into structured domain models (TracerGate, SpikeGate,
glossary terms, public seams, and micro-ADRs).

Zero external dependencies (100% Python standard library).
"""

import os
import re
from typing import Dict, Any, List, Optional
from core.gates.tracer_gate import TracerGate, SpikeGate


class Ledger:
    """Deep Module AST parser for FocusGate Task Ledgers."""

    def __init__(self, content: str, filepath: str = ".focusgate/GATES.md"):
        self.filepath = filepath
        self.raw_content = content
        self.title: str = "FocusGate Ledger"
        self.glossary: List[Dict[str, Any]] = []
        self.seams: List[Dict[str, Any]] = []
        self.spikes: List[SpikeGate] = []
        self.gates: List[TracerGate] = []
        self.adrs: List[Dict[str, Any]] = []
        self.state_meta: Dict[str, Any] = {"step_total": 4, "step_current": 1, "est_min": 20}
        self._parse()

    @classmethod
    def from_file(cls, path: str) -> "Ledger":
        if not os.path.exists(path):
            raise FileNotFoundError(f"Error: Ledger file not found at {path}")
        with open(path, "r", encoding="utf-8") as f:
            return cls(f.read(), filepath=path)

    def _parse(self):
        lines = self.raw_content.split("\n")
        in_glossary = False
        in_seams = False
        in_spikes = False
        in_gates = False
        in_adrs = False
        current_gate: Optional[TracerGate] = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            lower = line.lower()

            if line.startswith("# ") and not self.title.endswith(": "):
                self.title = line.replace("#", "").strip()

            state_m = re.search(r'state:\s*\[step\s*(\d+)\s*of\s*(\d+)\].*?\[est:\s*(\d+)\s*min\]', lower)
            if state_m:
                self.state_meta["step_current"] = int(state_m.group(1))
                self.state_meta["step_total"] = int(state_m.group(2))
                self.state_meta["est_min"] = int(state_m.group(3))

            if line.startswith("##") and ("micro-glossary" in lower or "domain anchor" in lower):
                in_glossary = True
                in_seams = in_spikes = in_gates = in_adrs = False
                current_gate = None
                continue
            if line.startswith("##") and ("public seam" in lower or "test boundar" in lower):
                in_seams = True
                in_glossary = in_spikes = in_gates = in_adrs = False
                current_gate = None
                continue
            if line.startswith("##") and ("acceptance gate" in lower or "vertical slice" in lower):
                in_gates = True
                in_glossary = in_seams = in_spikes = in_adrs = False
                current_gate = None
                continue
            if line.startswith("##") and ("micro-adr" in lower or "decision ledger" in lower):
                in_adrs = True
                in_glossary = in_seams = in_spikes = in_gates = False
                current_gate = None
                continue

            if in_gates and line.startswith("###") and ("spike" in lower or "throwaway" in lower or "prototype" in lower):
                in_spikes = True
                current_gate = None
                continue
            if in_gates and line.startswith("###") and ("production" in lower or "deliverable" in lower or "gates" in lower):
                in_spikes = False
                current_gate = None
                continue

            if in_glossary and stripped.startswith("- **"):
                m = re.match(r'- \*\*([^*]+)\*\*:\s*(.*)', stripped)
                if m:
                    self.glossary.append({"term": m.group(1).strip(), "def": m.group(2).strip(), "line_num": i + 1})
                continue

            if in_seams and stripped.startswith("- **"):
                m = re.match(r'- \*\*([^*]+)\*\*:\s*(.*)', stripped)
                if m:
                    self.seams.append({"name": m.group(1).strip(), "desc": m.group(2).strip(), "line_num": i + 1})
                continue

            gate_match = re.match(r'^-\s*\[([ xX])\]\s*([^:]+):\s*(.*)', stripped)
            if gate_match:
                checked = gate_match.group(1).lower() == 'x'
                gate_id = gate_match.group(2).strip()
                title = gate_match.group(3).strip()

                is_spike = in_spikes or gate_id.startswith("spike-")
                if is_spike:
                    current_gate = SpikeGate(gate_id, title, checked, line_num=i + 1)
                    self.spikes.append(current_gate)
                else:
                    current_gate = TracerGate(gate_id, title, checked, line_num=i + 1)
                    self.gates.append(current_gate)
                continue

            if current_gate:
                check_m = re.match(r'^\s*CHECK:\s*(.+)$', line)
                if check_m:
                    current_gate.check_cmd = check_m.group(1).strip()
                    continue
                expect_m = re.match(r'^\s*EXPECT:\s*(.+)$', line)
                if expect_m:
                    current_gate.expect_pattern = expect_m.group(1).strip()
                    continue
                timeout_m = re.match(r'^\s*TIMEOUT:\s*(\d+)$', line)
                if timeout_m:
                    current_gate.timeout = int(timeout_m.group(1).strip())
                    continue
                cwd_m = re.match(r'^\s*CWD:\s*(.+)$', line)
                if cwd_m:
                    current_gate.cwd = cwd_m.group(1).strip()
                    continue
                deps_m = re.match(r'^\s*(?:DEPS|AFTER):\s*(.+)$', line)
                if deps_m:
                    raw_deps = deps_m.group(1).strip()
                    cleaned_deps = raw_deps.strip("[]").strip()
                    current_gate.deps = [d.strip().strip("[]\"'") for d in re.split(r'[,;\s]+', cleaned_deps) if d.strip() and d.strip() not in ("[]", "[", "]")]
                    continue

                if isinstance(current_gate, SpikeGate):
                    branch_m = re.match(r'^\s*BRANCH:\s*(logic|ui)$', line, re.IGNORECASE)
                    if branch_m:
                        current_gate.branch = branch_m.group(1).strip().lower()
                        continue
                    quest_m = re.match(r'^\s*QUESTION:\s*(.+)$', line)
                    if quest_m:
                        current_gate.question = quest_m.group(1).strip()
                        continue
                    art_m = re.match(r'^\s*ARTIFACT:\s*(.+)$', line)
                    if art_m:
                        current_gate.artifact = art_m.group(1).strip()
                        continue

                if line.startswith("- [") or line.startswith("## ") or line.startswith("### "):
                    current_gate = None

            if in_adrs and (line.startswith("### [ADR-") or line.startswith("- **[ADR-")):
                adr_id_m = re.search(r'\[ADR-(\d+)\]\s*(.*)', line)
                adr_id = f"ADR-{adr_id_m.group(1)}" if adr_id_m else "ADR"
                adr_title = adr_id_m.group(2).strip() if adr_id_m else line.strip()
                self.adrs.append({"id": adr_id, "title": adr_title, "line_num": i + 1, "raw": line.strip()})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "filepath": self.filepath,
            "state_meta": self.state_meta,
            "glossary": self.glossary,
            "seams": self.seams,
            "spikes": [s.to_dict() for s in self.spikes],
            "gates": [g.to_dict() for g in self.gates],
            "adrs": self.adrs,
            "stats": {
                "spikes_settled": sum(1 for s in self.spikes if s.checked),
                "spikes_total": len(self.spikes),
                "gates_met": sum(1 for g in self.gates if g.checked),
                "gates_total": len(self.gates),
                "pct_complete": round((sum(1 for g in self.gates if g.checked) / len(self.gates) * 100)) if self.gates else 0
            }
        }
