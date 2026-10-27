"""Unit Tests for Loop 11 Distilled Router Adapter & Production Checkpoint (FocusGate v2.8).

Covers:
- Milestone 1: Pure Python stdlib safetensors parameter auditing and weight checksums.
- Milestone 2: Hexagonal ModelPort and LoRAModelAdapter routing and envelope formatting.
- Milestone 3: Orchestrator checkpoint engine model adapter provenance and cryptographic verification.
- Milestone 4: CLI argument registration and verification (--audit-adapter, --distilled-route).
- Milestone 5: Distillation benchmark evaluation scorecard (FGBench100).
"""

import unittest
import os
import sys
import json
import tempfile
import shutil

# Ensure workspace root is in sys.path
V28_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if V28_ROOT not in sys.path:
    sys.path.insert(0, V28_ROOT)

from adapters.model_adapter import ModelPort, LoRAModelAdapter
from core.orchestrator_kernel import OrchestratorKernel
from scripts.evaluate_distillation import DistillationEvaluator


@unittest.skipUnless(
    LoRAModelAdapter(repo_root=V28_ROOT).is_available(),
    "LoRA weights are quarantined (v3.2 Loop 64 / C15): 46MB of safetensors and "
    "tokenizer.json were removed from the source tree, so the neural path is "
    "unavailable. These tests verified the 35MB weight file, not the code. The "
    "code's behaviour without weights is covered by "
    "focus-gate-v3.2/tests/test_loop64_repo_hygiene.py::"
    "test_the_loader_degrades_when_the_weights_are_absent. Restore per "
    "models/router_adapter/MANIFEST.json to re-enable.")
