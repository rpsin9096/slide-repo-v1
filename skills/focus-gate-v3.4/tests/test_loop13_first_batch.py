"""Tests for FocusGate v2.8.5 — Milestone 10 (Loop 13: The First Batch of Fixes).

Covers:
1. Worktree Runner seam sanitization and legacy purge.
2. AST Syntax Pre-Flight Guard in ToolSelectionMatrix.
3. Template Engine decoupling and filesystem registry.
4. Monorepo workspace detection in WorkspaceDetector.
"""

import unittest
import os
import tempfile
import shutil
import json

from core.worktree_runner import WorktreeRunner
from core.tool_matrix import ToolSelectionMatrix, ASTSyntaxPreflightGuard
from core.template_engine import TemplateEngine
from core.workspace_detector import WorkspaceDetector


class TestWorktreeRunnerSanitization(unittest.TestCase):
    """Verifies that WorktreeRunner seam has been sanitized of legacy artifacts."""

    def test_no_init_wso_legacy_method(self):
        w = WorktreeRunner(".")
        self.assertFalse(hasattr(w, "__init_wso__"), "WorktreeRunner should not have legacy __init_wso__ method.")

    def test_no_candidate_comment_in_source(self):
        src_path = os.path.join(os.path.dirname(__file__), "..", "core", "worktree_runner.py")
        with open(src_path, "r", encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("Candidate 3: Smart-Zone", src, "WorktreeRunner should not contain dead Candidate 3 comment.")

    def test_clean_worktree_unification(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            w = WorktreeRunner(tmp_dir)
            gate_id = "test-unify-gate"
            wt_path = os.path.join(w.worktrees_dir, f"agent-{gate_id}")
            os.makedirs(wt_path, exist_ok=True)
            self.assertTrue(os.path.exists(wt_path))
            
            res = w.clean_worktree(gate_id)
            self.assertTrue(res)
            self.assertFalse(os.path.exists(wt_path))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


class TestASTSyntaxPreflightGuard(unittest.TestCase):
    """Verifies in-memory AST syntax validation during patch pre-condition verification."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.matrix = ToolSelectionMatrix(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_python_syntax_error_rejected(self):
        py_file = os.path.join(self.tmp_dir, "broken.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write("def foo():\n    return 1\n")

        check = self.matrix.verify_patch_preconditions(
            target_path="broken.py",
            search_block="    return 1\n",
            replacement_block="    def broken(:\n"
        )
        self.assertFalse(check.valid, "Syntax-breaking patch should be rejected.")
        self.assertIn("AST Pre-Flight Rejection", check.reason)
        self.assertIn("SyntaxError", check.reason)

    def test_json_syntax_error_rejected(self):
        json_file = os.path.join(self.tmp_dir, "config.json")
        with open(json_file, "w", encoding="utf-8") as f:
            f.write('{\n  "key": "value"\n}\n')

        check = self.matrix.verify_patch_preconditions(
            target_path="config.json",
            search_block='  "key": "value"\n',
            replacement_block='  "key": "value",,\n'
        )
        self.assertFalse(check.valid, "Malformed JSON patch should be rejected.")
        self.assertIn("AST Pre-Flight Rejection", check.reason)
        self.assertIn("JSONDecodeError", check.reason)

    def test_bracket_mismatch_rejected_in_typescript(self):
        ts_file = os.path.join(self.tmp_dir, "component.tsx")
        with open(ts_file, "w", encoding="utf-8") as f:
            f.write("export const App = () => {\n  return <div>Hello</div>;\n};\n")

        check = self.matrix.verify_patch_preconditions(
            target_path="component.tsx",
            search_block="  return <div>Hello</div>;\n",
            replacement_block="  return <div>Hello</div>;\n  {\n"  # dangling open brace
        )
        self.assertFalse(check.valid, "Mismatched brace patch in TypeScript should be rejected.")
        self.assertIn("AST Pre-Flight Rejection", check.reason)
        self.assertIn("Unbalanced", check.reason)

    def test_valid_python_patch_accepted(self):
        py_file = os.path.join(self.tmp_dir, "valid.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write("def calculate(x):\n    return x\n")

        check = self.matrix.verify_patch_preconditions(
            target_path="valid.py",
            search_block="    return x\n",
            replacement_block="    return x * 2\n"
        )
        self.assertTrue(check.valid, "Syntactically valid patch should pass pre-flight.")
        self.assertTrue(check.exact_match_found)


class TestTemplateEngineDecoupling(unittest.TestCase):
    """Verifies that TemplateEngine loads on-disk templates from templates/."""

    def test_template_engine_lists_templates(self):
        engine = TemplateEngine()
        templates = engine.list_templates()
        self.assertGreater(len(templates), 10, "TemplateEngine should discover registered templates on disk.")
        self.assertIn("AGENT-BRIEF.template.md", templates)

    def test_template_engine_loads_and_renders(self):
        engine = TemplateEngine()
        content = engine.get_template("AGENT-BRIEF.template.md")
        self.assertIsInstance(content, str)
        self.assertIn("{gate_id}", content)

    def test_template_engine_render_substitutions(self):
        engine = TemplateEngine()
        rendered = engine.render("AGENT-BRIEF.template.md", gate_id="TASK-99", task_title="Verify test engine")
        self.assertIn("TASK-99", rendered)
        self.assertIn("Verify test engine", rendered)


class TestMonorepoWorkspaceDetection(unittest.TestCase):
    """Verifies that WorkspaceDetector discovers monorepo structures."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_detect_pnpm_monorepo(self):
        with open(os.path.join(self.tmp_dir, "pnpm-workspace.yaml"), "w", encoding="utf-8") as f:
            f.write("packages:\n  - 'apps/*'\n  - 'packages/*'\n")
        
        info = WorkspaceDetector.detect_monorepo(self.tmp_dir)
        self.assertTrue(info["is_monorepo"])
        self.assertEqual(info["monorepo_type"], "pnpm")

    def test_detect_cargo_workspace(self):
        with open(os.path.join(self.tmp_dir, "Cargo.toml"), "w", encoding="utf-8") as f:
            f.write("[workspace]\nmembers = [\"core\", \"cli\"]\n")

        info = WorkspaceDetector.detect_monorepo(self.tmp_dir)
        self.assertTrue(info["is_monorepo"])
        self.assertEqual(info["monorepo_type"], "cargo")

    def test_detect_go_work(self):
        with open(os.path.join(self.tmp_dir, "go.work"), "w", encoding="utf-8") as f:
            f.write("go 1.22\n\nuse (\n\t./service\n)\n")

        info = WorkspaceDetector.detect_monorepo(self.tmp_dir)
        self.assertTrue(info["is_monorepo"])
        self.assertEqual(info["monorepo_type"], "go")

    def test_detect_non_monorepo(self):
        with open(os.path.join(self.tmp_dir, "pyproject.toml"), "w", encoding="utf-8") as f:
            f.write("[project]\nname = 'single-pkg'\n")

        info = WorkspaceDetector.detect_monorepo(self.tmp_dir)
        self.assertFalse(info["is_monorepo"])


if __name__ == "__main__":
    unittest.main()
