"""FocusGate v3.2 -- Evidence Gate.

Makes the framework's founding promise true: a gate settles only on real,
observed evidence. Three cohesive parts:

* GateIntegrity -- structural analysis of a CHECK/EXPECT pair. Answers "could this
  gate ever fail for the right reason?" by reading the shell structure, not by
  matching a denylist of strings.
* EvidenceLog   -- append-only, hash-chained record of every observation. Binds
  each observation to a fingerprint of the exact CHECK+EXPECT, so a check that is
  weakened after it was seen failing loses its red evidence.
* settle_gate / baseline / run_gates -- the verified operations the CLI exposes.

Zero external dependencies (100% Python standard library).
"""

import hashlib
import json
import os
import re
import shlex
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Finding:
    severity: str  # "error" | "warn"
    code: str
    message: str

    def render(self) -> str:
        return f"[{self.severity.upper()}] {self.code}: {self.message}"


# --------------------------------------------------------------------------- #
# Integrity analysis
# --------------------------------------------------------------------------- #

_OPERATORS = {";", "&&", "||", "|", "&", "|&"}
_ALWAYS_OK = {"true", ":", "echo", "printf"}          # exit 0 regardless of the project
_SELF_WORDS = _ALWAYS_OK | {"exit", "return", "sleep", "yes"}
_WRAPPERS = {"sudo", "env", "time", "nohup", "command", "exec", "nice"}
_RUNNERS = {"pytest", "py.test", "python", "python3", "npm", "npx", "yarn", "pnpm",
            "cargo", "go", "make", "mvn", "gradle", "gradlew", "dotnet", "rspec",
            "jest", "vitest", "tox", "nox", "ruby", "phpunit", "mocha", "deno",
            "bun", "mix", "ctest", "swift", "flutter"}
_FORMATTERS = {"tail", "head", "tee", "cat", "cut", "sort", "uniq", "less", "more", "sed"}
_PROBES = {"pwd", "date", "whoami", "uname", "hostname", "id", "uptime", "env", "printenv"}
_GIT_PROBES = {"status", "log", "branch", "remote", "rev-parse", "config", "version"}
_SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
_PLACEHOLDER = re.compile(r"\bTODO\b|\bFIXME\b|REPLACE_ME|<replace|\{\{|\}\}|<command", re.I)
_EXPECT_PROBES = ("", "zzz9 probe\nline two", "FAIL: boom (exit 1)")


def _tokenize(cmd: str) -> List[str]:
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    return list(lex)


def _segments(tokens: List[str]) -> Tuple[List[Dict[str, Any]], bool]:
    """Split top-level tokens into command segments. Parenthesised groups are opaque.

    Returns (segments, trailing_background). Each segment: {"op": preceding
    operator or None, "words": [...], "group": bool}.
    """
    segs: List[Dict[str, Any]] = []
    cur: List[str] = []
    op: Optional[str] = None
    depth = 0
    group = False
    trailing_bg = False
    for tok in tokens:
        if tok == "(":
            depth += 1
            group = True
            cur.append(tok)
            continue
        if tok == ")":
            depth = max(0, depth - 1)
            cur.append(tok)
            continue
        if depth == 0 and tok in _OPERATORS:
            if cur:
                segs.append({"op": op, "words": cur, "group": group})
            cur, group, op = [], False, tok
            trailing_bg = tok == "&"
            continue
        trailing_bg = False
        cur.append(tok)
    if cur:
        segs.append({"op": op, "words": cur, "group": group})
    return segs, trailing_bg


def _cmd_word(words: List[str]) -> str:
    for w in words:
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w) or w in _WRAPPERS:
            continue
        return os.path.basename(w).lower()
    return ""


def _is_zero_exit(words: List[str]) -> bool:
    return len(words) >= 2 and words[1] == "0"


def _always_succeeds(seg: Dict[str, Any]) -> bool:
    if seg["group"]:
        return False
    w = _cmd_word(seg["words"])
    if w in _ALWAYS_OK:
        return True
    return w == "exit" and _is_zero_exit(seg["words"])


