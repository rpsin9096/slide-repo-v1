"""FocusGate v2.9 — Reactive In-Memory Daemon & File Watcher.

Continuously tracks workspace source modifications, maintains an in-memory
AST cache, and re-evaluates stage verification matrix gates in <15ms.

Operates with zero external dependencies (100% Python standard library).
"""

import os
import sys
import time
import ast
import json
import signal
import threading
from typing import Dict, Any, List, Optional, Tuple, Callable


class FocusDaemon:
    """Reactive background daemon monitoring source files and caching ASTs."""

    IGNORED_DIRS = {
        ".git", "__pycache__", ".focusgate", "node_modules",
        "venv", ".venv", "dist", "build", ".pytest_cache", ".gemini"
    }

    TRACKED_EXTENSIONS = {
        ".py", ".ts", ".tsx", ".js", ".jsx", ".rs",
        ".go", ".json", ".md", ".css", ".html"
    }

    def __init__(self, workspace_root: Optional[str] = None, poll_interval: float = 0.2):
        self.workspace_root = os.path.abspath(workspace_root or os.getcwd())
        self.poll_interval = poll_interval
        self.file_snapshots: Dict[str, float] = {}
        self.ast_cache: Dict[str, Tuple[float, Any]] = {}
        self.running: bool = False
        self._initialized: bool = False
        self._thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable[[str, str], None]] = []

    def scan_snapshot(self) -> Dict[str, float]:
        """Scans workspace source files and returns mapping of relative path to mtime."""
        snapshot: Dict[str, float] = {}
        if not os.path.isdir(self.workspace_root):
            return snapshot

        for root, dirs, files in os.walk(self.workspace_root):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS and not d.startswith(".")]

            for fn in files:
                ext = os.path.splitext(fn)[1].lower()
                if ext in self.TRACKED_EXTENSIONS:
                    abs_path = os.path.join(root, fn)
                    rel_path = os.path.relpath(abs_path, self.workspace_root)
                    try:
                        snapshot[rel_path] = os.path.getmtime(abs_path)
                    except OSError:
                        pass
        return snapshot

    def get_cached_ast(self, rel_path: str) -> Optional[Any]:
        """Returns in-memory parsed AST for Python files with cache hit or re-parse on mutation."""
        abs_path = os.path.join(self.workspace_root, rel_path)
        if not os.path.isfile(abs_path) or not rel_path.endswith(".py"):
            return None

        try:
            mtime = os.path.getmtime(abs_path)
        except OSError:
            return None

        if rel_path in self.ast_cache:
            cached_mtime, cached_tree = self.ast_cache[rel_path]
            if cached_mtime == mtime:
                return cached_tree

        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            tree = ast.parse(content, filename=rel_path)
            self.ast_cache[rel_path] = (mtime, tree)
            return tree
        except (SyntaxError, OSError):
            return None

    def check_changes(self) -> List[Tuple[str, str]]:
        """Compares current file mtimes against snapshot and detects modifications, creations, deletions."""
        current_snapshot = self.scan_snapshot()
        changes: List[Tuple[str, str]] = []

        if not self._initialized:
            self.file_snapshots = current_snapshot
            self._initialized = True
            return changes

        # Check creations and modifications
        for path, mtime in current_snapshot.items():
            if path not in self.file_snapshots:
                changes.append((path, "CREATED"))
            elif mtime != self.file_snapshots[path]:
                changes.append((path, "MODIFIED"))

        # Check deletions
        for path in self.file_snapshots:
            if path not in current_snapshot:
                changes.append((path, "DELETED"))
                if path in self.ast_cache:
                    del self.ast_cache[path]

        self.file_snapshots = current_snapshot
        return changes

    def tick(self) -> Dict[str, Any]:
        """Executes a single polling cycle: detects changes, updates ASTs, evaluates gates."""
        t0 = time.perf_counter()
        changes = self.check_changes()
        syntax_clean = True
        syntax_errors: Dict[str, str] = {}

        from core.tool_matrix import ASTSyntaxPreflightGuard

        for path, event in changes:
            if event in ("CREATED", "MODIFIED"):
                abs_p = os.path.join(self.workspace_root, path)
                if os.path.isfile(abs_p):
                    try:
                        with open(abs_p, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                        valid, err = ASTSyntaxPreflightGuard.validate_syntax(path, content)
                        if not valid:
                            syntax_clean = False
                            syntax_errors[path] = err
                        elif path.endswith(".py"):
                            # Update AST cache on valid Python code
                            mtime = self.file_snapshots.get(path, time.time())
                            try:
                                tree = ast.parse(content, filename=path)
                                self.ast_cache[path] = (mtime, tree)
                            except SyntaxError:
                                pass
                    except OSError as exc:
                        syntax_clean = False
                        syntax_errors[path] = str(exc)

            for cb in self.callbacks:
                try:
                    cb(path, event)
                except (ValueError, TypeError, RuntimeError, OSError):
                    pass

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "changes": changes,
            "syntax_clean": syntax_clean,
            "syntax_errors": syntax_errors,
            "latency_ms": latency_ms,
            "tracked_files": len(self.file_snapshots)
        }

    def start_background(self) -> None:
        """Starts the watcher loop in a background daemon thread."""
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self) -> None:
        while self.running:
            self.tick()
            time.sleep(self.poll_interval)

    def stop(self) -> None:
        """Halts the watcher loop cleanly."""
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def run_foreground(self, max_ticks: Optional[int] = None) -> None:
        """Runs the watcher loop synchronously in foreground until interrupted or max_ticks reached."""
        self.running = True
        print(f"[FocusGate v2.9] Reactive Daemon active on: {self.workspace_root}")
        print("Monitoring source files (<15ms in-memory AST gate re-evaluation). Press Ctrl+C to stop.")

        def _handle_signal(sig, frame):
            print("\n[FocusGate v2.9] Gracefully shutting down reactive daemon...")
            self.running = False

        original_sigint = signal.signal(signal.SIGINT, _handle_signal)
        ticks = 0

        try:
            while self.running:
                cycle = self.tick()
                changes = cycle.get("changes", [])
                if changes:
                    for p, ev in changes:
                        print(f"  [{ev}] {p} (eval: {cycle['latency_ms']:.2f}ms)")
                    if not cycle.get("syntax_clean"):
                        for p, err in cycle.get("syntax_errors", {}).items():
                            print(f"    SYNTAX_ERROR in {p}: {err}", file=sys.stderr)

                ticks += 1
                if max_ticks is not None and ticks >= max_ticks:
                    break
                time.sleep(self.poll_interval)
        finally:
            signal.signal(signal.SIGINT, original_sigint)
