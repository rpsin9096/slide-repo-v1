"""`--init`: scaffold a task ledger."""
import os

from core.cli.registry import CommandContext, command


@command("init", ("--init",), "init", "Scaffold .focusgate/GATES.md with domain anchors.")
def init(ctx: CommandContext) -> int:
    from core.templates_embedded import EmbeddedTemplates
    target = "."
    if len(ctx.argv) > 1 and not ctx.argv[1].startswith("--"):
        target = ctx.argv[1]
    if ctx.explicit_root:
        focus_dir = ctx.ledger_root
    elif os.path.basename(os.path.abspath(target)).startswith("."):
        focus_dir = target
    else:
        focus_dir = os.path.join(target, ".focusgate")
    for sub in ("", "prototypes", "worktrees"):
        os.makedirs(os.path.join(focus_dir, sub), exist_ok=True)
    gates_file = os.path.join(focus_dir, "GATES.md")
    if os.path.exists(gates_file):
        print(f"FocusGate ledger already exists: {gates_file}")
        return 0
    rendered = EmbeddedTemplates.GATES_TASK_MD.format(
        task_name=os.path.basename(os.path.abspath(target)).replace("-", " ").title(),
        canonical_term="DomainModule",
        term_definition="Core domain component tracking verification states and acceptance gates.",
        term_avoid="GenericHandler, BlobManager",
        spike_name="core-logic",
        cli_path=ctx.cli_path,
    )
    with open(gates_file, "w", encoding="utf-8") as f:
        f.write(rendered)
    ctx.event_store.append("LEDGER_INITIALIZED", {"path": gates_file, "dir": target})
    print(f"Initialized FocusGate task ledger: {gates_file}")
    return 0