def _analyze_command(cmd: str, pipefail: bool = False, depth: int = 0) -> List[Finding]:
    out: List[Finding] = []
    try:
        tokens = _tokenize(cmd)
    except ValueError:
        return [Finding("warn", "UNPARSEABLE_CHECK",
                        "cannot parse this CHECK (unbalanced quotes?); integrity not verified")]
    segs, trailing_bg = _segments(tokens)
    if not segs:
        return out

    # Self-satisfying: every command is one that exits 0 whatever the project does.
    if all((not s["group"]) and _cmd_word(s["words"]) in _SELF_WORDS and
           not (_cmd_word(s["words"]) == "exit" and not _is_zero_exit(s["words"]))
           for s in segs):
        out.append(Finding("error", "SELF_SATISFYING",
                           "every command here succeeds regardless of the project "
                           "(echo/true/exit 0); it cannot fail, so it proves nothing"))

    # Exit-status masking.
    last = len(segs) - 1
    for i, s in enumerate(segs):
        w = _cmd_word(s["words"])
        if w == "set" and ("+e" in s["words"] or ("+o" in s["words"] and "errexit" in s["words"])):
            out.append(Finding("error", "MASKED_EXIT", "'set +e' disables failure detection"))
        if s["op"] == "||" and not s["group"] and (
                w in _ALWAYS_OK or (w == "exit" and _is_zero_exit(s["words"]))):
            out.append(Finding("error", "MASKED_EXIT",
                               "'|| %s' turns a failing command into exit 0" % w))
        if s["op"] == ";" and i == last and _always_succeeds(s):
            out.append(Finding("error", "MASKED_EXIT",
                               "the last command (%s) decides the exit status and always succeeds" % w))
    if trailing_bg:
        out.append(Finding("error", "MASKED_EXIT",
                           "a backgrounded command returns exit 0 immediately"))

    # Pipelines: the exit status is the last command's unless pipefail is set.
    pf = pipefail or any(_cmd_word(s["words"]) == "set" and any("pipefail" in x for x in s["words"])
                         for s in segs)
    if not pf:
        for i, s in enumerate(segs[:-1]):
            nxt = segs[i + 1]
            if (nxt["op"] in ("|", "|&") and _cmd_word(s["words"]) in _RUNNERS
                    and _cmd_word(nxt["words"]) in _FORMATTERS):
                out.append(Finding("warn", "PIPE_MASKS_EXIT",
                                   "piping '%s' into '%s' discards the runner's exit status; "
                                   "use bash -o pipefail -c '...'" % (_cmd_word(s["words"]),
                                                                    _cmd_word(nxt["words"]))))
                break

    # Project-independent probes.
    def tautological(s: Dict[str, Any]) -> bool:
        if s["group"]:
            return False
        w, words = _cmd_word(s["words"]), s["words"]
        if w in _PROBES:
            return True
        if w == "git":
            sub = next((x for x in words[1:] if not x.startswith("-")), "")
            return sub in _GIT_PROBES
        if w == "ls":
            return not [x for x in words[1:] if not x.startswith("-")]
        return False
    if all(tautological(s) for s in segs):
        out.append(Finding("warn", "TAUTOLOGY_CHECK",
                           "this probe passes in any repository, whatever you changed"))

    # Literal-output python one-liners.
    for s in segs:
        w = _cmd_word(s["words"])
        if w.startswith("python") and "-c" in s["words"]:
            code = s["words"][s["words"].index("-c") + 1] if s["words"].index("-c") + 1 < len(s["words"]) else ""
            if "print" in code and not re.search(r"import|open\(|assert|subprocess|exit\(|raise|os\.", code):
                out.append(Finding("warn", "LITERAL_OUTPUT",
                                   "python -c only prints a literal; the output is not evidence"))

    # Recurse into `bash -c '...'`.
    if depth < 3:
        for s in segs:
            if _cmd_word(s["words"]) in _SHELLS:
                words = s["words"]
                flag_idx = next((j for j, x in enumerate(words)
                                 if re.match(r"^-[a-zA-Z]*c[a-zA-Z]*$", x)), None)
                if flag_idx is not None and flag_idx + 1 < len(words):
                    inner_pf = "pipefail" in " ".join(words[:flag_idx])
                    out.extend(_analyze_command(words[flag_idx + 1], pipefail=inner_pf, depth=depth + 1))
    return out


