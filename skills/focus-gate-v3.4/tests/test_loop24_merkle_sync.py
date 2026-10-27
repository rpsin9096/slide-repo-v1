"""Tests for Loop 24: Merkle State Vector Consensus & Swarm Sync (Milestone 21).

Tests VectorClock causality, MerkleStateVector O(1) divergence detection,
MerkleSyncCoordinator 3-way DAG diff and deterministic synchronization,
and CLI flags --merkle-diff and --merkle-sync.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import unittest
from typing import Dict, Any

from core.merkle_ledger import MerkleEventNode, MerkleEventDAG
from core.consensus.vector_clock import VectorClock
from core.consensus.merkle_sync import MerkleStateVector, MerkleSyncCoordinator


class TestVectorClock(unittest.TestCase):
    """Test vector clock monotonic increments, causal precedence, and concurrency."""

    def test_tick_and_get(self):
        vc = VectorClock()
        self.assertEqual(vc.get("actor-1"), 0)
        self.assertEqual(vc.tick("actor-1"), 1)
        self.assertEqual(vc.get("actor-1"), 1)
        self.assertEqual(vc.tick("actor-1"), 2)
        self.assertEqual(vc.tick("actor-2"), 1)
        self.assertEqual(vc.get("actor-1"), 2)
        self.assertEqual(vc.get("actor-2"), 1)

    def test_merge(self):
        vc1 = VectorClock({"actor-1": 3, "actor-2": 1})
        vc2 = VectorClock({"actor-1": 1, "actor-2": 4, "actor-3": 2})
        merged = vc1.merge(vc2)
        self.assertEqual(merged.get("actor-1"), 3)
        self.assertEqual(merged.get("actor-2"), 4)
        self.assertEqual(merged.get("actor-3"), 2)

    def test_causality_happened_before(self):
        vc_a = VectorClock({"actor-1": 1, "actor-2": 1})
        vc_b = VectorClock({"actor-1": 2, "actor-2": 1})
        vc_c = VectorClock({"actor-1": 2, "actor-2": 2})

        self.assertTrue(vc_a.happened_before(vc_b))
        self.assertTrue(vc_b.happened_before(vc_c))
        self.assertTrue(vc_a.happened_before(vc_c))
        self.assertFalse(vc_b.happened_before(vc_a))
        self.assertFalse(vc_a.happened_before(vc_a))  # Not strictly before itself

    def test_concurrency_detection(self):
        # Branching: actor-1 advanced on branch 1, actor-2 advanced on branch 2
        vc_branch1 = VectorClock({"actor-1": 2, "actor-2": 1})
        vc_branch2 = VectorClock({"actor-1": 1, "actor-2": 2})

        self.assertTrue(vc_branch1.is_concurrent(vc_branch2))
        self.assertTrue(vc_branch2.is_concurrent(vc_branch1))
        self.assertFalse(vc_branch1.happened_before(vc_branch2))
        self.assertFalse(vc_branch2.happened_before(vc_branch1))

    def test_serialization_and_hash(self):
        vc = VectorClock({"actor-b": 2, "actor-a": 1})
        d = vc.to_dict()
        vc_copy = VectorClock.from_dict(d)
        self.assertEqual(vc.clock, vc_copy.clock)
        self.assertEqual(vc.hash(), vc_copy.hash())
        self.assertTrue(len(vc.hash()) == 64)


class TestMerkleStateVector(unittest.TestCase):
    """Test MerkleStateVector O(1) comparison and summary hashes."""

    def test_summary_hash_constant_time_comparison(self):
        vc = VectorClock({"actor-1": 1})
        vec1 = MerkleStateVector(
            actor_id="actor-1",
            vector_clock=vc,
            state_root="a" * 64,
            tip_hash="b" * 64,
            event_count=5
        )
        vec2 = MerkleStateVector(
            actor_id="actor-1",
            vector_clock=VectorClock({"actor-1": 1}),
            state_root="a" * 64,
            tip_hash="b" * 64,
            event_count=5
        )
        vec3 = MerkleStateVector(
            actor_id="actor-1",
            vector_clock=VectorClock({"actor-1": 2}),
            state_root="a" * 64,
            tip_hash="c" * 64,
            event_count=6
        )

        self.assertEqual(vec1.summary_hash(), vec2.summary_hash())
        self.assertNotEqual(vec1.summary_hash(), vec3.summary_hash())

    def test_from_dag(self):
        dag = MerkleEventDAG()
        dag.append("TASK_INIT", {"task": "test-1"})
        dag.append("GATE_CHECKED", {"gate": "gate-1"})

        vc = VectorClock({"actor-1": 2})
        vec = MerkleStateVector.from_dag(dag, actor_id="actor-1", vector_clock=vc)

        self.assertEqual(vec.actor_id, "actor-1")
        self.assertEqual(vec.event_count, 2)
        self.assertEqual(vec.state_root, dag.compute_state_root())
        self.assertEqual(vec.tip_hash, dag.tip_hash)
        self.assertEqual(vec.vector_clock.get("actor-1"), 2)


class TestMerkleSyncCoordinator(unittest.TestCase):
    """Test DAG diffing and synchronization."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_sync_test_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_vector_diff_status(self):
        coord = MerkleSyncCoordinator()

        # Identical
        vc = VectorClock({"node-1": 1})
        v1 = MerkleStateVector("node-1", vc, "root-a", "tip-a", 1)
        v2 = MerkleStateVector("node-2", VectorClock({"node-1": 1}), "root-a", "tip-a", 1)
        diff = coord.diff_vectors(v1, v2)
        self.assertEqual(diff["status"], "IDENTICAL")

        # Local ahead
        v_local_ahead = MerkleStateVector("node-1", VectorClock({"node-1": 2}), "root-b", "tip-b", 2)
        diff_ahead = coord.diff_vectors(v_local_ahead, v1)
        self.assertEqual(diff_ahead["status"], "LOCAL_AHEAD")

        # Remote ahead
        diff_behind = coord.diff_vectors(v1, v_local_ahead)
        self.assertEqual(diff_behind["status"], "REMOTE_AHEAD")

        # Divergent / Concurrent
        v_branch_a = MerkleStateVector("node-1", VectorClock({"node-1": 2, "node-2": 1}), "root-c", "tip-c", 3)
        v_branch_b = MerkleStateVector("node-2", VectorClock({"node-1": 1, "node-2": 2}), "root-d", "tip-d", 3)
        diff_divergent = coord.diff_vectors(v_branch_a, v_branch_b)
        self.assertEqual(diff_divergent["status"], "DIVERGENT")

    def test_dag_diff_fast_forward(self):
        dag_local = MerkleEventDAG()
        n1 = dag_local.append("INIT", {"v": 1})

        dag_remote = MerkleEventDAG()
        # Remote shares n1 then adds n2 and n3
        dag_remote.nodes.append(n1)
        dag_remote.tip_hash = n1.node_hash
        n2 = dag_remote.append("STEP_1", {"v": 2})
        n3 = dag_remote.append("STEP_2", {"v": 3})

        coord = MerkleSyncCoordinator()
        diff = coord.compute_dag_diff(dag_local, dag_remote)

        self.assertEqual(diff["common_ancestor_hash"], n1.node_hash)
        self.assertEqual(len(diff["local_only_events"]), 0)
        self.assertEqual(len(diff["remote_only_events"]), 2)
        self.assertFalse(diff["divergent"])

    def test_dag_sync_fast_forward(self):
        dag_local = MerkleEventDAG()
        n1 = dag_local.append("INIT", {"v": 1})

        dag_remote = MerkleEventDAG()
        dag_remote.nodes.append(n1)
        dag_remote.tip_hash = n1.node_hash
        dag_remote.append("STEP_1", {"v": 2})
        dag_remote.append("STEP_2", {"v": 3})

        coord = MerkleSyncCoordinator()
        res = coord.sync_dags(dag_local, dag_remote)

        self.assertEqual(res["status"], "SYNCED")
        self.assertEqual(res["events_merged"], 2)
        self.assertEqual(len(dag_local.nodes), 3)
        self.assertEqual(dag_local.compute_state_root(), dag_remote.compute_state_root())

        # Verify integrity of newly synced DAG
        valid, err = dag_local.verify_integrity()
        self.assertTrue(valid, err)

    def test_dag_sync_divergent_branches(self):
        # Genesis node
        n_genesis = MerkleEventNode.create("GENESIS", {"repo": "test"})

        dag_a = MerkleEventDAG()
        dag_a.nodes.append(n_genesis)
        dag_a.tip_hash = n_genesis.node_hash
        na1 = dag_a.append("ACTOR_A_WORK", {"work": "task-a"}, event_id="evt-a1")

        dag_b = MerkleEventDAG()
        dag_b.nodes.append(n_genesis)
        dag_b.tip_hash = n_genesis.node_hash
        nb1 = dag_b.append("ACTOR_B_WORK", {"work": "task-b"}, event_id="evt-b1")

        coord = MerkleSyncCoordinator()
        diff = coord.compute_dag_diff(dag_a, dag_b)
        self.assertTrue(diff["divergent"])
        self.assertEqual(diff["common_ancestor_hash"], n_genesis.node_hash)
        self.assertEqual(len(diff["local_only_events"]), 1)
        self.assertEqual(len(diff["remote_only_events"]), 1)

        # Merge dag_b into dag_a
        res = coord.sync_dags(dag_a, dag_b)
        self.assertEqual(res["status"], "SYNCED")
        self.assertEqual(res["conflicts_resolved"], 1)
        self.assertEqual(len(dag_a.nodes), 3)

        # Confirm cryptographic integrity is preserved after merge
        valid, err = dag_a.verify_integrity()
        self.assertTrue(valid, err)

    def test_file_diff_and_sync(self):
        file1 = os.path.join(self.temp_dir, "ledger1.events.jsonl")
        file2 = os.path.join(self.temp_dir, "ledger2.events.jsonl")

        dag1 = MerkleEventDAG(ledger_path=file1)
        dag1.append("INIT", {"val": 1})

        # Copy dag1 to dag2, then add to dag2
        shutil.copyfile(file1, file2)
        dag2 = MerkleEventDAG.load_from_file(file2)
        dag2.append("UPDATE_FROM_ACTOR_2", {"val": 2})

        coord = MerkleSyncCoordinator()
        diff = coord.diff_files(file1, file2)
        self.assertFalse(diff["divergent"])
        self.assertEqual(len(diff["remote_only_events"]), 1)

        # Sync file2 into file1
        sync_res = coord.sync_files(file1, file2)
        self.assertEqual(sync_res["status"], "SYNCED")

        # Reload file1 and assert it now has 2 nodes and valid integrity
        reloaded1 = MerkleEventDAG.load_from_file(file1)
        self.assertEqual(len(reloaded1.nodes), 2)
        valid, err = reloaded1.verify_integrity()
        self.assertTrue(valid, err)


