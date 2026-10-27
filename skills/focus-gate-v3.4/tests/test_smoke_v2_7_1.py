#!/usr/bin/env python3
"""Action-Oriented Smoke Test for FocusGate v2.7.1.

Runs quick, deterministic verification checks with 0 external dependencies (100% Python stdlib).
Validates:
1. Hydration across all 19 facets including bespoke invariants in writing, engineering, and cognitive.
2. Anti-cliché prose oracle detection (throat-clearing, buzzwords, sycophancy, faux-summaries).
3. Anti-cliché code architecture oracle detection (junk-drawer utils, shotgun error suppression).
4. Tool seam interception of shotgun error suppression patches.
5. Domain-specific bespoke prompt injection across writing, code, cognitive, and design sub-agents.
6. CLI execution of --version, --audit-prose-cliche, and --audit-code-cliche.
"""

import sys
import os
import unittest

# Ensure v2.7.1 root is in path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
V271_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))
if V271_ROOT not in sys.path:
    sys.path.insert(0, V271_ROOT)

import importlib.util

script_path = os.path.join(V271_ROOT, "scripts", "focus-gate.py")
spec = importlib.util.spec_from_file_location("focus_gate_cli", script_path)
fg_module = importlib.util.module_from_spec(spec)
sys.modules["focus_gate_cli"] = fg_module
spec.loader.exec_module(fg_module)

from core.facets.catalog import FacetCatalog
JITHydrationEngine = FacetCatalog.default()
from core.agent_brief import AgentBrief
from core.tool_matrix import ToolSelectionMatrix
from core.oracles.prose_cliche_oracle import ProseClicheOracle
from core.oracles.code_cliche_oracle import CodeClicheOracle