_ROOT_RM = re.compile(r"\brm\s+-\S*\s+(?:/(?:\s|$|\*)|~|\$HOME|\.\./)", re.IGNORECASE)


def _destructive_finding(check_cmd: str) -> Optional["Finding"]:
    """A CHECK is code that `--run` and `--baseline` execute unattended, so a ledger from someone
    else is a command channel. Refuse the catastrophic patterns of core/sandbox/command_guard.py.
    `rm -rf /tmp/build` (a scoped delete) stays allowed; only root/home targets are refused."""
    from core.sandbox.command_guard import CommandGuard
    blocked, reason = CommandGuard().is_destructive(check_cmd)
    if not blocked:
        return None
    if reason.startswith("Root deletion") and not _ROOT_RM.search(check_cmd):
        return None
    return Finding("error", "DESTRUCTIVE_COMMAND", "%s; a gate CHECK may not run this" % reason)


class GateIntegrity:
    """Structural honesty analysis of one CHECK/EXPECT pair."""

    @staticmethod
    def analyze(check_cmd: Optional[str], expect: Optional[str]) -> List[Finding]:
        findings: List[Finding] = []
        if check_cmd:
            if _PLACEHOLDER.search(check_cmd) or (expect and _PLACEHOLDER.search(expect)):
                findings.append(Finding("error", "UNFILLED_TEMPLATE",
                                        "CHECK/EXPECT still contains a template placeholder"))
            findings.extend(_analyze_command(check_cmd))
            destructive = _destructive_finding(check_cmd)
            if destructive is not None:
                findings.append(destructive)
        if expect:
            try:
                rx = re.compile(expect)
            except re.error as e:
                findings.append(Finding("error", "INVALID_EXPECT", "EXPECT is not a valid regex: %s" % e))
            else:
                if all(rx.search(p) is not None for p in _EXPECT_PROBES):
                    findings.append(Finding("error", "VACUOUS_EXPECT",
                                            "EXPECT matches any output, so it constrains nothing"))
        seen, unique = set(), []
        for f in findings:
            if (f.code, f.message) not in seen:
                seen.add((f.code, f.message))
                unique.append(f)
        return sorted(unique, key=lambda f: f.severity != "error")


def errors_of(findings: List[Finding]) -> List[Finding]:
    return [f for f in findings if f.severity == "error"]


# --------------------------------------------------------------------------- #
# Evidence log
# --------------------------------------------------------------------------- #

def fingerprint(check_cmd: Optional[str], expect: Optional[str]) -> str:
    raw = (check_cmd or "").strip() + "\0" + (expect or "").strip()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _canon(rec: Dict[str, Any]) -> str:
    return json.dumps(rec, sort_keys=True, separators=(",", ":"))


