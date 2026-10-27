"""Tests for Loop 29: Actor Context Compactor & Micro-Delta Bus.

Tests ActorContextCompactor brief budgeting (<=400 tokens),
MicroDeltaBus inter-actor delta ceiling (<=80 tokens),
sliding turn window management, ProofTreeCompactor ARCHIVE.md collapse,
and CLI flags --actor-context and --compact-swarm.

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
from typing import Dict, Any

from core.compaction.actor_context_compactor import ActorContextCompactor
from core.compaction.proof_tree_compactor import ProofTreeCompactor, MicroDeltaBus
from core.mesh import ActorMessage, MessagePriority


class TestActorContextCompactor(unittest.TestCase):
    """Test token budgeting, brief truncation, and sliding turn memory."""

    def setUp(self):
        self.compactor = ActorContextCompactor()

    def test_compact_brief_within_budget(self):
        desc = "Implement authentication gate with session tokens and secure cookies."
        criteria = ["Valid signature", "Token expiration in 3600s", "Zero leak"]
        anchors = {"Auth": "Session-based bearer tokens", "Cookie": "HttpOnly and SameSite=Strict"}

        brief = self.compactor.compact_brief(desc, criteria, anchors=anchors)
        tokens = ActorContextCompactor.estimate_tokens(brief)
        self.assertLessEqual(tokens, ActorContextCompactor.MAX_BRIEF_TOKENS)
        self.assertIn("Auth", brief)
        self.assertIn("Zero leak", brief)

    def test_compact_brief_over_budget_truncated(self):
        # Extremely verbose text that exceeds 400 tokens (~1600+ characters)
        desc = "Verbose explanation: " + ("lorem ipsum dolor sit amet " * 200)
        criteria = [f"Criterion {i}: " + ("detail " * 10) for i in range(20)]

        brief = self.compactor.compact_brief(desc, criteria)
        tokens = ActorContextCompactor.estimate_tokens(brief)
        self.assertLessEqual(tokens, ActorContextCompactor.MAX_BRIEF_TOKENS)
        self.assertTrue(brief.endswith("...") or "..." in brief)

    def test_sliding_turn_window(self):
        actor_id = "coder-01"
        for i in range(15):
            self.compactor.track_turn(actor_id, role="assistant", content=f"Step {i}: executed action")

        ctx = self.compactor.get_active_context(actor_id)
        self.assertEqual(len(ctx["turns"]), ActorContextCompactor.MAX_TURNS)
        # Should keep newest steps (5 to 14)
        self.assertIn("Step 14", ctx["turns"][-1]["content"])
        self.assertNotIn("Step 0", ctx["turns"][0]["content"])

    def test_enforce_delta_ceiling(self):
        small_payload = {"action": "check_gate", "target": "gate-1", "verdict": "PASS"}
        ok, tokens, payload = self.compactor.enforce_delta_ceiling(small_payload)
        self.assertTrue(ok)
        self.assertLessEqual(tokens, ActorContextCompactor.MAX_DELTA_TOKENS)

        huge_payload = {"raw_trace": "E" * 1000, "stack": "Traceback..." * 50}
        ok, tokens, compact_p = self.compactor.enforce_delta_ceiling(huge_payload)
        self.assertTrue(ok)
        self.assertLessEqual(tokens, ActorContextCompactor.MAX_DELTA_TOKENS)
        self.assertIn("truncated", compact_p)


class TestProofTreeCompactor(unittest.TestCase):
    """Test proof tree summarization and ARCHIVE.md generation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_proof_test_")
        self.ledger_path = os.path.join(self.temp_dir, "GATES.md")
        self.archive_path = os.path.join(self.temp_dir, "ARCHIVE.md")

        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write("""# FocusGate Ledger
State: [Step 1 of 2] [1/2 gates met]

## 1. Domain Anchors
- **Core**: Engine domain

## 2. Acceptance Gates
- [x] gate-done: Settled task
  CHECK: python3 -c 'print("DONE")'
  EXPECT: DONE
- [ ] gate-todo: Unsettled task
  CHECK: python3 -c 'print("TODO")'
  EXPECT: TODO
""")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_compact_ledger_proofs(self):
        compactor = ProofTreeCompactor(ledger_path=self.ledger_path, archive_path=self.archive_path)
        res = compactor.compact()

        self.assertEqual(res["settled_compacted"], 1)
        self.assertTrue(os.path.exists(self.archive_path))

        with open(self.archive_path, "r", encoding="utf-8") as f:
            arch_content = f.read()
        self.assertIn("gate-done", arch_content)
        self.assertIn("PROOF_HASH:", arch_content)

        # GATES.md now has only gate-todo
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            ledger_content = f.read()
        self.assertNotIn("gate-done", ledger_content)
        self.assertIn("gate-todo", ledger_content)


class TestMicroDeltaBus(unittest.TestCase):
    """Test MicroDeltaBus validation and message routing."""

    def test_bus_routes_valid_delta(self):
        bus = MicroDeltaBus()
        msg = ActorMessage(
            message_id="msg-1",
            priority=MessagePriority.NORMAL,
            source="actor-1",
            target="actor-2",
            topic="GATE_DISPATCH",
            payload={"gate_id": "gate-1", "action": "RUN"}
        )
        ok, res_msg = bus.validate_and_wrap(msg)
        self.assertTrue(ok)
        self.assertEqual(res_msg.message_id, "msg-1")

    def test_bus_compresses_oversized_payload(self):
        bus = MicroDeltaBus()
        oversized = {"log": "x" * 2000, "status": "FAIL"}
        msg = ActorMessage(
            message_id="msg-2",
            priority=MessagePriority.NORMAL,
            source="actor-1",
            target="actor-2",
            topic="TRACE",
            payload=oversized
        )
        ok, res_msg = bus.validate_and_wrap(msg)
        self.assertTrue(ok)
        tokens = ActorContextCompactor.estimate_tokens(json.dumps(res_msg.payload))
        self.assertLessEqual(tokens, ActorContextCompactor.MAX_DELTA_TOKENS)


class TestContextCompactorCLI(unittest.TestCase):
    """Test CLI dispatch for --actor-context and --compact-swarm."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_ctx_cli_")
        self.ledger_path = os.path.join(self.temp_dir, "GATES.md")
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write("""# FocusGate Ledger
## 2. Acceptance Gates
- [x] gate-1: Met
- [ ] gate-2: Pending
""")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_actor_context_json(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(actor_context=True, compact_swarm=None)
        clean_args = ["--actor-context", "coder-01", "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["actor_id"], "coder-01")
        self.assertIn("token_budget", output)

    def test_cli_compact_swarm_json(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(compact_swarm=True, actor_context=None)
        clean_args = ["--compact-swarm", self.ledger_path, "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["settled_compacted"], 1)


if __name__ == '__main__':
    unittest.main()
