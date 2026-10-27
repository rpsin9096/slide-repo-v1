"""FocusGate v3.0 — Sub-Second Wave Barrier Convergence & Ring Buffer Tests (Loop 37).

Verifies zero-dependency high-throughput ring buffer and sub-second multi-actor
wave barrier synchronization.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import json
import time
import threading
import unittest

from core.perf.ring_buffer import AtomicEventRingBuffer
from core.perf.wave_barrier import HighThroughputWaveBarrier, BarrierConvergenceReceipt


class TestRingBuffer(unittest.TestCase):
    """Verifies lock-efficient circular event ring buffer."""

    def test_buffer_push_and_latest(self):
        buf = AtomicEventRingBuffer(capacity=5)
        for i in range(3):
            buf.push({"msg": f"event_{i}"})

        self.assertEqual(buf.size(), 3)
        self.assertEqual(buf.total_pushed(), 3)
        latest = buf.latest(count=2)
        self.assertEqual(len(latest), 2)
        self.assertEqual(latest[-1][1]["msg"], "event_2")

    def test_buffer_wrap_around_overwrites_oldest(self):
        buf = AtomicEventRingBuffer(capacity=4)
        for i in range(10):
            buf.push({"idx": i})

        self.assertEqual(buf.size(), 4)
        self.assertEqual(buf.total_pushed(), 10)
        latest = buf.latest(count=4)
        indices = [item[1]["idx"] for item in latest]
        self.assertEqual(indices, [6, 7, 8, 9])

    def test_buffer_read_since(self):
        buf = AtomicEventRingBuffer(capacity=10)
        seqs = []
        for i in range(5):
            s = buf.push({"val": i})
            seqs.append(s)

        # Read since sequence 2
        items = buf.read_since(seq_num=seqs[1])
        self.assertEqual(len(items), 3)
        vals = [it[1]["val"] for it in items]
        self.assertEqual(vals, [2, 3, 4])

    def test_concurrent_push_thread_safety(self):
        buf = AtomicEventRingBuffer(capacity=500)
        num_threads = 5
        pushes_per_thread = 100

        def worker(tid):
            for i in range(pushes_per_thread):
                buf.push({"thread": tid, "val": i})

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(buf.total_pushed(), num_threads * pushes_per_thread)
        self.assertEqual(buf.size(), 500)


class TestWaveBarrier(unittest.TestCase):
    """Verifies sub-second wave barrier synchronization and metrics."""

    def test_barrier_convergence_under_200ms(self):
        actors = ["actor-arch-01", "actor-coder-01", "actor-verify-01", "actor-remed-01"]
        barrier = HighThroughputWaveBarrier(wave_id="wave-fast-01", expected_actors=actors)

        results = []

        def actor_run(aid, delay):
            time.sleep(delay)
            receipt = barrier.arrive_and_wait(actor_id=aid, timeout_sec=1.0)
            results.append(receipt)

        delays = [0.01, 0.02, 0.03, 0.04]
        threads = [
            threading.Thread(target=actor_run, args=(aid, d))
            for aid, d in zip(actors, delays)
        ]

        t0 = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total_wall_sec = time.time() - t0

        # Entire wave should converge well within 200ms
        self.assertLess(total_wall_sec, 0.25)
        self.assertEqual(len(results), 4)

        receipt = results[0]
        self.assertTrue(receipt.converged)
        self.assertEqual(receipt.total_actors, 4)
        self.assertLess(receipt.latency_ms, 200.0)
        self.assertEqual(receipt.slowest_actor, "actor-remed-01")

    def test_barrier_timeout_when_actor_missing(self):
        actors = ["actor-1", "actor-2"]
        barrier = HighThroughputWaveBarrier(wave_id="wave-timeout-01", expected_actors=actors)

        # Only actor-1 arrives
        receipt = barrier.arrive_and_wait(actor_id="actor-1", timeout_sec=0.08)
        self.assertFalse(receipt.converged)
        self.assertEqual(receipt.arrived_count, 1)


class TestPerfCLI(unittest.TestCase):
    """Verifies CLI barrier benchmark execution."""

    def test_cli_barrier_bench_json(self):
        from core.cli.dispatch import CLIDispatcher
        clean_args = ["--barrier-bench", "4"]

        import io
        import contextlib
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = CLIDispatcher.dispatch_barrier_bench(clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(stdout.getvalue())
        self.assertTrue(output.get("converged"))
        self.assertEqual(output.get("total_actors"), 4)
        self.assertLess(output.get("latency_ms"), 300.0)
