#!/usr/bin/env python3
"""FocusGate v2.8 — Loop 8 Deepening & Hardening Test Suite (TDD Contract)."""

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


class TestAsyncAndMultiLanguageUnlazyGuard(unittest.TestCase):
    def test_async_python_empty_function_detected(self):
        from core.unlazy_guard import ExecutionRigorGuard

        code_pass = "async def fetch_user_data(user_id: int) -> dict:\n    pass\n"
        res = ExecutionRigorGuard.scan_for_laziness(code_pass)
        self.assertFalse(res.is_valid, "Failed to catch async def ... pass")
        self.assertTrue(any(v.violation_type == "EMPTY_FUNCTION_STUB" for v in res.violations))

        code_ellipsis = "async def execute_task():\n    ...\n"
        res2 = ExecutionRigorGuard.scan_for_laziness(code_ellipsis)
        self.assertFalse(res2.is_valid, "Failed to catch async def ... ...")
        self.assertTrue(any(v.violation_type == "EMPTY_FUNCTION_STUB" for v in res2.violations))

    def test_js_ts_empty_function_detected(self):
        from core.unlazy_guard import ExecutionRigorGuard

        code_ts_arrow = "const handlePayment = async (orderId: string) => {}\n"
        res = ExecutionRigorGuard.scan_for_laziness(code_ts_arrow)
        self.assertFalse(res.is_valid, "Failed to catch TS arrow function stub")
        self.assertTrue(any(v.violation_type == "EMPTY_FUNCTION_STUB" for v in res.violations))

        code_js_func = "function submitForm(event) {}\n"
        res2 = ExecutionRigorGuard.scan_for_laziness(code_js_func)
        self.assertFalse(res2.is_valid, "Failed to catch JS function stub")
        self.assertTrue(any(v.violation_type == "EMPTY_FUNCTION_STUB" for v in res2.violations))

    def test_expanded_trivial_check_commands_rejected(self):
        from core.unlazy_guard import ExecutionRigorGuard
        from types import SimpleNamespace

        trivial_cmds = ["echo ok", "echo true", "echo 1", "echo done", "exit", "return", "python3 -c ''"]
        for cmd in trivial_cmds:
            gate = SimpleNamespace(check_cmd=cmd)
            is_valid, reasons = ExecutionRigorGuard.validate_completion(gate)
            self.assertFalse(is_valid, f"Command '{cmd}' should be rejected as trivial")
            self.assertTrue(any("TRIVIAL_CHECK_COMMAND" in r for r in reasons))


class TestContextBusOnDiskCompaction(unittest.TestCase):
    def test_evicted_deltas_do_not_resurrect_across_processes(self):
        from core.context_bus import SharedContextBus, ContextDeltaEvent

        with tempfile.TemporaryDirectory() as td:
            bus1 = SharedContextBus(workspace_root=td)
            d1 = ContextDeltaEvent.create(
                source_agent="gate-1",
                delta_type="REORIENT",
                content="Task gate-1 in progress"
            )
            d2 = ContextDeltaEvent.create(
                source_agent="orchestrator",
                delta_type="DOMAIN_ANCHOR",
                content="System initialized"
            )
            bus1.publish(d1)
            bus1.publish(d2)

            self.assertEqual(len(bus1.get_all_deltas()), 2)

            # Evict settled gate-1
            pruned = bus1.evict_settled("gate-1")
            self.assertEqual(pruned, 1)
            self.assertEqual(len(bus1.get_all_deltas()), 1)

            # Instantiate a fresh SharedContextBus instance simulating a new process
            bus2 = SharedContextBus(workspace_root=td)
            deltas2 = bus2.get_all_deltas()
            # The evicted delta MUST NOT be present on disk
            self.assertEqual(len(deltas2), 1, "Evicted delta was resurrected from uncompacted on-disk context_bus.jsonl")
            self.assertEqual(deltas2[0].delta_type, "DOMAIN_ANCHOR")


class TestAutoStageVerificationOnMerge(unittest.TestCase):
    def test_merge_results_auto_verifies_completed_stage(self):
        from core.orchestrator_kernel import OrchestratorKernel
        from core.agent_brief import AgentReceiptBundle
        from core.ephemeral_session import GateReceipt

        with tempfile.TemporaryDirectory() as td:
            orch = OrchestratorKernel(workspace_root=td)
            orch.plan_decomposition("Build seam interface")
            first_stage = orch.stage_definitions[0]
            first_gate_id = first_stage.gate_ids[0]
            orch.aggregate.gates[first_gate_id]["status"] = "ACTIVE"

            # Mark prerequisites if any and set receipt
            receipt = GateReceipt(
                session_id="sess_test",
                gate_id=first_gate_id,
                facet=first_stage.facet,
                status="PASS",
                evidence_hash="hash_evidence_123"
            )
            bundle = AgentReceiptBundle(
                bundle_id=f"bundle-{first_gate_id}",
                gate_id=first_gate_id,
                brief_id="brief-1",
                gate_receipts=[receipt.to_dict()],
                delta_ids=[],
                artifacts_produced=[],
                patch_hashes=[],
                status="PASS"
            )
            orch.active_bundles[first_gate_id] = bundle

            # Merge results for the first gate
            merged = orch.merge_results(first_gate_id)
            self.assertTrue(merged)

            # First stage should be automatically verified
            self.assertEqual(orch.stage_definitions[0].status, "VERIFIED", "Stage was not automatically verified upon gate merge")

            # Verify stage state persisted to stages.json
            stages_file = os.path.join(td, ".focusgate", "stages.json")
            self.assertTrue(os.path.exists(stages_file))
            with open(stages_file, "r", encoding="utf-8") as f:
                saved_stages = json.load(f)
            self.assertEqual(saved_stages[0]["status"], "VERIFIED")


class TestHandoffAuditChecksumVerification(unittest.TestCase):
    def test_audit_handoff_performance_includes_checksum_verification(self):
        from core.kernel import FocusKernel
        from plugins.engineering_plugin import EngineeringPlugin
        from plugins.design_plugin import DesignPlugin

        kernel = FocusKernel()
        kernel.register_plugin(EngineeringPlugin())
        kernel.register_plugin(DesignPlugin())
        kernel.boot()

        report = kernel.audit_handoff_performance()
        self.assertIn("handoffs", report)
        self.assertGreater(len(report["handoffs"]), 0)
        for h in report["handoffs"]:
            self.assertIn("checksum_valid", h, "audit_handoff_performance record missing 'checksum_valid' verification")
            self.assertTrue(h["checksum_valid"])


if __name__ == "__main__":
    unittest.main()
