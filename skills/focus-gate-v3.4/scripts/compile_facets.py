#!/usr/bin/env python3
"""FocusGate v2.8 Part 4 — Facet trigger index compiler (spec S-3).

Compiles facet-meta contracts into facets/facet_index.json: the single source
of trigger truth consumed by core/facet_router.py. Deterministic: same inputs
produce byte-identical output. Duplicate patterns at equal priority are a
compile-time error, never a runtime surprise (spec §10).
"""
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if SKILL_ROOT not in sys.path:
    sys.path.insert(0, SKILL_ROOT)

from core.facet_contract import FacetContractError
from core.facet_index import build_index


def main() -> int:
    facets_dir = os.path.join(SKILL_ROOT, "facets")
    try:
        index = build_index(facets_dir)
    except FacetContractError as e:
        print(f"compile_facets: {e}", file=sys.stderr)
        return 1
    out_path = os.path.join(facets_dir, "facet_index.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"Wrote {out_path}: {len(index['facets'])} facets, {len(index['triggers'])} triggers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
