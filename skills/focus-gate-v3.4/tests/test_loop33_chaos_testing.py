"""Tests for Loop 33: Zero-Day Fault Injection & Swarm Mesh Chaos Testing.

Tests ChaosMeshInjector packet drops, latency simulation, poisoned messages,
and PartitionRecoveryCoordinator actor revive, message replay, and split-brain resolution.

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
from typing import Dict, Any, List

from core.mesh import ActorMeshRouter, CoderActor, VerifierActor, ActorMessage, MessagePriority
from core.chaos.chaos_mesh import ChaosMeshInjector, ChaosConfig
from core.chaos.partition_recovery import PartitionRecoveryCoordinator


class TestChaosMeshInjector(unittest.TestCase):
    """Test fault injection into actor mesh routing and mailboxes."""

    def setUp(self):
        self.router = ActorMeshRouter()
        self.coder = CoderActor("coder-01")
        self.verifier = VerifierActor("verifier-01")
        self.router.register(self.coder)
        self.router.register(self.verifier)

    def test_chaos_packet_loss_drop(self):
        # Configure 100% drop rate
        config = ChaosConfig(drop_rate=1.0)
        injector = ChaosMeshInjector(self.router, config=config)

        msg = ActorMessage(
            message_id="msg-drop-1",
            priority=MessagePriority.NORMAL,
            source="coder-01",
            target="verifier-01",
            topic="CODE_PATCH",
            payload={"patch": "valid"}
        )
        routed = injector.route(msg)
        self.assertFalse(routed)
        self.assertEqual(len(injector.dropped_messages), 1)
        self.assertTrue(self.verifier.mailbox.empty())

    def test_chaos_message_poisoning(self):
        config = ChaosConfig(poison_rate=1.0)
        injector = ChaosMeshInjector(self.router, config=config)

        msg = ActorMessage(
            message_id="msg-poison-1",
            priority=MessagePriority.NORMAL,
            source="coder-01",
            target="verifier-01",
            topic="STATE_SYNC",
            payload={"hash": "original_hash"}
        )
        injector.route(msg)
        self.assertEqual(len(injector.poisoned_messages), 1)
        received = self.verifier.mailbox.get_nowait()
        self.assertIsNotNone(received)
        self.assertIn("CHAOS_CORRUPTED", str(received.payload))

    def test_chaos_actor_crash(self):
        injector = ChaosMeshInjector(self.router)
        injector.simulate_actor_crash("coder-01")
        self.assertEqual(self.coder.state, "STOPPED")
        self.assertTrue(injector.is_crashed("coder-01"))


class TestPartitionRecoveryCoordinator(unittest.TestCase):
    """Test self-healing partition recovery, actor revival, and message replay."""

    def setUp(self):
        self.router = ActorMeshRouter()
        self.coder = CoderActor("coder-01")
        self.verifier = VerifierActor("verifier-01")
        self.router.register(self.coder)
        self.router.register(self.verifier)

    def test_actor_revival_and_reconnect(self):
        config = ChaosConfig(drop_rate=0.0)
        injector = ChaosMeshInjector(self.router, config=config)
        coordinator = PartitionRecoveryCoordinator(self.router, injector=injector)

        # Crash actor
        injector.simulate_actor_crash("coder-01")
        self.assertEqual(self.coder.state, "STOPPED")

        # Recover
        revived = coordinator.recover_actor("coder-01")
        self.assertTrue(revived)
        actor = self.router.get_actor("coder-01")
        self.assertEqual(actor.state, "IDLE")

    def test_replay_dropped_messages(self):
        config = ChaosConfig(drop_rate=1.0)
        injector = ChaosMeshInjector(self.router, config=config)
        coordinator = PartitionRecoveryCoordinator(self.router, injector=injector)

        msg = ActorMessage(
            message_id="msg-replay-1",
            priority=MessagePriority.HIGH,
            source="coder-01",
            target="verifier-01",
            topic="VERIFY_REQ",
            payload={"test": "pass"}
        )
        injector.route(msg)
        self.assertEqual(len(injector.dropped_messages), 1)

        # Now heal network and replay
        injector.config.drop_rate = 0.0
        replayed_count = coordinator.replay_dead_letters()
        self.assertEqual(replayed_count, 1)
        self.assertFalse(self.verifier.mailbox.empty())
        replayed_msg = self.verifier.mailbox.get_nowait()
        self.assertEqual(replayed_msg.message_id, "msg-replay-1")


class TestChaosCLI(unittest.TestCase):
    """Test CLI dispatch for --chaos-test and --chaos-report."""

    def test_cli_chaos_test_json(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(chaos_test=["mild"], chaos_report=False)
        clean_args = ["--chaos-test", "mild", "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertIn("profile", output)
        self.assertIn("recovered", output)
        self.assertTrue(output["recovered"])


if __name__ == '__main__':
    unittest.main()
