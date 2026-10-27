"""Tests for FocusGate v2.9 — Milestone 16 (Loop 19: Cryptographic Merkle State Tree & Content-Addressed Event Ledger).

Covers:
1. MerkleEventNode SHA-256 content-addressing and parent link verification.
2. MerkleEventDAG append, tip tracking, and deterministic state root generation.
3. Tamper detection: detecting modified payloads, altered timestamps, and broken parent links.
4. JSONL persistence and lossless round-trip reconstruction.
5. CLI --verify-merkle flag registration and execution.
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

from core.merkle_ledger import MerkleEventNode, MerkleEventDAG


class TestMerkleNodeAndHashing(unittest.TestCase):
    """Verifies cryptographic properties of individual Merkle nodes."""

    def test_node_hash_determinism(self):
        payload = {"gate_id": "gate-core", "status": "CHECKED"}
        node1 = MerkleEventNode.create("GATE_CHECKED", payload, prev_hash="0000000000000000")
        node2 = MerkleEventNode.create("GATE_CHECKED", payload, prev_hash="0000000000000000")
        self.assertEqual(node1.node_hash, node2.node_hash)
        self.assertEqual(len(node1.node_hash), 64)  # SHA-256 length

    def test_node_hash_changes_on_payload_change(self):
        node1 = MerkleEventNode.create("GATE_CHECKED", {"status": "CHECKED"}, prev_hash="0000")
        node2 = MerkleEventNode.create("GATE_CHECKED", {"status": "FAILED"}, prev_hash="0000")
        self.assertNotEqual(node1.node_hash, node2.node_hash)

    def test_node_hash_changes_on_parent_change(self):
        payload = {"x": 1}
        node1 = MerkleEventNode.create("EVENT", payload, prev_hash="aaaa")
        node2 = MerkleEventNode.create("EVENT", payload, prev_hash="bbbb")
        self.assertNotEqual(node1.node_hash, node2.node_hash)

    def test_node_to_dict_and_from_dict_roundtrip(self):
        node = MerkleEventNode.create("PIPELINE_INIT", {"pipeline": "P1"}, prev_hash="")
        d = node.to_dict()
        reconstructed = MerkleEventNode.from_dict(d)
        self.assertEqual(node.node_hash, reconstructed.node_hash)
        self.assertEqual(node.event_id, reconstructed.event_id)
        self.assertEqual(node.payload, reconstructed.payload)


class TestMerkleEventDAG(unittest.TestCase):
    """Verifies Merkle DAG append, traversal, and state root consensus."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, "merkle.events.jsonl")
        self.dag = MerkleEventDAG(ledger_path=self.log_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_append_forms_valid_parent_chain(self):
        n1 = self.dag.append("GENESIS", {"desc": "Start of ledger"})
        self.assertEqual(n1.prev_hash, "")
        self.assertEqual(self.dag.tip_hash, n1.node_hash)

        n2 = self.dag.append("GATE_CHECKED", {"gate_id": "gate-1"})
        self.assertEqual(n2.prev_hash, n1.node_hash)
        self.assertEqual(self.dag.tip_hash, n2.node_hash)

        n3 = self.dag.append("GATE_CHECKED", {"gate_id": "gate-2"})
        self.assertEqual(n3.prev_hash, n2.node_hash)
        self.assertEqual(self.dag.tip_hash, n3.node_hash)

        valid, err = self.dag.verify_integrity()
        self.assertTrue(valid, f"Verification failed: {err}")
        self.assertEqual(len(self.dag.nodes), 3)

    def test_deterministic_state_root(self):
        self.dag.append("EV1", {"data": "A"})
        self.dag.append("EV2", {"data": "B"})
        root1 = self.dag.compute_state_root()

        # Reconstruct identical DAG
        dag2 = MerkleEventDAG()
        dag2.append("EV1", {"data": "A"})
        dag2.append("EV2", {"data": "B"})
        root2 = dag2.compute_state_root()

        self.assertEqual(root1, root2)
        self.assertEqual(len(root1), 64)

    def test_tamper_detection_modified_payload(self):
        self.dag.append("INIT", {"v": 1})
        self.dag.append("CRITICAL_ACTION", {"balance": 100})
        self.dag.append("FINALIZE", {"v": 2})

        valid, _ = self.dag.verify_integrity()
        self.assertTrue(valid)

        # Corrupt node in-memory
        self.dag.nodes[1].payload["balance"] = 1000000  # Tampered!
        valid, err = self.dag.verify_integrity()
        self.assertFalse(valid)
        self.assertIn("Corrupted hash", err)

    def test_tamper_detection_broken_parent_link(self):
        self.dag.append("N1", {"v": 1})
        self.dag.append("N2", {"v": 2})
        self.dag.append("N3", {"v": 3})

        # Break parent hash link on node 2 without changing its node_hash
        self.dag.nodes[2].prev_hash = "ffffffffffffffff" * 4
        valid, err = self.dag.verify_integrity()
        self.assertFalse(valid)

    def test_disk_persistence_and_reload(self):
        self.dag.append("STAGE_1", {"status": "PASSED"})
        self.dag.append("STAGE_2", {"status": "PASSED"})
        expected_root = self.dag.compute_state_root()

        # Reload in separate DAG instance
        loaded_dag = MerkleEventDAG.load_from_file(self.log_path)
        self.assertEqual(len(loaded_dag.nodes), 2)
        self.assertEqual(loaded_dag.compute_state_root(), expected_root)
        valid, _ = loaded_dag.verify_integrity()
        self.assertTrue(valid)


class TestMerkleCLI(unittest.TestCase):
    """Verifies CLI integration of --verify-merkle."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, "merkle.events.jsonl")
        dag = MerkleEventDAG(ledger_path=self.log_path)
        dag.append("BOOT", {"system": "ok"})
        dag.append("CHECK", {"gate": "g1"})

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_merkle_flag_in_help(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--verify-merkle", proc.stdout)

    def test_cli_verify_merkle_clean_pass(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--verify-merkle", self.log_path],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0, f"Error: {proc.stderr}")
        self.assertIn("MERKLE_DAG_PASS:", proc.stdout)
        self.assertIn("Root:", proc.stdout)

    def test_cli_verify_merkle_tampered_fails(self):
        # Tamper disk file directly
        with open(self.log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        corrupted_obj = json.loads(lines[0])
        corrupted_obj["payload"]["system"] = "HACKED"  # Payload tampered, hash untouched
        lines[0] = json.dumps(corrupted_obj) + "\n"
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        proc = subprocess.run(
            [sys.executable, SCRIPT, "--verify-merkle", self.log_path],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("MERKLE_DAG_FAIL:", proc.stdout)


if __name__ == "__main__":
    unittest.main()
