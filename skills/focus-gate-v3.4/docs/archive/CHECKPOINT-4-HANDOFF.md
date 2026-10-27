<!-- ARCHIVED. This document describes FocusGate v2.8 and is SUPERSEDED: v2.9 (Loop 22 CLI decomposition) and then the whole v3.0/v3.1 grid.
     Moved here by FocusGate v3.2 Loop 65 (AUDIT F18). Kept, not deleted, so the
     decision is on the record. Do not implement against it; read SPEC.md,
     ROADMAP.md and SKILL.md instead. -->

# FocusGate v2.8 — CHECKPOINT 4 HANDOFF
## Single-Source Facet Lifecycle + Unified Wave Verification

**Owner of this doc:** orchestrator (you already read it).
**Executor:** a focused agent with *minimal* reasoning. Do exactly the numbered steps. Do not improvise.
**Location:** this file lives in `focus-gate-v2.7.1/` (the v2.8 working checkpoint).
**Rule of the checkpoint:** you are *consolidating* things that already exist. You are NOT adding new engines, new pip packages, or new external APIs. If a step seems to need one, STOP and report.

---

## 0. READ FIRST (the only 6 rules)

1. Before any code change, run `python3 -m unittest discover -s tests` and confirm everything is `OK`. Baseline today = **all green** (verified: parts 1-4 + smoke = 86 tests pass).
2. Work ONE task at a time, in order: 4.1 → 4.2 → 4.3 → 4.4 → 4.5. Each task = RED test first, then minimal code, then GREEN, then one commit.
3. Paste the test code given here **verbatim** into the new test file. Do not rename tests.
4. Never edit any file in `facets/` except when a step explicitly says to. Never touch `.focusgate/` event files.
5. Zero new dependencies. `python3` stdlib only.
6. If any *previously green* test turns red and you cannot fix it inside the current task, `git stash` nothing — stop and print: `BLOCKED <task> <test-name> <error>`.

---

## 1. Micro-Glossary (4 anchors — memorize these, nothing else)

- **Compiled Index** = `facets/facet_index.json`. The ONE machine-readable truth about every facet (id, context, mode=WINDOW/EPHEMERAL, priority, triggers, oracle). Produced by `compile_facets.py` from facet-meta blocks.
- **Facet-Meta Contract** = the ```` ```facet-meta ```` fenced block at the top of each `facets/<context>/<id>.md`. The human-editable source of the Compiled Index.
- **Registry (the thing we delete)** = `JITHydrationEngine.FACET_REGISTRY`, a hand-typed dict inside `scripts/focus-gate.py` that duplicates the Compiled Index and drifts from it.
- **Wave** = one orchestration run. **Wave Verification** = one command that answers "is this whole wave actually done?" by running every verifier and printing ONE verdict.

---

## 2. Friction Audit (why Checkpoint 4 exists — evidence, not opinion)

| ID | Friction | Evidence (file:line) | Why it hurts a low-reasoning agent |
|----|----------|----------------------|------------------------------------|
| F1 | **Dual facet source-of-truth.** `--hydrate-facet` / `--list-facets` read the hand-typed `FACET_REGISTRY`; routing/orchestrate read `facet_index.json`. Their `mode` fields use *different vocabularies* (`"Bespoke Visual Identity"` vs `WINDOW`). | `scripts/focus-gate.py:696-716` (registry) vs `facets/facet_index.json` + `core/facet_router.py:1-6`. | Same facet shows two different "mode" values depending on which command you run. Agent can't tell truth. |
| F2 | **No drift guard on the Compiled Index.** `compile_facets.py` is deterministic, but *no test* asserts the committed `facet_index.json` equals the compiled output. | `scripts/compile_facets.py` (whole); `grep compile_facets tests/ → NONE`. | Edit one facet-meta → routing silently stale until a human re-runs compile. |
| F3 | **Canonical token estimator duplicated** at 5 call sites using raw `len(...)//4` instead of importing `core.tokens.estimate_tokens`. | `scripts/focus-gate.py:741, 762, 968, 971, 1049` vs canonical `core/tokens.py:7-13`. | Reported token counts can disagree with the 400/150 ceilings enforced elsewhere. |
| F4 | **CLI discoverability / version drift.** 3855-line CLI exposes **60** commands; SKILL.md documents **12** (none from v2.8). Help text still says engine `1.3.5`; runtime prints `2.7.1`. 3 spike commands have empty `help=''`. | help: `scripts/focus-gate.py:1975`, `2074` (`1.3.5`); runtime `2102-2104` (`2.7.1`); spike help `2047-2049`; SKILL.md §4 lists only v2.7 cmds. | Agent cannot discover the v2.8 gates (`--lint-facets`, `--audit-context-sufficiency`, `--synthesize-pipeline`); stale version makes it doubt which build it has. |
| F6 | **Mode mapping triplicated.** EPHEMERAL/WINDOW lives in facet-meta AND `context_policy.py` keyword tables AND a manual reconcile check inside `--lint-facets`. | `core/context_policy.py:10-25` (keyword tables) vs contract `mode:`; reconcile at `scripts/focus-gate.py:3182-3184`. | Three places to keep in sync; a weak agent edits one and breaks two. |