class TestFocusGateV271Smoke(unittest.TestCase):

    def test_01_all_19_facets_and_bespoke_invariants(self):
        """Verify all 19 facets hydrate and target facets contain bespoke invariants."""
        facets = {f["facet"]: f for f in JITHydrationEngine.summary_rows()}
        self.assertEqual(len(facets), 19, f"Expected 19 facets, found {len(facets)}")

        writing_shape = JITHydrationEngine.hydrate_info("writing-shape")["directive"]
        self.assertIn("ANTI_PROSE_CLICHE", writing_shape)
        self.assertIn("DOMAIN_GROUNDING", writing_shape)

        codebase_design = JITHydrationEngine.hydrate_info("codebase-design")["directive"]
        self.assertIn("ANTI_SHALLOW_ABSTRACTION", codebase_design)
        self.assertIn("NO_JUNK_DRAWER_UTILS", codebase_design)

        diagnosing_bugs = JITHydrationEngine.hydrate_info("diagnosing-bugs")["directive"]
        self.assertIn("ANTI_SHOTGUN_PATCHING", diagnosing_bugs)

        grilling = JITHydrationEngine.hydrate_info("grilling")["directive"]
        self.assertIn("MICRO_STATE_CONCRETENESS", grilling)

    def test_02_prose_cliche_oracle(self):
        """Verify ProseClicheOracle detects AI writing tells and passes clean prose."""
        cliche_text = (
            "Certainly! Here is a comprehensive guide.\n"
            "In today's fast-paced world, it is important to note that we must delve into the details.\n"
            "This is a testament to the intricate tapestry of our architecture.\n"
            "In conclusion, we are done."
        )
        res = ProseClicheOracle.audit_content(cliche_text)
        self.assertFalse(res.clean)
        rule_ids = {f.rule_id for f in res.findings}
        self.assertIn("PROSE_THROAT_CLEARING", rule_ids)
        self.assertIn("PROSE_BUZZWORD_DELVE", rule_ids)
        self.assertIn("PROSE_BUZZWORD_TESTAMENT", rule_ids)
        self.assertIn("PROSE_BUZZWORD_TAPESTRY", rule_ids)
        self.assertIn("PROSE_FAUX_SUMMARY_CLOSING", rule_ids)

        clean_text = "The SQLite adapter commits transactions synchronously via WAL mode."
        clean_res = ProseClicheOracle.audit_content(clean_text)
        self.assertTrue(clean_res.clean)

    def test_03_code_cliche_oracle(self):
        """Verify CodeClicheOracle detects shotgun suppression and junk-drawer modules."""
        shotgun_code = (
            "def fetch_data():\n"
            "    try:\n"
            "        do_work()\n"
            "    except Exception:\n"
            "        pass\n"
        )
        res = CodeClicheOracle.audit_content(shotgun_code, filename="repo/worker.py")
        self.assertFalse(res.clean)
        rule_ids = {f.rule_id for f in res.findings}
        self.assertIn("CODE_SHOTGUN_SUPPRESSION", rule_ids)

        junk_code = (
            "def a(): return 1\n"
            "def b(): return 2\n"
            "def c(): return 3\n"
            "def d(): return 4\n"
        )
        junk_res = CodeClicheOracle.audit_content(junk_code, filename="utils.py")
        self.assertFalse(junk_res.clean)
        self.assertIn("CODE_JUNK_DRAWER_MODULE", {f.rule_id for f in junk_res.findings})

        clean_code = (
            "class TokenCache:\n"
            "    def __init__(self):\n"
            "        self._store = {}\n"
            "    def get(self, key: str):\n"
            "        return self._store.get(key)\n"
        )
        clean_res = CodeClicheOracle.audit_content(clean_code, filename="token_cache.py")
        self.assertTrue(clean_res.clean)

    def test_04_tool_seam_shotgun_rejection(self):
        """Verify ToolSelectionMatrix rejects patches with shotgun error suppression."""
        matrix = ToolSelectionMatrix(workspace_root=V271_ROOT)
        shotgun_patch = (
            "def run_query():\n"
            "    try:\n"
            "        execute()\n"
            "    except Exception:\n"
            "        pass\n"
        )
        check = matrix.verify_patch_preconditions(
            target_path="SKILL.md",
            search_block="# FocusGate v2.7.1",
            replacement_block=shotgun_patch
        )
        self.assertFalse(check.valid)
        self.assertIn("Bespoke Code Rigor Rejection", check.reason)
        self.assertIn("Shotgun error suppression", check.reason)

    def test_05_domain_specific_bespoke_prompt_injection(self):
        """Verify AgentBrief injects contract-sourced facet directives (registered) or bespoke fallback (legacy)."""
        # Writing brief
        writing_brief = AgentBrief.create(
            gate_id="g1", facet="writing-shape", task_summary="Shape technical spec",
            acceptance_criteria=["CHECK: true", "EXPECT: true"]
        )
        writing_prompt = writing_brief.to_prompt()
        self.assertIn("## Facet Directive: writing-shape", writing_prompt)
        self.assertIn("ANTI_PROSE_CLICHE", writing_prompt)

        # Engineering brief
        code_brief = AgentBrief.create(
            gate_id="g2", facet="codebase-design", task_summary="Design deep module",
            acceptance_criteria=["CHECK: true", "EXPECT: true"]
        )
        code_prompt = code_brief.to_prompt()
        self.assertIn("## Facet Directive: codebase-design", code_prompt)
        self.assertIn("ANTI_SHALLOW_ABSTRACTION", code_prompt)

        # Cognitive brief
        cognitive_brief = AgentBrief.create(
            gate_id="g3", facet="grilling", task_summary="Stress-test architecture",
            acceptance_criteria=["CHECK: true", "EXPECT: true"]
        )
        cognitive_prompt = cognitive_brief.to_prompt()
        self.assertIn("## Facet Directive: grilling", cognitive_prompt)
        self.assertIn("FRONTIER_ROUNDS", cognitive_prompt)

        # Design brief
        design_brief = AgentBrief.create(
            gate_id="g4", facet="frontend-design", task_summary="Design UI layout",
            acceptance_criteria=["CHECK: true", "EXPECT: true"]
        )
        design_prompt = design_brief.to_prompt()
        self.assertIn("## Facet Directive: frontend-design", design_prompt)
        self.assertIn("ANTI_CLICHE_GUARD", design_prompt)

        # v2.8 Part 4 re-contract: unregistered facets keep bespoke keyword fallback
        legacy_prompt = AgentBrief.create(
            gate_id="g5", facet="legacy-writing-suite", task_summary="t",
            acceptance_criteria=["CHECK: true", "EXPECT: true"]
        ).to_prompt()
        self.assertIn("Bespoke Writing Directive", legacy_prompt)

    def test_06_cli_execution(self):
        """Verify CLI execution of --version, --audit-prose-cliche, and --audit-code-cliche."""
        import subprocess
        # 1. --version
        r_ver = subprocess.run([sys.executable, script_path, "--version"], capture_output=True, text=True)
        self.assertEqual(r_ver.returncode, 0)
        # v3.2 Loop 65: read the release label from the single source instead
        # of pinning the literal "v2.8", which the banner no longer (and
        # should no longer) claim at a v3.1-PROD release.
        sys.path.insert(0, V271_ROOT)
        from core.version import RELEASE_LABEL
        self.assertIn(RELEASE_LABEL, r_ver.stdout)

        # 2. --audit-prose-cliche
        r_prose = subprocess.run([sys.executable, script_path, "--audit-prose-cliche", os.path.join(V271_ROOT, "SPEC.md"), "--json"], capture_output=True, text=True)
        self.assertEqual(r_prose.returncode, 0)
        self.assertIn("clean", r_prose.stdout)

        # 3. --audit-code-cliche
        r_code = subprocess.run([sys.executable, script_path, "--audit-code-cliche", script_path, "--json"], capture_output=True, text=True)
        self.assertEqual(r_code.returncode, 0)
        self.assertIn("clean", r_code.stdout)


if __name__ == "__main__":
    unittest.main()
