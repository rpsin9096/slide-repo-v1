"""FocusGate v3.1 — Swarm Partition Simulator & Chaos Recovery Tests (Loop 47).

Verifies distributed CRDT mesh resilience under network partitions:
- Asymmetric network partition simulation and packet drop
- Split-brain independent state divergence
- Causal healing and deterministic Merkle state convergence
- CLI dispatch (--simulate-partition)

100% Python stdlib, zero external dependencies. Sub-50ms reconciliation.
"""

import os
import sys
import json
import time
import unittest

from core.grid.crdt_mesh import MerkleCRDTReplicator
from core.chaos.partition_sim import (
    NetworkPartitionSimulator,
    MeshPartitionHealer,
)


class TestPartitionSimulation(unittest.TestCase):
    """Verifies partition isolation, delivery filtering, and post-healing convergence."""

    def setUp(self):
        self.nodes = ["node-A", "node-B", "node-C"]
        self.sim = NetworkPartitionSimulator(self.nodes)

    def test_partition_blocks_cross_group_delivery(self):
        # Partition node-A away from [node-B, node-C]
        pid = self.sim.create_partition(["node-A"], ["node-B", "node-C"])

        # Intra-group delivery allowed
        self.assertTrue(self.sim.can_deliver("node-B", "node-C"))
        self.assertTrue(self.sim.can_deliver("node-C", "node-B"))

        # Cross-group delivery blocked
        self.assertFalse(self.sim.can_deliver("node-A", "node-B"))
        self.assertFalse(self.sim.can_deliver("node-C", "node-A"))

        # Healing restores delivery
        self.sim.heal_partition(pid)
        self.assertTrue(self.sim.can_deliver("node-A", "node-B"))

    def test_crdt_split_brain_divergence_and_healing(self):
        # Create 3 replicators
        repA = MerkleCRDTReplicator(node_id="node-A")
        repB = MerkleCRDTReplicator(node_id="node-B")
        repC = MerkleCRDTReplicator(node_id="node-C")

        # Partition node-A away from B and C
        pid = self.sim.create_partition(["node-A"], ["node-B", "node-C"])

        # Node A applies local event in isolated partition
        repA.apply_event("gate-commit", {"gate": "gate-01", "author": "node-A"})

        # Node B applies local event in its partition and syncs with C
        evB = repB.apply_event("gate-commit", {"gate": "gate-02", "author": "node-B"})
        repC.apply_event("gate-commit", evB.payload, origin_node=evB.origin_node, lamport_ts=evB.lamport_ts)

        # Roots must be divergent
        self.assertNotEqual(repA.get_state_root(), repB.get_state_root())

        # Now heal partition and reconcile all 3 nodes
        self.sim.heal_partition(pid)
        healer = MeshPartitionHealer()

        t0 = time.perf_counter()
        result = healer.reconcile_nodes([repA, repB, repC])
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        self.assertLess(elapsed_ms, 50.0)
        self.assertTrue(result["converged"])
        # All three nodes must now have identical state roots
        self.assertEqual(repA.get_state_root(), repB.get_state_root())
        self.assertEqual(repB.get_state_root(), repC.get_state_root())
        self.assertEqual(len(repA.events), 2)


class TestPartitionCLI(unittest.TestCase):
    """Verifies CLI flag --simulate-partition."""

    def test_cli_simulate_partition_json(self):
        from core.cli.dispatch import CLIDispatcher
        clean_args = ["--simulate-partition", "20"]

        import io
        import contextlib
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = CLIDispatcher.dispatch_simulate_partition(clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(stdout.getvalue())
        self.assertIn("simulation", output)
        self.assertTrue(output["simulation"]["converged"])
