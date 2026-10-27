"""FacetCatalog: the one seam through which facets are loaded, routed, rendered, linted.

Before v3.3 four callers each owned a loader: the hydrate command (index + file
read), `AgentBrief.to_prompt` (re-parsed every facet on every call, swallowing
errors), the router (its own JSON load) and the lint command. They drifted. Now
all of them cross this interface:

    cat = FacetCatalog.default()
    cat.get("unlazy")                     -> Facet
    cat.route("fix the crash", top_k=4)   -> [(facet_id, priority)]
    cat.render("unlazy", 400)             -> injected block (rules with definitions)
    cat.render("unlazy", 4000, depth="playbook")
    cat.lint()                            -> ["<facet>: CODE: message", ...]

The catalog re-stats the facet directory on each access (one stat per file) and
reloads only when a path, size or mtime changed, so an edit on disk is visible
without a restart and an unchanged tree costs no parsing.
"""
import os
import re
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from core.facet_contract import FacetContract, FacetContractError, parse_facet_file, render_compact
from core.facets.playbook import Directive, Playbook
from core.tokens import estimate_tokens

_FENCE = "```facet-meta"
_SKILL_FACETS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "facets")

TIER_TWO_CAP = 1500          # tokens: whole facet file (directives + playbook)
MODE_CEILING = {"WINDOW": 400, "EPHEMERAL": 150}   # tokens: injected render
MIN_RULES_INJECTED = 3       # a facet must still show this many rules at its ceiling

_VAGUE = ("best practice", "world-class", "robust and scalable", "high-quality", "high quality",
          "as appropriate", "where possible", "if applicable", "leverage", "ensure quality",
          "think step by step", "do your best", "etc.")
_OBSERVABLE = re.compile(r"`|exit|\d|\.md|\.json|\.py|--[a-z]|file:line|PASS|RED|green|red |"
                         r"count|zero|none|empty|equal|matches|lists|names|cites|contains|byte", re.I)


class UnknownFacet(ValueError):
    pass


@dataclass(frozen=True)
class Facet:
    id: str
    contract: FacetContract
    directives: Tuple[Directive, ...]
    playbook: Optional[Playbook]
    text: str
    path: str
    tokens: int


