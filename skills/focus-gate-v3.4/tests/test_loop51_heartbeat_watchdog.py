#!/usr/bin/env python3
"""FocusGate v3.1 Loop 51 Test Suite — Dynamic Swarm Actor Heartbeat & Adaptive Liveness Watchdog."""
import os
import sys
import time
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.grid.heartbeat_watchdog import (
    ActorHeartbeatRecord,
    ActorLivenessPolicy,
    DeadlockDetector,
    SwarmHeartbeatMonitor,
)


class TestActorHeartbeatRecord(unittest.TestCase):
    def test_record_initialization_and_touch(self):
        record = ActorHeartbeatRecord(actor_id="actor-tester-01")
        self.assertEqual(record.actor_id, "actor-tester-01")
        self.assertEqual(record.status, "ALIVE")
        t0 = record.last_beat_ts
        time.sleep(0.01)
        record.touch(cpu_delta_ms=12.5, pending=2)
        self.assertGreater(record.last_beat_ts, t0)
        self.assertEqual(record.cpu_time_ms, 12.5)
        self.assertEqual(record.pending_tasks, 2)

    def test_is_expired(self):
        now = 100.0
        record = ActorHeartbeatRecord(actor_id="actor-test", last_beat_ts=90.0)
        self.assertFalse(record.is_expired(now=94.0, timeout=5.0))
        self.assertTrue(record.is_expired(now=96.0, timeout=5.0))


class TestActorLivenessPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = ActorLivenessPolicy(
            warning_timeout=2.0,
            hung_timeout=5.0,
            dead_timeout=10.0,
            auto_recycle=True,
        )

    def test_evaluate_status_alive(self):
        record = ActorHeartbeatRecord("a1", last_beat_ts=100.0)
        self.assertEqual(self.policy.evaluate_status(record, now=101.0), "ALIVE")

    def test_evaluate_status_degraded(self):
        record = ActorHeartbeatRecord("a1", last_beat_ts=100.0)
        self.assertEqual(self.policy.evaluate_status(record, now=103.0), "DEGRADED")

    def test_evaluate_status_hung(self):
        record = ActorHeartbeatRecord("a1", last_beat_ts=100.0)
        self.assertEqual(self.policy.evaluate_status(record, now=106.0), "HUNG")

    def test_evaluate_status_dead(self):
        record = ActorHeartbeatRecord("a1", last_beat_ts=100.0)
        self.assertEqual(self.policy.evaluate_status(record, now=112.0), "DEAD")


class TestDeadlockDetector(unittest.TestCase):
    def test_no_cycle(self):
        detector = DeadlockDetector()
        detector.add_wait_dependency("actor-A", "actor-B")
        detector.add_wait_dependency("actor-B", "actor-C")
        cycles = detector.detect_cycles()
        self.assertEqual(len(cycles), 0)

    def test_simple_cycle_detection(self):
        detector = DeadlockDetector()
        detector.add_wait_dependency("actor-1", "actor-2")
        detector.add_wait_dependency("actor-2", "actor-1")
        cycles = detector.detect_cycles()
        self.assertGreaterEqual(len(cycles), 1)
        cycle_actors = set(cycles[0])
        self.assertTrue({"actor-1", "actor-2"}.issubset(cycle_actors))

    def test_transitive_cycle_detection(self):
        detector = DeadlockDetector()
        detector.add_wait_dependency("A", "B")
        detector.add_wait_dependency("B", "C")
        detector.add_wait_dependency("C", "A")
        cycles = detector.detect_cycles()
        self.assertGreaterEqual(len(cycles), 1)
        self.assertEqual(set(cycles[0][:3]), {"A", "B", "C"})

    def test_clear_dependency(self):
        detector = DeadlockDetector()
        detector.add_wait_dependency("A", "B")
        detector.add_wait_dependency("B", "A")
        detector.remove_dependency("A", "B")
        self.assertEqual(len(detector.detect_cycles()), 0)


class TestSwarmHeartbeatMonitor(unittest.TestCase):
    def test_monitor_lifecycle_and_sweep(self):
        monitor = SwarmHeartbeatMonitor(
            policy=ActorLivenessPolicy(warning_timeout=1.0, hung_timeout=2.0, dead_timeout=4.0, auto_recycle=True)
        )
        monitor.register_actor("worker-1")
        monitor.register_actor("worker-2")

        # Initial check at t=0
        report = monitor.check_liveness(now=time.time())
        self.assertEqual(report["total_actors"], 2)
        self.assertEqual(report["alive_count"], 2)
        self.assertEqual(report["hung_count"], 0)
        self.assertEqual(report["dead_count"], 0)
        self.assertEqual(len(report["deadlocks"]), 0)

        # Simulate time jump: worker-1 beats, worker-2 is hung
        now = time.time() + 2.5
        monitor.record_heartbeat("worker-1", ts=now)
        report2 = monitor.check_liveness(now=now)
        self.assertEqual(report2["alive_count"], 1)
        self.assertEqual(report2["hung_count"], 1)

    def test_monitor_auto_recycle(self):
        monitor = SwarmHeartbeatMonitor(
            policy=ActorLivenessPolicy(warning_timeout=1.0, hung_timeout=2.0, dead_timeout=3.0, auto_recycle=True)
        )
        recycled = []
        monitor.on_actor_recycled = lambda actor_id: recycled.append(actor_id)

        monitor.register_actor("zombie-actor")
        report = monitor.check_liveness(now=time.time() + 5.0)
        self.assertIn("zombie-actor", recycled)
        self.assertIn("zombie-actor", report["recycled_actors"])


class TestSwarmLivenessCLI(unittest.TestCase):
    def test_cli_swarm_liveness_json(self):
        import subprocess
        import json
        cmd = [sys.executable, os.path.join(ROOT, "scripts", "focus-gate.py"), "--swarm-liveness", "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["total_actors"], 4)
        self.assertEqual(data["alive_count"], 4)
        self.assertEqual(data["dead_count"], 0)


if __name__ == "__main__":
    unittest.main()