(F5 = "no single end-to-end verify gate" — the verifiers all exist as separate commands: `--run`, `--verify-stage`, `--orchestrator-verify`, `--audit-all`, `--audit-context-sufficiency`, `--lint-facets`, `--validate-contracts` — but nothing aggregates them.)

**Conclusion:** the v2.8 parts 1-4 collapsed *routing* into the Compiled Index but left the Registry, the mode tables, the token formula, the doc, and the "am I done?" flow as separate drifting sources. **Checkpoint 4 finishes the collapse and adds one aggregate gate.** No new capability — only single-sourcing + one aggregator.

---

## 3. Definition of Done (copy into your final report)

Checkpoint 4 is DONE only when ALL are true:
```
CHECK: python3 -m unittest discover -s tests
EXPECT: OK  (parts 1-4 still green AND tests/test_facet_lifecycle_v28_part5.py green)

CHECK: grep -c "FACET_REGISTRY" scripts/focus-gate.py
EXPECT: 0   (grep exits 1, count 0)

CHECK: python3 scripts/focus-gate.py --list-facets --json | python3 -c "import sys,json;d=json.load(sys.stdin);assert all(f['mode'] in ('WINDOW','EPHEMERAL') for f in d);assert len(d)==19;print('OK')"
EXPECT: OK

CHECK: grep -c "_EPHEMERAL_KEYWORDS\|_WINDOW_KEYWORDS" core/context_policy.py
EXPECT: 0

CHECK: python3 scripts/focus-gate.py --lint-facets; echo "EXIT=$?"
EXPECT: clean / no errors, EXIT=0

CHECK: python3 scripts/focus-gate.py --verify-wave --json | python3 -c "import sys,json;print(json.load(sys.stdin)['clean'])"
EXPECT: True

CHECK: python3 scripts/focus-gate.py --help | grep -c "1.3.5"
EXPECT: 0
```

---

## 4. Vertical Slices (execute in order — TDD: RED → minimal GREEN → commit)

Create the shared test file once, append to it each task:
`tests/test_facet_lifecycle_v28_part5.py`
Header (paste once, top of file):
```python
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
```

---

### TASK 4.1 — Hydrate from Compiled Index; delete FACET_REGISTRY (fixes F1)
**Est: 20 min.** Single file touched: `scripts/focus-gate.py`.

**RED** — append to the test file:
```python
class TestHydrateFromIndex(unittest.TestCase):
    def _engine(self):
        sys.argv = ["focus-gate.py"]
        # load CLI module without running main()
        import importlib.util
        spec = importlib.util.spec_from_file_location("fg_cli", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.JITHydrationEngine

    def test_hydrate_mode_is_window_ephemeral_vocabulary(self):
        from core.tokens import estimate_tokens
        eng = self._engine()
        info = eng.hydrate("frontend-design")
        self.assertEqual(info["context"], "design")
        self.assertEqual(info["mode"], "WINDOW")          # NOT the old prose label
        self.assertEqual(info["tokens"], estimate_tokens(info["directive"]))

    def test_list_facets_modes_all_valid(self):
        eng = self._engine()
        modes = {f["mode"] for f in eng.list_facets()}
        self.assertTrue(modes <= {"WINDOW", "EPHEMERAL"}, modes)
        self.assertEqual(len(eng.list_facets()), 19)

    def test_unknown_facet_lists_index_ids(self):
        eng = self._engine()
        with self.assertRaises(ValueError) as ctx:
            eng.hydrate("no-such-facet-xyz")
        self.assertIn("frontend-design", str(ctx.exception))

    def test_facet_registry_constant_is_gone(self):
        with open(SCRIPT, encoding="utf-8") as f:
            self.assertNotIn("FACET_REGISTRY", f.read())
```
Run: `python3 tests/test_facet_lifecycle_v28_part5.py TestHydrateFromIndex` → expect **FAIL/ERROR**.

