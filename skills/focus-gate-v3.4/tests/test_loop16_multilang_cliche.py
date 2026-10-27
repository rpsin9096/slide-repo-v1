"""Tests for FocusGate v2.8.5 — Milestone 13 (Loop 16: Universal Multilingual Anti-Cliché & Socratic Dialectic).

Covers:
1. Prescriptive remedy snippets attached to CodeClicheFinding.
2. TypeScript/JavaScript static cliché detection (shotgun catch, any spree, junk drawer).
3. Rust static cliché detection (excessive unwrap, todo!/unimplemented! stubs).
4. Adversarial dialectic tournament integration and CLI registration.
"""

import unittest
import os
import subprocess
import json

from core.oracles.code_cliche_oracle import CodeClicheOracle, CodeClicheFinding
from core.adversarial_runner import AdversarialRunner, AdversarialVerdict


class TestPrescriptiveRemedies(unittest.TestCase):
    """Verifies that all code cliché findings carry concrete prescriptive remedies."""

    def test_python_shotgun_remedy_attached(self):
        code = "def handle():\n    try:\n        do_work()\n    except Exception:\n        pass\n"
        res = CodeClicheOracle.audit_content(code, filename="worker.py")
        self.assertFalse(res.clean)
        violations = [f for f in res.findings if f.rule_id == "CODE_SHOTGUN_SUPPRESSION"]
        self.assertEqual(len(violations), 1)
        finding = violations[0]
        self.assertTrue(hasattr(finding, "prescribed_remedy"), "Finding must have prescribed_remedy field.")
        self.assertIn("except", finding.prescribed_remedy)
        self.assertGreater(len(finding.prescribed_remedy), 15)

    def test_junk_drawer_remedy_attached(self):
        code = "\n".join([f"def func_{i}(): return {i}" for i in range(5)])
        res = CodeClicheOracle.audit_content(code, filename="utils.py")
        self.assertFalse(res.clean)
        violations = [f for f in res.findings if f.rule_id == "CODE_JUNK_DRAWER_MODULE"]
        self.assertEqual(len(violations), 1)
        self.assertIn("domain", violations[0].prescribed_remedy.lower())


class TestTypeScriptCodeCliche(unittest.TestCase):
    """Verifies static anti-cliché detection for TypeScript / JavaScript."""

    def test_ts_shotgun_catch_detected(self):
        ts_code = """
        export function fetchData() {
            try {
                return apiCall();
            } catch (err) {}
        }
        """
        res = CodeClicheOracle.audit_content(ts_code, filename="service.ts")
        self.assertFalse(res.clean)
        self.assertTrue(any(f.rule_id == "CODE_SHOTGUN_SUPPRESSION_TS" for f in res.findings))
        shotgun_f = next(f for f in res.findings if f.rule_id == "CODE_SHOTGUN_SUPPRESSION_TS")
        self.assertIn("console.error", shotgun_f.prescribed_remedy)

    def test_ts_unchecked_any_spree(self):
        ts_code = """
        const a: any = 1;
        const b = val as any;
        function parse(x: any): any {
            return x as any;
        }
        """
        res = CodeClicheOracle.audit_content(ts_code, filename="parser.ts")
        self.assertFalse(res.clean)
        self.assertTrue(any(f.rule_id == "CODE_UNCHECKED_ANY_SPREE" for f in res.findings))

    def test_ts_junk_drawer_name(self):
        ts_code = "export const A = 1;\nexport const B = 2;\nexport function c() {}\nexport function d() {}\n"
        res = CodeClicheOracle.audit_content(ts_code, filename="helpers.ts")
        self.assertFalse(res.clean)
        self.assertTrue(any(f.rule_id == "CODE_JUNK_DRAWER_MODULE" for f in res.findings))

    def test_clean_typescript_passes(self):
        ts_code = """
        interface User {
            id: string;
            name: string;
        }

        export function getUser(id: string): User | null {
            try {
                return fetchUser(id);
            } catch (err) {
                logger.error("Failed to fetch user", { id, err });
                throw new UserFetchError(id);
            }
        }
        """
        res = CodeClicheOracle.audit_content(ts_code, filename="user_service.ts")
        self.assertTrue(res.clean, f"Clean TypeScript should pass audit: {[f.description for f in res.findings]}")


class TestRustCodeCliche(unittest.TestCase):
    """Verifies static anti-cliché detection for Rust implementations."""

    def test_rust_excessive_unwrap_detected(self):
        rs_code = """
        pub fn process_data(input: &str) -> String {
            let parsed = parse_raw(input).unwrap();
            let validated = validate(&parsed).unwrap();
            let formatted = format_output(&validated).unwrap();
            formatted
        }
        """
        res = CodeClicheOracle.audit_content(rs_code, filename="lib.rs")
        self.assertFalse(res.clean)
        self.assertTrue(any(f.rule_id == "CODE_UNCONSTRAINED_UNWRAP_RUST" for f in res.findings))
        unwrap_f = next(f for f in res.findings if f.rule_id == "CODE_UNCONSTRAINED_UNWRAP_RUST")
        self.assertIn("?", unwrap_f.prescribed_remedy)

    def test_rust_todo_macro_detected(self):
        rs_code = """
        pub fn handle_event(event: Event) {
            match event {
                Event::Start => println!("Starting"),
                Event::Stop => todo!(),
            }
        }
        """
        res = CodeClicheOracle.audit_content(rs_code, filename="handler.rs")
        self.assertFalse(res.clean)
        self.assertTrue(any(f.rule_id == "CODE_TODO_STUB_RUST" for f in res.findings))

    def test_clean_rust_passes(self):
        rs_code = """
        use std::error::Error;

        pub fn process_data(input: &str) -> Result<String, Box<dyn Error>> {
            let parsed = parse_raw(input)?;
            let validated = validate(&parsed)?;
            Ok(format_output(&validated))
        }
        """
        res = CodeClicheOracle.audit_content(rs_code, filename="processor.rs")
        self.assertTrue(res.clean, f"Clean Rust should pass audit: {[f.description for f in res.findings]}")


class TestAdversarialSocraticIntegration(unittest.TestCase):
    """Verifies adversarial tournament execution and CLI command exposure."""

    def test_adversarial_tournament_runs_and_verifies(self):
        runner = AdversarialRunner(max_rounds=3)
        proposal = "Implement distributed shared cache with in-memory TTL and atomic CAS updates."
        verdict = runner.run_tournament("prop-cache-1", proposal)
        self.assertIsInstance(verdict, AdversarialVerdict)
        self.assertEqual(verdict.total_rounds, 3)
        self.assertIn(verdict.status, ("APPROVED", "REJECTED_NEEDS_HARDENING"))
        self.assertGreaterEqual(verdict.vulnerabilities_mitigated, 1)

    def test_cli_adversarial_flag_registered(self):
        cli_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "focus-gate.py")
        proc = subprocess.run(
            ["python3", cli_path, "--help"],
            capture_output=True,
            text=True,
            check=False
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--adversarial-audit", proc.stdout)


if __name__ == "__main__":
    unittest.main()
