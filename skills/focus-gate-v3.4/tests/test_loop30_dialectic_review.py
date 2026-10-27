"""Tests for Loop 30: Autonomous Cross-Actor Dialectic & Socratic Peer Review.

Tests SocraticMeshProtocol 3-round convergence, AutonomousPeerReviewer
invariant validation, signed CoherenceReceipt generation, and CLI dispatch.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import json
import io
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from contextlib import redirect_stdout
from typing import Dict, Any, List

from core.dialectic.socratic_mesh import SocraticMeshProtocol, DialecticResult
from core.dialectic.peer_review import AutonomousPeerReviewer, CoherenceReceipt, CoherenceRegistry


class TestSocraticMeshProtocol(unittest.TestCase):
    """Test 3-round dialectic tournament between proposer and verifier."""

    def test_dialectic_three_round_convergence(self):
        protocol = SocraticMeshProtocol(max_rounds=3)
        proposal = {
            "title": "Token-bucket Rate Limiter",
            "spec": "Enforce 100 requests per minute with in-memory redis sliding window.",
            "invariants": ["Zero drift under concurrent bursts", "Fail-open on store timeout"]
        }
        res = protocol.run_dialectic(proposer_id="actor-arch", verifier_id="actor-critique", proposal=proposal)
        self.assertIsInstance(res, DialecticResult)
        self.assertEqual(res.status, "CONVERGED")
        self.assertEqual(len(res.rounds), 3)
        self.assertTrue(res.is_approved())
        self.assertIn("synthesis", res.to_dict())

    def test_dialectic_unmitigated_vulnerability_rejects(self):
        protocol = SocraticMeshProtocol(max_rounds=3)
        unmitigated_proposal = {
            "title": "Insecure Shared Cache",
            "spec": "Global unprotected dict without lock or TTL.",
            "invariants": []
        }
        # Inject challenger that rejects all mitigations
        def stubborn_verifier(round_idx: int, proposal_ctx: str) -> Dict[str, Any]:
            return {
                "critique": "Fatal race condition and memory unbounded leak.",
                "vulnerabilities": ["unbounded_leak", "race_condition"],
                "mitigated": []
            }

        res = protocol.run_dialectic(
            proposer_id="actor-arch",
            verifier_id="actor-critique",
            proposal=unmitigated_proposal,
            verifier_func=stubborn_verifier
        )
        self.assertEqual(res.status, "REJECTED")
        self.assertFalse(res.is_approved())
        self.assertGreater(len(res.unmitigated_vulnerabilities), 0)

    def test_dialectic_token_bounded_exchanges(self):
        protocol = SocraticMeshProtocol(max_rounds=3)
        proposal = {
            "title": "Compact Seam",
            "spec": "A" * 800,  # potentially large input
            "invariants": ["No regression"]
        }
        res = protocol.run_dialectic(proposer_id="actor-1", verifier_id="actor-2", proposal=proposal)
        for r in res.rounds:
            self.assertLessEqual(len(r["proposer_statement"]) // 4, 150)
            self.assertLessEqual(len(r["verifier_critique"]) // 4, 150)


class TestAutonomousPeerReviewer(unittest.TestCase):
    """Test AutonomousPeerReviewer invariant evaluation and CoherenceReceipt generation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_dialectic_test_")
        self.registry_dir = os.path.join(self.temp_dir, ".focusgate", "receipts")
        os.makedirs(self.registry_dir, exist_ok=True)
        self.registry = CoherenceRegistry(storage_dir=self.registry_dir)
        self.reviewer = AutonomousPeerReviewer(registry=self.registry)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_peer_review_generates_signed_receipt(self):
        receipt = self.reviewer.review_gate(
            actor_id="coder-01",
            gate_id="gate-12",
            diff_or_code="def execute(): return 42\n",
            invariants=["Deterministic execution", "Zero side effects"]
        )
        self.assertIsInstance(receipt, CoherenceReceipt)
        self.assertEqual(receipt.status, "APPROVED")
        self.assertEqual(receipt.actor_id, "coder-01")
        self.assertEqual(receipt.gate_id, "gate-12")
        self.assertTrue(receipt.verify_signature())

        # Check receipt saved in registry
        saved = self.registry.get_receipt("gate-12")
        self.assertIsNotNone(saved)
        self.assertEqual(saved.receipt_id, receipt.receipt_id)

    def test_coherence_receipt_signature_tamper_detection(self):
        receipt = self.reviewer.review_gate(
            actor_id="coder-02",
            gate_id="gate-13",
            diff_or_code="x = 10\n"
        )
        self.assertTrue(receipt.verify_signature())

        # Tamper with status
        receipt.status = "TAMPERED"
        self.assertFalse(receipt.verify_signature())

    def test_peer_review_rejects_syntax_error(self):
        receipt = self.reviewer.review_gate(
            actor_id="coder-03",
            gate_id="gate-broken",
            diff_or_code="def broken(:\n    pass\n"
        )
        self.assertEqual(receipt.status, "REJECTED")
        self.assertIn("syntax", receipt.rejection_reason.lower())


class TestDialecticCLI(unittest.TestCase):
    """Test CLI dispatch for --dialectic-review and --coherence-status."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_dialectic_cli_")
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        os.makedirs(".focusgate/receipts", exist_ok=True)

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_dialectic_review_json(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(dialectic_review=["actor-01", "gate-10"], coherence_status=None)
        clean_args = ["--dialectic-review", "actor-01", "gate-10", "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["actor_id"], "actor-01")
        self.assertEqual(output["gate_id"], "gate-10")
        self.assertIn("signature", output)
        self.assertIn("status", output)

    def test_cli_coherence_status_json(self):
        from core.cli.dispatch import CLIDispatcher
        from core.dialectic.peer_review import CoherenceRegistry, CoherenceReceipt

        # Pre-seed receipt
        reg = CoherenceRegistry(storage_dir=os.path.join(self.temp_dir, ".focusgate", "receipts"))
        rec = CoherenceReceipt(
            receipt_id="rec-test-1",
            actor_id="actor-02",
            gate_id="gate-20",
            status="APPROVED",
            invariants=["Test invariant"],
            dialectic_summary={"rounds": 3}
        )
        rec.sign()
        reg.save_receipt(rec)

        args = SimpleNamespace(dialectic_review=None, coherence_status=["gate-20"])
        clean_args = ["--coherence-status", "gate-20", "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["gate_id"], "gate-20")
        self.assertEqual(output["status"], "APPROVED")


if __name__ == '__main__':
    unittest.main()
