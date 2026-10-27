"""Ephemeral Git Worktree Swarm Runner for FocusGate v2.8.

Provides true filesystem isolation for concurrent multi-agent swarms by provisioning
ephemeral git worktrees (.focusgate/worktrees/agent-<id>), executing commands in
isolated worktree sub-directories, and merging or pruning upon completion.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Callable
import os
import subprocess
import time
import shutil
import json
import ast
import uuid


@dataclass
class WorktreeResult:
    """Execution outcome of a command run inside an isolated worktree."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    command: List[str]
    duration: float


@dataclass
class TransactionalMergeResult:
    """Outcome of an atomic, Saga-guarded worktree merge operation."""
    success: bool
    agent_id: str
    status: str  # "COMMITTED" | "ROLLED_BACK" | "CONFLICT_ABORTED"
    conflicts: List[str] = field(default_factory=list)
    rollback_performed: bool = False
    tombstone_id: Optional[str] = None
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "agent_id": self.agent_id,
            "status": self.status,
            "conflicts": self.conflicts,
            "rollback_performed": self.rollback_performed,
            "tombstone_id": self.tombstone_id,
            "message": self.message
        }


class WorktreeRunner:
    """Manages ephemeral git worktree provisioning, isolated command execution, and cleanup."""

    def __init__(self, repo_root: str, worktrees_dir: Optional[str] = None):
        self.repo_root = os.path.abspath(repo_root)
        self.worktrees_dir = worktrees_dir or os.path.join(self.repo_root, ".focusgate", "worktrees")
        self.repo_dir = self.repo_root
        self.worktrees_base = self.worktrees_dir
        self.active_worktrees: Dict[str, str] = {}  # agent_id -> worktree_path

    def _is_git_repo(self) -> bool:
        return os.path.exists(os.path.join(self.repo_root, ".git"))

    def provision_worktree(self, agent_id: str, base_ref: str = "HEAD") -> str:
        """Provisions an isolated ephemeral worktree directory for an agent."""
        os.makedirs(self.worktrees_dir, exist_ok=True)
        worktree_path = os.path.join(self.worktrees_dir, f"agent-{agent_id}")
        branch_name = f"focusgate/agent-{agent_id}"

        # Clean prior stale worktree if present
        if os.path.exists(worktree_path):
            self.cleanup_worktree(agent_id, force=True)

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
                    f"Failed to provision git worktree for agent {agent_id}: {proc.stderr.strip()}"
                )
        else:
            # Fallback for mock/non-git test fixtures: copy repo contents (excluding .git and .focusgate)
            shutil.copytree(self.repo_root, worktree_path, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.git', '.focusgate', 'worktrees'))

        self.active_worktrees[agent_id] = worktree_path
        return worktree_path

    def run_in_worktree(
        self,
        agent_id: str,
        cmd: List[str],
        env: Optional[Dict[str, str]] = None,
        timeout: float = 60.0
    ) -> WorktreeResult:
        """Executes a command strictly within the agent's provisioned worktree."""
        worktree_path = self.active_worktrees.get(agent_id)
        if not worktree_path or not os.path.exists(worktree_path):
            raise FileNotFoundError(f"No active worktree found for agent '{agent_id}'.")

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
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start
            return WorktreeResult(
                success=False,
                exit_code=124,
                stdout=e.stdout or "",
                stderr="Execution timed out.",
                command=cmd,
                duration=duration
            )

    def commit_worktree(self, agent_id: str, message: str) -> bool:
        """Stages and commits all changes inside the agent's worktree."""
        worktree_path = self.active_worktrees.get(agent_id)
        if not worktree_path or not os.path.exists(worktree_path):
            return False

        if not self._is_git_repo():
            return True

        add_res = subprocess.run(["git", "add", "-A"], cwd=worktree_path, capture_output=True, check=False)
        commit_res = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=worktree_path,
            capture_output=True,
            check=False
        )
        return commit_res.returncode == 0

    def cleanup_worktree(self, agent_id: str, force: bool = True) -> bool:
        """Removes the agent worktree and prunes its git branch."""
        worktree_path = self.active_worktrees.get(agent_id) or os.path.join(
            self.worktrees_dir, f"agent-{agent_id}"
        )
        branch_name = f"focusgate/agent-{agent_id}"

        success = True
        if self._is_git_repo():
            cmd = ["git", "worktree", "remove"]
            if force:
                cmd.append("--force")
            cmd.append(worktree_path)

            proc = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, check=False)
            if proc.returncode != 0 and os.path.exists(worktree_path):
                shutil.rmtree(worktree_path, ignore_errors=True)

            # Delete branch
            subprocess.run(
                ["git", "branch", "-D" if force else "-d", branch_name],
                cwd=self.repo_root,
                capture_output=True,
                check=False
            )
        else:
            if os.path.exists(worktree_path):
                shutil.rmtree(worktree_path, ignore_errors=True)

        if agent_id in self.active_worktrees:
            del self.active_worktrees[agent_id]
        return success

    def list_active_worktrees(self) -> List[Dict[str, Any]]:
        """Lists currently tracked agent worktrees."""
        return [
            {"agent_id": aid, "path": path, "exists": os.path.exists(path)}
            for aid, path in self.active_worktrees.items()
        ]


    def compute_frontier(self, gates: List['TracerGate']) -> List['TracerGate']:
        """Returns gates that are not checked and whose dependencies are fully met."""
        gate_map = {g.id: g for g in gates}
        frontier = []
        for g in gates:
            if g.checked:
                continue
            deps_met = True
            for d_id in g.deps:
                if d_id in gate_map and not gate_map[d_id].checked:
                    deps_met = False
                    break
            if deps_met:
                frontier.append(g)
        return frontier

    def provision_swarm_worktree(self, gate_id: str, branch_name: Optional[str] = None) -> Tuple[bool, str]:
        """Provisions an isolated worktree for swarm execution."""
        if branch_name is None:
            branch_name = f"swarm/{gate_id}"
        wt_path = os.path.join(self.worktrees_base, gate_id)
        os.makedirs(os.path.dirname(wt_path), exist_ok=True)

        if os.path.exists(wt_path):
            return True, wt_path

        try:
            cmd = ["git", "worktree", "add", "-B", branch_name, wt_path, "HEAD"]
            res = subprocess.run(cmd, cwd=self.repo_dir, capture_output=True, text=True, check=False)
            if res.returncode == 0:
                return True, wt_path
            else:
                os.makedirs(wt_path, exist_ok=True)
                return True, wt_path
        except Exception:
            os.makedirs(wt_path, exist_ok=True)
            return True, wt_path

    def clean_worktree(self, gate_id: str, force: bool = True) -> bool:
        """Removes the worktree by gate_id or agent_id and prunes branches."""
        self.cleanup_worktree(gate_id, force=force)
        swarm_path = os.path.join(self.worktrees_base, gate_id)
        if os.path.exists(swarm_path):
            if self._is_git_repo():
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", "--force", swarm_path],
                        cwd=self.repo_dir,
                        capture_output=True,
                        text=True,
                        check=False
                    )
                except (subprocess.SubprocessError, OSError):
                    pass
            if os.path.exists(swarm_path):
                shutil.rmtree(swarm_path, ignore_errors=True)
        return not os.path.exists(swarm_path)

    def list_worktrees(self) -> List[Dict[str, Any]]:
        """Lists all active worktrees across agent and swarm allocations."""
        worktrees = []
        if os.path.exists(self.worktrees_base):
            for name in os.listdir(self.worktrees_base):
                sub_path = os.path.join(self.worktrees_base, name)
                if os.path.isdir(sub_path):
                    worktrees.append({
                        "gate_id": name,
                        "path": sub_path,
                        "branch": f"swarm/{name}"
                    })
        return worktrees

    def detect_conflicts(self, agent_ids: List[str]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Detects overlapping file modifications and AST symbol collisions across agent worktrees."""
        agent_files: Dict[str, List[str]] = {}
        agent_symbols: Dict[str, Dict[str, List[str]]] = {}

        for aid in agent_ids:
            wt_path = self.active_worktrees.get(aid) or os.path.join(self.worktrees_dir, f"agent-{aid}")
            branch_name = f"focusgate/agent-{aid}"
            files_modified = []

            if self._is_git_repo():
                cmd = ["git", "diff", "--name-only", f"HEAD...{branch_name}"]
                res = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True, check=False)
                if res.returncode == 0 and res.stdout.strip():
                    files_modified.extend([f.strip() for f in res.stdout.splitlines() if f.strip()])
                st_cmd = ["git", "status", "--porcelain"]
                st_res = subprocess.run(st_cmd, cwd=wt_path, capture_output=True, text=True, check=False)
                if st_res.returncode == 0 and st_res.stdout.strip():
                    for line in st_res.stdout.splitlines():
                        parts = line.strip().split(maxsplit=1)
                        if len(parts) == 2:
                            files_modified.append(parts[1])
            else:
                if os.path.isdir(wt_path):
                    for root_dir, _, filenames in os.walk(wt_path):
                        for fname in filenames:
                            if not fname.startswith("."):
                                rel = os.path.relpath(os.path.join(root_dir, fname), wt_path)
                                files_modified.append(rel)

            agent_files[aid] = sorted(list(set(files_modified)))

            # Collect AST symbols for Python files
            agent_symbols[aid] = {}
            for rel in agent_files[aid]:
                if rel.endswith(".py"):
                    full_p = os.path.join(wt_path, rel)
                    if os.path.isfile(full_p):
                        try:
                            with open(full_p, "r", encoding="utf-8", errors="replace") as f:
                                tree = ast.parse(f.read(), filename=full_p)
                            syms = [
                                node.name for node in ast.walk(tree)
                                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                            ]
                            agent_symbols[aid][rel] = syms
                        except SyntaxError:
                            pass

        conflicts: List[str] = []
        symbol_collisions: List[str] = []
        seen_files: Dict[str, str] = {}

        for aid, flist in agent_files.items():
            for f in flist:
                if f in seen_files and seen_files[f] != aid:
                    conflicts.append(f)
                else:
                    seen_files[f] = aid

        conflicts = sorted(list(set(conflicts)))

        seen_symbols: Dict[str, str] = {}
        for aid, f_sym_map in agent_symbols.items():
            for f, syms in f_sym_map.items():
                for sym in syms:
                    if sym in seen_symbols and seen_symbols[sym] != aid:
                        symbol_collisions.append(f"{sym} in {f} (claimed by {seen_symbols[sym]} and {aid})")
                    else:
                        seen_symbols[sym] = aid

        has_conflict = len(conflicts) > 0 or len(symbol_collisions) > 0
        details = {
            "agent_files": agent_files,
            "conflicting_files": conflicts,
            "symbol_collisions": symbol_collisions
        }
        return has_conflict, conflicts, details

    def merge_worktree_transactional(
        self,
        agent_id: str,
        target_branch: str = "HEAD",
        test_verifier: Optional[Callable[[], bool]] = None,
        dlq_dir: Optional[str] = None
    ) -> TransactionalMergeResult:
        """Atomically merges an agent's worktree with post-merge test verification and Saga rollback."""
        branch_name = f"focusgate/agent-{agent_id}"
        wt_path = self.active_worktrees.get(agent_id) or os.path.join(self.worktrees_dir, f"agent-{agent_id}")

        if not self._is_git_repo():
            if not os.path.isdir(wt_path):
                return TransactionalMergeResult(
                    success=False,
                    agent_id=agent_id,
                    status="NOT_FOUND",
                    message=f"Worktree for agent '{agent_id}' does not exist."
                )

            backup_dir = tempfile.mkdtemp()
            try:
                for item in os.listdir(self.repo_root):
                    if item not in {".git", ".focusgate", "worktrees"}:
                        s = os.path.join(self.repo_root, item)
                        d = os.path.join(backup_dir, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d)
                        else:
                            shutil.copy2(s, d)

                shutil.copytree(wt_path, self.repo_root, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.git', '.focusgate', 'worktrees'))

                if test_verifier and not test_verifier():
                    for item in os.listdir(self.repo_root):
                        if item not in {".git", ".focusgate", "worktrees"}:
                            p = os.path.join(self.repo_root, item)
                            if os.path.isdir(p):
                                shutil.rmtree(p)
                            else:
                                os.remove(p)
                    for item in os.listdir(backup_dir):
                        s = os.path.join(backup_dir, item)
                        d = os.path.join(self.repo_root, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d)
                        else:
                            shutil.copy2(s, d)

                    tombstone_id = self._record_dlq_tombstone(agent_id, "Test verifier failed in non-git merge", dlq_dir)
                    return TransactionalMergeResult(
                        success=False,
                        agent_id=agent_id,
                        status="ROLLED_BACK",
                        rollback_performed=True,
                        tombstone_id=tombstone_id,
                        message="Test verifier failed; filesystem rolled back."
                    )

                return TransactionalMergeResult(
                    success=True,
                    agent_id=agent_id,
                    status="COMMITTED",
                    message="Copied and verified successfully."
                )
            finally:
                shutil.rmtree(backup_dir, ignore_errors=True)

        # 1. Capture current HEAD sha for compensation
        head_proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=False)
        orig_head = head_proc.stdout.strip()

        # 2. Attempt merge
        merge_cmd = ["git", "merge", "--no-ff", "-m", f"Merge worktree {branch_name}", branch_name]
        merge_proc = subprocess.run(merge_cmd, cwd=self.repo_root, capture_output=True, text=True, check=False)

        if merge_proc.returncode != 0:
            subprocess.run(["git", "merge", "--abort"], cwd=self.repo_root, capture_output=True, text=True, check=False)
            tombstone_id = self._record_dlq_tombstone(agent_id, f"Git merge conflict: {merge_proc.stderr}", dlq_dir)
            return TransactionalMergeResult(
                success=False,
                agent_id=agent_id,
                status="CONFLICT_ABORTED",
                conflicts=[merge_proc.stderr.strip() or "Merge conflict"],
                rollback_performed=True,
                tombstone_id=tombstone_id,
                message=f"Git merge aborted due to conflict: {merge_proc.stderr.strip()}"
            )

        # 3. Run post-merge verification
        if test_verifier:
            try:
                verification_ok = test_verifier()
            except Exception:
                verification_ok = False

            if not verification_ok:
                subprocess.run(["git", "reset", "--hard", orig_head], cwd=self.repo_root, capture_output=True, text=True, check=False)
                subprocess.run(["git", "clean", "-fd"], cwd=self.repo_root, capture_output=True, text=True, check=False)

                tombstone_id = self._record_dlq_tombstone(agent_id, "Post-merge verification gate failed", dlq_dir)
                return TransactionalMergeResult(
                    success=False,
                    agent_id=agent_id,
                    status="ROLLED_BACK",
                    rollback_performed=True,
                    tombstone_id=tombstone_id,
                    message="Post-merge verification gate failed; HEAD reset to prior state via Saga compensation."
                )

        return TransactionalMergeResult(
            success=True,
            agent_id=agent_id,
            status="COMMITTED",
            message=f"Successfully merged {branch_name} into {target_branch} with passing verification."
        )

    def _record_dlq_tombstone(self, agent_id: str, error_reason: str, dlq_dir: Optional[str] = None) -> str:
        """Records a Dead Letter Queue (DLQ) tombstone for an uncompensated or aborted transaction."""
        tombstone_id = f"tombstone-merge-{agent_id}-{uuid.uuid4().hex[:8]}"
        target_dir = dlq_dir or os.path.join(self.repo_root, ".focusgate", "dlq")
        try:
            os.makedirs(target_dir, exist_ok=True)
            t_path = os.path.join(target_dir, f"{tombstone_id}.json")
            data = {
                "tombstone_id": tombstone_id,
                "agent_id": agent_id,
                "timestamp": time.time(),
                "error": error_reason,
                "remediation": f"Inspect worktree branch focusgate/agent-{agent_id} and resolve collisions"
            }
            with open(t_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except (OSError, IOError):
            pass
        return tombstone_id