class TestLoop11DistilledRouter(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ledger_root = os.path.join(self.test_dir, ".focusgate")
        os.makedirs(self.ledger_root, exist_ok=True)
        self.adapter = LoRAModelAdapter(repo_root=V28_ROOT)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_m1_adapter_presence_and_safetensors_audit(self):
        """M1: Validates LoRA adapter presence, tensor count, and parameter calculation in pure stdlib.

        The expected checksum is read from models/router_adapter/MANIFEST.json
        rather than pasted here. It was a literal in this file before Loop 64,
        which meant the file pinned a specific blob of quarantined weights; the
        manifest is where that fact now lives.
        """
        self.assertTrue(self.adapter.is_available(), "LoRA adapter should be detected in repo models directory")
        
        tensors, total_params = self.adapter.read_safetensors_header()
        self.assertEqual(len(tensors), 392, "Adapter should have exactly 392 weight tensors")
        self.assertEqual(total_params, 18464768, "Adapter should have exactly 18,464,768 trainable parameters")

        integrity = self.adapter.verify_integrity()
        self.assertTrue(integrity["valid"], f"Adapter integrity failed: {integrity.get('errors')}")
        self.assertEqual(integrity["base_model"], "Qwen/Qwen2.5-1.5B-Instruct")
        self.assertEqual(integrity["peft_type"], "LORA")
        self.assertEqual(integrity["r"], 16)
        self.assertEqual(integrity["lora_alpha"], 32)
        self.assertEqual(integrity["tensor_count"], 392)
        self.assertEqual(integrity["trainable_parameters"], 18464768)
        with open(os.path.join(V28_ROOT, "models", "router_adapter", "MANIFEST.json"), encoding="utf-8") as _mf:
            _expected = {e["path"]: e["sha256"] for e in json.load(_mf)["files"]}
        self.assertEqual(integrity["checksum"], _expected["adapter_model.safetensors"])

    def test_m2_hexagonal_port_and_routing(self):
        """M2: LoRAModelAdapter implements ModelPort and generates/parses valid Action Envelopes."""
        self.assertIsInstance(self.adapter, ModelPort)

        query = "Build a modern high-contrast button component with accessible states"
        routed = self.adapter.route(query)

        self.assertIn("action_envelope", routed)
        self.assertTrue(routed["action_envelope"].startswith("▶ NEXT ACTION:"))
        self.assertIn("State: [Pipeline:", routed["action_envelope"])
        self.assertIn("■ ACTIVE FOCUS:", routed["action_envelope"])
        self.assertTrue(routed["adapter_verified"])
        with open(os.path.join(V28_ROOT, "models", "router_adapter", "MANIFEST.json"), encoding="utf-8") as _mf:
            self.assertEqual(routed["adapter_checksum"],
                             {e["path"]: e["sha256"] for e in json.load(_mf)["files"]}["adapter_model.safetensors"])

        # Test parsing of Action Envelope
        parsed = self.adapter.parse_action_envelope(routed["action_envelope"])
        self.assertTrue(parsed["next_action"])
        self.assertTrue(parsed["pipeline"])
        self.assertTrue(parsed["active_gate"])
        self.assertGreaterEqual(parsed["est_minutes"], 1)

    def test_m3_orchestrator_checkpoint_with_model_provenance(self):
        """M3: Orchestrator creates and verifies checkpoints with model adapter cryptographic binding."""
        # Use V28_ROOT workspace so OrchestratorKernel finds the active model adapter
        orch = OrchestratorKernel(self.ledger_root)
        orch.workspace_root = V28_ROOT
        orch.plan_decomposition("Production telemetry ingress subsystem")

        manifest = orch.create_checkpoint("v2.8-distilled-test")
        self.assertEqual(manifest["checkpoint_id"], "v2.8-distilled-test")
        self.assertEqual(manifest["version"], "2.8")
        self.assertIn("model_adapter", manifest)
        self.assertEqual(manifest["model_adapter"]["base_model"], "Qwen/Qwen2.5-1.5B-Instruct")
        self.assertEqual(manifest["model_adapter"]["rank"], 16)
        self.assertEqual(manifest["model_adapter"]["trainable_parameters"], 18464768)
        self.assertTrue(manifest["checksum"])

        # Check list_checkpoints reports model adapter
        cps = orch.list_checkpoints()
        target_cp = next((c for c in cps if c["checkpoint_id"] == "v2.8-distilled-test"), None)
        self.assertIsNotNone(target_cp)
        self.assertTrue(target_cp["checksum_valid"])
        self.assertIsNotNone(target_cp.get("model_adapter"))

        # Test tamper detection on model adapter metadata
        cp_file = os.path.join(orch._checkpoints_dir, "v2.8-distilled-test.json")
        with open(cp_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["model_adapter"]["rank"] = 32  # Tamper with rank
        with open(cp_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        with self.assertRaises(ValueError):
            orch.restore_checkpoint("v2.8-distilled-test")

    def test_m4_cli_flags_registered(self):
        """M4: CLI parser exposes --audit-adapter, --audit-model, and --distilled-route."""
        import importlib
        sys.path.insert(0, os.path.join(V28_ROOT, "scripts"))
        focus_gate_mod = importlib.import_module("focus-gate")
        parser = focus_gate_mod.build_parser()
        help_text = parser.format_help()

        self.assertIn("--audit-adapter", help_text)
        self.assertIn("--audit-model", help_text)
        self.assertIn("--distilled-route", help_text)

    def test_m5_fgbench100_distillation_evaluation(self):
        """M5: FGBench100 benchmark scorecard passes all RRR, BAS, and TCR production candidate gates."""
        fgbench_path = os.path.join(V28_ROOT, "tests", "fgbench100.json")
        self.assertTrue(os.path.exists(fgbench_path), "tests/fgbench100.json benchmark dataset must exist")

        scorecard = DistillationEvaluator.run_eval(fgbench_path)
        self.assertEqual(scorecard["total_scenarios"], 100)
        self.assertEqual(scorecard["rrr"], 100.0, "RRR should be 100% on canonical benchmark")
        self.assertEqual(scorecard["bas"], 100.0, "BAS must be 100% compliant with Invariant Action Envelope")
        self.assertGreaterEqual(scorecard["tcr"], 85.0, "TCR must exceed 85% compression gate")
        self.assertLess(scorecard["avg_latency_ms"], 10.0, "Average triage latency must be <10ms")
        self.assertTrue(scorecard["passed"], "Distillation evaluation scorecard must PASS")


if __name__ == "__main__":
    unittest.main()
