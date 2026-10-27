#!/usr/bin/env python3
"""FocusGate v2.8 — Loop 6 Deepening & Hardening Test Suite (TDD RED)."""

import os
import sys
import json
import tempfile
import unittest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
V28_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))
if V28_ROOT not in sys.path:
    sys.path.insert(0, V28_ROOT)

SCRIPT = os.path.join(V28_ROOT, "scripts", "focus-gate.py")


class TestStageMatrixArtifactSchemaValidation(unittest.TestCase):
    def test_json_artifact_syntax_validation(self):
        from core.stage_matrix import StageDefinition, StageVerificationMatrix
        with tempfile.TemporaryDirectory() as td:
            matrix = StageVerificationMatrix(workspace_root=td)
            
            # 1. Invalid JSON file
            bad_json_path = os.path.join(td, "payload.json")
            with open(bad_json_path, "w", encoding="utf-8") as f:
                f.write("{ invalid json payload: missing quote }")
            
            stage = StageDefinition(
                stage_id="s_json",
                index=0,
                name="JSON Delivery Stage",
                facet="engineering",
                gate_ids=["g_json"],
                required_artifacts=["payload.json"]
            )
            agg = {"g_json": {"status": "CHECKED"}}
            
            verified, reasons, evidence = matrix.verify_stage_completion(stage, agg)
            self.assertFalse(verified)
            self.assertTrue(any("invalid json" in r.lower() for r in reasons), f"Expected JSON syntax rejection, got: {reasons}")

            # 2. Valid JSON file
            with open(bad_json_path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"valid": True, "deliverable": "complete"}))
            
            verified, reasons, evidence = matrix.verify_stage_completion(stage, agg)
            self.assertTrue(verified, f"Expected PASS for valid JSON artifact, got: {reasons}")


class TestCliBannersV28Harmonization(unittest.TestCase):
    def test_no_legacy_subcommand_banners_in_focus_gate_cli(self):
        with open(SCRIPT, "r", encoding="utf-8") as f:
            cli_text = f.read()
        self.assertNotIn("FOCUSGATE v2.7 MASTER ORCHESTRATOR", cli_text)
        self.assertNotIn("FOCUSGATE v2.7 STAGE VERIFICATION MATRIX", cli_text)
        self.assertNotIn("FOCUSGATE DOMAIN MODELING & AGENT AUDIT REPORT (v1.5.2)", cli_text)
        self.assertNotIn("FOCUSGATE CONTRACT & SCHEMA VALIDATION REPORT (v1.5.2)", cli_text)


class TestEphemeralRetrieverTokenBounding(unittest.TestCase):
    def test_retrieve_snippet_respects_token_ceiling(self):
        from core.ephemeral_retriever import EphemeralContextRetriever
        from core.tokens import estimate_tokens
        
        with tempfile.TemporaryDirectory() as td:
            retriever = EphemeralContextRetriever(workspace_root=td)
            test_file = os.path.join(td, "large_matches.txt")
            # Create a file with many matches that would blow a token window
            with open(test_file, "w", encoding="utf-8") as f:
                for i in range(100):
                    f.write(f"Line {i}: TARGET_KEYWORD verbose metadata payload with long descriptions and diagnostic notes {i}\n")
            
            snippet = retriever.retrieve_snippet("large_matches.txt", pattern="TARGET_KEYWORD", max_tokens=300)
            self.assertIsNotNone(snippet)
            token_count = estimate_tokens(snippet)
            self.assertLessEqual(token_count, 300, f"Snippet tokens {token_count} exceeded 300-token ceiling")
            self.assertIn("TARGET_KEYWORD", snippet)


class TestDynamicOutputFoldingInGateExecution(unittest.TestCase):
    def test_verbose_test_output_is_folded_and_logged(self):
        from adapters.oracle_adapter import ShellOracleAdapter
        from core.tokens import estimate_tokens
        from types import SimpleNamespace

        with tempfile.TemporaryDirectory() as td:
            adapter = ShellOracleAdapter()
            # Command that prints 100 lines of verbose test logs
            cmd = sys.executable + " -c 'for i in range(100): print(\"TEST_LINE_VERBOSE: line index\", i)'"
            gate = SimpleNamespace(
                id="g_verbose_test",
                check_cmd=cmd,
                timeout=10,
                expect_pattern=None,
                cwd=None
            )
            passed, msg, meta = adapter.execute_tracer(gate, base_dir=td)
            self.assertTrue(passed)
            self.assertIn("raw_output", meta)
            self.assertIn("log_file_path", meta)
            self.assertTrue(os.path.exists(meta["log_file_path"]))
            with open(meta["log_file_path"], "r", encoding="utf-8") as f:
                saved_log = f.read()
            self.assertIn("TEST_LINE_VERBOSE: line index 99", saved_log)
            # Verify folded output is bounded under 150 tokens
            folded_tokens = estimate_tokens(meta["output"])
            self.assertLessEqual(folded_tokens, 150, f"Folded output exceeded 150 tokens: {folded_tokens}")


if __name__ == "__main__":
    unittest.main()
