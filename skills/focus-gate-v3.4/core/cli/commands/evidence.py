"""`--check`, `--baseline`, `--evidence`: the Evidence Gate loop."""
import json
import os
import sys

from core.cli.registry import CommandContext, command

_DEFAULT_LEDGER = ".focusgate/GATES.md"


def _missing(path: str) -> bool:
    if not os.path.exists(path):
        print(f"Error: Ledger file not found at {path}", file=sys.stderr)
        return True
    return False


@command("check", ("--check",), "check",
         "Run one gate CHECK; tick [x] only on exit 0 + EXPECT (--strict needs a prior red).")
def check(ctx: CommandContext) -> int:
    if len(ctx.argv) < 2:
        print("Usage: focus-gate.py --check <gate_id> [ledger_path] [--strict] [--force] [--waive-red <reason>]",
              file=sys.stderr)
        return 1
    gate = ctx.argv[1]
    ledger = ctx.argv[2] if len(ctx.argv) > 2 else _DEFAULT_LEDGER
    if _missing(ledger):
        return 1
    from core.gates.evidence import settle_gate
    outcome = settle_gate(ledger, gate, strict=ctx.strict, force=ctx.force, waive_reason=ctx.waive)
    for line in outcome.lines:
        print(line, file=sys.stdout if outcome.ok else sys.stderr)
    if outcome.ok:
        ctx.event_store.append("GATE_CHECKED", {"id": gate, "ledger": ledger, "verified": True})
    return 0 if outcome.ok else 1


@command("baseline", ("--baseline",), "baseline",
         "Run every open gate once BEFORE the work and record which are red.")
def baseline(ctx: CommandContext) -> int:
    ledger = ctx.argv[1] if len(ctx.argv) > 1 else _DEFAULT_LEDGER
    if _missing(ledger):
        return 1
    from core.gates.evidence import baseline as run_baseline
    rows = run_baseline(ledger)
    if ctx.is_json:
        print(json.dumps({"baseline": rows}, indent=2))
        return 0
    notes = {"RED": "good: fails now, can prove your change",
             "ALREADY_GREEN": "passes before any work; cannot prove your change"}
    for r in rows:
        print(f"{r['id']:<20} {r['status']:<14} exit={r['exit_code']}  {notes.get(r['status'], r['message'])}")
        for fl in r["findings"]:
            print(f"    {fl}")
    if not rows:
        print("No open gates with a CHECK to baseline.")
    return 0


@command("evidence", ("--evidence",), "evidence",
         "Show the hash-chained evidence log and verify it was not altered.")
def evidence(ctx: CommandContext) -> int:
    ledger = ctx.argv[1] if len(ctx.argv) > 1 else _DEFAULT_LEDGER
    if _missing(ledger):
        return 1
    from core.gates.evidence import evidence_report
    ok, lines = evidence_report(ledger)
    print("\n".join(lines))
    return 0 if ok else 1
