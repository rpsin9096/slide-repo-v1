"""FocusGate v2.8 Part 4 — Facet Router: single-source opportunistic matching.

Consumes facets/facet_index.json (compiled from facet-meta contracts). All
keyword routing in the kernel goes through match_facets so the five drifting
keyword tables of v2.7 (F-02) collapse into one derived index.
"""
import json
import os
import re
from functools import lru_cache
from typing import Dict, List, Tuple

_DEFAULT_INDEX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "facets", "facet_index.json",
)


def load_index(path: str = None) -> dict:
    with open(path or _DEFAULT_INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_INFLECT = r"(?:s|es|ed|ing|ally|ly)?"


@lru_cache(maxsize=1024)
def _compile(pattern: str):
    """Whole-word match with plain English inflections: `fail` hits `failing`
    but not `failover`; `fix` hits `fixes` but not `prefix`; `idea` not `ideal`."""
    return re.compile(r"(?<![a-z0-9])" + re.escape(pattern) + _INFLECT + r"(?![a-z0-9])")


def _hit(pattern: str, q: str) -> bool:
    return _compile(pattern).search(q) is not None


def match_facets(query: str, index: dict, top_k: int = 4) -> List[Tuple[str, int]]:
    """Ranked `(facet_id, priority)` for a query.

    Rank is evidence-weighted, not priority alone: a facet hit by several
    distinct triggers, or by a multi-word phrase, outranks one lone hit on a
    higher-priority word. The returned int stays the facet priority.
    """
    q = (query or "").lower()
    never = {fid: tuple(meta.get("never_when", ())) for fid, meta in index.get("facets", {}).items()}
    hits: Dict[str, List[str]] = {}
    prio: Dict[str, int] = {}
    for entry in index.get("triggers", []):
        facet, pattern = entry["facet"], entry["pattern"]
        if not _hit(pattern, q):
            continue
        if any(_hit(guard, q) for guard in never.get(facet, ())):
            continue
        hits.setdefault(facet, []).append(pattern)
        prio[facet] = max(prio.get(facet, 0), entry["priority"])

    def score(facet: str) -> float:
        pats = hits[facet]
        longest = max(len(p.split()) for p in pats)
        return prio[facet] + 1.5 * min(len(pats) - 1, 3) + 0.5 * (longest - 1)

    ranked = sorted(hits, key=lambda f: (-score(f), f))
    return [(f, prio[f]) for f in ranked[:top_k]]


_cached_index = None


def default_index():
    """Cached facet_index.json; None if not compiled (callers fall back)."""
    global _cached_index
    if _cached_index is None:
        try:
            _cached_index = load_index()
        except (OSError, ValueError):
            return None
    return _cached_index


def matched_ids(query: str, top_k: int = 6) -> list:
    index = default_index()
    if index is None:
        return []
    return [fid for fid, _prio in match_facets(query, index, top_k=top_k)]


def scripted_facets(query: str, scripted: list, top_k: int = 6) -> list:
    """Scripted pipeline facets plus router-sourced opportunistic matches."""
    extras = [fid for fid in matched_ids(query, top_k=top_k) if fid not in scripted]
    return list(scripted) + extras[:2]
