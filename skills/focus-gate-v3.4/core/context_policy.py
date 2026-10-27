"""FocusGate v2.8 — Facet Context Policy Router."""
from enum import Enum


class FacetContextMode(str, Enum):
    EPHEMERAL = "EPHEMERAL"
    WINDOW = "WINDOW"


def mode_for_facet(facet: str) -> FacetContextMode:
    from core.facet_router import default_index
    idx = default_index()
    if idx:
        meta = idx.get("facets", {}).get((facet or "").strip().lower())
        if meta and meta.get("mode"):
            return FacetContextMode(meta["mode"])
    return FacetContextMode.WINDOW  # safe default for legacy/unregistered facets


def subscriptions_for(facet: str) -> list:
    if mode_for_facet(facet) == FacetContextMode.EPHEMERAL:
        return ["RECEIPT"]
    return ["RECEIPT", "DOMAIN_ANCHOR", "FILE_PATCH"]


def brief_budget(facet: str) -> int:
    if mode_for_facet(facet) == FacetContextMode.EPHEMERAL:
        return 150
    return 400


def richness_floor(facet: str) -> int:
    if mode_for_facet(facet) == FacetContextMode.EPHEMERAL:
        return 0
    return 120