**GREEN (minimal):** rewrite the two classmethods on `JITHydrationEngine` (currently `scripts/focus-gate.py:718-772`) and delete `FACET_REGISTRY` (696-716). Do not add imports at top of the 3855-line file if the module already imports `core.facet_router` lazily elsewhere — use function-local imports:
```python
@classmethod
def hydrate(cls, facet_name):
    from core.facet_router import load_index
    from core.tokens import estimate_tokens
    norm = facet_name.strip().lower()
    index = load_index(os.path.join(cls.get_facets_dir(), "facet_index.json"))
    meta = index.get("facets", {}).get(norm)
    if meta is None:
        raise ValueError(f"Unknown facet: {facet_name!r}. Available: {sorted(index.get('facets', {}))}")
    path = os.path.join(cls.get_facets_dir(), meta["context"], norm + ".md")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Facet directive file not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"facet": norm, "context": meta["context"], "mode": meta["mode"],
            "path": path, "tokens": estimate_tokens(content), "directive": content}

@classmethod
def list_facets(cls):
    from core.facet_router import load_index
    from core.tokens import estimate_tokens
    idx_dir = cls.get_facets_dir()
    index = load_index(os.path.join(idx_dir, "facet_index.json"))
    out = []
    for fid, meta in index.get("facets", {}).items():
        path = os.path.join(idx_dir, meta["context"], fid + ".md")
        exists = os.path.exists(path)
        tok = estimate_tokens(open(path, encoding="utf-8").read()) if exists else 0
        out.append({"facet": fid, "context": meta["context"], "mode": meta["mode"],
                    "tokens": tok, "available": exists})
    return sorted(out, key=lambda f: f["facet"])
```
Also update the `--list-facets` header line that prints `available={len(JITHydrationEngine.FACET_REGISTRY)}` (`scripts/focus-gate.py:3149`) → `available={len(JITHydrationEngine.list_facets())}`.

**GREEN command:** `python3 tests/test_facet_lifecycle_v28_part5.py TestHydrateFromIndex` → `OK`. Then full suite green.
**Commit:** `feat(v2.8-c4): hydrate facets from compiled index, remove FACET_REGISTRY (F1)`

---

### TASK 4.2 — Index freshness guard + reusable builder in core (fixes F2)
**Est: 25 min.** Files: create `core/facet_index.py`, thin `scripts/compile_facets.py`, edit `core/facet_router.py`, edit `--lint-facets`.

**Why core:** `--lint-facets` and `--verify-wave` (core-adjacent CLI code) must reuse the compiler without `core/` importing `scripts/` (layering violation). → **Micro-ADR 4.2** below.

**RED:**
```python
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
```
Run the first two → **FAIL** (`ModuleNotFoundError: core.facet_index`).

**GREEN (minimal):**
1. Create `core/facet_index.py` holding the builder **moved verbatim** from `scripts/compile_facets.py` plus the freshness check:
```python
import json, os
from core.facet_contract import load_contracts, FacetContractError  # keep same error type

def build_index(facets_dir: str) -> dict:
    ...  # paste the exact body from scripts/compile_facets.py:21-57

def index_is_current(facets_dir: str) -> bool:
    committed_path = os.path.join(facets_dir, "facet_index.json")
    try:
        with open(committed_path, encoding="utf-8") as f:
            committed = json.load(f)
    except (OSError, ValueError):
        return False
    try:
        fresh = build_index(facets_dir)
    except FacetContractError:
        return False
    return json.dumps(committed, sort_keys=True) == json.dumps(fresh, sort_keys=True)
```
2. Rewrite `scripts/compile_facets.py` `build_index` to `from core.facet_index import build_index` (delete the local copy, keep `main()` calling it).
3. In `--lint-facets` (`scripts/focus-gate.py` ~3163, after loading `facets_dir`) add:
```python
        from core.facet_index import index_is_current
        if not index_is_current(facets_dir):
            errors.append(f"{facets_dir}/facet_index.json is stale — re-run: python3 scripts/compile_facets.py")
```

