#!/usr/bin/env python3
"""Action-Oriented Smoke Test for FocusGate v2.7.

Runs quick, deterministic verification checks with 0 external dependencies (100% Python stdlib).
Validates:
1. Hydration across all 19 facets.
2. P12 Bespoke Frontend Design pipeline synthesis.
3. Dual-phase /unlazy 4-pass prompt injection & stage anchor.
4. Tool seam anti-laziness pre-patch verification guard.
5. Intra-stage verification matrix & boundary guard.
6. Anti-cliché design oracle detection.
"""

import sys
import os
import unittest

# Ensure v2.7 root is in path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
V27_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))
if V27_ROOT not in sys.path:
    sys.path.insert(0, V27_ROOT)

import importlib.util

script_path = os.path.join(V27_ROOT, "scripts", "focus-gate.py")
spec = importlib.util.spec_from_file_location("focus_gate_cli", script_path)
fg_module = importlib.util.module_from_spec(spec)
sys.modules["focus_gate_cli"] = fg_module
spec.loader.exec_module(fg_module)

from core.facets.catalog import FacetCatalog
JITHydrationEngine = FacetCatalog.default()
from core.pipeline_synthesizer import PipelineSynthesizer

from core.agent_brief import AgentBrief
from core.tool_matrix import ToolSelectionMatrix
from core.stage_matrix import StageDefinition, StageVerificationMatrix, StageBoundaryGuard, StageBoundaryViolationError
from core.oracles.cliche_oracle import ClicheOracle


class TestFocusGateV27Smoke(unittest.TestCase):

    def test_01_all_19_facets_hydration(self):
        """Verify all 19 facets across 5 Bounded Contexts hydrate with zero error."""
        facets = {f["facet"]: f for f in JITHydrationEngine.summary_rows()}
        self.assertEqual(len(facets), 19, f"Expected 19 facets, found {len(facets)}")
        self.assertIn("frontend-design", facets)
        self.assertIn("unlazy", facets)

        for facet_name in facets:
            res = JITHydrationEngine.hydrate_info(facet_name)
            self.assertIn("directive", res)
            self.assertTrue(len(res["directive"]) > 50, f"Facet {facet_name} directive too short")

    def test_02_p12_bespoke_frontend_pipeline_synthesis(self):
        """Verify P12 Bespoke Frontend Design & Implementation synthesis."""
        plan = PipelineSynthesizer.synthesize("Design a bespoke landing page with distinctive typography and custom palette")
        self.assertEqual(plan["archetype"], "FRONTEND_BESPOKE")
        self.assertEqual(plan["pipeline"], "Bespoke Frontend Design & Implementation")
        stages = [s["facet"] for s in plan["stages"]]
        self.assertEqual(stages, ["frontend-design", "design-tokens", "prototype", "codebase-design", "unlazy", "code-review"])

    def test_03_dual_phase_unlazy_prompt_injection(self):
        """Verify AgentBrief.to_prompt() injects 4-Pass Rigor and Stage Progress Anchor."""
        brief = AgentBrief.create(
            gate_id="gate-2-tokens",
            facet="design-tokens",
            task_summary="Extract 3-layer CSS variables for bespoke palette",
            acceptance_criteria=["CHECK: python3 -c 'print(\"TOKENS_OK\")'", "EXPECT: TOKENS_OK"],
            stage_context={"stage_index": 2, "total_stages": 5, "stage_name": "Tokens"}
        )
        prompt = brief.to_prompt()

        # Check Stage Anchor
        self.assertIn("[STAGE MATRIX: Stage 2 of 5 — Tokens]", prompt)

        # Check 4-Pass Rigor Directive
        self.assertIn("Mandatory Implementation Rigor Directive (Dual-Phase /unlazy)", prompt)
        self.assertIn("Pass 1 (Complete Deliverable)", prompt)
        self.assertIn("Pass 2 (Domain Elevation)", prompt)
        self.assertIn("Pass 3 (Boundary Defense)", prompt)
        self.assertIn("Pass 4 (Low-Cost Polish)", prompt)

    def test_04_tool_seam_anti_laziness_guard(self):
        """Verify ToolSelectionMatrix rejects patches with placeholder stubs before writing."""
        matrix = ToolSelectionMatrix(workspace_root=V27_ROOT)
        
        # Candidate lazy code
        lazy_replacement = "def solve_task():\n    # TODO: implement logic\n    pass\n"
        
        check = matrix.verify_patch_preconditions(
            target_path="SKILL.md",
            search_block="# FocusGate v2.7",
            replacement_block=lazy_replacement
        )
        self.assertFalse(check.valid)
        self.assertIn("Unlazy Rigor Rejection", check.reason)
        self.assertIn("TODO_STUB", check.reason)

    def test_05_intra_stage_matrix_and_boundary_guard(self):
        """Verify StageBoundaryGuard blocks out-of-order execution across stages."""
        matrix = StageVerificationMatrix(workspace_root=V27_ROOT)
        stage_1 = StageDefinition(
            stage_id="stage-1-spec",
            index=1,
            name="Design Spec",
            facet="frontend-design",
            gate_ids=["gate-1-spec"]
        )
        stage_2 = StageDefinition(
            stage_id="stage-2-tokens",
            index=2,
            name="Tokens Extraction",
            facet="design-tokens",
            gate_ids=["gate-2-tokens"]
        )
        stages = [stage_1, stage_2]

        # Case A: Stage 1 is PENDING -> attempting to execute gate-2-tokens must fail
        gates_state = {
            "gate-1-spec": {"id": "gate-1-spec", "status": "PENDING"},
            "gate-2-tokens": {"id": "gate-2-tokens", "status": "PENDING"}
        }

        with self.assertRaises(StageBoundaryViolationError):
            StageBoundaryGuard.assert_can_activate_gate("gate-2-tokens", stages, gates_state, matrix)

        # Case B: Stage 1 is CHECKED -> executing gate-2-tokens must succeed
        gates_state["gate-1-spec"]["status"] = "CHECKED"
        # Should not raise exception
        StageBoundaryGuard.assert_can_activate_gate("gate-2-tokens", stages, gates_state, matrix)

    def test_06_anti_cliche_design_oracle(self):
        """Verify ClicheOracle detects AI template tells."""
        html_cliche = """
        <div class="card" style="box-shadow: rgba(0,0,0,0.1) 0 4px 6px;">
            <span class="eyebrow" style="letter-spacing: 0.2em; text-transform: uppercase;">CATEGORY</span>
            <h1 style="color: #d97757; background: #f4f1ea;">Header <span class="accent">Special</span></h1>
            <a href="#">Learn More &rarr;</a>
        </div>
        """
        audit = ClicheOracle.audit_content(html_cliche)
        self.assertFalse(audit.clean)
        rule_ids = [f.rule_id for f in audit.findings]
        self.assertIn("CLICHE_PALETTE_TERRACOTTA", rule_ids)
        self.assertIn("CLICHE_CHROME_TRACKED_EYEBROW", rule_ids)
        self.assertIn("CLICHE_CHROME_BUTTON_ARROW", rule_ids)
        self.assertIn("CLICHE_LAYOUT_SAAS_CARD_SHADOW", rule_ids)
        self.assertIn("CLICHE_TYPO_SINGLE_WORD_ACCENT", rule_ids)


if __name__ == "__main__":
    unittest.main()
