"""Writing-facet commands: fragments, briefs, shape, beats, grounding, spec compile."""
import json
import os
import sys

from core.cli.documents import collect_documents
from core.cli.registry import CommandContext
from core.cli.registry import command
from core.gates import Ledger
from core.grounding import ConceptGroundingLinter
from core.grounding import SpecToLedgerCompiler
from core.writing_suite import WritingSuite


def _match_fragment(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'fragment', None) is not None


@command('fragment', flags=('--fragment',), dest=None, summary='fragment command', matches=_match_fragment, order=247)
def fragment(ctx: CommandContext) -> int:
    """fragment command"""
    args = ctx.args
    clean_args = ctx.argv
    event_store = ctx.event_store
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --fragment \"<note_text>\" [path]", file=sys.stderr)
        return (1)
    fragment_text = clean_args[1]
    target_path = clean_args[2] if len(clean_args) > 2 else os.path.join(ledger_root, "FRAGMENTS.md")
    res_file = WritingSuite.append_fragment(fragment_text, target_path)
    event_store.append("FRAGMENT_APPENDED", {"file": res_file, "snippet": fragment_text[:60]})
    if is_json:
        print(json.dumps({"status": "SUCCESS", "file": res_file, "appended_length": len(fragment_text)}, indent=2))
    else:
        print(f"Appended fragment to {res_file}")
        print(f"▶ NEXT ACTION: view {res_file} or run --shape to synthesize RFC")
    return (0)


def _match_brief(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'brief', None) is not None


@command('brief', flags=('--brief',), dest=None, summary='brief command', matches=_match_brief, order=248)
def brief(ctx: CommandContext) -> int:
    """brief command"""
    args = ctx.args
    clean_args = ctx.argv
    event_store = ctx.event_store
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --brief <gate_id> [ledger_path] [--out <output_path>]", file=sys.stderr)
        return (1)
    gate_target = clean_args[1]
    out_target = None
    target_ledger = os.path.join(ledger_root, "GATES.md")
    if '--out' in clean_args:
        out_idx = clean_args.index('--out')
        if out_idx + 1 < len(clean_args):
            out_target = clean_args[out_idx + 1]
        rem = clean_args[2:out_idx]
        if rem:
            target_ledger = rem[0]
    elif len(clean_args) > 2:
        target_ledger = clean_args[2]

    if not os.path.exists(target_ledger):
        print(f"Error: Ledger file not found at {target_ledger}", file=sys.stderr)
        return (1)
    ledger = Ledger.from_file(target_ledger)
    matching = [g for g in (ledger.spikes + ledger.gates) if g.id == gate_target]
    if not matching:
        print(f"Error: Gate '{gate_target}' not found in {target_ledger}", file=sys.stderr)
        return (1)
    brief_doc = WritingSuite.compile_agent_brief(matching[0], ledger, out_target)
    event_store.append("AGENT_BRIEF_COMPILED", {"gate_id": gate_target, "out": out_target})
    if is_json:
        print(json.dumps({"gate_id": gate_target, "brief": brief_doc, "out": out_target}, indent=2))
    elif out_target:
        print(f"Compiled agent brief for {gate_target} to {out_target}")
    else:
        print(brief_doc)
    return (0)


def _match_shape(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'shape', None) is not None