**GREEN command:** `python3 scripts/compile_facets.py` (must still print `19 facets, 187 triggers`) then the test class → `OK`.
**Commit:** `feat(v2.8-c4): facet_index builder in core + freshness lint guard (F2)`

---

### TASK 4.3 — facet-meta `mode` is the single authority (fixes F6)
**Est: 20 min.** File: `core/context_policy.py` (+ remove now-tautological lint check).

**RED:**
```python
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
```
→ **FAIL** (mode_for_facet currently uses keyword heuristic).

**GREEN (minimal):** replace `mode_for_facet` in `core/context_policy.py` to read the Compiled Index; delete both keyword tables; keep the keyword fallback ONLY for when the index is missing (unregistered/legacy facet), so existing behaviour for unknown names is preserved:
```python
def mode_for_facet(facet: str) -> FacetContextMode:
    from core.facet_router import default_index
    idx = default_index()
    if idx:
        meta = idx.get("facets", {}).get((facet or "").strip().lower())
        if meta and meta.get("mode"):
            return FacetContextMode(meta["mode"])
    return FacetContextMode.WINDOW  # safe default for legacy/unregistered facets
```
`subscriptions_for`, `brief_budget`, `richness_floor` stay exactly as-is (they only branch on the mode).
Then delete the dead reconcile check inside `--lint-facets` (`scripts/focus-gate.py:3182-3184`, the `mode mismatch: contract ... != context_policy` block) — it is now tautologically true.
```

**GREEN command:** `python3 -m unittest discover -s tests` → `OK` (parts 1-4 must stay green; they only assert per-facet results, which still hold).
**Commit:** `refactor(v2.8-c4): derive facet mode from compiled index, drop keyword tables (F6)`

---

### TASK 4.4 — Canonical token estimator everywhere (fixes F3)
**Est: 10 min.** File: `scripts/focus-gate.py`.

**RED:**
```python
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
```
**GREEN:** replace every `len(...) // 4` in `scripts/focus-gate.py` (741, 762 already removed in 4.1; also 968, 971, 1049) with `estimate_tokens(...)` imported function-local `from core.tokens import estimate_tokens`. For `SmartZoneCompactor.estimate_tokens`, if it takes a path, read content then delegate; keep the same return type (int).
**GREEN command:** tests → `OK`; `python3 scripts/focus-gate.py --estimate-tokens SKILL.md` still prints a number.
**Commit:** `refactor(v2.8-c4): route all token math through core.tokens.estimate_tokens (F3)`

---

### TASK 4.5 — `--verify-wave` aggregator + CLI/doc/version cleanup (fixes F4 + F5)
**Est: 30 min.** Files: `scripts/focus-gate.py` (new handler + argparse + version/help fixes), `SKILL.md`.

**RED:**
```python
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

class TestSkillDocCoversV28(unittest.TestCase):
    def test_skill_md_documents_new_gates(self):
        with open(os.path.join(V271_ROOT, "SKILL.md"), encoding="utf-8") as f:
            md = f.read()
        for c in ("--verify-wave", "--lint-facets", "--audit-context-sufficiency", "--synthesize-pipeline"):
            self.assertIn(c, md, c)
```
**GREEN (minimal):**
1. **Version/help:** change `1.3.5` → `2.7.1` at `scripts/focus-gate.py:1975` and `:2074`. Fill the 3 empty spike `help=''` (`:2047-2049`) with one-line strings.
2. **Add argparse flag** in the Master Orchestrator group: `grp_Master_Orchestrator.add_argument('--verify-wave', action='store_true', help='Runs every verifier (index, contracts, tokens, help, stage, sufficiency) and prints ONE aggregate verdict (v2.8 Checkpoint 4).')`.
3. **Add handler** near the other orchestrator handlers. READ-ONLY — it must not write ledger/events. Gate sources (reuse existing code; mark `SKIP` when a live ledger/brief is absent):
   - `facet_index_fresh` = `core.facet_index.index_is_current(JITHydrationEngine.get_facets_dir())`
   - `facet_contracts` = run the same checks `--lint-facets` performs and count errors==0 (extract that body into `def _lint_facet_contracts(facets_dir)->list:` and call it here)
   - `token_consistency` = `True` iff `--list-facets --json` modes valid AND no `// 4` remains (cheap: import check) → simplest: `True` when both above true
   - `cli_help_clean` = `"1.3.5" not in <help output>` (reuse `build_parser().format_help()`)
   - `stage_matrix` = if a `.focusgate/GATES.md` ledger exists, call the same code `--verify-stage` uses; else `SKIP`
   - `context_sufficiency` = if an `AGENT-BRIEF*.md` exists in cwd, audit it with `RichnessSufficiencyOracle`; else `SKIP`
   Print `{"clean": <all non-SKIP == PASS>, "gates": {...}}` for `--json`; else a 6-line table. `sys.exit(0 if clean else 1)`.
