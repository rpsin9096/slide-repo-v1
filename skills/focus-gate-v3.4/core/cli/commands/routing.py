"""`-p` / `--synthesize-pipeline`."""
import json
import sys

from core.cli.registry import CommandContext, command
from core.pipeline_synthesizer import PipelineSynthesizer


@command("synthesize-pipeline", ("--synthesize-pipeline", "-p"), "synthesize_pipeline",
         "Classify a task and print the stage pipeline with a falsifiable 2-minute seed.")
def synthesize(ctx: CommandContext) -> int:
    if len(ctx.argv) < 2:
        print('Usage: focus-gate.py --synthesize-pipeline "<task_description>"', file=sys.stderr)
        return 1
    task = ctx.argv[1]
    plan = PipelineSynthesizer.synthesize(task)
    ctx.event_store.append("PIPELINE_SYNTHESIZED", {"query": task, "pipeline": plan["pipeline"],
                                                    "archetype": plan["archetype"]})
    if ctx.is_json:
        print(json.dumps(plan, indent=2))
        return 0
    print(f"Synthesized Execution Pipeline for: '{plan['query']}'")
    print(f"Archetype: {plan['archetype']} | Est: {plan['est_minutes']} min")
    print(f"Pipeline:  {plan['pipeline']}\n")
    print("Execution Stages:")
    for idx, s in enumerate(plan["stages"], 1):
        print(f"  {idx}. [{s['facet']}] {s['description']}")
    print("\nInitial 2-Minute Seed Action:")
    print(f"  Action: {plan['seed_step']['action']}")
    print(f"  Check:  {plan['seed_step']['check']}")
    print(f"  Expect: {plan['seed_step']['expect']}")
    return 0
