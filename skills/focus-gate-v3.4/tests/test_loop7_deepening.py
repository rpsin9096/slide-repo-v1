#!/usr/bin/env python3
"""FocusGate v2.8 — Loop 7 Deepening & Hardening Test Suite (TDD Contract)."""

import os
import sys
import json
import tempfile
import unittest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
V28_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))
if V28_ROOT not in sys.path:
    sys.path.insert(0, V28_ROOT)

SCRIPT = os.path.join(V28_ROOT, "scripts", "focus-gate.py")



def read_cli_source():
    """Text of the CLI: the entry script plus every module under core/cli (v3.4 moved the code)."""
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    paths = [os.path.join(root, "scripts", "focus-gate.py")]
    for dp, _d, fns in os.walk(os.path.join(root, "core", "cli")):
        paths += [os.path.join(dp, f) for f in sorted(fns) if f.endswith(".py")]
    out = []
    for p in paths:
        with open(p, "r", encoding="utf-8") as fh:
            out.append(fh.read())
    return "\n".join(out)


class TestStageLifecyclePersistence(unittest.TestCase):
    def test_orchestrator_persists_and_reconstructs_stages(self):
        from core.orchestrator_kernel import OrchestratorKernel
        from core.stage_matrix import StageDefinition

        with tempfile.TemporaryDirectory() as td:
            # 1. First process / instance decomposes plan and saves stages
            orch1 = OrchestratorKernel(workspace_root=td)
            orch1.plan_decomposition("Design and implement a responsive navbar")
            self.assertGreater(len(orch1.stage_definitions), 0)
            stage1_id = orch1.stage_definitions[0].stage_id

            # 2. Second process / instance loads stages from disk / aggregate
            orch2 = OrchestratorKernel(workspace_root=td)
            self.assertGreater(len(orch2.stage_definitions), 0, "Stages were not restored in new OrchestratorKernel instance")
            loaded_ids = [s.stage_id for s in orch2.stage_definitions]
            self.assertIn(stage1_id, loaded_ids)

    def test_verify_stage_updates_stage_status_to_verified(self):
        from core.stage_matrix import StageDefinition, StageVerificationMatrix

        with tempfile.TemporaryDirectory() as td:
            matrix = StageVerificationMatrix(workspace_root=td)
            stage = StageDefinition(
                stage_id="s_test",
                index=1,
                name="Test Stage",
                facet="engineering",
                gate_ids=["g_done"],
                required_artifacts=[]
            )
            agg = {"g_done": {"status": "CHECKED"}}
            self.assertEqual(stage.status, "PENDING")
            verified, reasons, evidence = matrix.verify_stage_completion(stage, agg)
            self.assertTrue(verified)
            self.assertEqual(stage.status, "VERIFIED", "StageDefinition.status was not mutated to VERIFIED upon passing")


class TestStageTransitionEventSourcing(unittest.TestCase):
    def test_verify_stage_emits_stage_verified_domain_event(self):
        from core.orchestrator_kernel import OrchestratorKernel

        with tempfile.TemporaryDirectory() as td:
            orch = OrchestratorKernel(workspace_root=td)
            orch.plan_decomposition("Build landing page feature")
            first_stage = orch.stage_definitions[0]
            # Mark all gates in first stage as CHECKED
            for gid in first_stage.gate_ids:
                orch.aggregate.gates[gid]["status"] = "CHECKED"

            # Execute verify_stage on orch
            self.assertTrue(hasattr(orch, "verify_stage"), "OrchestratorKernel lacks verify_stage method")
            success, reasons = orch.verify_stage(first_stage.stage_id)
            self.assertTrue(success, f"Stage verification failed: {reasons}")

            # Verify domain event in event store
            events = orch.event_store.get_events()
            stage_verified_events = [e for e in events if getattr(e, "event_type", "") == "STAGE_VERIFIED" or getattr(e, "type", "") == "STAGE_VERIFIED"]
            self.assertGreater(len(stage_verified_events), 0, "No STAGE_VERIFIED domain event emitted into event store")


class TestEphemeralHandoffChecksumValidation(unittest.TestCase):
    def test_handoff_packet_checksum_validation(self):
        from core.ephemeral_handoff import EphemeralHandoffPacket, HandoffChecksumMismatchError, HandoffCoordinator
        from core.ephemeral_session import GateReceipt

        receipt = GateReceipt(
            session_id="sess_123",
            gate_id="g_test",
            facet="design",
            status="PASS",
            evidence_hash="abcd1234efgh5678"
        )
        packet = EphemeralHandoffPacket(
            source_facet="design",
            target_facet="engineering",
            receipt=receipt,
            delta_payload={"key": "token_color_blue"}
        )
        self.assertTrue(hasattr(packet, "verify_checksum"), "EphemeralHandoffPacket lacks verify_checksum method")
        self.assertTrue(packet.verify_checksum())

        # Tamper with delta payload
        packet.delta_payload["key"] = "tampered_value"
        self.assertFalse(packet.verify_checksum(), "Checksum verification should fail after tampering")

        class DummyPlugin:
            id = "engineering"
            name = "EngineeringPlugin"

        with self.assertRaises(HandoffChecksumMismatchError):
            HandoffCoordinator.execute_handoff(
                source_plugin="design",
                target_plugin=DummyPlugin(),
                packet=packet
            )


class TestWaveVerificationWorktreeSufficiency(unittest.TestCase):
    def test_wave_verification_audits_dispatched_briefs_and_worktrees(self):
        cli_code = read_cli_source()
        # Verify that context_sufficiency checkpoint scans .focusgate/briefs and .focusgate/worktrees
        self.assertIn(".focusgate", cli_code)
        self.assertIn("AGENT_PROMPT.md", cli_code)


if __name__ == "__main__":
    unittest.main()