4. **SKILL.md:** add a `## 4b. Wave Verification & v2.8 Gates` block documenting `--verify-wave`, `--lint-facets`, `--audit-context-sufficiency`, `--synthesize-pipeline` with one example each.
**GREEN command:** `python3 scripts/focus-gate.py --verify-wave` prints a clean table, exit 0; tests → `OK`.
**Commit:** `feat(v2.8-c4): --verify-wave aggregate gate + CLI/doc/version hygiene (F4,F5)`

---

## 5. Micro-ADRs (log these in SPEC.md §"v2.8 Checkpoint 4 Decisions")

- **ADR-4.2 — Move `build_index` from `scripts/compile_facets.py` into `core/facet_index.py`.** Context: `--lint-facets`/`--verify-wave` need the compiler but `core/` must not import `scripts/`. Decision: relocate builder to core; scripts becomes a thin wrapper. Consequence: `scripts/compile_facets.py` loses its body; byte-identical output preserved (recompile prints `19 facets, 187 triggers`).
- **ADR-4.3 — facet-meta `mode:` is the single authority for EPHEMERAL/WINDOW.** `context_policy.mode_for_facet` derives from the Compiled Index; keyword tables and the lint reconcile-check are deleted. Consequence: adding a facet needs exactly ONE edit (its `facet-meta`) + `compile_facets.py`.
- **ADR-4.5 — `--verify-wave` is additive/read-only.** It aggregates existing verifiers, never mutates ledger, never auto-settles gates. Keeps the verification-vs-settlement boundary intact.

---

## 6. Sequenced Roadmap (copy into a todo list, one `in_progress` at a time)

| # | Task | File(s) | Gate to clear | Est |
|---|------|---------|---------------|-----|
| 4.1 | Hydrate from index, delete Registry | `scripts/focus-gate.py` | `grep -c FACET_REGISTRY → 0` + tests green | 20m |
| 4.2 | Core index builder + freshness lint | `core/facet_index.py`, `scripts/compile_facets.py`, `--lint-facets` | `--lint-facets` clean; `test_index_is_current` green | 25m |
| 4.3 | Single mode authority | `core/context_policy.py` | `test_mode_for_facet_matches_contract` green; parts 1-4 still green | 20m |
| 4.4 | Canonical tokens | `scripts/focus-gate.py` | `src.count("// 4") == 0` green | 10m |
| 4.5 | `--verify-wave` + hygiene | `scripts/focus-gate.py`, `SKILL.md` | `--verify-wave` exit 0; doc/version tests green | 30m |
| — | Full regression + DoD | — | Section 3 checklist all pass | 10m |

Total ≈ **1h35m**. Do not start 4.n+1 until 4.n's `GREEN command` prints `OK` and the whole suite is green.

---

## 7. What NOT to do (guardrails for a low-reasoning executor)

- Do NOT edit any `facets/**.md` contract text or `facets/facet_index.json` by hand (4.2 regenerates it via the script).
- Do NOT change token ceilings (150/400/120) or the richness/pointer behaviour from parts 1-4.
- Do NOT add pip packages, network calls, or new oracle files beyond `core/facet_index.py`.
- Do NOT delete `.focusgate/` files or touch `--run`/`--check` settlement logic.
- Do NOT rename existing commands, tests, or public function names.
- If a step's expected number differs (e.g. compile prints `18 facets`), STOP: print the number and `BLOCKED`.

---

## 8. Final report format the executor must print

```
CHECKPOINT 4 COMPLETE
tests: <X> passed, all green
FACET_REGISTRY removed: yes
context_policy keyword tables removed: yes
--verify-wave: clean=<True/False>, gates=<6>
SKILL.md v2.8 commands documented: yes
commit shas: <4.1> <4.2> <4.3> <4.4> <4.5>
```
