"""FocusGate v2.8 Part 5 (Checkpoint 4) — Facet index builder and freshness guard.

Reusable compiler and freshness verification for facets/facet_index.json.
Zero-dependency, pure Python stdlib.
"""
import json
import os
from core.facet_contract import load_contracts, FacetContractError


def build_index(facets_dir: str) -> dict:
    return index_from_contracts(load_contracts(facets_dir))


def index_from_contracts(contracts: dict) -> dict:
    """Pure: same input contracts, byte-identical index. No disk access."""
    facets = {}
    best: dict = {}  # pattern -> (priority, facet_id)
    for facet_id in sorted(contracts):
        c = contracts[facet_id]
        facets[facet_id] = {
            "context": c.context,
            "mode": c.mode,
            "priority": c.priority,
            "summary": c.summary,
            "seed": c.seed,
            "oracle": list(c.oracle),
            "socratic_cap": c.socratic_cap,
            "never_when": list(c.never_when),
        }
        for term in c.applies_when:
            prev = best.get(term)
            if prev is not None:
                if prev[0] == c.priority:
                    raise FacetContractError(
                        f"trigger collision: pattern '{term}' owned by both "
                        f"'{prev[1]}' and '{facet_id}' at priority {c.priority}"
                    )
                if prev[0] > c.priority:
                    continue
            best[term] = (c.priority, facet_id)
    triggers = [
        {"pattern": pattern, "facet": facets_id, "priority": priority}
        for pattern, (priority, facets_id) in best.items()
    ]
    triggers.sort(key=lambda t: (t["pattern"], t["facet"]))
    return {
        "generated_from": "facet-meta schema 1",
        "facets": facets,
        "triggers": triggers,
    }


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
