"""FocusGate v3.0 — Actor Ephemeral Worktree Manager.

Provides true filesystem isolation for concurrent swarm actors by dynamically
allocating ephemeral git worktrees (.focusgate/worktrees/actor-<id>), executing
commands in isolated sub-environments, and safely pruning on completion.

Zero external dependencies (100% Python stdlib).
"""

import os
import sys
import time
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class WorktreeResult:
    """Execution outcome of a command run inside an isolated actor worktree."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    command: List[str]
    duration: float

    def to_dict(self) -> Dict[str, Any]:
        """Serializes result to dictionary."""
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "command": self.command,
            "duration": round(self.duration, 4)
        }


class ActorWorktreeManager:
    """Manages ephemeral git worktree provisioning, execution, and cleanup per swarm actor."""

    def __init__(self, repo_root: Optional[str] = None, worktrees_dir: Optional[str] = None):
        self.repo_root = os.path.abspath(repo_root or os.getcwd())
        self.worktrees_dir = os.path.abspath(worktrees_dir or os.path.join(self.repo_root, ".focusgate", "worktrees"))
        self.active_worktrees: Dict[str, str] = {}

    def _is_git_repo(self) -> bool:
        """Determines if repo_root is inside a valid git repository."""
        return os.path.exists(os.path.join(self.repo_root, ".git"))

    def provision_worktree(self, actor_id: str, base_ref: str = "HEAD") -> str:
        """Provisions an isolated ephemeral worktree directory for a specific actor."""
        os.makedirs(self.worktrees_dir, exist_ok=True)
        sanitized_id = actor_id.replace("/", "_").replace("\\", "_")
        worktree_path = os.path.join(self.worktrees_dir, f"actor-{sanitized_id}")
        branch_name = f"focusgate/actor-{sanitized_id}"

        # Clean prior stale worktree if present
        if os.path.exists(worktree_path):
            self.cleanup_worktree(actor_id, force=True)

        if self._is_git_repo():
            cmd = ["git", "worktree", "add", "-B", branch_name, worktree_path, base_ref]
            proc = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False
            )
            if proc.returncode != 0 and not os.path.exists(worktree_path):
                raise RuntimeError(
                    f"Failed to provision git worktree for actor {actor_id}: {proc.stderr.strip()}"
                )
        else:
            # Fallback for mock/non-git fixtures: copy repo contents excluding .git and .focusgate
            shutil.copytree(
                self.repo_root,
                worktree_path,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('.git', '.focusgate', 'worktrees')
            )

        self.active_worktrees[actor_id] = worktree_path
        return worktree_path

    def get_worktree_path(self, actor_id: str) -> Optional[str]:
        """Returns active worktree path if provisioned and on disk."""
        path = self.active_worktrees.get(actor_id)
        if path and os.path.isdir(path):
            return path
        candidate = os.path.join(self.worktrees_dir, f"actor-{actor_id}")
        if os.path.isdir(candidate):
            self.active_worktrees[actor_id] = candidate
            return candidate
        return None

    def run_in_worktree(
        self,
        actor_id: str,
        cmd: List[str],
        env: Optional[Dict[str, str]] = None,
        timeout: float = 60.0
    ) -> WorktreeResult:
        """Executes a command strictly within the actor's provisioned worktree."""
        worktree_path = self.get_worktree_path(actor_id)
        if not worktree_path:
            raise FileNotFoundError(f"No active worktree provisioned for actor '{actor_id}'.")

        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        start = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=worktree_path,
                env=merged_env,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            duration = time.time() - start
            return WorktreeResult(
                success=(proc.returncode == 0),
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                command=cmd,
                duration=duration
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.time() - start
            return WorktreeResult(
                success=False,
                exit_code=124,
                stdout=exc.stdout or "",
                stderr="Execution timed out.",
                command=cmd,
                duration=duration
            )
        except OSError as exc:
            duration = time.time() - start
            return WorktreeResult(
                success=False,
                exit_code=127,
                stdout="",
                stderr=f"Command execution failed: {exc}",
                command=cmd,
                duration=duration
            )

    def cleanup_worktree(self, actor_id: str, force: bool = True) -> bool:
        """Removes the worktree and cleans up its tracking branch."""
        sanitized_id = actor_id.replace("/", "_").replace("\\", "_")
        worktree_path = self.active_worktrees.get(actor_id) or os.path.join(self.worktrees_dir, f"actor-{sanitized_id}")
        branch_name = f"focusgate/actor-{sanitized_id}"

        if self._is_git_repo():
            subprocess.run(
                ["git", "worktree", "remove", "--force", worktree_path],
                cwd=self.repo_root,
                capture_output=True,
                check=False
            )
            subprocess.run(
                ["git", "worktree", "prune"],
                cwd=self.repo_root,
                capture_output=True,
                check=False
            )
            if force:
                subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    cwd=self.repo_root,
                    capture_output=True,
                    check=False
                )

        if os.path.exists(worktree_path):
            shutil.rmtree(worktree_path, ignore_errors=True)

        self.active_worktrees.pop(actor_id, None)
        return not os.path.exists(worktree_path)

    def cleanup_all(self, force: bool = True) -> None:
        """Prunes all active and orphaned actor worktrees."""
        for actor_id in list(self.active_worktrees.keys()):
            self.cleanup_worktree(actor_id, force=force)

        if os.path.isdir(self.worktrees_dir):
            try:
                for entry in os.listdir(self.worktrees_dir):
                    if entry.startswith("actor-"):
                        full_p = os.path.join(self.worktrees_dir, entry)
                        if os.path.isdir(full_p):
                            shutil.rmtree(full_p, ignore_errors=True)
            except OSError:
                pass
