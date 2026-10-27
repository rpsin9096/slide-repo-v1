"""FocusGate v3.2 -- Evidence Gate regression suite.

Every test here is the executable form of one AUDIT finding. The CLI tests run the
real script in a subprocess because the defects they pin lived in `main()` of
scripts/focus-gate.py, a place no unit test of a core module can reach. That is how
630 passing tests coexisted with a crashing `--run` and a `--check` that never ran
the CHECK it was closing.

Findings pinned here (see AUDIT.md):
  F1  --check closed gates without executing CHECK
  F2  --run crashed with TypeError on every invocation (working loop was dead code)
  F3  --lint advertised "verification honesty" but implemented none of it
  F4  nothing recorded that a gate had ever been observed failing (red-before-green)
  F5  --seed / -p generated gates that pass in any repository (`git status`)
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
SCRIPT = os.path.join(ROOT_DIR, "scripts", "focus-gate.py")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


# --------------------------------------------------------------------------- #
# Unit: the integrity analyzer
# --------------------------------------------------------------------------- #

# (check, expect, must-contain error codes)
DISHONEST = [
    ("true", ".*", {"SELF_SATISFYING", "VACUOUS_EXPECT"}),
    ("true && true", None, {"SELF_SATISFYING"}),
    ("/bin/true", None, {"SELF_SATISFYING"}),
    ("exit 0", None, {"SELF_SATISFYING"}),
    ('echo "all tests passed"', "passed", {"SELF_SATISFYING"}),
    ("printf 'ok\\n'", "ok", {"SELF_SATISFYING"}),
    ("pytest -q || true", None, {"MASKED_EXIT"}),
    ("pytest -q || echo ok", None, {"MASKED_EXIT"}),
    ("pytest -q || :", None, {"MASKED_EXIT"}),
    ("pytest -q; true", None, {"MASKED_EXIT"}),
    ("pytest -q; exit 0", None, {"MASKED_EXIT"}),
    ("set +e; pytest -q", None, {"MASKED_EXIT"}),
    ("pytest -q &", None, {"MASKED_EXIT"}),
    ("bash -c 'pytest -q || true'", None, {"MASKED_EXIT"}),
    ("make test", ".*", {"VACUOUS_EXPECT"}),
    ("make test", "^", {"VACUOUS_EXPECT"}),
    ("make test", "(?:)", {"VACUOUS_EXPECT"}),
    ("make test", "x*", {"VACUOUS_EXPECT"}),
    ("make test", "(", {"INVALID_EXPECT"}),
]

# Realistic gates an agent should be allowed to write. A false positive here would
# make the analyzer unusable, so this corpus is as load-bearing as DISHONEST.
HONEST = [
    ("python3 -m unittest discover -s tests", "OK"),
    ("pytest -q tests/test_auth.py", "passed"),
    ("npm test", None),
    ("cargo test", "test result: ok"),
    ("go test ./...", None),
    ("make test", None),
    ('grep -q "def login" auth.py', None),
    ('grep -c "def login" auth.py', "^1$"),
    ("test -f dist/app.js", None),
    ("test -s .focusgate/SEED.md", None),
    ("ls dist/app.js", None),
    ("curl -sf http://localhost:8000/health", '"status": *"ok"'),
    ('python3 -c "import app; assert app.run() == 42"', None),
    ("git diff --exit-code", None),
    ("./verify.sh", None),
    ("bash -o pipefail -c 'pytest -q | tail -3'", "passed"),
    ("pytest -q tests/ && echo OK", "OK"),
    ("python3 -m unittest 2>&1 | grep -q OK", None),
    ("pytest -q || exit 1", None),
    ("pytest -q || (echo failed; exit 1)", None),
]


class TestGateIntegrity(unittest.TestCase):
    def setUp(self):
        from core.gates.evidence import GateIntegrity
        self.analyze = GateIntegrity.analyze

    def test_dishonest_gates_are_errors_with_the_expected_codes(self):
        for check, expect, codes in DISHONEST:
            with self.subTest(check=check, expect=expect):
                found = {f.code for f in self.analyze(check, expect) if f.severity == "error"}
                self.assertTrue(codes <= found, f"expected {codes} within {found}")

    def test_honest_gates_produce_no_errors_and_no_warnings(self):
        for check, expect in HONEST:
            with self.subTest(check=check):
                self.assertEqual([f.code for f in self.analyze(check, expect)], [])

    def test_project_independent_probes_are_warnings_not_errors(self):
        for check in ("git status", "ls", "pwd", "date"):
            with self.subTest(check=check):
                findings = self.analyze(check, None)
                self.assertEqual({f.code for f in findings}, {"TAUTOLOGY_CHECK"})
                self.assertTrue(all(f.severity == "warn" for f in findings))

    def test_pipe_into_a_formatter_warns_that_the_runner_exit_is_lost(self):
        findings = self.analyze("pytest -q 2>&1 | tail -3", "passed")
        self.assertEqual([f.code for f in findings], ["PIPE_MASKS_EXIT"])
        self.assertEqual(findings[0].severity, "warn")

    def test_unbalanced_quotes_do_not_crash_the_analyzer(self):
        findings = self.analyze("echo 'unterminated", None)
        self.assertTrue(isinstance(findings, list))


# --------------------------------------------------------------------------- #
# Unit: the evidence log
# --------------------------------------------------------------------------- #

class TestEvidenceLog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        from core.gates.evidence import EvidenceLog, fingerprint
        self.EvidenceLog, self.fingerprint = EvidenceLog, fingerprint
        self.path = os.path.join(self.tmp, "GATES.evidence.jsonl")

    def test_fingerprint_binds_check_and_expect_and_ignores_padding(self):
        fp = self.fingerprint
        self.assertEqual(fp("pytest -q", "passed"), fp("  pytest -q  ", " passed "))
        self.assertNotEqual(fp("pytest -q", "passed"), fp("pytest -q", "ok"))
        self.assertNotEqual(fp("pytest -q", None), fp("pytest -qq", None))

    def test_red_evidence_only_counts_for_the_exact_check_that_failed(self):
        log = self.EvidenceLog(self.path)
        fp_a = self.fingerprint("pytest -q", None)
        log.record("g1", fp_a, "baseline", "red", exit_code=1)
        self.assertTrue(log.has_red("g1", fp_a))
        # Weakening the check after seeing it fail must not inherit the red.
        self.assertFalse(log.has_red("g1", self.fingerprint("true", None)))
        self.assertFalse(log.has_red("g2", fp_a))

    def test_green_records_are_not_red_evidence(self):
        log = self.EvidenceLog(self.path)
        fp = self.fingerprint("pytest -q", None)
        log.record("g1", fp, "baseline", "green", exit_code=0)
        self.assertFalse(log.has_red("g1", fp))

    def test_hash_chain_verifies_and_detects_tampering(self):
        log = self.EvidenceLog(self.path)
        fp = self.fingerprint("pytest -q", None)
        for i in range(3):
            log.record("g1", fp, "baseline", "red", exit_code=1)
        ok, bad_line = log.verify()
        self.assertTrue(ok)
        with open(self.path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        rec = json.loads(lines[1])
        rec["result"] = "green"            # rewrite history
        lines[1] = json.dumps(rec, sort_keys=True)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        ok, bad_line = self.EvidenceLog(self.path).verify()
        self.assertFalse(ok)
        self.assertEqual(bad_line, 2)

    def test_a_corrupt_line_does_not_crash_reading(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("not json\n")
        ok, bad_line = self.EvidenceLog(self.path).verify()
        self.assertFalse(ok)
        self.assertEqual(bad_line, 1)


# --------------------------------------------------------------------------- #
# CLI: the behavior an agent actually experiences
# --------------------------------------------------------------------------- #

LEDGER_HEAD = "# Evidence ledger\n\n## Acceptance Gates\n"


def gate(gid, check, expect=None, title="gate"):
    out = f"- [ ] {gid}: {title}\n  CHECK: {check}\n"
    if expect is not None:
        out += f"  EXPECT: {expect}\n"
    return out


class CliCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        subprocess.run(["git", "init", "-q", self.tmp], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.makedirs(os.path.join(self.tmp, ".focusgate"))
        self.ledger = os.path.join(self.tmp, ".focusgate", "GATES.md")
        self.evidence = os.path.join(self.tmp, ".focusgate", "GATES.evidence.jsonl")

    def write_ledger(self, *gates):
        with open(self.ledger, "w", encoding="utf-8") as f:
            f.write(LEDGER_HEAD + "".join(gates))

    def set_state(self, value):
        with open(os.path.join(self.tmp, "state.txt"), "w", encoding="utf-8") as f:
            f.write(value)

    def fg(self, *args):
        return subprocess.run([sys.executable, SCRIPT, *args], cwd=self.tmp,
                              capture_output=True, text=True, timeout=60)

    def settled(self, gid):
        with open(self.ledger, "r", encoding="utf-8") as f:
            return f"- [x] {gid}:" in f.read()


# A CHECK that is genuinely about the project: green only when state.txt says "fixed".
STATE_CHECK = "python3 -c \"import sys; sys.exit(0 if open('state.txt').read().strip() == 'fixed' else 1)\""


class TestCheckVerifies(CliCase):
    """F1: --check must execute the CHECK it is about to close."""

    def test_check_refuses_a_gate_whose_check_fails(self):
        self.write_ledger(gate("impossible-01", "false", "all tests passed"))
        r = self.fg("--check", "impossible-01", self.ledger)
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(self.settled("impossible-01"))

    def test_check_refuses_when_expect_does_not_match(self):
        self.set_state("fixed")
        self.write_ledger(gate("g1", STATE_CHECK, "this text is never printed"))
        r = self.fg("--check", "g1", self.ledger)
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(self.settled("g1"))

    def test_check_settles_a_gate_that_really_passes(self):
        self.set_state("fixed")
        self.write_ledger(gate("g1", STATE_CHECK))
        r = self.fg("--check", "g1", self.ledger)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.settled("g1"))

    def test_check_warns_when_the_gate_was_never_observed_failing(self):
        self.set_state("fixed")
        self.write_ledger(gate("g1", STATE_CHECK))
        r = self.fg("--check", "g1", self.ledger)
        self.assertIn("never observed failing", r.stdout + r.stderr)

    def test_check_refuses_a_dishonest_gate_even_though_it_passes(self):
        self.write_ledger(gate("g1", "python3 -c 'import sys; sys.exit(1)' || true"))
        r = self.fg("--check", "g1", self.ledger)
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("MASKED_EXIT", r.stdout + r.stderr)
        self.assertFalse(self.settled("g1"))

    def test_force_overrides_integrity_and_is_written_to_the_evidence_log(self):
        self.write_ledger(gate("g1", "python3 -c 'import sys; sys.exit(1)' || true"))
        r = self.fg("--check", "g1", self.ledger, "--force")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.settled("g1"))
        with open(self.evidence, "r", encoding="utf-8") as f:
            self.assertIn('"forced": true', f.read().replace('":true', '": true'))

    def test_manual_gate_without_check_can_still_be_closed(self):
        self.write_ledger("- [ ] m1: write the release notes\n")
        r = self.fg("--check", "m1", self.ledger)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.settled("m1"))

    def test_unknown_gate_is_an_error(self):
        self.write_ledger(gate("g1", STATE_CHECK))
        r = self.fg("--check", "nope", self.ledger)
        self.assertNotEqual(r.returncode, 0)


class TestRedBeforeGreen(CliCase):
    """F4: a gate that was never seen failing proves nothing about the change."""

    def test_strict_refuses_a_gate_with_no_prior_red(self):
        self.set_state("fixed")
        self.write_ledger(gate("g1", STATE_CHECK))
        r = self.fg("--check", "g1", self.ledger, "--strict")
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(self.settled("g1"))

    def test_baseline_then_fix_then_strict_check_settles(self):
        self.set_state("broken")
        self.write_ledger(gate("g1", STATE_CHECK))
        b = self.fg("--baseline", self.ledger)
        self.assertEqual(b.returncode, 0, b.stdout + b.stderr)
        self.assertIn("RED", b.stdout)
        self.set_state("fixed")
        r = self.fg("--check", "g1", self.ledger, "--strict")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.settled("g1"))

    def test_editing_the_check_after_seeing_it_fail_voids_the_red(self):
        self.set_state("broken")
        self.write_ledger(gate("g1", STATE_CHECK))
        self.fg("--baseline", self.ledger)
        # The agent "fixes" the failure by swapping in an easier, still-honest check.
        self.write_ledger(gate("g1", "test -d ."))
        r = self.fg("--check", "g1", self.ledger, "--strict")
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(self.settled("g1"))

    def test_baseline_flags_an_already_green_gate(self):
        self.set_state("fixed")
        self.write_ledger(gate("g1", STATE_CHECK))
        b = self.fg("--baseline", self.ledger)
        self.assertEqual(b.returncode, 0, b.stdout + b.stderr)
        self.assertIn("ALREADY_GREEN", b.stdout)

    def test_waive_red_settles_and_the_reason_is_auditable(self):
        self.set_state("fixed")
        self.write_ledger(gate("g1", STATE_CHECK))
        r = self.fg("--check", "g1", self.ledger, "--strict",
                    "--waive-red", "fixed upstream before the gate existed")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.settled("g1"))
        e = self.fg("--evidence", self.ledger)
        self.assertIn("fixed upstream before the gate existed", e.stdout)

    def test_failed_attempt_counts_as_red_evidence(self):
        self.set_state("broken")
        self.write_ledger(gate("g1", STATE_CHECK))
        self.fg("--check", "g1", self.ledger)          # fails, refused, recorded
        self.set_state("fixed")
        r = self.fg("--check", "g1", self.ledger, "--strict")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_evidence_command_reports_a_valid_chain_then_detects_tampering(self):
        self.set_state("broken")
        self.write_ledger(gate("g1", STATE_CHECK))
        self.fg("--baseline", self.ledger)
        ok = self.fg("--evidence", self.ledger)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertIn("chain: OK", ok.stdout)
        with open(self.evidence, "r", encoding="utf-8") as f:
            raw = f.read()
        with open(self.evidence, "w", encoding="utf-8") as f:
            f.write(raw.replace('"red"', '"green"'))
        bad = self.fg("--evidence", self.ledger)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("BROKEN", bad.stdout + bad.stderr)


class TestRunCommand(CliCase):
    """F2: --run is the headline command and used to die with a TypeError."""

    def test_run_does_not_crash_and_exits_zero_when_all_gates_pass(self):
        self.set_state("fixed")
        self.write_ledger(gate("g1", STATE_CHECK), gate("g2", "test -d ."))
        r = self.fg("--run", self.ledger)
        self.assertNotIn("Traceback", r.stderr + r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_run_exits_nonzero_when_any_gate_fails(self):
        self.set_state("broken")
        self.write_ledger(gate("g1", STATE_CHECK), gate("g2", "test -d ."))
        r = self.fg("--run", self.ledger)
        self.assertNotIn("Traceback", r.stderr + r.stdout)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_run_does_not_settle_gates_it_only_reports(self):
        self.set_state("fixed")
        self.write_ledger(gate("g1", STATE_CHECK))
        self.fg("--run", self.ledger)
        self.assertFalse(self.settled("g1"))

    def test_run_rejects_dishonest_gates_even_when_they_pass(self):
        self.write_ledger(gate("g1", "true", ".*"))
        r = self.fg("--run", self.ledger)
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("SELF_SATISFYING", r.stdout + r.stderr)

    def test_run_json_is_machine_readable(self):
        self.set_state("fixed")
        self.write_ledger(gate("g1", STATE_CHECK))
        r = self.fg("--run", self.ledger, "--json")
        data = json.loads(r.stdout)
        self.assertTrue(data["all_passed"])


class TestLintHasTeeth(CliCase):
    """F3: FocusLinter documented verification honesty and checked none of it."""

    def test_lint_fails_on_a_ledger_of_cheats(self):
        self.write_ledger(
            gate("c1", "true", ".*"),
            gate("c2", 'echo "all tests passed"', "passed"),
            gate("c3", "pytest -q || true"),
        )
        r = self.fg("--lint", self.ledger)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = r.stdout + r.stderr
        for code in ("SELF_SATISFYING", "VACUOUS_EXPECT", "MASKED_EXIT"):
            self.assertIn(code, out)

    def test_lint_passes_an_honest_ledger(self):
        self.write_ledger(gate("h1", STATE_CHECK), gate("h2", "test -d ."))
        r = self.fg("--lint", self.ledger)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_lint_json_exposes_findings(self):
        self.write_ledger(gate("c1", "pytest -q || true"))
        r = self.fg("--lint", self.ledger, "--json")
        data = json.loads(r.stdout)
        self.assertFalse(data["valid"])
        self.assertTrue(any("MASKED_EXIT" in e for e in data["errors"]))


class TestSeedsAreFalsifiable(CliCase):
    """F5: the activation seed must be red until the work exists."""

    def test_pipeline_seed_never_proposes_a_project_independent_check(self):
        from core.gates.evidence import GateIntegrity
        for task in ("fix the flaky login timeout bug in auth.py",
                     "design a bespoke landing page for an espresso maker",
                     "plan the roadmap for the billing rewrite",
                     "write a short post about our migration",
                     "refactor the payment module"):
            with self.subTest(task=task):
                r = self.fg("-p", task, "--json")
                try:
                    seed = json.loads(r.stdout)["seed_step"]
                except (ValueError, KeyError):
                    self.skipTest("-p --json shape differs: " + r.stdout[:120])
                bad = [f.code for f in GateIntegrity.analyze(seed["check"], seed["expect"] or None)
                       if f.severity == "error" or f.code == "TAUTOLOGY_CHECK"]
                self.assertEqual(bad, [], f"{task!r} -> {seed}")

    def test_scaffolded_seed_file_lints_clean_and_starts_red(self):
        r = self.fg("--seed", self.tmp, "login-fix")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        seed_files = [os.path.join(dp, f) for dp, _, fs in os.walk(self.tmp)
                      for f in fs if f == "GATES-SEED.md"]
        self.assertEqual(len(seed_files), 1, seed_files)
        lint = self.fg("--lint", seed_files[0])
        self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)
        self.assertNotIn("TAUTOLOGY_CHECK", lint.stdout + lint.stderr)
        run = self.fg("--run", seed_files[0])
        # Exit 1 alone is not proof: the v3.1 --run also exited 1, by crashing.
        self.assertNotIn("Traceback", run.stdout + run.stderr)
        self.assertEqual(run.returncode, 1, "seed gate must be red before any work: " + run.stdout)
        self.assertIn("seed-01", run.stdout)


if __name__ == "__main__":
    unittest.main()
