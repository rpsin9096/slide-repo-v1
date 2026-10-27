"""FocusGate v3.0 — Multi-Agent Swarm Trajectory Harvester.

Records, indexes, and persists end-to-end multi-agent problem-solving traces
including actor step traces, dialectic debates, and signed coherence receipts.

100% Python stdlib, zero external dependencies.
"""

import os
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class SwarmTrajectory:
    """A verified multi-agent problem-solving execution trajectory."""
    trajectory_id: str
    task_brief: str
    actor_traces: List[Dict[str, Any]]
    dialectics: List[Dict[str, Any]]
    receipt: Optional[Dict[str, Any]]
    verdict: str  # "SUCCESS" | "FAILED"
    token_count: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trajectory_id": self.trajectory_id,
            "task_brief": self.task_brief,
            "actor_traces": self.actor_traces,
            "dialectics": self.dialectics,
            "receipt": self.receipt,
            "verdict": self.verdict,
            "token_count": self.token_count,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SwarmTrajectory":
        return cls(
            trajectory_id=data.get("trajectory_id", ""),
            task_brief=data.get("task_brief", ""),
            actor_traces=data.get("actor_traces", []),
            dialectics=data.get("dialectics", []),
            receipt=data.get("receipt"),
            verdict=data.get("verdict", "FAILED"),
            token_count=data.get("token_count", 0),
            timestamp=data.get("timestamp", 0.0)
        )


class TrajectoryHarvester:
    """Persists and queries multi-agent swarm trajectories."""

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = os.path.abspath(
            storage_dir or os.path.join(os.getcwd(), ".focusgate", "trajectories")
        )
        os.makedirs(self.storage_dir, exist_ok=True)
        self.log_file = os.path.join(self.storage_dir, "trajectories.jsonl")

    @classmethod
    def estimate_tokens(cls, obj: Any) -> int:
        """Estimates token count (~4 characters per token)."""
        raw = json.dumps(obj) if isinstance(obj, (dict, list)) else str(obj)
        return max(1, len(raw) // 4)

    def record(
        self,
        task_brief: str,
        actor_traces: List[Dict[str, Any]],
        dialectics: List[Dict[str, Any]],
        receipt: Optional[Dict[str, Any]],
        verdict: str = "SUCCESS"
    ) -> SwarmTrajectory:
        """Records a new execution trajectory and appends to persistent log."""
        tid = f"traj-{int(time.time()*1000)}-{hashlib.sha256(task_brief.encode('utf-8')).hexdigest()[:8]}"
        tokens = (
            self.estimate_tokens(task_brief) +
            self.estimate_tokens(actor_traces) +
            self.estimate_tokens(dialectics) +
            (self.estimate_tokens(receipt) if receipt else 0)
        )

        traj = SwarmTrajectory(
            trajectory_id=tid,
            task_brief=task_brief,
            actor_traces=actor_traces,
            dialectics=dialectics,
            receipt=receipt,
            verdict=verdict,
            token_count=tokens,
            timestamp=time.time()
        )

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(traj.to_dict()) + "\n")

        return traj

    def load_trajectories(self) -> List[SwarmTrajectory]:
        """Loads all recorded trajectories from disk."""
        trajectories: List[SwarmTrajectory] = []
        if not os.path.isfile(self.log_file):
            return trajectories

        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        trajectories.append(SwarmTrajectory.from_dict(json.loads(line)))
        except (OSError, json.JSONDecodeError):
            pass

        return trajectories

    def get_successful_trajectories(self) -> List[SwarmTrajectory]:
        """Returns only successful trajectories eligible for fine-tuning."""
        return [t for t in self.load_trajectories() if t.verdict == "SUCCESS"]
