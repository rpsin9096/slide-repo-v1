#!/usr/bin/env python3
"""FocusGate v3.1 Loop 52 Test Suite — Merkle Proof Verification & State Attestation."""
import os
import sys
import hashlib
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.consensus.merkle_attestation import (
    build_merkle_tree,
    generate_inclusion_proof,
    verify_inclusion_proof,
    StateAttestation,
    MeshStateAttestor,
)


class TestMerkleInclusionProof(unittest.TestCase):
    def setUp(self):
        self.raw_items = ["event-alpha", "event-beta", "event-gamma", "event-delta"]
        self.leaf_hashes = [hashlib.sha256(item.encode()).hexdigest() for item in self.raw_items]

    def test_build_tree_and_root(self):
        root, levels = build_merkle_tree(self.leaf_hashes)
        self.assertTrue(isinstance(root, str))
        self.assertEqual(len(root), 64)
        self.assertEqual(len(levels[0]), 4)
        self.assertEqual(levels[-1][0], root)

    def test_valid_inclusion_proofs_all_leaves(self):
        root, levels = build_merkle_tree(self.leaf_hashes)
        for i, leaf in enumerate(self.leaf_hashes):
            proof = generate_inclusion_proof(i, levels)
            self.assertTrue(verify_inclusion_proof(leaf, proof, root))

    def test_tampered_leaf_fails(self):
        root, levels = build_merkle_tree(self.leaf_hashes)
        proof = generate_inclusion_proof(0, levels)
        tampered_leaf = hashlib.sha256(b"fraudulent-event").hexdigest()
        self.assertFalse(verify_inclusion_proof(tampered_leaf, proof, root))

    def test_odd_number_of_leaves(self):
        odd_leaves = self.leaf_hashes[:3]
        root, levels = build_merkle_tree(odd_leaves)
        for i, leaf in enumerate(odd_leaves):
            proof = generate_inclusion_proof(i, levels)
            self.assertTrue(verify_inclusion_proof(leaf, proof, root))


class TestStateAttestor(unittest.TestCase):
    def test_attestation_signature_and_verification(self):
        attestor = MeshStateAttestor(secret="swarm-cluster-key")
        att = attestor.create_attestation(
            epoch=1,
            state_root="a" * 64,
            node_id="node-1",
        )
        self.assertTrue(att.verify(secret="swarm-cluster-key"))
        self.assertFalse(att.verify(secret="wrong-secret"))

    def test_quorum_attestations(self):
        attestor = MeshStateAttestor(secret="shared-key")
        state_root = "b" * 64

        # 3 nodes in cluster, need 2 for 2/3 supermajority
        att1 = attestor.create_attestation(epoch=5, state_root=state_root, node_id="node-1")
        att2 = attestor.create_attestation(epoch=5, state_root=state_root, node_id="node-2")
        att3_divergent = attestor.create_attestation(epoch=5, state_root="c" * 64, node_id="node-3")

        self.assertTrue(attestor.add_attestation(att1))
        self.assertTrue(attestor.add_attestation(att2))
        self.assertTrue(attestor.add_attestation(att3_divergent))

        # Check quorum for state_root: 2 of 3 nodes agree -> True
        self.assertTrue(attestor.has_quorum_attestation(epoch=5, state_root=state_root, total_nodes=3))
        # Divergent root only has 1 node -> False
        self.assertFalse(attestor.has_quorum_attestation(epoch=5, state_root="c" * 64, total_nodes=3))


class TestMerkleAttestationCLI(unittest.TestCase):
    def test_cli_verify_attestation_valid(self):
        import subprocess
        import json
        cmd = [
            sys.executable,
            os.path.join(ROOT, "scripts", "focus-gate.py"),
            "--verify-attestation",
            "dummy-event",
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["verified"])
        self.assertIn("state_root", data)

    def test_cli_verify_attestation_forged(self):
        import subprocess
        import json
        cmd = [
            sys.executable,
            os.path.join(ROOT, "scripts", "focus-gate.py"),
            "--verify-attestation",
            "dummy-event",
            "f" * 64,
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stdout)
        self.assertFalse(data["verified"])


if __name__ == "__main__":
    unittest.main()
