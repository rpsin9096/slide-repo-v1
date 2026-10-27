"""FocusGate v3.4 -- one dispatcher, a thin entry point, no dead flags.

Findings pinned here (see AUDIT.md):
  G1  main() was ~1880 lines of ~70 branches; the script held 2900 lines and 13 domain classes
  G2  two dispatchers: CLIDispatcher.dispatch (if-chain) and main()'s own chain
  G3  4 branches of main() were unreachable duplicates of early routes (dead code)
  G4  the parser documented flags nothing reads (--install-guardrails, --retro)
  G5  ContractValidator raised NameError (DomainEvent was never imported)
  G6  two facades kept only for tests (JITHydrationEngine, _lint_facet_contracts)
Ratchets may only go DOWN.
"""
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import shutil
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SCRIPT = os.path.join(ROOT, "scripts", "focus-gate.py")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# --- ratchets (lower only) -------------------------------------------------
MAX_APP_MAIN_LINES = 95
MAX_SCRIPT_LINES = 28
MAX_DISPATCH_METHOD_LINES = 15
MAX_COMMAND_MODULE_LINES = 650
# ---------------------------------------------------------------------------

# Flags that modify another command instead of being one. Each must still be READ somewhere.
MODIFIERS = {"--json", "--strict", "--force", "--waive-red", "--ledger-root", "--depth", "--help",
             "--version", "--preview", "--dispatch", "--receipt", "--limit", "--dry-run"}


def read(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return f.read()


def py_files(*parts):
    out = []
    for dp, _d, fns in os.walk(os.path.join(ROOT, *parts)):
        out += [os.path.join(dp, f) for f in sorted(fns) if f.endswith(".py")]
    return out


def run(*args, cwd=None, timeout=60):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, cwd=cwd, timeout=timeout)


class TestThinEntry(unittest.TestCase):
    def test_script_is_an_entry_point_only(self):
        src = read("scripts", "focus-gate.py")
        self.assertLessEqual(len(src.splitlines()), MAX_SCRIPT_LINES)
        tree = ast.parse(src)
        self.assertEqual([n.name for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))], [])

    def test_main_is_dispatch_not_branches(self):
        src = read("core", "cli", "app.py")
        tree = ast.parse(src)
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        self.assertLessEqual(main.end_lineno - main.lineno + 1, MAX_APP_MAIN_LINES)
        # only the preamble flags (--help, --version) are read in app.py; every command is resolved
        self.assertEqual(set(re.findall(r"getattr\(args, '(\w+)'", src)) - {"help", "version"}, set())

    def test_no_command_module_grows_past_the_cap(self):
        for p in py_files("core", "cli", "commands"):
            self.assertLessEqual(len(open(p, encoding="utf-8").read().splitlines()), MAX_COMMAND_MODULE_LINES, p)

    def test_facades_are_gone(self):
        for p in py_files("core") + [SCRIPT]:
            text = open(p, encoding="utf-8").read()
            self.assertNotIn("class JITHydrationEngine", text, p)
            self.assertNotIn("def _lint_facet_contracts", text, p)

    def test_moved_classes_live_in_core(self):
        from core.cli.pipeline import FocusDriverPipeline
        from core.domain_audit import ContractValidator, DomainAuditor
        from core.focus_support import ActivationSeed, DistractionRecovery, SingleItemQueue
        from core.writing_suite import WritingSuite
        from core.cli.intent import AutonomousRouter
        from core.cli.parser import build_parser, known_flags
        self.assertIn("--hydrate-facet", known_flags())
        self.assertTrue(all([FocusDriverPipeline, ContractValidator, DomainAuditor, ActivationSeed,
                             DistractionRecovery, SingleItemQueue, WritingSuite, AutonomousRouter, build_parser]))


