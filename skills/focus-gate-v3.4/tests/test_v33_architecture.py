"""FocusGate v3.3 -- architecture fitness suite.

These tests pin structure, not behavior: they fail when a seam is bypassed.
Ratchet constants below may only go DOWN. Raising one is a regression; lower it
in the same commit that removes code.
  F4  briefs ignored the v3.2 loop and shared one rigor block across all facets
  F5  three writers of `[x]` bypassed settle_gate (AUDIT O6)
  F6  main() was a ~2100-line, ~70-branch function beside a second dispatcher
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SCRIPT = os.path.join(ROOT, "scripts", "focus-gate.py")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# --- ratchets (lower only) -------------------------------------------------
MAX_MAIN_LINES = 95
MAX_SCRIPT_LINES = 28
# ---------------------------------------------------------------------------

MIGRATED_FLAGS = ("--hydrate-facet", "--list-facets", "--lint-facets", "-p", "--synthesize-pipeline",
                  "--check", "--baseline", "--evidence", "--lint", "--run", "--init")


def read(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return f.read()


def _brief(facet, gate="g1", criteria=("CHECK: python3 -m unittest x", "EXPECT: OK")):
    from core.agent_brief import AgentBrief
    return AgentBrief.create(gate_id=gate, facet=facet, task_summary="t",
                             acceptance_criteria=list(criteria)).to_prompt()


class TestBriefComposer(unittest.TestCase):
    def test_every_registered_facet_brief_teaches_the_v32_loop(self):
        from core.facets.catalog import FacetCatalog
        for fid in FacetCatalog.default().ids():
            p = _brief(fid, gate="gate-7")
            self.assertIn("## Evidence Protocol", p, fid)
            self.assertIn("--baseline", p, fid)
            self.assertIn("--check gate-7 --strict", p, fid)

    def test_protocol_follows_the_budgeted_sections(self):
        p = _brief("unlazy")
        self.assertGreater(p.index("## Evidence Protocol"), p.index("## Mandatory"))

    def test_rigor_block_is_tailored_by_context(self):
        eng = _brief("codebase-design")
        wri = _brief("writing-shape")
        self.assertIn("Pass 1 (Complete Deliverable)", wri)  # eval-03 contract kept
        self.assertIn("NotImplementedError", eng)
        self.assertNotIn("NotImplementedError", wri)
        self.assertNotIn("dummy returns", wri)

    def test_engineering_bespoke_block_is_not_stamped_on_every_facet(self):
        self.assertNotIn("ANTI_SHOTGUN_DEBUGGING", _brief("code-review"))
        self.assertNotIn("ANTI_SHOTGUN_DEBUGGING", _brief("prototype"))
        self.assertIn("ANTI_SHOTGUN", _brief("diagnosing-bugs"))

    def test_unregistered_facet_keeps_legacy_fallback(self):
        self.assertIn("Bespoke Writing Directive", _brief("legacy-writing-suite"))
        self.assertNotIn("## Facet Directive:", _brief("bespoke-legacy-facet"))

    def test_no_dead_branches_left_in_to_prompt(self):
        src = read("core", "agent_brief.py")
        self.assertNotIn('elif ctx == "engineering"', src)


class TestSingleSettlementPath(unittest.TestCase):
    """Only core/gates/evidence.py may turn `[ ]` into `[x]` (AUDIT O6)."""

    def test_no_other_module_writes_the_checkbox(self):
        offenders = []
        for base in ("core", "scripts", "adapters", "plugins"):
            for dp, _d, fns in os.walk(os.path.join(ROOT, base)):
                for fn in fns:
                    if not fn.endswith(".py"):
                        continue
                    path = os.path.join(dp, fn)
                    rel = os.path.relpath(path, ROOT)
                    if rel == os.path.join("core", "gates", "evidence.py"):
                        continue
                    with open(path, encoding="utf-8") as f:
                        if re.search(r"\[x\]\s*\\1", f.read()):
                            offenders.append(rel)
        self.assertEqual(offenders, [])

    def _ledger(self, tmp, check, expect):
        os.makedirs(os.path.join(tmp, ".focusgate"))
        p = os.path.join(tmp, ".focusgate", "GATES.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("# T\n\n## 2. Acceptance Gates\n\n### Production Gates\n"
                    f"- [ ] g1: demo\n  CHECK: {check}\n  EXPECT: {expect}\n")
        return p

    def test_swarm_wave_cannot_tick_a_self_satisfying_gate(self):
        tmp = tempfile.mkdtemp()
        try:
            p = self._ledger(tmp, "echo ok", "ok")
            subprocess.run([sys.executable, SCRIPT, "--swarm-wave", p], cwd=tmp,
                           capture_output=True, text=True, timeout=120)
            self.assertIn("- [ ] g1:", open(p, encoding="utf-8").read())
        finally:
            shutil.rmtree(tmp)

    def test_swarm_wave_settles_through_the_evidence_log(self):
        tmp = tempfile.mkdtemp()
        try:
            p = self._ledger(tmp, "python3 -c \\\"print('M' if 1+1==2 else 'X')\\\"", "M")
            subprocess.run([sys.executable, SCRIPT, "--swarm-wave", p], cwd=tmp,
                           capture_output=True, text=True, timeout=120)
            if "- [x] g1:" in open(p, encoding="utf-8").read():
                log = os.path.join(tmp, ".focusgate", "GATES.evidence.jsonl")
                self.assertTrue(os.path.exists(log), "gate ticked without evidence record")
                self.assertIn('"settle"', open(log, encoding="utf-8").read())
        finally:
            shutil.rmtree(tmp)

    def test_spike_settlement_is_logged(self):
        from core.gates import evidence
        self.assertTrue(callable(getattr(evidence, "settle_spike", None)))


class TestCommandRegistry(unittest.TestCase):
    def test_loop_commands_are_registered(self):
        from core.cli.registry import REGISTRY
        flags = REGISTRY.flags()
        for f in MIGRATED_FLAGS:
            self.assertIn(f, flags, f)

    def test_handlers_return_exit_codes_and_have_one_owner(self):
        from core.cli.registry import REGISTRY
        seen = {}
        for cmd in REGISTRY.commands():
            self.assertTrue(callable(cmd.handler), cmd.name)
            self.assertTrue(cmd.summary, cmd.name)
            for fl in cmd.flags:
                self.assertNotIn(fl, seen, f"{fl} owned by {seen.get(fl)} and {cmd.name}")
                seen[fl] = cmd.name

    def test_migrated_branches_left_main(self):
        src = read("core", "cli", "app.py")
        for dest in ("hydrate_facet", "list_facets", "lint_facets", "baseline", "evidence"):
            self.assertNotIn(f"getattr(args, '{dest}'", src, dest)

    def test_command_modules_do_not_import_each_other(self):
        d = os.path.join(ROOT, "core", "cli", "commands")
        mods = {f[:-3] for f in os.listdir(d) if f.endswith(".py") and f != "__init__.py"}
        for m in mods:
            tree = ast.parse(read("core", "cli", "commands", m + ".py"))
            for n in ast.walk(tree):
                if isinstance(n, ast.ImportFrom) and n.module:
                    last = n.module.split(".")[-1]
                    self.assertFalse(n.level and last in mods - {m}, f"{m} imports sibling {last}")

    def test_cli_behavior_is_unchanged_for_migrated_commands(self):
        run = lambda *a, cwd=None: subprocess.run([sys.executable, SCRIPT, *a], capture_output=True,
                                                  text=True, cwd=cwd, timeout=60)
        r = run("--hydrate-facet", "unlazy")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Hydrated Facet: [cognitive] unlazy", r.stdout)
        r = run("--hydrate-facet", "unlazy", "--depth", "playbook")
        self.assertIn("### Phases", r.stdout)
        self.assertEqual(run("--hydrate-facet", "nope").returncode, 1)
        r = run("--lint-facets")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Facet lint clean", r.stdout)
        self.assertEqual(run("--list-facets", "--json").returncode, 0)
        r = run("-p", "fix the failing login bug")
        self.assertIn("Archetype: DEFECT", r.stdout)


class TestStatusCommand(unittest.TestCase):
    """F7: `--status` raised KeyError('stats') on every ledger (v3.2 shipped it broken)."""

    def _run(self, *args, cwd):
        return subprocess.run([sys.executable, SCRIPT, *args], cwd=cwd, capture_output=True,
                              text=True, timeout=60)

    def test_status_reports_counts_and_exits_zero(self):
        tmp = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(tmp, ".focusgate"))
            p = os.path.join(tmp, ".focusgate", "GATES.md")
            with open(p, "w", encoding="utf-8") as f:
                f.write("# T\n\n## 2. Acceptance Gates\n\n### Production Gates\n"
                        "- [x] a: done\n  CHECK: test -e x\n  EXPECT: .\n"
                        "- [ ] b: open\n  CHECK: test -e y\n  EXPECT: .\n")
            r = self._run("--status", p, cwd=tmp)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Production Gates: 1/2 met", r.stdout)
            self.assertNotIn("Traceback", r.stderr)
            j = self._run("--status", p, "--json", cwd=tmp)
            self.assertEqual(j.returncode, 0, j.stderr)
            self.assertIn("stats", json.loads(j.stdout))
        finally:
            shutil.rmtree(tmp)


class TestFitness(unittest.TestCase):
    def test_main_only_shrinks(self):
        tree = ast.parse(read("core", "cli", "app.py"))
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        self.assertLessEqual(main.end_lineno - main.lineno + 1, MAX_MAIN_LINES)

    def test_script_only_shrinks(self):
        self.assertLessEqual(len(read("scripts", "focus-gate.py").splitlines()), MAX_SCRIPT_LINES)

    def test_core_never_imports_scripts(self):
        bad = []
        for dp, _d, fns in os.walk(os.path.join(ROOT, "core")):
            for fn in fns:
                if fn.endswith(".py"):
                    tree = ast.parse(open(os.path.join(dp, fn), encoding="utf-8").read())
                    for n in ast.walk(tree):
                        names = [a.name for a in n.names] if isinstance(n, ast.Import) else \
                                [n.module or ""] if isinstance(n, ast.ImportFrom) else []
                        if any(x == "scripts" or x.startswith("scripts.") for x in names):
                            bad.append(os.path.join(dp, fn))
        self.assertEqual(bad, [])


class TestV33Docs(unittest.TestCase):
    def test_single_version_source(self):
        from core.version import RELEASE_LABEL, VERSION
        self.assertEqual(RELEASE_LABEL, f"v{VERSION}-PROD")
        for doc in ("SKILL.md", "SPEC.md"):
            self.assertIn(RELEASE_LABEL, read(doc), doc)

    def test_facet_authoring_guide_exists_and_names_every_lint_code(self):
        guide = read("references", "facets.md")
        for code in ("NO_PLAYBOOK", "PHASE_NO_EXIT", "TELL_NO_DETECT", "DANGLING_HANDOFF",
                     "TEMPLATE_DISHONEST", "OVER_BUDGET", "THIN_DIRECTIVE", "VAGUE_PHRASE"):
            self.assertIn(code, guide, code)

    def test_changelog_and_audit_cover_v33(self):
        self.assertIn("## v3.3-PROD", read("CHANGELOG.md"))
        a = read("AUDIT.md")
        self.assertIn("v3.3", a)
        self.assertIn("Open items", a)


if __name__ == "__main__":
    unittest.main()