class TestMerkleSyncCLI(unittest.TestCase):
    """Test CLI integration of --merkle-diff and --merkle-sync."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_cli_sync_test_")
        self.file1 = os.path.join(self.temp_dir, "node1.events.jsonl")
        self.file2 = os.path.join(self.temp_dir, "node2.events.jsonl")

        d1 = MerkleEventDAG(ledger_path=self.file1)
        d1.append("EVENT_1", {"msg": "hello"})

        shutil.copyfile(self.file1, self.file2)
        d2 = MerkleEventDAG.load_from_file(self.file2)
        d2.append("EVENT_2", {"msg": "world"})

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_diff_json(self):
        from core.cli.dispatch import CLIDispatcher
        from types import SimpleNamespace

        args = SimpleNamespace(merkle_diff=True, merkle_sync=None)
        clean_args = ["--merkle-diff", self.file1, self.file2, "--json"]

        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertIn("common_ancestor_hash", output)
        self.assertEqual(len(output["remote_only_events"]), 1)

    def test_cli_sync(self):
        from core.cli.dispatch import CLIDispatcher
        from types import SimpleNamespace

        args = SimpleNamespace(merkle_sync=True, merkle_diff=None)
        clean_args = ["--merkle-sync", self.file1, self.file2, "--json"]

        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["status"], "SYNCED")
        self.assertEqual(output["events_merged"], 1)


if __name__ == '__main__':
    unittest.main()
