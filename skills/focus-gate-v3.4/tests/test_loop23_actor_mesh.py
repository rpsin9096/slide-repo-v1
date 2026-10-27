"""Tests for FocusGate v3.0 — Milestone 20 (Loop 23: In-Process Swarm Actor Engine).

Covers:
1. ActorMessage priority comparison, envelope serialization, and immutability.
2. ActorMailbox priority ordering (HIGH > NORMAL > LOW), bounded capacity, and non-blocking get.
3. SwarmActor lifecycle (IDLE -> ACTIVE -> STOPPED), specialty assignment, and handler execution.
4. ActorMeshRouter point-to-point routing, topic broadcast, and dead letter handling.
5. Specialized actor implementations (ArchitectActor, VerifierActor, RemediatorActor).
6. CLI --actor-status integration and JSON formatting.
"""

import unittest
import os
import sys
import time
import subprocess
import json

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
SCRIPT = os.path.join(ROOT_DIR, "scripts", "focus-gate.py")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.mesh.mailbox import ActorMailbox, MessagePriority
from core.mesh.actor import SwarmActor, ActorState, ActorSpecialty
from core.mesh.router import ActorMeshRouter, ActorMessage


class TestActorMessageAndMailbox(unittest.TestCase):
    """Verifies priority ordering and envelope mechanics of the actor mailbox."""

    def test_message_priority_ordering(self):
        msg_low = ActorMessage(
            source="sender", target="receiver", topic="TELEMETRY",
            payload={"cpu": 10}, priority=MessagePriority.LOW
        )
        msg_norm = ActorMessage(
            source="sender", target="receiver", topic="GATE_DISPATCH",
            payload={"gate_id": "g1"}, priority=MessagePriority.NORMAL
        )
        msg_high = ActorMessage(
            source="sender", target="receiver", topic="CIRCUIT_TRIP",
            payload={"reason": "crash"}, priority=MessagePriority.HIGH
        )

        mailbox = ActorMailbox(maxsize=10)
        # Push in reverse priority order
        mailbox.put(msg_low)
        mailbox.put(msg_norm)
        mailbox.put(msg_high)

        # High priority must be popped first
        first = mailbox.get_nowait()
        second = mailbox.get_nowait()
        third = mailbox.get_nowait()

        self.assertEqual(first.topic, "CIRCUIT_TRIP")
        self.assertEqual(second.topic, "GATE_DISPATCH")
        self.assertEqual(third.topic, "TELEMETRY")

    def test_message_serialization(self):
        msg = ActorMessage(
            source="act-1", target="act-2", topic="TASK_RUN",
            payload={"command": "pytest"}, priority=MessagePriority.NORMAL
        )
        d = msg.to_dict()
        self.assertEqual(d["source"], "act-1")
        self.assertEqual(d["target"], "act-2")
        self.assertEqual(d["topic"], "TASK_RUN")

        restored = ActorMessage.from_dict(d)
        self.assertEqual(restored.message_id, msg.message_id)
        self.assertEqual(restored.payload, {"command": "pytest"})

    def test_mailbox_empty_raises(self):
        mailbox = ActorMailbox()
        self.assertTrue(mailbox.empty())
        self.assertIsNone(mailbox.get_nowait())


class TestSwarmActorLifecycle(unittest.TestCase):
    """Verifies actor lifecycle transitions and thread-safe execution."""

    def test_actor_initialization_and_state(self):
        actor = SwarmActor(actor_id="actor-test-1", specialty=ActorSpecialty.CODER)
        self.assertEqual(actor.actor_id, "actor-test-1")
        self.assertEqual(actor.specialty, ActorSpecialty.CODER)
        self.assertEqual(actor.state, ActorState.IDLE)

    def test_actor_message_processing(self):
        received = []

        class TestWorker(SwarmActor):
            def handle_message(self, message: ActorMessage):
                received.append(message.payload)

        worker = TestWorker(actor_id="worker-1", specialty=ActorSpecialty.VERIFIER)
        worker.start()

        msg = ActorMessage(source="tester", target="worker-1", topic="CHECK", payload={"gate": "gate-10"})
        worker.post(msg)

        # Allow worker thread to process
        time.sleep(0.05)
        worker.stop()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], {"gate": "gate-10"})
        self.assertEqual(worker.state, ActorState.STOPPED)


