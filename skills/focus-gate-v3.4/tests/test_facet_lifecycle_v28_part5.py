#!/usr/bin/env python3
"""FocusGate v2.8 Part 5 (Checkpoint 4) — Single-Source Facet Lifecycle & Wave Verification."""
import json
import os
import shutil
import sys
import tempfile
import unittest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
V271_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))
if V271_ROOT not in sys.path:
    sys.path.insert(0, V271_ROOT)
SCRIPT = os.path.join(V271_ROOT, "scripts", "focus-gate.py")
FACETS_DIR = os.path.join(V271_ROOT, "facets")


class TestHydrateFromIndex(unittest.TestCase):
    def _engine(self):
        sys.argv = ["focus-gate.py"]
        # load CLI module without running main()
        import importlib.util
        spec = importlib.util.spec_from_file_location("fg_cli", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        from core.facets.catalog import FacetCatalog
        return FacetCatalog.default()

    def test_hydrate_mode_is_window_ephemeral_vocabulary(self):
        from core.tokens import estimate_tokens
        eng = self._engine()
        info = eng.hydrate_info("frontend-design")
        self.assertEqual(info["context"], "design")
        self.assertEqual(info["mode"], "WINDOW")          # NOT the old prose label
        self.assertEqual(info["tokens"], estimate_tokens(info["directive"]))

    def test_list_facets_modes_all_valid(self):
        eng = self._engine()
        modes = {f["mode"] for f in eng.summary_rows()}
        self.assertTrue(modes <= {"WINDOW", "EPHEMERAL"}, modes)
        self.assertEqual(len(eng.summary_rows()), 19)

    def test_unknown_facet_lists_index_ids(self):
        eng = self._engine()
        with self.assertRaises(ValueError) as ctx:
            eng.hydrate_info("no-such-facet-xyz")
        self.assertIn("frontend-design", str(ctx.exception))

    def test_facet_registry_constant_is_gone(self):
        with open(SCRIPT, encoding="utf-8") as f:
            self.assertNotIn("FACET_REGISTRY", f.read())


class TestIndexFreshness(unittest.TestCase):
    def test_committed_index_is_current(self):
        from core.facet_index import index_is_current
        self.assertTrue(index_is_current(FACETS_DIR))

    def test_stale_index_is_detected(self):
        from core.facet_index import index_is_current
        tmp = tempfile.mkdtemp(prefix="fg-c4-stale-")
        try:
            for name in os.listdir(FACETS_DIR):
                s = os.path.join(FACETS_DIR, name)
                if os.path.isdir(s):
                    shutil.copytree(s, os.path.join(tmp, name))
            with open(os.path.join(tmp, "facet_index.json"), "w", encoding="utf-8") as f:
                json.dump({"generated_from": "stale", "facets": {}, "triggers": []}, f)
            self.assertFalse(index_is_current(tmp))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_lint_facets_reports_stale_index(self):
        import subprocess
        env = dict(os.environ)
        r = subprocess.run([sys.executable, SCRIPT, "--lint-facets", "--json"],
                           capture_output=True, text=True, env=env, cwd=V271_ROOT)
        data = json.loads(r.stdout)
        self.assertTrue(data["clean"], data)


ALL_IDS = ["banner-safe-zone","code-review","codebase-design","design-tokens","diagnosing-bugs",
 "focus-design","frontend-design","grilling","i-have-adhd","loop-me","prototype","triage",
 "ui-ux-pro-max","unlazy","wayfinder","writing-beats","writing-for-agents","writing-fragments","writing-shape"]

class TestSingleModeAuthority(unittest.TestCase):
    def test_mode_for_facet_matches_contract(self):
        from core.context_policy import mode_for_facet
        from core.facet_router import load_index
        facets = load_index(os.path.join(FACETS_DIR, "facet_index.json"))["facets"]
        for fid in ALL_IDS:
            self.assertEqual(mode_for_facet(fid).value, facets[fid]["mode"], fid)

    def test_no_hardcoded_mode_tables(self):
        with open(os.path.join(V271_ROOT, "core", "context_policy.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("_EPHEMERAL_KEYWORDS", src)
        self.assertNotIn("_WINDOW_KEYWORDS", src)


class TestCanonicalTokens(unittest.TestCase):
    def test_estimate_tokens_cli_matches_core(self):
        sys.argv = ["focus-gate.py"]
        import importlib.util
        spec = importlib.util.spec_from_file_location("fg_cli2", SCRIPT)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        from core.tokens import estimate_tokens
        sample = "hello world this is a longer sample string for tokens"
        self.assertEqual(mod.SmartZoneCompactor.estimate_tokens(sample), estimate_tokens(sample))

    def test_no_raw_divide_token_formula(self):
        with open(SCRIPT, encoding="utf-8") as f:
            src = f.read()
        self.assertEqual(src.count("// 4"), 0)


def _cli(args):
    import subprocess
    r = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True, cwd=V271_ROOT)
    return r


class TestVerifyWave(unittest.TestCase):
    EXPECT_GATES = {"facet_index_fresh", "facet_contracts", "token_consistency",
                    "cli_help_clean", "stage_matrix", "context_sufficiency"}

    def test_verify_wave_envelope_and_clean(self):
        r = _cli(["--verify-wave", "--json"])
        data = json.loads(r.stdout)
        self.assertEqual(set(data["gates"]), self.EXPECT_GATES)
        for g in data["gates"].values():
            self.assertIn(g["status"], ("PASS", "FAIL", "SKIP"))
        self.assertTrue(data["clean"], data)


class TestCliHygiene(unittest.TestCase):
    def test_no_stale_version_string(self):
        r = _cli(["--help"])
        self.assertNotIn("1.3.5", r.stdout)

    def test_every_command_has_help(self):
        sys.argv = ["focus-gate.py"]
        import importlib.util
        spec = importlib.util.spec_from_file_location("fg_cli3", SCRIPT)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        for a in mod.build_parser()._actions:
            if a.option_strings:
                self.assertTrue((a.help or "").strip(), a.option_strings)

    def test_no_dead_version_handler_2_5_6(self):
        with open(SCRIPT, encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("2.5.6", content)


class TestSkillDocCoversV28(unittest.TestCase):
    def test_skill_md_documents_new_gates(self):
        with open(os.path.join(V271_ROOT, "SKILL.md"), encoding="utf-8") as f:
            md = f.read()
        for c in ("--verify-wave", "--lint-facets", "--audit-context-sufficiency", "--synthesize-pipeline"):
            self.assertIn(c, md, c)


class TestCliOracleJsonRouting(unittest.TestCase):
    def test_audit_code_cliche_json_exits_cleanly(self):
        r = _cli(["--audit-code-cliche", "scripts/", "--json"])
        self.assertNotIn("IsADirectoryError", r.stderr)
        self.assertNotIn("IsADirectoryError", r.stdout)
        data = json.loads(r.stdout)
        self.assertIn("clean", data)

    def test_audit_prose_cliche_json_exits_cleanly(self):
        r = _cli(["--audit-prose-cliche", "SKILL.md", "--json"])
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("Unknown command", r.stdout)
        data = json.loads(r.stdout)
        self.assertTrue(data["clean"])

    def test_audit_design_cliche_json_exits_cleanly(self):
        r = _cli(["--audit-design-cliche", "SPEC.md", "--json"])
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("Unknown command", r.stdout)
        data = json.loads(r.stdout)
        self.assertTrue(data["clean"])

    def test_audit_tokens_json_exits_cleanly(self):
        r = _cli(["--audit-tokens", "templates/design-tokens.template.json", "--json"])
        self.assertNotIn("Unknown command", r.stdout)
        data = json.loads(r.stdout)
        self.assertIn("passed", data)


class TestCodeClicheHygiene(unittest.TestCase):
    def test_core_has_zero_shotgun_suppression(self):
        r = _cli(["--audit-code-cliche", "core/", "--json"])
        data = json.loads(r.stdout)
        violations = [f for f in data.get("findings", []) if f.get("rule_id") == "CODE_SHOTGUN_SUPPRESSION"]
        self.assertEqual(len(violations), 0, f"Found shotgun suppressions in core/: {violations}")
        self.assertTrue(data.get("clean"))
        self.assertEqual(r.returncode, 0)

    def test_scripts_harvest_has_zero_shotgun_suppression(self):
        r = _cli(["--audit-code-cliche", "scripts/harvest_trajectories.py", "--json"])
        data = json.loads(r.stdout)
        violations = [f for f in data.get("findings", []) if f.get("rule_id") == "CODE_SHOTGUN_SUPPRESSION"]
        self.assertEqual(len(violations), 0, f"Found shotgun suppressions in harvest_trajectories: {violations}")
        self.assertTrue(data.get("clean"))
        self.assertEqual(r.returncode, 0)


class TestTemplateHygiene(unittest.TestCase):
    def test_templates_have_zero_design_cliches(self):
        r = _cli(["--audit-design-cliche", "templates/", "--json"])
        data = json.loads(r.stdout)
        self.assertEqual(len(data.get("findings", [])), 0, f"Found design cliches in templates/: {data.get('findings')}")
        self.assertTrue(data.get("clean"))
        self.assertEqual(r.returncode, 0)


class TestOracleAdapterIntegrity(unittest.TestCase):
    def test_oracle_adapter_compiles_cleanly(self):
        import py_compile
        adapter_path = os.path.join(V271_ROOT, "adapters", "oracle_adapter.py")
        py_compile.compile(adapter_path, doraise=True)

    def test_oracle_adapter_exports(self):
        from adapters.oracle_adapter import ShellOracleAdapter, ContrastOracleAdapter
        self.assertTrue(callable(getattr(ShellOracleAdapter, "execute_tracer", None)))
        self.assertTrue(callable(getattr(ContrastOracleAdapter, "verdict", None)))

    def test_contrast_oracle_adapter_verdict(self):
        from adapters.oracle_adapter import ContrastOracleAdapter
        v = ContrastOracleAdapter.verdict("#000000", "#ffffff")
        self.assertTrue(v["pass_aa"])
        self.assertGreaterEqual(v["ratio"], 20.0)


class TestSynthesizePipelineCli(unittest.TestCase):
    def test_synthesize_pipeline_no_args_prints_usage_without_crashing(self):
        r = _cli(["--synthesize-pipeline"])
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("NameError", r.stderr)
        self.assertIn("Usage: focus-gate.py --synthesize-pipeline", r.stderr)


class TestCliMissingImportsResolved(unittest.TestCase):
    def test_audit_contrast_executes_without_name_error(self):
        r = _cli(["--audit-contrast", "#000000", "#ffffff"])
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("NameError", r.stderr)
        self.assertIn("CONTRAST_PASS_AA", r.stdout)

    def test_audit_contrast_json(self):
        r = _cli(["--audit-contrast", "#000000", "#ffffff", "--json"])
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("NameError", r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data.get("pass_aa"))
        self.assertGreaterEqual(data.get("ratio", 0), 20.0)

    def test_swarm_status_executes_without_name_error(self):
        r = _cli(["--swarm-status"])
        self.assertNotIn("NameError", r.stderr)
        self.assertEqual(r.returncode, 0)

    def test_swarm_clean_executes_without_name_error(self):
        r = _cli(["--swarm-clean", "nonexistent-gate-for-test"])
        self.assertNotIn("NameError", r.stderr)


class TestOracleDeduplicationAndSingleSourceOfTruth(unittest.TestCase):
    def test_no_legacy_scripts_oracles_directory(self):
        scripts_oracles_dir = os.path.join(V271_ROOT, "scripts", "oracles")
        self.assertFalse(os.path.exists(scripts_oracles_dir), "scripts/oracles directory must be eliminated")

    def test_safe_zone_oracle_cli_functional(self):
        r = _cli(["--audit-safe-zone", "1920x1080"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("SAFE_ZONE_PASS", r.stdout)

    def test_safe_zone_oracle_cli_json(self):
        r = _cli(["--audit-safe-zone", "1920x1080", "--json"])
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertTrue(data.get("pass"))


class TestStageMatrixIntegrity(unittest.TestCase):
    def test_stage_matrix_has_get_active_stage(self):
        from core.stage_matrix import StageDefinition, StageVerificationMatrix
        matrix = StageVerificationMatrix()
        self.assertTrue(hasattr(matrix, "get_active_stage"), "StageVerificationMatrix must implement get_active_stage")
        stage1 = StageDefinition(stage_id="s1", index=1, name="Stage 1", facet="f1", gate_ids=["g1"], status="VERIFIED")
        stage2 = StageDefinition(stage_id="s2", index=2, name="Stage 2", facet="f2", gate_ids=["g2"], status="PENDING")
        active = matrix.get_active_stage([stage1, stage2], {"g1": {"status": "CHECKED"}, "g2": {"status": "PENDING"}})
        self.assertIsNotNone(active)
        self.assertEqual(active.stage_id, "s2")


class TestTokenConsistencyAndDistillationIntegrity(unittest.TestCase):
    def test_evaluate_distillation_imports_cleanly(self):
        import importlib
        mod = importlib.import_module("scripts.evaluate_distillation")
        self.assertTrue(hasattr(mod, "DistillationEvaluator"))

    def test_no_raw_divide_in_core_context_bus(self):
        bus_path = os.path.join(V271_ROOT, "core", "context_bus.py")
        with open(bus_path, encoding="utf-8") as f:
            src = f.read()
        raw = "//" + " 4"
        self.assertNotIn(raw, src, "core/context_bus.py must route tokens through core.tokens.estimate_tokens")

    def test_no_raw_divide_in_evaluate_distillation(self):
        eval_path = os.path.join(V271_ROOT, "scripts", "evaluate_distillation.py")
        with open(eval_path, encoding="utf-8") as f:
            src = f.read()
        raw = "//" + " 4"
        self.assertNotIn(raw, src, "scripts/evaluate_distillation.py must route tokens through core.tokens.estimate_tokens")

    def test_distillation_evaluator_run_eval_mock(self):
        import tempfile
        from scripts.evaluate_distillation import DistillationEvaluator
        scenarios = [
            {
                "query": "Fix bug in auth handler",
                "expected_pipeline": "P1",
                "expected_archetype": "DEFECT"
            }
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
            json.dump(scenarios, tf)
            tpath = tf.name
        try:
            scorecard = DistillationEvaluator.run_eval(tpath)
            self.assertEqual(scorecard["total_scenarios"], 1)
            self.assertEqual(scorecard["rrr"], 100.0)
            self.assertEqual(scorecard["bas"], 100.0)
        finally:
            if os.path.exists(tpath):
                os.remove(tpath)


class TestCliParserCompleteness(unittest.TestCase):
    def test_all_handled_cli_flags_registered_in_parser(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("fg_cli4", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        parser = mod.build_parser()
        parser_dests = set(a.dest for a in parser._actions)
        required_dests = {
            "unlazy_rigor",
            "select_tool",
            "patch_lint",
            "slice_facet",
            "retrieve_snippet",
            "ephemeral_run",
            "handoff",
            "audit_handoffs",
            "harvest_trajectories",
        }
        for dest in required_dests:
            self.assertIn(dest, parser_dests, f"CLI flag for {dest} missing from build_parser()")

    def test_patch_lint_exit_code_failure_on_non_unique(self):
        r = _cli(["--patch-lint", "SPEC.md", "FocusGate", "--json"])
        self.assertEqual(r.returncode, 1)
        data = json.loads(r.stdout)
        self.assertFalse(data["valid"])

    def test_patch_lint_exit_code_success_on_unique(self):
        # v3.2 Loop 65: the block used to be matched was the literal SPEC.md
        # H1, which Loop 65 corrected from "v2.8" to "v3.1" — so this test
        # began failing for a reason unrelated to --patch-lint. A fixture that
        # hardcodes a string the docs are expected to change is a test that
        # fails every time the documentation is fixed. Read the real H1
        # instead, and additionally assert the failure mode still works.
        spec = os.path.join(V271_ROOT, "SPEC.md")
        with open(spec, encoding="utf-8") as fh:
            h1 = fh.readline().rstrip("\n")
        r = _cli(["--patch-lint", spec, h1, "--json"])
        self.assertEqual(r.returncode, 0, "patch-lint rejected a block that exists: %s" % r.stdout)
        data = json.loads(r.stdout)
        self.assertTrue(data["valid"])
        self.assertTrue(data["exact_match_found"])

        # The negative case, so the fix cannot have turned it into a stub that
        # always returns valid.
        r2 = _cli(["--patch-lint", spec, h1 + " (a line that is not there)", "--json"])
        self.assertEqual(r2.returncode, 1)
        self.assertFalse(json.loads(r2.stdout)["valid"])


class TestPluginVersionHygiene(unittest.TestCase):
    def test_no_stale_plugin_version_docstrings(self):
        plugins_dir = os.path.join(V271_ROOT, "plugins")
        for fname in os.listdir(plugins_dir):
            if fname.endswith(".py"):
                fpath = os.path.join(plugins_dir, fname)
                with open(fpath, encoding="utf-8") as f:
                    content = f.read()
                self.assertNotIn("v2.5.", content, f"Found stale version in {fname}")


class TestLoop5HelpAndParserSynchronization(unittest.TestCase):
    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("fg_cli5", SCRIPT)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_print_help_banner_and_parser_description_v28(self):
        # v3.2 Loop 65: this test previously asserted the help banner names
        # "v2.8", pinning the very defect claim C12 reports (no single version
        # source; the product named itself v2.8 at a v3.1-PROD tag). It now
        # asserts the CURRENT release, read from the single source rather than
        # retyped, so it cannot drift again the moment the version moves.
        import sys
        sys.path.insert(0, V271_ROOT)   # V271_ROOT is the repo root itself
        from core.version import RELEASE_LABEL

        parser = self.mod.build_parser()
        self.assertNotIn("v2.6", parser.description)

        import io
        import contextlib
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.mod.print_help()
        help_out = f.getvalue()

        # The banner carries the bare version; the -PROD channel suffix
        # belongs to the release label that `--version` reports.
        self.assertIn("FocusGate v%s" % RELEASE_LABEL.lstrip("v").split("-")[0], help_out)
        self.assertNotIn("v2.6 JIT Cognitive", help_out)
        # No superseded release may be advertised in the help text.
        self.assertNotIn("FocusGate v2.8", help_out)
        self.assertEqual(help_out.count("Usage:"), 1, "Expected 'Usage:' to appear exactly once in print_help()")
        self.assertIn("--verify-wave", help_out)
        self.assertIn("--audit-all", help_out)
        self.assertIn("--unlazy-rigor", help_out)
        self.assertIn("--patch-lint", help_out)


class TestLoop5PluginBaseVersion(unittest.TestCase):
    def test_plugin_version_is_28(self):
        from plugins.cognitive_plugin import CognitivePlugin
        from plugins.engineering_plugin import EngineeringPlugin
        from plugins.writing_plugin import WritingPlugin
        from plugins.design_plugin import DesignPlugin

        for cls in (CognitivePlugin, EngineeringPlugin, WritingPlugin, DesignPlugin):
            inst = cls()
            self.assertEqual(inst.version, "2.8", f"{cls.__name__}.version is {inst.version}, expected 2.8")

    def test_core_oracles_exports_unified_audit(self):
        import core.oracles as oracles
        self.assertTrue(hasattr(oracles, "UnifiedAuditOracle"), "core.oracles must export UnifiedAuditOracle")


class TestLoop5StageMatrixDigestVerification(unittest.TestCase):
    def test_verify_stage_completion_checks_receipt_hashes(self):
        from core.stage_matrix import StageDefinition, StageVerificationMatrix
        matrix = StageVerificationMatrix(workspace_root=V271_ROOT)
        stage = StageDefinition(
            stage_id="s1",
            index=0,
            name="Spec Stage",
            facet="unlazy",
            gate_ids=["g1"],
            receipt_hashes={"g1": "expected_sha256_hash_123"}
        )

        # 1. Gate has wrong receipt hash -> FAIL
        agg_wrong = {
            "g1": {"status": "CHECKED", "receipt_hash": "different_hash_999"}
        }
        verified, reasons, evidence = matrix.verify_stage_completion(stage, agg_wrong)
        self.assertFalse(verified)
        self.assertTrue(any("receipt hash mismatch" in r.lower() for r in reasons))

        # 2. Gate has matching receipt hash -> PASS
        agg_correct = {
            "g1": {"status": "CHECKED", "receipt_hash": "expected_sha256_hash_123"}
        }
        verified, reasons, evidence = matrix.verify_stage_completion(stage, agg_correct)
        self.assertTrue(verified, f"Expected PASS but got reasons: {reasons}")


class TestV28RepositoryVersionHygiene(unittest.TestCase):
    def test_core_modules_version_v28(self):
        core_dir = os.path.join(V271_ROOT, "core")
        for fname in os.listdir(core_dir):
            if fname.endswith(".py"):
                fpath = os.path.join(core_dir, fname)
                with open(fpath, encoding="utf-8") as f:
                    content = f.read()
                self.assertNotIn("FocusGate v2.6", content, f"Stale FocusGate v2.6 in core/{fname}")
                self.assertNotIn("FocusGate v2.7", content, f"Stale FocusGate v2.7 in core/{fname}")

    def test_core_oracles_version_v28(self):
        oracles_dir = os.path.join(V271_ROOT, "core", "oracles")
        for fname in os.listdir(oracles_dir):
            if fname.endswith(".py"):
                fpath = os.path.join(oracles_dir, fname)
                with open(fpath, encoding="utf-8") as f:
                    content = f.read()
                self.assertNotIn("v2.7", content, f"Stale v2.7 in core/oracles/{fname}")

    def test_schemas_support_v28(self):
        handoff_schema_path = os.path.join(V271_ROOT, "schemas", "handoff.schema.json")
        with open(handoff_schema_path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("2.8", data["properties"]["schema_version"]["enum"])

    def test_skill_and_spec_version_v28(self):
        skill_path = os.path.join(V271_ROOT, "SKILL.md")
        # v3.2 Loop 65: was `assertIn("FocusGate v2.8", ...)`. That asserted the
        # defect. The invariant worth keeping is "the docs name the release,
        # and no superseded one" — the name itself now comes from
        # core/version.py, the single source (C12).
        import sys
        sys.path.insert(0, V271_ROOT)   # V271_ROOT is the repo root itself
        from core.version import RELEASE_LABEL
        version_bare = RELEASE_LABEL.lstrip("v").split("-")[0]      # "3.1"

        with open(skill_path, encoding="utf-8") as f:
            skill_text = f.read()
        self.assertIn(RELEASE_LABEL, skill_text)
        self.assertIn("FocusGate v%s" % version_bare, skill_text)
        self.assertNotIn("FocusGate v2.7", skill_text)
        self.assertNotIn("FocusGate v2.8 / v3.1", skill_text)

        spec_path = os.path.join(V271_ROOT, "SPEC.md")
        with open(spec_path, encoding="utf-8") as f:
            spec_text = f.read()
        self.assertIn("FocusGate v%s" % version_bare, spec_text)
        self.assertNotIn("FocusGate v2.7", spec_text)


if __name__ == "__main__":
    unittest.main()