class EvidenceLog:
    """Append-only JSONL, each record chained to the previous by SHA-256."""

    def __init__(self, path: str):
        self.path = path

    @staticmethod
    def path_for(ledger_path: str) -> str:
        return os.path.splitext(ledger_path)[0] + ".evidence.jsonl"

    def _lines(self) -> List[str]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            return [ln for ln in f.read().splitlines() if ln.strip()]

    def records(self, gate_id: Optional[str] = None) -> List[Dict[str, Any]]:
        out = []
        for ln in self._lines():
            try:
                rec = json.loads(ln)
            except ValueError:
                continue
            if gate_id is None or rec.get("gate") == gate_id:
                out.append(rec)
        return out

    def _last_hash(self) -> str:
        lines = self._lines()
        if not lines:
            return "0" * 64
        try:
            return json.loads(lines[-1]).get("hash", "")
        except ValueError:
            return ""

    def record(self, gate_id: str, fp: str, phase: str, result: str,
               exit_code: Optional[int] = None, dedupe: bool = False, **extra: Any) -> None:
        if dedupe:
            prior = [r for r in self.records(gate_id) if r.get("fp") == fp]
            if prior and prior[-1].get("result") == result:
                return
        rec: Dict[str, Any] = {"v": 1, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                               "gate": gate_id, "fp": fp, "phase": phase, "result": result,
                               "exit_code": exit_code, "prev": self._last_hash()}
        rec.update(extra)
        rec["hash"] = hashlib.sha256(_canon(rec).encode("utf-8")).hexdigest()
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")

    def has_red(self, gate_id: str, fp: str) -> bool:
        return any(r.get("fp") == fp and r.get("result") == "red" for r in self.records(gate_id))

    def verify(self) -> Tuple[bool, int]:
        prev = "0" * 64
        for n, ln in enumerate(self._lines(), 1):
            try:
                rec = json.loads(ln)
            except ValueError:
                return False, n
            stored = rec.pop("hash", None)
            if rec.get("prev") != prev or hashlib.sha256(_canon(rec).encode("utf-8")).hexdigest() != stored:
                return False, n
            prev = stored
        return True, 0


# --------------------------------------------------------------------------- #
# Verified operations
# --------------------------------------------------------------------------- #

@dataclass
class Observation:
    gate_id: str
    fp: str
    passed: bool
    result: str            # "red" | "green" | "error"
    exit_code: Optional[int]
    message: str
    output: str


def project_root_for(ledger_path: str) -> str:
    d = os.path.dirname(os.path.abspath(ledger_path))
    return os.path.dirname(d) if os.path.basename(d) == ".focusgate" else d


def observe(gate: Any, base_dir: str) -> Observation:
    """Run the gate's CHECK once and classify the result."""
    from adapters.oracle_adapter import ShellOracleAdapter
    fp = fingerprint(gate.check_cmd, gate.expect_pattern)
    refusal = _destructive_finding(gate.check_cmd or "")
    if refusal is not None:   # never execute it, `--force` or not: see AUDIT O2
        return Observation(gate.id, fp, False, "error", None,
                           f"REFUSED_DESTRUCTIVE: {refusal.message}", "")
    try:
        passed, msg, meta = ShellOracleAdapter().execute_tracer(gate, base_dir=base_dir)
    except re.error as e:
        return Observation(gate.id, fp, False, "error", None, f"INVALID_EXPECT: {e}", "")
    code = meta.get("exit_code")
    raw = meta.get("raw_output") or meta.get("output", "")
    if passed:
        result = "green"
        try:
            from core.unlazy_guard import ExecutionRigorGuard
            ok, reasons = ExecutionRigorGuard.validate_completion(gate, test_output=raw)
            if not ok:
                passed, result, msg = False, "red", "FAILED_RIGOR: " + "; ".join(reasons)
        except ImportError:
            pass
    elif code in (126, 127) or msg.startswith(("TIMEOUT", "ERROR")):
        result = "error"
        msg = f"{msg} -- not valid red evidence (tool missing or timed out, not a real failure)"
    else:
        result = "red"
    return Observation(gate.id, fp, passed, result, code, msg, raw)


def _git_head(base_dir: str) -> Optional[str]:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=base_dir,
                           capture_output=True, text=True, timeout=3)
        return r.stdout.strip() or None if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _find_gate(ledger: Any, gate_id: str) -> Optional[Any]:
    return next((g for g in ledger.spikes + ledger.gates if g.id == gate_id), None)


@dataclass
class SettleOutcome:
    ok: bool
    lines: List[str]


