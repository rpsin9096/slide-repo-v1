"""`--hydrate-facet`, `--list-facets`, `--lint-facets`."""
import json
import sys

from core.cli.registry import CommandContext, command
from core.facets.catalog import FacetCatalog, lint_all


def _catalog() -> FacetCatalog:
    return FacetCatalog.default()


@command("hydrate-facet", ("--hydrate-facet",), "hydrate_facet",
         "Print one facet; --depth directive|playbook|full (default full).")
def hydrate(ctx: CommandContext) -> int:
    pos = ctx.positionals()
    if not pos:
        print("Usage: focus-gate.py --hydrate-facet <facet_name> [--depth directive|playbook|full]", file=sys.stderr)
        return 1
    depth = getattr(ctx.args, "depth", None) or "full"
    try:
        info = _catalog().hydrate_info(pos[0], depth)
    except ValueError as exc:
        print(f"Error hydrating facet: {exc}", file=sys.stderr)
        return 1
    ctx.event_store.append("FACET_HYDRATED", {"facet": info["facet"], "context": info["context"],
                                              "tokens": info["tokens"], "depth": depth})
    if ctx.is_json:
        print(json.dumps(info, indent=2))
    else:
        print(f"Hydrated Facet: [{info['context']}] {info['facet']} (~{info['tokens']} tokens)")
        print("-" * 60)
        print(info["directive"].strip())
    return 0


@command("list-facets", ("--list-facets",), "list_facets",
         "List facets with context, mode, tokens and trigger counts.")
def list_facets(ctx: CommandContext) -> int:
    cat = _catalog()
    rows = cat.summary_rows()
    counts = {}
    for t in cat.index().get("triggers", []):
        counts[t["facet"]] = counts.get(t["facet"], 0) + 1
    if ctx.is_json:
        for r in rows:
            r["trigger_count"] = counts.get(r["facet"], 0)
        print(json.dumps(rows, indent=2))
        return 0
    print(f"FocusGate JIT Declarative Facets (available={len(rows)}):")
    print(f"{'Facet':<22} {'Context':<14} {'Tokens':<8} {'Triggers':<9} {'Mode'}")
    print("-" * 72)
    for r in rows:
        print(f"{r['facet']:<22} {r['context']:<14} {r['tokens']:<8} {counts.get(r['facet'], 0):<9} {r['mode']}")
    return 0


@command("lint-facets", ("--lint-facets",), "lint_facets",
         "Lint facet contracts and depth: playbooks, tells, gate templates, handoffs, budgets.")
def lint_facets(ctx: CommandContext) -> int:
    facets_dir = _catalog().dir
    errors, warnings, contracts, owner = lint_all(facets_dir, ctx.known_flags())
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if ctx.is_json:
        print(json.dumps({"clean": not errors, "errors": errors, "warnings": warnings}, indent=2))
    elif errors:
        print(f"Facet lint FAILED ({len(errors)} error(s)):")
        for e in errors:
            print(f"  - {e}")
    else:
        print(f"Facet lint clean: {len(contracts)} contracts, {len(owner)} unique trigger patterns.")
    return 1 if errors else 0
