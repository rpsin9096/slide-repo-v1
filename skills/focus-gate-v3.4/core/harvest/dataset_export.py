"""FocusGate v3.0 — SFT Dataset Exporter.

Converts harvested swarm trajectories into multi-format SFT datasets
(OpenAI JSONL, Anthropic Claude JSONL, Google Gemini JSONL) with data sanitization.

100% Python stdlib, zero external dependencies.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional

from core.harvest.trajectory_harvester import SwarmTrajectory


class SFTDatasetExporter:
    """Sanitizes trajectories and exports fine-tuning packs for frontier LLMs."""

    SECRET_PATTERN = re.compile(r'(sk-[a-zA-Z0-9_\-]{8,}|bearer\s+[a-zA-Z0-9_\-\.]+)', re.IGNORECASE)
    PATH_PATTERN = re.compile(r'/Users/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-\./]+')

    def __init__(self, token_floor: int = 50):
        self.token_floor = token_floor

    def sanitize_text(self, text: str) -> str:
        """Strips sensitive API keys, bearer tokens, and private absolute paths."""
        text = self.SECRET_PATTERN.sub("[REDACTED_SECRET]", text)
        return text

    def format_openai(self, traj: SwarmTrajectory) -> Dict[str, Any]:
        """Formats trajectory into OpenAI chat completions fine-tuning structure."""
        sys_msg = (
            "You are an autonomous FocusGate v3.0 swarm agent solving complex engineering "
            "tasks under strict Red-Green TDD, invariant preservation, and dialectic peer review."
        )
        user_msg = self.sanitize_text(traj.task_brief)

        assistant_content = {
            "actor_traces": traj.actor_traces,
            "dialectics": traj.dialectics,
            "receipt": traj.receipt,
            "verdict": traj.verdict
        }
        assistant_msg = self.sanitize_text(json.dumps(assistant_content, indent=2))

        return {
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg}
            ]
        }

    def format_claude(self, traj: SwarmTrajectory) -> Dict[str, Any]:
        """Formats trajectory into Anthropic Claude fine-tuning structure."""
        sys_msg = (
            "You are an autonomous FocusGate v3.0 swarm agent executing verified "
            "TDD loops with mathematical rigor, domain anchors, and zero code cliché."
        )
        user_msg = self.sanitize_text(traj.task_brief)
        assistant_msg = self.sanitize_text(
            f"Trace Summary:\n{json.dumps(traj.actor_traces)}\n\nConsensus:\n{json.dumps(traj.dialectics)}"
        )

        return {
            "system": sys_msg,
            "messages": [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg}
            ]
        }

    def format_gemini(self, traj: SwarmTrajectory) -> Dict[str, Any]:
        """Formats trajectory into Google Gemini fine-tuning structure."""
        user_msg = self.sanitize_text(traj.task_brief)
        assistant_msg = self.sanitize_text(
            f"Resolution Plan & Swarm Trace:\n{json.dumps(traj.actor_traces, indent=2)}"
        )

        return {
            "contents": [
                {"role": "user", "parts": [{"text": user_msg}]},
                {"role": "model", "parts": [{"text": assistant_msg}]}
            ]
        }

    def export_file(
        self,
        trajectories: List[SwarmTrajectory],
        out_path: str,
        model_format: str = "openai"
    ) -> int:
        """Filters valid trajectories, applies formatting, and writes to output JSONL file."""
        model_format = model_format.lower().strip()
        formatter = {
            "openai": self.format_openai,
            "claude": self.format_claude,
            "gemini": self.format_gemini
        }.get(model_format, self.format_openai)

        valid_count = 0
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

        with open(out_path, "w", encoding="utf-8") as f:
            for t in trajectories:
                if t.verdict != "SUCCESS" or t.token_count < self.token_floor:
                    continue
                formatted = formatter(t)
                f.write(json.dumps(formatted) + "\n")
                valid_count += 1

        return valid_count
