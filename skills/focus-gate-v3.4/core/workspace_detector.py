"""FocusGate v2.8.1 — Workspace Stack & Context Detector.

Fast-path deterministic repository inspection (<3ms) for zero-compute environments.
Detects project language, manifests, and preferred test runners to contextualize Action Envelopes.
100% Pure Python standard library (zero external dependencies).
"""

import os
import re
import json
from typing import Dict, Any, List, Optional


class WorkspaceDetector:
    """Zero-dependency workspace scanner that detects project runtime, test harness, and target files."""

    MANIFEST_PATTERNS = {
        "python": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile", "tox.ini", "pytest.ini"],
        "typescript_node": ["package.json", "tsconfig.json", "deno.json", "bun.lockb", "pnpm-lock.yaml", "yarn.lock"],
        "rust": ["Cargo.toml", "Cargo.lock"],
        "go": ["go.mod", "go.sum"],
    }

    FILE_EXT_PATTERN = re.compile(r"\b([\w\-_./]+\.(?:py|tsx?|jsx?|rs|go|html|css|json|md|sql|ya?ml))\b", re.IGNORECASE)

    # Added in v3.2 Loop 64. The name of the runtime state directory. Every
    # component that roots a workspace must refuse to root it here.
    STATE_DIR = ".focusgate"

    @classmethod
    def resolve_root(cls, start: Optional[str] = None) -> str:
        """The real workspace root for `start`, walking OUT of any state directory.

        The bug this exists to fix: every component resolved its root from
        `os.getcwd()` and then joined `".focusgate"` onto it. Run the CLI from
        inside `.focusgate/sub/` and the root became `.focusgate/sub`, so the
        state directory was created *inside itself* — `.focusgate/sub/
        .focusgate/`, complete with `ledger.events.db`, `-wal` and `-shm`
        sidecars, because `SQLiteStorageAdapter` rewrites a `.jsonl` path to
        `.db` and enables WAL. Each run grew the tree, and the tree was
        committed: 14 of the 34 tracked artifacts were nested inside it.

        Resolution is deliberately conservative. It walks up while the current
        directory is *named* `.focusgate` or is *inside* one, then keeps walking
        up while a parent still looks like the same project. It does not guess
        from a manifest, because a monorepo's real root is the git root, and it
        never returns a path that contains the state directory as a component.
        """
        root = os.path.abspath(start or os.getcwd())

        # 1. Climb out of any state directory, however deep.
        while True:
            parts = root.split(os.sep)
            if cls.STATE_DIR in parts:
                idx = len(parts) - 1 - parts[::-1].index(cls.STATE_DIR)
                root = os.sep if idx <= 1 else os.sep.join(parts[:idx])
                continue
            break

        # 2. Prefer the git root when there is one: it is the only unambiguous
        #    answer for a nested package, and it cannot be a state directory.
        probe = root
        while True:
            if os.path.isdir(os.path.join(probe, ".git")):
                return probe
            parent = os.path.dirname(probe)
            if parent == probe:
                return root
            probe = parent

    @classmethod
    def detect(cls, workspace_root: Optional[str] = None) -> Dict[str, Any]:
        """Detects the primary stack and test runner of a target directory in <3ms.

        `workspace_root=None` resolves the true workspace via `resolve_root()`
        rather than the process cwd, so a run from inside `.focusgate/` audits
        the project instead of the state directory.
        """
        root = cls.resolve_root(workspace_root) if workspace_root is None \
            else os.path.abspath(workspace_root)
        if not os.path.isdir(root):
            return {
                "stack": "generic",
                "test_runner": "git status",
                "manifests": [],
                "root": root
            }

        try:
            top_files = set(os.listdir(root))
        except (OSError, PermissionError):
            top_files = set()

        detected_manifests: List[str] = []
        stack = "generic"
        test_runner = "git status"

        # Check Python
        python_matches = [m for m in cls.MANIFEST_PATTERNS["python"] if m in top_files]
        if python_matches:
            stack = "python"
            detected_manifests.extend(python_matches)
            if "pytest.ini" in top_files or any("pytest" in m for m in python_matches) or "pyproject.toml" in top_files:
                test_runner = "pytest"
            else:
                test_runner = "python3 -m unittest"

        # Check Node / TypeScript
        node_matches = [m for m in cls.MANIFEST_PATTERNS["typescript_node"] if m in top_files]
        if node_matches and stack == "generic":
            stack = "typescript_node"
            detected_manifests.extend(node_matches)
            if "pnpm-lock.yaml" in top_files:
                test_runner = "pnpm test"
            elif "yarn.lock" in top_files:
                test_runner = "yarn test"
            else:
                test_runner = "npm test"

        # Check Rust
        rust_matches = [m for m in cls.MANIFEST_PATTERNS["rust"] if m in top_files]
        if rust_matches and stack == "generic":
            stack = "rust"
            detected_manifests.extend(rust_matches)
            test_runner = "cargo test"

        # Check Go
        go_matches = [m for m in cls.MANIFEST_PATTERNS["go"] if m in top_files]
        if go_matches and stack == "generic":
            stack = "go"
            detected_manifests.extend(go_matches)
            test_runner = "go test ./..."

        return {
            "stack": stack,
            "test_runner": test_runner,
            "manifests": detected_manifests,
            "root": root
        }

    @classmethod
    def extract_target_files(cls, query: str, workspace_root: str = ".") -> List[str]:
        """Extracts referenced file paths from query text that exist within the workspace."""
        matches = cls.FILE_EXT_PATTERN.findall(query)
        if not matches:
            return []

        root = os.path.abspath(workspace_root)
        valid_files = []
        for m in matches:
            clean_path = m.lstrip("/").lstrip("\\")
            full_path = os.path.join(root, clean_path)
            if os.path.exists(full_path):
                valid_files.append(clean_path)
            else:
                # Include basename reference if mentioned specifically
                valid_files.append(clean_path)

        return valid_files

    @classmethod
    def detect_monorepo(cls, workspace_root: str = ".") -> Dict[str, Any]:
        """Detects whether a workspace is a monorepo and identifies its package topology."""
        root = os.path.abspath(workspace_root)
        if not os.path.isdir(root):
            return {"is_monorepo": False, "monorepo_type": "none", "members": []}

        try:
            top_files = set(os.listdir(root))
        except (OSError, PermissionError):
            top_files = set()

        # 1. pnpm-workspace.yaml
        if "pnpm-workspace.yaml" in top_files:
            return {
                "is_monorepo": True,
                "monorepo_type": "pnpm",
                "manifest": "pnpm-workspace.yaml",
                "root": root
            }

        # 2. Cargo.toml workspace
        if "Cargo.toml" in top_files:
            cargo_path = os.path.join(root, "Cargo.toml")
            try:
                with open(cargo_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                if "[workspace]" in content:
                    return {
                        "is_monorepo": True,
                        "monorepo_type": "cargo",
                        "manifest": "Cargo.toml",
                        "root": root
                    }
            except (OSError, IOError):
                pass

        # 3. go.work
        if "go.work" in top_files:
            return {
                "is_monorepo": True,
                "monorepo_type": "go",
                "manifest": "go.work",
                "root": root
            }

        # 4. lerna.json or package.json with workspaces
        if "lerna.json" in top_files:
            return {
                "is_monorepo": True,
                "monorepo_type": "lerna",
                "manifest": "lerna.json",
                "root": root
            }

        if "package.json" in top_files:
            pkg_path = os.path.join(root, "package.json")
            try:
                with open(pkg_path, "r", encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "workspaces" in data:
                    return {
                        "is_monorepo": True,
                        "monorepo_type": "npm_workspaces",
                        "manifest": "package.json",
                        "root": root
                    }
            except (OSError, IOError, json.JSONDecodeError, ValueError, KeyError):
                pass

        return {"is_monorepo": False, "monorepo_type": "none", "members": []}