def settle_gate(ledger_path: str, gate_id: str, *, strict: bool = False, force: bool = False,
                waive_reason: Optional[str] = None) -> SettleOutcome:
    """Close a gate only if its CHECK passes now. The only function that writes [x]."""
    from core.gates.ledger import Ledger
    lines: List[str] = []
    ledger = Ledger.from_file(ledger_path)
    gate = _find_gate(ledger, gate_id)
    if gate is None or gate.checked:
        return SettleOutcome(False, [f"Gate '{gate_id}' not found as unchecked gate in {ledger_path}"])
    base = project_root_for(ledger_path)
    log = EvidenceLog(EvidenceLog.path_for(ledger_path))

    if not gate.check_cmd:
        log.record(gate_id, fingerprint(None, None), "settle", "manual", head=_git_head(base))
        lines.append(f"Gate '{gate_id}' has no CHECK: settled on your attestation (unverified).")
        _flip(ledger_path, gate_id)
        return SettleOutcome(True, lines)

    findings = GateIntegrity.analyze(gate.check_cmd, gate.expect_pattern)
    errs = errors_of(findings)
    lines.extend(f.render() for f in findings)
    if errs and not force:
        lines.append(f"Refused: gate '{gate_id}' cannot serve as evidence. Fix the CHECK/EXPECT "
                     "(or --force to override; the override is logged).")
        return SettleOutcome(False, lines)

    obs = observe(gate, base)
    red_known = log.has_red(gate_id, obs.fp)          # read BEFORE recording this attempt
    extra: Dict[str, Any] = {"head": _git_head(base)}
    if force and errs:
        extra["forced"] = True
    if waive_reason and not red_known:
        extra["waived_red"] = waive_reason
    log.record(gate_id, obs.fp, "settle", obs.result, exit_code=obs.exit_code, **extra)

    if not obs.passed:
        lines.append(f"Refused: {obs.message}")
        return SettleOutcome(False, lines)
    if not red_known:
        if waive_reason:
            lines.append(f"Red-before-green waived: {waive_reason}")
        elif strict:
            lines.append(f"Refused (--strict): gate '{gate_id}' was never observed failing with this exact "
                         "CHECK/EXPECT, so passing proves nothing about your change. Run --baseline "
                         "before implementing, or pass --waive-red \"<reason>\".")
            return SettleOutcome(False, lines)
        else:
            lines.append(f"Warning: gate '{gate_id}' was never observed failing; passing now does not "
                         "show your change made the difference. Use --baseline first (and --strict).")
    _flip(ledger_path, gate_id)
    lines.append(f"Checked gate '{gate_id}' (verified: CHECK executed and passed).")
    return SettleOutcome(True, lines)


def _flip(ledger_path: str, gate_id: str) -> None:
    with open(ledger_path, "r", encoding="utf-8") as f:
        content = f.read()
    pat = rf"-\s*\[\s*\]\s*({re.escape(gate_id)}):"
    with open(ledger_path, "w", encoding="utf-8") as f:
        f.write(re.sub(pat, r"- [x] \1:", content, count=1))