class TestOneDispatcher(unittest.TestCase):
    def test_dispatch_is_a_registry_lookup_not_a_chain(self):
        tree = ast.parse(read("core", "cli", "dispatch.py"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        d = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "dispatch")
        self.assertLessEqual(d.end_lineno - d.lineno + 1, MAX_DISPATCH_METHOD_LINES)
        self.assertEqual(sum(isinstance(n, ast.If) for n in d.body), 0)

    def test_registry_holds_every_command(self):
        from core.cli.registry import REGISTRY
        cmds = REGISTRY.commands()
        self.assertGreaterEqual(len(cmds), 110)
        self.assertGreaterEqual(sum(c.early for c in cmds), 50)

    def test_early_routes_resolve_before_ledger_commands(self):
        from core.cli.registry import REGISTRY, CommandContext
        import argparse
        ns = argparse.Namespace(**{k: None for k in ("heal",)}, mcp=False)
        ns.swarm_status = None
        ctx = CommandContext(args=argparse.Namespace(), argv=["--actor-status"], is_json=False, cmd="--actor-status")
        c = REGISTRY.resolve(ctx)
        self.assertIsNotNone(c)
        self.assertTrue(c.early)

    def test_resolve_order_is_stable_and_names_unique(self):
        from core.cli.registry import REGISTRY
        names = [c.name for c in REGISTRY.commands()]
        self.assertEqual(len(names), len(set(names)))

    def test_checkpoint_commands_still_work_through_the_registry(self):
        tmp = tempfile.mkdtemp()
        try:
            run("--init", ".", cwd=tmp)
            r = run("--list-checkpoints", cwd=tmp)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            shutil.rmtree(tmp)

    def test_unknown_command_still_errors_with_help(self):
        r = run("--no-such-flag-xyz")
        self.assertNotEqual(r.returncode, 0)


class TestHandlersReturnCodes(unittest.TestCase):
    def test_handlers_do_not_call_sys_exit(self):
        offenders = []
        for p in py_files("core", "cli", "commands"):
            tree = ast.parse(open(p, encoding="utf-8").read())
            for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
                stack = list(ast.iter_child_nodes(fn))
                while stack:
                    n = stack.pop()
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                        continue
                    if isinstance(n, ast.Call) and ast.unparse(n.func) == "sys.exit":
                        offenders.append(f"{os.path.relpath(p, ROOT)}:{n.lineno}")
                    stack.extend(ast.iter_child_nodes(n))
        self.assertEqual(offenders, [])

    def test_the_rules_cover_every_command(self):
        """The two rules above are only meaningful if the commands actually live in these modules."""
        n = 0
        for p in py_files("core", "cli", "commands"):
            tree = ast.parse(open(p, encoding="utf-8").read())
            n += sum(1 for fn in tree.body if isinstance(fn, ast.FunctionDef) and fn.args.args
                     and fn.args.args[0].arg == "ctx" and not fn.name.startswith("_"))
        self.assertGreaterEqual(n, 70)   # 62 migrated + the 14 flag commands, minus helpers

    def test_handlers_end_in_an_explicit_exit_code(self):
        """A handler that falls off the end returns None, i.e. exit 0 on a path that may have failed."""
        def exits(st):
            if not st:
                return False
            l = st[-1]
            if isinstance(l, (ast.Return, ast.Raise)):
                return True
            if isinstance(l, ast.If):
                return exits(l.body) and exits(l.orelse)
            if isinstance(l, ast.Try):
                return (exits(l.body) and all(exits(h.body) for h in l.handlers)) or exits(l.finalbody)
            return False
        from core.cli.registry import REGISTRY
        loose = []
        for p in py_files("core", "cli", "commands"):
            tree = ast.parse(open(p, encoding="utf-8").read())
            for fn in tree.body:
                if isinstance(fn, ast.FunctionDef) and fn.args.args and fn.args.args[0].arg == "ctx" \
                        and not fn.name.startswith("_match") and not exits(fn.body):
                    loose.append(f"{os.path.basename(p)}:{fn.name}")
        self.assertEqual(loose, [])
        self.assertTrue(REGISTRY.commands())


class TestNoDeadFlags(unittest.TestCase):
    def test_every_parser_flag_is_a_command_or_a_read_modifier(self):
        from core.cli.parser import known_flags
        from core.cli.registry import REGISTRY
        registered = REGISTRY.flags()
        sources = "\n".join(open(p, encoding="utf-8").read() for p in py_files("core") + py_files("scripts")
                            if not p.endswith(os.path.join("cli", "parser.py")))
        dead = []
        for flag in sorted(f for f in known_flags() if f.startswith("--")):
            if flag in registered:
                continue
            dest = flag[2:].replace("-", "_")
            read_somewhere = (f'"{flag}"' in sources or f"'{flag}'" in sources
                              or f"args.{dest}" in sources or f"'{dest}'" in sources or f'"{dest}"' in sources)
            if flag not in MODIFIERS or not read_somewhere:
                dead.append(flag)
        self.assertEqual(dead, [], "documented flags that nothing reads or runs")

    def test_phantom_flags_are_removed_from_help(self):
        from core.cli.parser import known_flags
        self.assertNotIn("--install-guardrails", known_flags())
        self.assertNotIn("--retro", known_flags())

    def test_preview_and_dispatch_are_exclusive(self):
        tmp = tempfile.mkdtemp()
        try:
            r = run("--orchestrate", "x", "--preview", "--dispatch", cwd=tmp)
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("opposites", r.stderr)
            self.assertFalse(os.path.exists(os.path.join(tmp, ".focusgate", "stages.json")),
                             "validation must happen before any orchestrator state is written")
        finally:
            shutil.rmtree(tmp)


class TestLatentBugs(unittest.TestCase):
    def test_validate_contracts_reads_a_real_event_log(self):
        tmp = tempfile.mkdtemp()
        try:
            p = os.path.join(tmp, "ev.jsonl")
            with open(p, "w", encoding="utf-8") as f:
                f.write(json.dumps({"id": "e1", "type": "X", "payload": {}, "timestamp": 1.0, "version": 1}) + "\n")
            r = run("--validate-contracts", p, cwd=tmp)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn("NameError", r.stderr)
            self.assertIn("Valid: 1/1", r.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_contract_validator_imports_its_schema(self):
        from core.domain_audit import ContractValidator
        res = ContractValidator.validate_events_file(os.path.join(ROOT, "nonexistent.jsonl"))
        self.assertEqual(res["status"], "PASS")
        self.assertIn("DomainEvent", read("core", "domain_audit.py").split("class DomainAuditor")[0])


class TestRigorSeesSwallowedExceptions(unittest.TestCase):
    """O10: the guard waved `except: pass` through as an idiom."""

    def _scan(self, code):
        from core.unlazy_guard import ExecutionRigorGuard
        return {v.violation_type for v in ExecutionRigorGuard.scan_for_laziness(code).violations}

    def test_broad_handlers_that_do_nothing_are_flagged(self):
        for code in ("try:\n    f()\nexcept Exception:\n    pass\n",
                     "try:\n    f()\nexcept:\n    pass\n",
                     "try:\n    f()\nexcept BaseException as e:\n    ...\n",
                     "try:\n    f()\nexcept Exception: pass\n"):
            self.assertIn("SWALLOWED_EXCEPTION", self._scan(code), code)

    def test_narrow_or_handled_exceptions_are_not(self):
        for code in ("try:\n    import x\nexcept ImportError:\n    pass\n",
                     "try:\n    f()\nexcept KeyError:\n    pass\n",
                     "try:\n    f()\nexcept Exception as e:\n    log(e)\n    raise\n"):
            self.assertNotIn("SWALLOWED_EXCEPTION", self._scan(code), code)

    def test_cli_reports_it(self):
        tmp = tempfile.mkdtemp()
        try:
            p = os.path.join(tmp, "sw.py")
            with open(p, "w", encoding="utf-8") as f:
                f.write("def f(x):\n    try:\n        return x.y\n    except Exception:\n        pass\n")
            r = run("--unlazy-rigor", p, cwd=tmp)
            self.assertIn("SWALLOWED_EXCEPTION", r.stdout)
        finally:
            shutil.rmtree(tmp)


class TestDestructiveChecksAreNeverExecuted(unittest.TestCase):
    """O2: a ledger from someone else is a command channel; --run/--baseline execute CHECKs unattended."""

    def _ledger(self, tmp, check):
        os.makedirs(os.path.join(tmp, ".focusgate"))
        p = os.path.join(tmp, ".focusgate", "GATES.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("# T\n\n## 2. Acceptance Gates\n\n### Production Gates\n"
                    f"- [ ] d: demo\n  CHECK: {check}\n  EXPECT: ran\n")
        return p

    def test_analyzer_flags_root_wipes_but_allows_scoped_deletes(self):
        from core.gates.evidence import GateIntegrity, errors_of
        codes = lambda c: {f.code for f in errors_of(GateIntegrity.analyze(c, "x"))}
        self.assertIn("DESTRUCTIVE_COMMAND", codes("rm -rf /"))
        self.assertIn("DESTRUCTIVE_COMMAND", codes("rm -rf ~ && echo done"))
        self.assertIn("DESTRUCTIVE_COMMAND", codes("git push --force origin main"))
        self.assertNotIn("DESTRUCTIVE_COMMAND", codes("rm -rf /tmp/build && test ! -e /tmp/build"))

    def test_baseline_run_and_force_never_execute_it(self):
        tmp = tempfile.mkdtemp()
        sentinel = os.path.join(tmp, "sentinel")
        try:
            # `dd if=` matches the guard's raw-disk rule; `of=` makes the sentinel file if it ever runs.
            p = self._ledger(tmp, f"dd if=/dev/null of={sentinel} count=0 && echo ran")
            self.assertEqual(run("--baseline", p, cwd=tmp).returncode, 0)
            run("--run", p, cwd=tmp)
            r = run("--check", "d", p, "--force", cwd=tmp)
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse(os.path.exists(sentinel), "the destructive CHECK was executed")
            self.assertIn("- [ ] d:", open(p, encoding="utf-8").read())
        finally:
            shutil.rmtree(tmp)

    def test_lint_reports_it_as_an_error(self):
        tmp = tempfile.mkdtemp()
        try:
            p = self._ledger(tmp, "dd if=/dev/null of=/dev/null count=0 && echo ran")
            r = run("--lint", p, cwd=tmp)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("DESTRUCTIVE_COMMAND", r.stdout + r.stderr)
        finally:
            shutil.rmtree(tmp)


class TestV34Docs(unittest.TestCase):
    def test_version_and_docs_agree(self):
        from core.version import RELEASE_LABEL, VERSION
        self.assertEqual((VERSION, RELEASE_LABEL), ("3.4", "v3.4-PROD"))
        for doc in ("SKILL.md", "SPEC.md"):
            self.assertIn(RELEASE_LABEL, read(doc), doc)

    def test_changelog_and_audit_cover_v34(self):
        self.assertIn("## v3.4-PROD", read("CHANGELOG.md"))
        a = read("AUDIT.md")
        self.assertIn("v3.4", a)
        self.assertIn("Open items", a)
        for fid in ("G1", "G2", "G3", "G4", "G5", "G6"):
            self.assertIn(fid, a, fid)

    def test_architecture_doc_names_the_registry_layout(self):
        doc = read("references", "architecture.md")
        for needle in ("core/cli/app.py", "core/cli/commands", "REGISTRY.resolve"):
            self.assertIn(needle, doc, needle)


if __name__ == "__main__":
    unittest.main()
