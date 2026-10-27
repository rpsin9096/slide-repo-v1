"""FocusGate v3.1 — Distributed Merkle CRDT & Grid Networking Tests (Loop 40).

Verifies zero-dependency TCP grid sockets, delta-state Merkle CRDT synchronization,
causal convergence across distributed nodes, and CLI dispatch.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import time
import json
import unittest

from core.grid.crdt_mesh import (
    GridNode,
    MerkleCRDTReplicator,
    GridMessage
)
from core.consensus.vector_clock import VectorClock


class TestMerkleCRDTReplicator(unittest.TestCase):
    """Verifies delta-state CRDT event reconciliation and causal convergence."""

    def setUp(self):
        self.rep_a = MerkleCRDTReplicator(node_id="node-alpha")
        self.rep_b = MerkleCRDTReplicator(node_id="node-beta")

    def test_apply_local_event_increments_clock(self):
        ev = self.rep_a.apply_local_event("GATE_CHECKED", {"gate_id": "gate-1"})
        self.assertEqual(self.rep_a.vector_clock.get("node-alpha"), 1)
        self.assertIn(ev["event_id"], self.rep_a.events)
        self.assertIn("hash", ev)

    def test_reconcile_two_nodes_converges(self):
        # Node A creates event
        self.rep_a.apply_local_event("GATE_CHECKED", {"gate_id": "gate-1"})
        # Node B creates concurrent event
        self.rep_b.apply_local_event("GATE_CHECKED", {"gate_id": "gate-2"})

        # Initial divergence
        self.assertEqual(len(self.rep_a.events), 1)
        self.assertEqual(len(self.rep_b.events), 1)

        # 2-way sync
        transferred = self.rep_a.reconcile_with_peer(self.rep_b)
        self.assertGreater(transferred, 0)

        # Both nodes must converge to 2 events with identical vector clocks
        self.assertEqual(len(self.rep_a.events), 2)
        self.assertEqual(len(self.rep_b.events), 2)
        self.assertEqual(
            self.rep_a.vector_clock.to_dict(),
            self.rep_b.vector_clock.to_dict()
        )
        self.assertEqual(
            self.rep_a.get_state_root(),
            self.rep_b.get_state_root()
        )

    def test_3_node_transitive_convergence(self):
        rep_c = MerkleCRDTReplicator(node_id="node-gamma")

        self.rep_a.apply_local_event("EVENT_A", {"data": 100})
        self.rep_b.apply_local_event("EVENT_B", {"data": 200})
        rep_c.apply_local_event("EVENT_C", {"data": 300})

        # Reconcile A <-> B
        self.rep_a.reconcile_with_peer(self.rep_b)
        # Reconcile B <-> C
        self.rep_b.reconcile_with_peer(rep_c)
        # Reconcile C <-> A
        rep_c.reconcile_with_peer(self.rep_a)

        # All 3 nodes must have all 3 events and identical roots
        self.assertEqual(len(self.rep_a.events), 3)
        self.assertEqual(len(self.rep_b.events), 3)
        self.assertEqual(len(rep_c.events), 3)
        self.assertEqual(self.rep_a.get_state_root(), rep_c.get_state_root())


class TestGridNodeNetworking(unittest.TestCase):
    """Verifies TCP socket communication and real-time CRDT replication between live nodes."""

    def setUp(self):
        self.node_a = GridNode(node_id="node-srv-a", host="127.0.0.1", port=0)
        self.node_b = GridNode(node_id="node-srv-b", host="127.0.0.1", port=0)
        self.node_a.start()
        self.node_b.start()
        time.sleep(0.1)

    def tearDown(self):
        self.node_a.stop()
        self.node_b.stop()

    def test_nodes_connect_and_ping(self):
        port_a = self.node_a.server_port
        connected = self.node_b.connect_peer("127.0.0.1", port_a)
        self.assertTrue(connected)
        time.sleep(0.1)

        # Send ping
        pong = self.node_b.ping_peer(f"127.0.0.1:{port_a}")
        self.assertTrue(pong)

    def test_live_crdt_delta_broadcast_replicates(self):
        port_a = self.node_a.server_port
        self.node_b.connect_peer("127.0.0.1", port_a)
        time.sleep(0.1)

        # Node A applies an event and broadcasts
        ev = self.node_a.apply_event("GATE_AUTO_RESOLVED", {"gate_id": "gate-net-01"})
        time.sleep(0.15)

        # Node B should receive and apply delta
        self.assertIn(ev["event_id"], self.node_b.replicator.events)
        self.assertEqual(
            self.node_b.replicator.vector_clock.get("node-srv-a"),
            1
        )


class TestGridCLI(unittest.TestCase):
    """Verifies CLI flag --grid-status."""

    def test_cli_grid_status_json(self):
        from core.cli.dispatch import CLIDispatcher
        clean_args = ["--grid-status"]

        import io
        import contextlib
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = CLIDispatcher.dispatch_grid_status(clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(stdout.getvalue())
        self.assertIn("grid_status", output)
        self.assertIn("node_id", output)