def settle_spike(ledger_path: str, target: str, adr_text: str) -> Optional[str]:
    """Settle a prototype spike: tick it, log it, append its micro-ADR.

    Returns the spike id, or None when no open spike matches `target`. Spikes carry
    no CHECK, so the log records them as `phase=settle result=spike` with the ADR.
    """
    with open(ledger_path, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.search(rf"-\s*\[\s*\]\s*({re.escape(target)}|spike-[a-z]+-{re.escape(target)}):", content)
    if not m:
        return None
    spike_id = m.group(1)
    EvidenceLog(EvidenceLog.path_for(ledger_path)).record(
        spike_id, fingerprint(None, None), "settle", "spike", adr=adr_text)
    _flip(ledger_path, spike_id)
    with open(ledger_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "## 3. Micro-ADR Ledger" in content:
        content = content.replace("- **None yet.**\n", "").replace("- **None yet.**", "")
        entry = f"\n- **[ADR-{int(time.time()) % 10000:04d}]**: {adr_text}\n"
        content = content.replace("## 3. Micro-ADR Ledger", f"## 3. Micro-ADR Ledger\n{entry}", 1)
        with open(ledger_path, "w", encoding="utf-8") as f:
            f.write(content)
    return spike_id


def baseline(ledger_path: str) -> List[Dict[str, Any]]:
    """Run every open gate once, before any work, and record whether it is red."""
    from core.gates.ledger import Ledger
    ledger = Ledger.from_file(ledger_path)
    base = project_root_for(ledger_path)
    log = EvidenceLog(EvidenceLog.path_for(ledger_path))
    rows = []
    for g in ledger.spikes + ledger.gates:
        if g.checked or not g.check_cmd:
            continue
        findings = GateIntegrity.analyze(g.check_cmd, g.expect_pattern)
        obs = observe(g, base)
        log.record(g.id, obs.fp, "baseline", obs.result, exit_code=obs.exit_code, head=_git_head(base))
        status = {"red": "RED", "green": "ALREADY_GREEN", "error": "ERROR"}[obs.result]
        rows.append({"id": g.id, "status": status, "exit_code": obs.exit_code,
                     "message": obs.message, "findings": [f.render() for f in findings]})
    return rows


def run_gates(ledger_path: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """Execute every gate that has a CHECK. Reports; never settles."""
    from core.gates.ledger import Ledger
    ledger = Ledger.from_file(ledger_path)
    base = project_root_for(ledger_path)
    log = EvidenceLog(EvidenceLog.path_for(ledger_path))
    results, all_ok = [], True
    for g in ledger.spikes + ledger.gates:
        if not g.check_cmd:
            results.append({"id": g.id, "status": "SKIPPED", "reason": "manual", "findings": []})
            continue
        findings = GateIntegrity.analyze(g.check_cmd, g.expect_pattern)
        errs = errors_of(findings)
        obs = observe(g, base)
        log.record(g.id, obs.fp, "run", obs.result, exit_code=obs.exit_code, dedupe=True)
        ok = obs.passed and not errs
        all_ok = all_ok and ok
        results.append({"id": g.id, "status": "PASSED" if ok else "FAILED",
                        "exit_code": obs.exit_code, "settled": g.checked,
                        "red_observed": log.has_red(g.id, obs.fp),
                        "reason": obs.message if not obs.passed else
                                  ("integrity: " + ", ".join(f.code for f in errs) if errs else "ok"),
                        "findings": [f.render() for f in findings]})
    return all_ok, results


def evidence_report(ledger_path: str) -> Tuple[bool, List[str]]:
    log = EvidenceLog(EvidenceLog.path_for(ledger_path))
    ok, bad = log.verify()
    recs = log.records()
    out = [("chain: OK (%d records)" % len(recs)) if ok else f"chain: BROKEN at line {bad} -- evidence was altered or corrupted"]
    by_gate: Dict[str, List[Dict[str, Any]]] = {}
    for r in recs:
        by_gate.setdefault(r["gate"], []).append(r)
    for gid, rs in by_gate.items():
        counts = {k: sum(1 for r in rs if r["result"] == k) for k in ("red", "green", "error", "manual")}
        line = f"{gid}: red={counts['red']} green={counts['green']} error={counts['error']}"
        for r in rs:
            if r.get("forced"):
                line += " FORCED"
            if r.get("waived_red"):
                line += f" WAIVED_RED({r['waived_red']})"
        out.append(line)
    return ok, out


def falsifiable_seed(check: str, expect: str, action: str) -> Tuple[str, str, str]:
    """Replace a project-independent seed check with one that is red until the work exists."""
    findings = GateIntegrity.analyze(check, expect or None)
    if not any(f.severity == "error" or f.code == "TAUTOLOGY_CHECK" for f in findings):
        return check, expect, action
    m = re.search(r"\.focusgate/[A-Za-z0-9_.\-]+", action)
    path = m.group(0) if m else ".focusgate/SEED.md"
    if not m:
        action = f"{action} (record the result in {path})"
    return f"test -s {path} && echo SEED_PRESENT", "SEED_PRESENT", action