class FacetCatalog:
    _by_dir: Dict[str, "FacetCatalog"] = {}
    _default_lock = threading.Lock()

    def __init__(self, facets_dir: str):
        self.dir = facets_dir
        self._lock = threading.RLock()
        self._sig: Optional[tuple] = None
        self._facets: Dict[str, Facet] = {}
        self._errors: List[str] = []
        self._index: Optional[dict] = None

    @classmethod
    def for_dir(cls, facets_dir: str) -> "FacetCatalog":
        """One cached catalog per directory; tests and the CLI share it."""
        key = os.path.abspath(facets_dir)
        with cls._default_lock:
            if key not in cls._by_dir:
                cls._by_dir[key] = cls(key)
            return cls._by_dir[key]

    @classmethod
    def default(cls) -> "FacetCatalog":
        return cls.for_dir(_SKILL_FACETS)

    # -- loading ---------------------------------------------------------
    def _paths(self) -> List[str]:
        out = []
        for dp, _d, fns in os.walk(self.dir):
            out.extend(os.path.join(dp, f) for f in sorted(fns) if f.endswith(".md"))
        return sorted(out)

    def _signature(self, paths: List[str]) -> tuple:
        sig = []
        for p in paths:
            try:
                st = os.stat(p)
                sig.append((p, st.st_mtime_ns, st.st_size))
            except OSError:
                sig.append((p, 0, 0))
        return tuple(sig)

    def _ensure(self) -> None:
        paths = self._paths()
        sig = self._signature(paths)
        with self._lock:
            if sig == self._sig:
                return
            facets: Dict[str, Facet] = {}
            errors: List[str] = []
            for path in paths:
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        text = fh.read()
                except OSError:
                    continue
                if _FENCE not in text:
                    continue  # legacy fence-less file: skipped, as load_contracts does
                try:
                    c = parse_facet_file(text, filename=path)
                except FacetContractError as exc:
                    errors.append(f"{os.path.basename(path)[:-3]}: CONTRACT_INVALID: {exc}")
                    continue
                if c.id in facets:
                    errors.append(f"{c.id}: DUPLICATE_ID: also defined in {path}")
                    continue
                facets[c.id] = Facet(c.id, c, c.directives, c.playbook, text, path, estimate_tokens(text))
            self._facets, self._errors, self._sig = facets, errors, sig
            self._index = None

    # -- queries ---------------------------------------------------------
    def ids(self) -> List[str]:
        self._ensure()
        return sorted(self._facets)

    def get(self, facet_id: str) -> Facet:
        self._ensure()
        key = (facet_id or "").strip().lower()
        f = self._facets.get(key)
        if f is None:
            raise UnknownFacet(f"Unknown facet: {facet_id!r}. Available: {sorted(self._facets)}")
        return f

    def has(self, facet_id: str) -> bool:
        self._ensure()
        return (facet_id or "").strip().lower() in self._facets

    def contracts(self) -> Dict[str, FacetContract]:
        self._ensure()
        return {fid: f.contract for fid, f in self._facets.items()}

    def index(self) -> dict:
        from core.facet_index import index_from_contracts
        self._ensure()
        with self._lock:
            if self._index is None:
                self._index = index_from_contracts(self.contracts())
            return self._index

    def route(self, query: str, top_k: int = 4) -> List[Tuple[str, int]]:
        from core.facet_router import match_facets
        return match_facets(query, self.index(), top_k=top_k)

    # -- rendering -------------------------------------------------------
    def render(self, facet_id: str, budget_tokens: int, depth: str = "directive") -> str:
        """depth: `directive` (injected rules under the ceiling), `playbook`
        (directives + playbook, clipped to the budget) or `full` (the file)."""
        f = self.get(facet_id)
        if depth == "directive":
            return render_compact(f.contract, budget_tokens)
        if depth == "full":
            return f.text
        if depth != "playbook":
            raise ValueError(f"unknown depth {depth!r}; use directive, playbook or full")
        body = f.text[f.text.index("## Invariant Directives"):] if "## Invariant Directives" in f.text else f.text
        if estimate_tokens(body) <= budget_tokens:
            return body
        return body[:budget_tokens * 4].rsplit("\n", 1)[0] + "\n…[clipped to budget]"

    def hydrate_info(self, facet_id: str, depth: str = "full") -> dict:
        """Dict consumed by `--hydrate-facet`; `directive` holds the rendered text."""
        f = self.get(facet_id)
        ceiling = MODE_CEILING.get(f.contract.mode, 400)
        text = self.render(f.id, ceiling if depth == "directive" else 10 ** 6, depth)
        return {"facet": f.id, "context": f.contract.context, "mode": f.contract.mode,
                "path": f.path, "depth": depth, "tokens": estimate_tokens(text), "directive": text}

    def summary_rows(self) -> List[dict]:
        self._ensure()
        return [{"facet": fid, "context": f.contract.context, "mode": f.contract.mode,
                 "tokens": f.tokens, "available": True,
                 "has_playbook": f.playbook is not None}
                for fid, f in sorted(self._facets.items())]

    # -- lint ------------------------------------------------------------
    def lint(self) -> List[str]:
        """Depth and honesty problems, one per line as `<facet>: CODE: message`."""
        from core.gates.evidence import GateIntegrity, errors_of
        self._ensure()
        problems = list(self._errors)
        known = set(self._facets)
        for fid, f in sorted(self._facets.items()):
            def bad(code, msg):
                problems.append(f"{fid}: {code}: {msg}")

            for d in f.directives:
                if len(d.definition.split()) < 8:
                    bad("THIN_DIRECTIVE", f"{d.name} has a {len(d.definition.split())}-word definition (min 8)")
            if not f.directives:
                bad("THIN_DIRECTIVE", "no `N. NAME: definition` directives found")
            if f.tokens > TIER_TWO_CAP:
                bad("OVER_BUDGET", f"whole file is ~{f.tokens} tokens (cap {TIER_TWO_CAP})")
            ceiling = MODE_CEILING.get(f.contract.mode, 400)
            shown = render_compact(f.contract, ceiling).count("\n- ")
            want = min(MIN_RULES_INJECTED, len(f.directives))
            if f.directives and shown < want:
                bad("OVER_BUDGET", f"only {shown} rule(s) fit the {ceiling}-token injected ceiling (need {want})")

            pb = f.playbook
            if pb is None:
                bad("NO_PLAYBOOK", "add `## Playbook` with Phases, Lazy Tells, Gate Templates, Handoff")
                continue
            if len(pb.phases) < 3:
                bad("FEW_PHASES", f"{len(pb.phases)} phase(s); a process needs at least 3")
            for ph in pb.phases:
                if not _OBSERVABLE.search(ph.exit):
                    bad("UNOBSERVABLE_EXIT", f"phase '{ph.name}' EXIT names nothing a command or file can show")
            if len(pb.tells) < 2:
                bad("FEW_TELLS", f"{len(pb.tells)} lazy tell(s); name at least 2 shortcuts")
            if not pb.templates:
                bad("NO_GATE_TEMPLATE", "no ```gate template")
            for t in pb.templates:
                chk = re.sub(r"\{[a-z_]+\}", "x", t.check)
                exp = re.sub(r"\{[a-z_]+\}", "x", t.expect)
                for e in errors_of(GateIntegrity.analyze(chk, exp)):
                    bad("TEMPLATE_DISHONEST", f"gate '{t.gate_id}': {e.render()}")
            if not pb.handoffs:
                bad("NO_HANDOFF", "no `- NEXT: <facet> | WHEN: <condition>`")
            for h in pb.handoffs:
                if h.next not in known:
                    bad("DANGLING_HANDOFF", f"NEXT '{h.next}' is not a facet")
            prose = " ".join([d.definition for d in f.directives]
                             + [x for ph in pb.phases for x in (ph.do, ph.exit)]
                             + [x for t in pb.tells for x in (t.detect, t.instead)]).lower()
            for phrase in _VAGUE:
                if phrase in prose:
                    bad("VAGUE_PHRASE", f"'{phrase}' constrains nothing; state the input, transform or exit")
        return problems