@command('shape', flags=('--shape',), dest=None, summary='shape command', matches=_match_shape, order=249)
def shape(ctx: CommandContext) -> int:
    """shape command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    frag_target = clean_args[1] if len(clean_args) > 1 and not clean_args[1].startswith("-") else os.path.join(ledger_root, "FRAGMENTS.md")
    if is_json:
        print(json.dumps({"status": "SHAPING_INITIALIZED", "fragments_file": frag_target}, indent=2))
    else:
        print(f"Initiating technical spec shaping from: {frag_target}")
        print("▶ NEXT ACTION: establish prerequisite concepts and draft 2-3 candidate openings")
    return (0)


def _match_beat(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'beat', None) is not None


@command('beat', flags=('--beat',), dest=None, summary='beat command', matches=_match_beat, order=250)
def beat(ctx: CommandContext) -> int:
    """beat command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    beat_target = clean_args[1] if len(clean_args) > 1 and not clean_args[1].startswith("-") else "BEATS.md"
    if is_json:
        print(json.dumps({"status": "BEAT_EVALUATED", "file": beat_target}, indent=2))
    else:
        print(f"Evaluating narrative beats for: {beat_target}")
        print("▶ NEXT ACTION: propose candidate next beat based on grounded prerequisites")
    return (0)


def _match_lint_grounding(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'lint_grounding', None) is not None


@command('lint-grounding', flags=('--lint-grounding',), dest=None, summary='lint-grounding command', matches=_match_lint_grounding, order=292)
def lint_grounding(ctx: CommandContext) -> int:
    """lint-grounding command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --lint-grounding <doc_file> [ledger_path]", file=sys.stderr)
        return (1)
    doc_file = clean_args[1]
    ledger_path = clean_args[2] if len(clean_args) > 2 else '.focusgate/GATES.md'
    if not os.path.exists(doc_file):
        print(f"Error: Document file not found: {doc_file}", file=sys.stderr)
        return (1)

    # A directory is a workspace, not a document. Before Loop 63 this went
    # straight to open() and raised IsADirectoryError — a traceback from a
    # documented flag. Walk it instead, and say so.
    doc_files = collect_documents(doc_file) if os.path.isdir(doc_file) else [doc_file]

    glossary_set = set()
    if os.path.exists(ledger_path):
        l = Ledger.from_file(ledger_path)
        glossary_set = {g["term"] for g in l.glossary}

    violations = []
    for df in doc_files:
        try:
            with open(df, "r", encoding="utf-8") as f:
                doc_content = f.read()
        except (IsADirectoryError, PermissionError) as exc:
            print(f"ERROR: cannot read {df}: {exc}", file=sys.stderr)
            return (2)
        violations.extend(ConceptGroundingLinter.lint_grounding(doc_content, glossary_set))
    if is_json:
        print(json.dumps({"valid": len(violations) == 0, "violations": violations}, indent=2))
    else:
        if not violations:
            print("GROUNDING_LINT_PASSED: All domain concepts are properly grounded.")
        else:
            print(f"GROUNDING_LINT_FAILED: Found {len(violations)} ungrounded concept violation(s):")
            for v in violations:
                print(f"  - Paragraph {v['paragraph_index']}: ungrounded {v['ungrounded_concepts']}")
    return (0 if len(violations) == 0 else 1)


def _match_compile_spec(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'compile_spec', None) is not None


@command('compile-spec', flags=('--compile-spec',), dest=None, summary='compile-spec command', matches=_match_compile_spec, order=293)
def compile_spec(ctx: CommandContext) -> int:
    """compile-spec command"""
    args = ctx.args
    clean_args = ctx.argv
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --compile-spec <spec_markdown_file> [--out <ledger_path>]", file=sys.stderr)
        return (1)
    spec_file = clean_args[1]
    out_file = None
    if '--out' in clean_args:
        out_idx = clean_args.index('--out')
        if out_idx + 1 < len(clean_args):
            out_file = clean_args[out_idx + 1]

    if not os.path.exists(spec_file):
        print(f"Error: Spec file not found: {spec_file}", file=sys.stderr)
        return (1)
    with open(spec_file, "r", encoding="utf-8") as f:
        spec_content = f.read()

    compiled_ledger = SpecToLedgerCompiler.compile_spec(spec_content)
    if out_file:
        os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as of:
            of.write(compiled_ledger)
        print(f"Compiled specification to ledger: {out_file}")
    else:
        print(compiled_ledger)
    return (0)