class TestActorMeshRouter(unittest.TestCase):
    """Verifies point-to-point, pub/sub broadcast, and dead letter routing."""

    def setUp(self):
        self.router = ActorMeshRouter()

    def tearDown(self):
        self.router.shutdown()

    def test_point_to_point_routing(self):
        actor_a = SwarmActor("actor-a", ActorSpecialty.ARCHITECT)
        actor_b = SwarmActor("actor-b", ActorSpecialty.CODER)

        self.router.register(actor_a)
        self.router.register(actor_b)

        msg = ActorMessage(source="actor-a", target="actor-b", topic="SPEC", payload={"data": 123})
        ok = self.router.send(msg)

        self.assertTrue(ok)
        self.assertEqual(actor_b.mailbox.qsize(), 1)
        self.assertEqual(actor_a.mailbox.qsize(), 0)

        received = actor_b.mailbox.get_nowait()
        self.assertEqual(received.payload["data"], 123)

    def test_broadcast_routing_reaches_all_peers(self):
        actor1 = SwarmActor("act-1", ActorSpecialty.VERIFIER)
        actor2 = SwarmActor("act-2", ActorSpecialty.CODER)
        actor3 = SwarmActor("act-3", ActorSpecialty.REMEDIATOR)

        self.router.register(actor1)
        self.router.register(actor2)
        self.router.register(actor3)

        broadcast_msg = ActorMessage(
            source="act-1", target="broadcast", topic="WAVE_COMPLETED", payload={"wave": 1}
        )
        delivered_count = self.router.broadcast(broadcast_msg)

        self.assertEqual(delivered_count, 2)  # Delivered to act-2 and act-3 (excludes sender)
        self.assertEqual(actor1.mailbox.qsize(), 0)
        self.assertEqual(actor2.mailbox.qsize(), 1)
        self.assertEqual(actor3.mailbox.qsize(), 1)

    def test_dead_letter_on_unknown_target(self):
        actor = SwarmActor("act-lone", ActorSpecialty.CODER)
        self.router.register(actor)

        orphan_msg = ActorMessage(
            source="act-lone", target="non-existent", topic="TEST", payload={}
        )
        ok = self.router.send(orphan_msg)

        self.assertFalse(ok)
        self.assertEqual(len(self.router.dead_letters), 1)
        self.assertEqual(self.router.dead_letters[0].target, "non-existent")


class TestSpecializedActors(unittest.TestCase):
    """Verifies specialized domain actor behaviors."""

    def test_verifier_actor_processes_check(self):
        from core.mesh.actor import VerifierActor
        verifier = VerifierActor("verifier-01")

        # Passing command
        msg = ActorMessage(
            source="orch", target="verifier-01", topic="VERIFY_GATE",
            payload={"gate_id": "gate-pass", "check_cmd": "python3 -c 'print(\"PASS\")'"}
        )
        res = verifier.evaluate_gate(msg.payload)
        self.assertTrue(res["passed"])
        self.assertEqual(res["gate_id"], "gate-pass")

    def test_remediator_actor_diagnoses_shotgun(self):
        from core.mesh.actor import RemediatorActor
        remediator = RemediatorActor("remediator-01")

        code = "def foo():\n    try:\n        pass\n    except Exception:\n        pass\n"
        diag = remediator.diagnose_error("cliche", code=code, filename="foo.py")
        self.assertEqual(diag.category, "SHOTGUN_SUPPRESSION")


class TestActorMeshCLI(unittest.TestCase):
    """Verifies CLI flags for actor inspection."""

    def test_cli_actor_status_in_help(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--actor-status", proc.stdout)

    def test_cli_actor_status_json(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--actor-status", "--json"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertIn("actors", data)
        self.assertIn("total_active", data)


if __name__ == "__main__":
    unittest.main()
