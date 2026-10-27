"""Prototype spike verify, scaffold and settle."""
import json
import os
import sys

from core.cli.registry import CommandContext
from core.cli.registry import command
from core.gates import SpikeValidator
from core.templates_embedded import EmbeddedTemplates


def _match_verify_spike(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'verify_spike', None) is not None


@command('verify-spike', flags=('--verify-spike',), dest=None, summary='verify-spike command', matches=_match_verify_spike, order=279)
def verify_spike(ctx: CommandContext) -> int:
    """verify-spike command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Error: Missing prototype artifact path to verify.", file=sys.stderr)
        return (1)
    artifact_path = clean_args[1]
    valid, errors = SpikeValidator.verify_logic_prototype(artifact_path)
    if is_json:
        print(json.dumps({"valid": valid, "errors": errors, "artifact": artifact_path}))
        return (0 if valid else 1)
    if valid:
        print("VALID_LOGIC_PROTOTYPE")
        return (0)
    else:
        print(f"FAILED_PROTOTYPE_VERIFICATION: {artifact_path}", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return (1)


def _match_scaffold_spike(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'scaffold_spike', None) is not None


@command('scaffold-spike', flags=('--scaffold-spike',), dest=None, summary='scaffold-spike command', matches=_match_scaffold_spike, order=280)
def scaffold_spike(ctx: CommandContext) -> int:
    """scaffold-spike command"""
    args = ctx.args
    clean_args = ctx.argv
    event_store = ctx.event_store
    is_json = ctx.is_json
    if len(clean_args) < 4:
        print("Usage: focus-gate.py --scaffold-spike <logic|ui> <name> \"<question>\" [ledger-path]", file=sys.stderr)
        return (1)
    branch = clean_args[1].lower()
    name = clean_args[2]
    question = clean_args[3]
    ledger_path = clean_args[4] if len(clean_args) > 4 else '.focusgate/GATES.md'

    if branch not in ('logic', 'ui'):
        print("Error: branch must be 'logic' or 'ui'", file=sys.stderr)
        return (1)

    proto_dir = ".focusgate/prototypes"
    os.makedirs(proto_dir, exist_ok=True)
    cli_path = ctx.cli_path

    if branch == 'logic':
        target_file = f"{proto_dir}/{name}.html"
        rendered = EmbeddedTemplates.LOGIC_PROTOTYPE_HTML.format(
            prototype_title=name.replace("-", " ").title(),
            prototype_question=question
        )
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(rendered)
        check_cmd = f"python3 {cli_path} --verify-spike {target_file}"
    else:
        target_file = f"{proto_dir}/{name}-guide.md"
        rendered = EmbeddedTemplates.UI_PROTOTYPE_MD.format(
            prototype_name=name.replace("-", " ").title(),
            question=question
        )
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(rendered)
        check_cmd = f"test -f {target_file} && echo 'UI_SPEC_OK'"

    spike_id = f"spike-{branch}-{name}"
    if os.path.exists(ledger_path):
        with open(ledger_path, "r", encoding="utf-8") as f:
            content = f.read()
        if spike_id not in content:
            spike_block = f"""
- [ ] {spike_id}: {name.replace('-', ' ').title()} Exploration
  BRANCH: {branch}
  QUESTION: {question}
  ARTIFACT: {target_file}
  CHECK: {check_cmd}
  EXPECT: {'VALID_LOGIC_PROTOTYPE' if branch == 'logic' else 'UI_SPEC_OK'}
"""
            if "### Spikes" in content:
                content = content.replace("### Spikes (Throwaway Explorations)", f"### Spikes (Throwaway Explorations)\n{spike_block}")
            elif "## 2. Acceptance Gates" in content:
                content = content.replace("## 2. Acceptance Gates", f"## 2. Acceptance Gates\n\n### Spikes (Throwaway Explorations)\n{spike_block}\n### Production Gates")
            with open(ledger_path, "w", encoding="utf-8") as f:
                f.write(content)

    event_store.append("SPIKE_SCAFFOLDED", {
        "spike_id": spike_id,
        "branch": branch,
        "artifact": target_file,
        "question": question
    })

    if is_json:
        print(json.dumps({"spike_id": spike_id, "branch": branch, "artifact": target_file, "ledger": ledger_path}))
    else:
        print(f"Scaffolded {branch.upper()} Prototype: {target_file}")
        print(f"Registered {spike_id} into {ledger_path}")
        print(f"Verify with: {check_cmd}")
    return (0)


def _match_settle_spike(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'settle_spike', None) is not None


@command('settle-spike', flags=('--settle-spike',), dest=None, summary='settle-spike command', matches=_match_settle_spike, order=281)
def settle_spike(ctx: CommandContext) -> int:
    """settle-spike command"""
    args = ctx.args
    clean_args = ctx.argv
    event_store = ctx.event_store
    if len(clean_args) < 3:
        print("Usage: focus-gate.py --settle-spike <spike_name_or_id> \"<adr_text>\" [ledger_path]", file=sys.stderr)
        return (1)
    spike_target = clean_args[1]
    adr_text = clean_args[2]
    ledger_path = clean_args[3] if len(clean_args) > 3 else '.focusgate/GATES.md'

    if not os.path.exists(ledger_path):
        print(f"Error: Ledger not found at {ledger_path}", file=sys.stderr)
        return (1)

    from core.gates.evidence import settle_spike
    if settle_spike(ledger_path, spike_target, adr_text) is None:
        print(f"Error: no open spike matching '{spike_target}' in {ledger_path}", file=sys.stderr)
        return (1)

    event_store.append("SPIKE_SETTLED", {
        "spike_target": spike_target,
        "adr": adr_text,
        "ledger": ledger_path
    })
    print(f"Settled spike {spike_target} and recorded Micro-ADR.")
    return (0)