def contract_lint(facets_dir: str, known_flags: set):
    """Contract-level checks formerly inlined in the CLI script.

    Returns (errors, warnings, contracts_by_path, trigger_owner): stale index,
    unparseable contracts, dead oracle flags, trigger collisions, `never_when`
    guards that shadow other facets.
    """
    from core.facet_index import index_is_current
    errors: List[str] = []
    warnings: List[str] = []
    if not index_is_current(facets_dir):
        errors.append(f"{facets_dir}/facet_index.json is stale — re-run: python3 scripts/compile_facets.py")
    contracts: Dict[str, FacetContract] = {}
    for dp, _d, fns in os.walk(facets_dir):
        for fn in sorted(fns):
            if fn.endswith(".md"):
                path = os.path.join(dp, fn)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        contracts[path] = parse_facet_file(fh.read(), filename=path)
                except FacetContractError as exc:
                    errors.append(str(exc))
    for path, c in sorted(contracts.items()):
        if not c.applies_when:
            errors.append(f"{path}: zero triggers for facet '{c.id}'")
        for flag in c.oracle:
            if flag not in known_flags:
                errors.append(f"{path}: dead oracle flag '{flag}' not found in argparse")
    owner: Dict[str, Tuple[int, str]] = {}
    for c in contracts.values():
        for term in c.applies_when:
            if term in owner and owner[term][0] == c.priority:
                errors.append(f"collision: '{term}' owned by '{owner[term][1]}' and '{c.id}' at priority {c.priority}")
            elif term not in owner or owner[term][0] < c.priority:
                owner[term] = (c.priority, c.id)
    for c in contracts.values():
        for guard in c.never_when:
            shadowed = sorted({o.id for o in contracts.values()
                               if o.id != c.id and any(guard in t for t in o.applies_when)})
            if len(shadowed) > 3:
                errors.append(f"never_when '{guard}' on '{c.id}' shadows more than 3 facets: {', '.join(shadowed)}")
            if c.applies_when and all(guard in t for t in c.applies_when):
                warnings.append(f"never_when '{guard}' zeroes facet '{c.id}'")
    return errors, warnings, contracts, owner


def lint_all(facets_dir: str, known_flags: set):
    """Contract checks plus depth checks: (errors, warnings, contracts, trigger_owner)."""
    errors, warnings, contracts, owner = contract_lint(facets_dir, known_flags)
    return errors + FacetCatalog.for_dir(facets_dir).lint(), warnings, contracts, owner
