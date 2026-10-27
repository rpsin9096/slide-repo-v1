"""FocusGate v3.1 — Byzantine Fault Detection & Quorum Consensus Tests (Loop 45).

Verifies multi-node decentralized gate settlement:
- Cryptographic vote signing and verification
- Byzantine detector flagging divergent roots and causal clock jumps
- 2/3 supermajority quorum consensus evaluation
- CLI dispatch (--quorum-vote)

100% Python stdlib, zero external dependencies. Sub-50ms consensus evaluation.
"""

import os
import sys
import json
import time
import unittest

from core.grid.byzantine_consensus import (
    QuorumVote,
    ByzantineDetector,
    QuorumVoteCollector,
)


class TestByzantineConsensus(unittest.TestCase):
    """Verifies vote validation, Byzantine detection, and quorum thresholds."""

    def setUp(self):
        self.detector = ByzantineDetector(trusted_state_root="root-sha-001")
        self.collector = QuorumVoteCollector(gate_id="gate-03-tdd", detector=self.detector)

    def test_valid_vote_collection_reaches_quorum(self):
        # 3 nodes in total, quorum is 2/3 (ceil(3 * 0.6667) = 2)
        vote1 = QuorumVote(
            node_id="node-1",
            gate_id="gate-03-tdd",
            verdict="PASS",
            state_root="root-sha-001",
            vector_clock={"node-1": 1}
        )
        vote2 = QuorumVote(
            node_id="node-2",
            gate_id="gate-03-tdd",
            verdict="PASS",
            state_root="root-sha-001",
            vector_clock={"node-1": 1, "node-2": 1}
        )

        ok1 = self.collector.record_vote(vote1)
        ok2 = self.collector.record_vote(vote2)
        self.assertTrue(ok1)
        self.assertTrue(ok2)

        outcome = self.collector.evaluate_consensus(total_nodes=3)
        self.assertEqual(outcome["status"], "DECIDED")
        self.assertEqual(outcome["verdict"], "PASS")
        self.assertEqual(outcome["votes_count"], 2)
        self.assertEqual(len(outcome["byzantine_nodes"]), 0)

    def test_detect_byzantine_divergent_state_root(self):
        # Malicious node sends fabricated state root
        bad_vote = QuorumVote(
            node_id="node-rogue",
            gate_id="gate-03-tdd",
            verdict="PASS",
            state_root="forged-root-sha-666",
            vector_clock={"node-rogue": 100}
        )
        ok = self.collector.record_vote(bad_vote)
        self.assertFalse(ok)
        self.assertIn("node-rogue", self.collector.byzantine_nodes)

    def test_detect_byzantine_tampered_signature(self):
        vote = QuorumVote(
            node_id="node-tampered",
            gate_id="gate-03-tdd",
            verdict="PASS",
            state_root="root-sha-001",
            vector_clock={"node-tampered": 1},
            signature="corrupted_signature_123"
        )
        # Verify tampered signature fails validation
        fault = self.detector.audit_vote(vote)
        self.assertIsNotNone(fault)
        self.assertIn("signature", fault.lower())

    def test_quorum_not_reached_when_insufficient_votes(self):
        # 5 nodes total, need 4 votes for 2/3 quorum. Only 2 provided.
        vote1 = QuorumVote(node_id="node-1", gate_id="gate-03-tdd", verdict="PASS", state_root="root-sha-001")
        vote2 = QuorumVote(node_id="node-2", gate_id="gate-03-tdd", verdict="PASS", state_root="root-sha-001")
        self.collector.record_vote(vote1)
        self.collector.record_vote(vote2)

        outcome = self.collector.evaluate_consensus(total_nodes=5)
        self.assertEqual(outcome["status"], "PENDING")
        self.assertIsNone(outcome["verdict"])


class TestByzantineCLI(unittest.TestCase):
    """Verifies CLI flag --quorum-vote."""

    def test_cli_quorum_vote_json(self):
        from core.cli.dispatch import CLIDispatcher
        clean_args = ["--quorum-vote", "gate-03-tdd", "--nodes", "3"]

        import io
        import contextlib
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = CLIDispatcher.dispatch_quorum_vote(clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(stdout.getvalue())
        self.assertIn("gate_id", output)
        self.assertIn("consensus", output)
        self.assertIn("status", output["consensus"])
