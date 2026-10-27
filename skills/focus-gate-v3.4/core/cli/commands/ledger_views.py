"""Ledger-bound views: `--header`, `--next`, `--frontier`, `--status`, `--lint`, `--run`."""
import json
import os
import sys

from core.cli.registry import CommandContext, command

_DEFAULT_LEDGER = ".focusgate/GATES.md"


def _load(ctx: CommandContext):
    """(ledger, path) or (None, path) after printing the standard error."""
    from core.gates import Ledger
    path = ctx.argv[1] if len(ctx.argv) > 1 else _DEFAULT_LEDGER
    if not os.path.exists(path):
        print(f"Error: Ledger file not found at {path}", file=sys.stderr)
        return None, path
    return Ledger.from_file(path), path


def _header(ctx: CommandContext) -> int:
    from core.gates.views import StateSynthesizer
    ledger, _ = _load(ctx)
    if ledger is None:
        return 1
    line1, line2, meta = StateSynthesizer.synthesize(ledger, cli_path=ctx.cli_path)
    if ctx.is_json:
        print(json.dumps({"line1": line1, "line2": line2, "meta": meta}, indent=2))
    else:
        print(line1)
        print(line2)
    return 0


@command("header", ("--header",), "header", "Print the Action-First line and the State line.")
def header(ctx: CommandContext) -> int:
    return _header(ctx)


@command("next", ("--next",), "next", "Print the next recommended action and the state header.")
def next_action(ctx: CommandContext) -> int:
    return _header(ctx)


@command("frontier", ("--frontier",), "frontier", "List unblocked DAG gates ready for parallel dispatch.")
def frontier(ctx: CommandContext) -> int:
    from core.worktree_runner import WorktreeRunner
    ledger, _ = _load(ctx)
    if ledger is None:
        return 1
    gates = WorktreeRunner(".").compute_frontier(ledger.gates)
    if ctx.is_json:
        print(json.dumps([g.to_dict() for g in gates], indent=2))
        return 0
    print(f"DAG Frontier Gates ({len(gates)} ready for parallel dispatch):")
    for g in gates:
        print(f"  - {g.id}: {g.title} (check: {g.check_cmd})")
    return 0


@command("status", ("--status",), "status", "Print gate and spike counts, ADRs and terms for the ledger.")
def status(ctx: CommandContext) -> int:
    ledger, path = _load(ctx)
    if ledger is None:
        return 1
    data = ledger.to_dict()
    if ctx.kernel is not None:
        # v3.3 (F7): the kernel vector has no `stats`; merge instead of replacing.
        data = {**data, **ctx.kernel.aggregate.get_state_vector()}
    if ctx.is_json:
        print(json.dumps(data, indent=2))
        return 0
    stats = data["stats"]
    print(f"FocusGate Status for {path}:")
    print(f"- Production Gates: {stats['gates_met']}/{stats['gates_total']} met ({stats['pct_complete']}%)")
    print(f"- Prototype Spikes: {stats['spikes_settled']}/{stats['spikes_total']} settled")
    print(f"- Terms anchored: {len(ledger.glossary)}")
    print(f"- Micro-ADRs recorded: {len(ledger.adrs)}\n")
    if ledger.spikes:
        print("Spikes (Throwaway):")
        for s in ledger.spikes:
            print(f"  [{'X' if s.checked else ' '}] {s.id}: {s.title} ({s.branch})")
        print()
    print("Production Gates:")
    for g in ledger.gates:
        print(f"  [{'X' if g.checked else ' '}] {g.id}: {g.title}")
    return 0


@command("lint", ("--lint",), "lint", "Lint working-memory bounds, anchors and gate honesty.")
def lint(ctx: CommandContext) -> int:
    from core.gates.views import FocusLinter
    ledger, path = _load(ctx)
    if ledger is None:
        return 1
    report = FocusLinter.lint(ledger)
    if ctx.is_json:
        print(json.dumps(report, indent=2))
        return 0 if report["valid"] else 1
    print(f"Linting FocusGate ledger: {path}\n")
    print(f"[{'PASS' if len(ledger.glossary) <= 5 else 'ERROR'}] Glossary terms: {len(ledger.glossary)}/5")
    print(f"[{'PASS' if (len(ledger.gates) + len(ledger.spikes)) > 0 else 'ERROR'}] Items: "
          f"{len(ledger.spikes)} spike(s), {len(ledger.gates)} production gate(s).")
    for w in report["warnings"]:
        print(f"[WARN] {w}")
    for e in report["errors"]:
        print(f"[ERROR] {e}", file=sys.stderr)
    print(f"\nLint result: {report['error_count']} error(s), {report['warning_count']} warning(s).")
    return 0 if report["valid"] else 1


@command("run", ("--run",), "run", "Execute the CHECK of every runnable gate.")
def run(ctx: CommandContext) -> int:
    from core.gates.evidence import run_gates
    path = ctx.argv[1] if len(ctx.argv) > 1 else _DEFAULT_LEDGER
    if not os.path.exists(path):
        print(f"Error: Ledger file not found at {path}", file=sys.stderr)
        return 1
    all_passed, results = run_gates(path)
    if ctx.is_json:
        print(json.dumps({"all_passed": all_passed, "results": results}, indent=2))
        return 0 if all_passed else 1
    print(f"Executing runnable gates in {path}:\n")
    for r in results:
        if r["status"] == "SKIPPED":
            print(f"[-] Skip {r['id']}: manual gate")
            continue
        tag = "red-observed" if r.get("red_observed") else "never-red"
        print(f"{r['status']:<7} {r['id']}  [{tag}]" + ("" if r["status"] == "PASSED" else f"  {r['reason']}"))
        for fl in r["findings"]:
            print(f"    {fl}")
    return 0 if all_passed else 1
