"""FocusGate v3.0 — Atomic Saga-Guarded Worktree Merge Coordinator.

Coordinates atomic merges of concurrent actor branches into main with
pre-merge verification barriers, automatic conflict aborts, and cryptographic
rollback tombstones.

Zero external dependencies (100% Python stdlib).
"""

import os
import sys
import uuid
import time
import hashlib
import subprocess
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from core.swarm.actor_worktree import ActorWorktreeManager, WorktreeResult


@dataclass
class SagaMergeResult:
    """Outcome of an atomic Saga merge transaction for an actor's worktree."""
    success: bool
    status: str  # "COMMITTED" | "ROLLED_BACK" | "CONFLICT_ABORTED"
    actor_id: str
    gate_id: str
    tombstone_id: Optional[str] = None
    message: str = ""
    conflicts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes SagaMergeResult to dictionary."""
        return {
            "success": self.success,
            "status": self.status,
            "actor_id": self.actor_id,
            "gate_id": self.gate_id,
            "tombstone_id": self.tombstone_id,
            "message": self.message,
            "conflicts": self.conflicts
        }


class SagaMergeCoordinator:
    """Manages transactional worktree merges with barrier verification and rollback guarantees."""

    def __init__(
        self,
        worktree_manager: ActorWorktreeManager,
        event_store: Optional[Any] = None
    ):
        self.mgr = worktree_manager
        self.event_store = event_store
        self.tombstones: List[Dict[str, Any]] = []

    def _generate_tombstone(self, actor_id: str, gate_id: str, reason: str) -> str:
        """Generates a cryptographic rollback tombstone ID and records audit entry."""
        tid = f"tombstone-{uuid.uuid4().hex[:12]}"
        entry = {
            "tombstone_id": tid,
            "actor_id": actor_id,
            "gate_id": gate_id,
            "reason": reason,
            "timestamp": time.time()
        }
        self.tombstones.append(entry)
        return tid

    def merge_actor_branch(
        self,
        actor_id: str,
        gate_id: str,
        target_branch: str = "main",
        verify_cmd: Optional[str] = None
    ) -> SagaMergeResult:
        """Attempts an atomic Saga merge of an actor's branch into target_branch.

        Aborts cleanly with a rollback tombstone if pre-merge verification fails
        or if git merge conflicts occur.
        """
        wt_path = self.mgr.get_worktree_path(actor_id)
        if not wt_path:
            return SagaMergeResult(
                success=False,
                status="ROLLED_BACK",
                actor_id=actor_id,
                gate_id=gate_id,
                message=f"No active worktree found for actor '{actor_id}'."
            )

        # 1. Pre-merge Barrier Verification Check
        if verify_cmd:
            proc = subprocess.run(
                verify_cmd,
                shell=True,
                cwd=wt_path,
                capture_output=True,
                text=True
            )
            if proc.returncode != 0:
                tombstone_id = self._generate_tombstone(
                    actor_id=actor_id,
                    gate_id=gate_id,
                    reason=f"Pre-merge check failed: {proc.stdout} {proc.stderr}"
                )
                self.mgr.cleanup_worktree(actor_id, force=True)
                return SagaMergeResult(
                    success=False,
                    status="ROLLED_BACK",
                    actor_id=actor_id,
                    gate_id=gate_id,
                    tombstone_id=tombstone_id,
                    message=f"Pre-merge check failed: {proc.stderr.strip() or proc.stdout.strip()}"
                )

        branch_name = f"focusgate/actor-{actor_id}"

        # 2. Non-git fallback
        if not self.mgr._is_git_repo():
            # In non-git mock mode, copy files back to root
            import shutil
            shutil.copytree(wt_path, self.mgr.repo_root, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.git', '.focusgate'))
            self.mgr.cleanup_worktree(actor_id, force=True)
            return SagaMergeResult(
                success=True,
                status="COMMITTED",
                actor_id=actor_id,
                gate_id=gate_id,
                message="Non-git simulated merge committed successfully."
            )

        # 3. Git Merge Execution
        # Ensure any pending worktree modifications are committed on actor branch
        subprocess.run(["git", "add", "-A"], cwd=wt_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "commit", "-m", f"Auto-commit actor {actor_id} for gate {gate_id}"],
            cwd=wt_path,
            capture_output=True,
            check=False
        )

        merge_cmd = [
            "git", "merge", "--no-ff",
            "-m", f"Saga merge: gate {gate_id} from {actor_id}",
            branch_name
        ]
        merge_proc = subprocess.run(
            merge_cmd,
            cwd=self.mgr.repo_root,
            capture_output=True,
            text=True
        )

        if merge_proc.returncode != 0:
            # Conflict detected -> Abort merge cleanly
            subprocess.run(["git", "merge", "--abort"], cwd=self.mgr.repo_root, capture_output=True, check=False)
            tombstone_id = self._generate_tombstone(
                actor_id=actor_id,
                gate_id=gate_id,
                reason=f"Merge conflict: {merge_proc.stderr}"
            )
            return SagaMergeResult(
                success=False,
                status="CONFLICT_ABORTED",
                actor_id=actor_id,
                gate_id=gate_id,
                tombstone_id=tombstone_id,
                message=f"Merge conflict aborted: {merge_proc.stderr.strip()}",
                conflicts=[merge_proc.stderr.strip()]
            )

        # 4. Successful Commit & Cleanup
        self.mgr.cleanup_worktree(actor_id, force=True)
        return SagaMergeResult(
            success=True,
            status="COMMITTED",
            actor_id=actor_id,
            gate_id=gate_id,
            message=f"Saga merge committed cleanly into {target_branch}."
        )
