"""Tests for FocusGate v2.9 — Milestone 18 (Loop 21: Autonomous Self-Healing Remediation Loops).

Covers:
1. Error classification and prescriptive remedy correlation (Python, TypeScript, Rust, Syntax).
2. Autonomous code remediation patch synthesis.
3. End-to-end gate healing with verifier re-execution on isolated worktree.
4. Circuit breaker enforcement: 3 failed attempts trip circuit and escalate to DLQ.
5. CLI --heal flag registration and execution.
"""

import unittest
import os
import sys
import subprocess
import json
import tempfile

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
SCRIPT = os.path.join(ROOT_DIR, "scripts", "focus-gate.py")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.self_healing import SelfHealingCoordinator, FailureDiagnosis, HealAttemptReceipt



class TestDiagnosisAndRemediation(unittest.TestCase):
    """Verifies failure classification and remedy matching."""

    def setUp(self):
        self.coordinator = SelfHealingCoordinator(workspace_root=ROOT_DIR)

    def test_diagnose_python_shotgun_suppression(self):
        code = "def process():\n    try:\n        do_work()\n    except Exception:\n        pass\n"
        diag = self.coordinator.diagnose_failure(
            error_output="Verification failed: Code cliché detected",
            code_content=code,
            filename="processor.py"
        )
        self.assertEqual(diag.category, "SHOTGUN_SUPPRESSION")
        self.assertIn("except", diag.prescribed_remedy)
        self.assertIsNotNone(diag.remediation_patch)
        self.assertIn("search", diag.remediation_patch)
        self.assertIn("replace", diag.remediation_patch)

    def test_diagnose_ts_shotgun_catch(self):
        code = "export function api() {\n    try {\n        fetch();\n    } catch (err) {}\n}\n"
        diag = self.coordinator.diagnose_failure(
            error_output="TypeScript code cliché detected",
            code_content=code,
            filename="api.ts"
        )
        self.assertEqual(diag.category, "SHOTGUN_SUPPRESSION")
        self.assertIn("console.error", diag.prescribed_remedy)
        self.assertIn("catch (err) {}", diag.remediation_patch["search"])

    def test_diagnose_rust_unwrap(self):
        code = "pub fn run() -> String {\n    let a = parse().unwrap();\n    let b = validate().unwrap();\n    let c = format().unwrap();\n    c\n}\n"
        diag = self.coordinator.diagnose_failure(
            error_output="Rust excessive unwrap detected",
            code_content=code,
            filename="lib.rs"
        )
        self.assertEqual(diag.category, "UNCONSTRAINED_UNWRAP")
        self.assertIn("?", diag.prescribed_remedy)

    def test_diagnose_syntax_error(self):
        bad_code = "def broken(x:\n    return x\n"
        diag = self.coordinator.diagnose_failure(
            error_output="SyntaxError at line 1",
            code_content=bad_code,
            filename="broken.py"
        )
        self.assertEqual(diag.category, "SYNTAX_ERROR")
        self.assertIn("AST Pre-Flight", diag.root_cause)

    def test_apply_remediation_fixes_content(self):
        code = "def worker():\n    try:\n        step()\n    except Exception:\n        pass\n"
        diag = self.coordinator.diagnose_failure("Error", code_content=code, filename="worker.py")
        fixed_code = self.coordinator.apply_remediation(diag, code)
        self.assertNotIn("except Exception:\n        pass", fixed_code)
        self.assertIn("except", fixed_code)


class TestHealingExecutionAndCircuitBreaker(unittest.TestCase):
    """Verifies end-to-end self-healing loop execution and circuit-breaker behavior."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = self.temp_dir.name
        self.coordinator = SelfHealingCoordinator(workspace_root=self.workspace, max_attempts=3)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_heal_gate_successful_recovery(self):
        target_file = os.path.join(self.workspace, "handler.py")
        dirty_code = "def handle():\n    try:\n        run()\n    except Exception:\n        pass\n"
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(dirty_code)

        # Verifier checks for absence of shotgun suppression
        check_cmd = f"python3 -c \"import sys; content = open('{target_file}').read(); sys.exit(1 if 'except Exception:\\n        pass' in content else 0)\""

        receipt = self.coordinator.heal_gate(
            gate_id="gate-shotgun-test",
            verifier_cmd=check_cmd,
            file_path=target_file
        )

        self.assertEqual(receipt.status, "HEALED")
        self.assertLessEqual(receipt.attempt_number, 3)

        # Verify target file was remediated on disk
        with open(target_file, "r", encoding="utf-8") as f:
            clean_content = f.read()
        self.assertNotIn("except Exception:\n        pass", clean_content)

    def test_heal_gate_circuit_breaker_after_max_attempts(self):
        target_file = os.path.join(self.workspace, "unfixable.py")
        with open(target_file, "w", encoding="utf-8") as f:
            f.write("def always_fails(): return False\n")

        # Command that always fails regardless of remediation
        impossible_cmd = "python3 -c 'import sys; sys.exit(1)'"

        receipt = self.coordinator.heal_gate(
            gate_id="gate-impossible",
            verifier_cmd=impossible_cmd,
            file_path=target_file
        )

        self.assertEqual(receipt.status, "CIRCUIT_OPEN")
        self.assertEqual(receipt.attempt_number, 3)
        self.assertIn("circuit breaker", receipt.test_output.lower())


class TestSelfHealingCLI(unittest.TestCase):
    """Verifies CLI registration and command interface for --heal."""

    def test_cli_heal_flag_in_help(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--heal", proc.stdout)

    def test_cli_heal_execution_json(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tf:
            tf.write("def sample():\n    try:\n        pass\n    except Exception:\n        pass\n")
            target_path = tf.name

        try:
            verifier = f"python3 -c \"import sys; content = open('{target_path}').read(); sys.exit(1 if 'except Exception:\\n        pass' in content else 0)\""
            proc = subprocess.run(
                [sys.executable, SCRIPT, "--heal", "test-gate", "--file", target_path, "--verifier", verifier, "--json"],
                capture_output=True,
                text=True,
                cwd=ROOT_DIR,
                check=False
            )
            self.assertEqual(proc.returncode, 0)
            data = json.loads(proc.stdout)
            self.assertEqual(data["status"], "HEALED")
        finally:
            if os.path.exists(target_path):
                os.remove(target_path)



if __name__ == "__main__":
    unittest.main()
