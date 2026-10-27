"""FocusGate v2.8 Part 4 — Facet Contract parser (facet-meta schema 1).

Machine-parseable facet files: markdown body stays human-readable; one fenced
```facet-meta block carries the declarative contract (triggers, socratic
protocol, usability layer). Line-parsed with the stdlib only — no YAML, no
third-party parser (v2.8 zero-dependency rule).
"""
import json
import os
import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from core.facets.playbook import PlaybookError, parse_directives, parse_playbook

_FENCE_OPEN = "```facet-meta"
_FENCE_CLOSE = "```"

_ALLOWED_TOP = ("schema", "id", "context", "summary", "priority", "mode",
                "applies_when", "never_when", "oracle", "socratic", "usability")
_REQUIRED_TOP = ("schema", "id", "summary", "priority", "mode", "applies_when")
_LIST_KEYS = ("applies_when", "never_when", "oracle")
_ALLOWED_SOCRATIC = ("grounding", "stems", "cap")
_ALLOWED_USABILITY = ("seed", "example", "criterion")

_TOP_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")
_NESTED_KEY_RE = re.compile(r"^\s+([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")
_ITEM_RE = re.compile(r"^\s*-\s+(.*)$")
_CONTEXT_HEADER_RE = re.compile(r"^\s*Context:\s*([^|]+)\|", re.IGNORECASE | re.MULTILINE)
_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_RULE_TITLE_RE = re.compile(r"^\s*\d+\.\s+([A-Z][A-Z0-9_]*)\b")


@dataclass(frozen=True)
class FacetContract:
    id: str
    context: str
    mode: str
    summary: str
    priority: int
    applies_when: Tuple[str, ...]
    never_when: Tuple[str, ...]
    oracle: Tuple[str, ...]
    socratic_grounding: Tuple[str, ...]
    socratic_stems: Tuple[str, ...]
    socratic_cap: int
    seed: str
    example: str
    criterion: str
    directive_titles: Tuple[str, ...] = ()
    directives: Tuple = ()            # Tuple[Directive]: name + definition (v3.3)
    playbook: Optional[object] = None  # Playbook, or None for legacy facets (v3.3)


class FacetContractError(ValueError):
    """Raised with '<file>:<line>: <message>' for any contract violation."""


def _strip_quotes(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        return v[1:-1]
    return v


def _parse_inline_list(raw: str) -> Tuple[str, ...]:
    raw = raw.strip()
    try:
        items = json.loads(raw)
        if not isinstance(items, list):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        inner = raw[1:-1] if raw.startswith("[") and raw.endswith("]") else raw
        items = inner.split(",")
    return tuple(_strip_quotes(str(i)) for i in items if str(i).strip())


def _split_scalar_and_comment(raw: str) -> str:
    # Only treat an unquoted ' #' as a trailing comment.
    v = raw.strip()
    if v.startswith(('"', "'")):
        return v
    cut = v.find(" #")
    return (v[:cut] if cut != -1 else v).strip()


def parse_facet_file(text: str, filename: Optional[str] = None) -> FacetContract:
    where = filename if filename else "<string>"
    lines = (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")

    header_ctx = ""
    fence_start = -1
    fence_end = -1
    for idx, ln in enumerate(lines):
        if ln.strip() == _FENCE_OPEN and fence_start == -1:
            fence_start = idx
            continue
        if fence_start != -1 and ln.strip() == _FENCE_CLOSE:
            fence_end = idx
            break
    if fence_start == -1:
        raise FacetContractError(f"{where}:1: missing ```facet-meta fence")
    if fence_end == -1:
        raise FacetContractError(f"{where}:{fence_start + 1}: unterminated ```facet-meta fence")

    fence_lineno = fence_start + 1
    scalars: Dict[str, str] = {}
    lists: Dict[str, list] = {}
    nested: Dict[str, Dict[str, object]] = {"socratic": {}, "usability": {}}
    key_lines: Dict[str, int] = {}
    section = None
    pending_list: Optional[Tuple[str, object]] = None  # (key, container)

    def _err(lineno: int, message: str) -> "FacetContractError":
        return FacetContractError(f"{where}:{lineno}: {message}")

    for idx in range(fence_start + 1, fence_end):
        raw = lines[idx]
        lineno = idx + 1
        if not raw.strip() or raw.strip().startswith("#"):
            continue

        item = _ITEM_RE.match(raw)
        if item:
            if pending_list is None:
                raise _err(lineno, "list item without a list key")
            key, container = pending_list
            if isinstance(container, list):
                container.append(_strip_quotes(item.group(1)))
            else:
                raise _err(lineno, f"'{key}' does not accept a dash list")
            continue

        top = _TOP_KEY_RE.match(raw)
        nested_key = _NESTED_KEY_RE.match(raw) if not top else None
        if top:
            key, value = top.group(1), _split_scalar_and_comment(top.group(2))
            if key not in _ALLOWED_TOP:
                raise _err(lineno, f"unknown top-level key '{key}'")
            if key in key_lines:
                raise _err(lineno, f"duplicate top-level key '{key}'")
            key_lines[key] = lineno
            section = key if key in ("socratic", "usability") else None
            pending_list = None
            if key in _LIST_KEYS:
                if value == "":
                    lists[key] = []
                    pending_list = (key, lists[key])
                elif value.startswith("["):
                    lists[key] = list(_parse_inline_list(value))
                else:
                    lists[key] = [_strip_quotes(value)]
            elif section:
                if value != "":
                    raise _err(lineno, f"section '{key}' must not carry an inline value")
            else:
                scalars[key] = value
        elif nested_key and section:
            key, value = nested_key.group(1), _split_scalar_and_comment(nested_key.group(2))
            allowed = _ALLOWED_SOCRATIC if section == "socratic" else _ALLOWED_USABILITY
            if key not in allowed:
                raise _err(lineno, f"unknown key '{key}' under section '{section}'")
            pending_list = None
            if section == "socratic":
                if key in ("grounding", "stems"):
                    if value == "":
                        bucket: list = []
                        nested["socratic"][key] = bucket
                        pending_list = (f"{section}.{key}", bucket)
                    elif value.startswith("["):
                        nested["socratic"][key] = list(_parse_inline_list(value))
                    else:
                        nested["socratic"][key] = [_strip_quotes(value)]
                elif key == "cap":
                    try:
                        cap = int(value)
                    except ValueError:
                        raise _err(lineno, f"socratic cap must be an integer, got '{value}'")
                    if cap < 0:
                        raise _err(lineno, "socratic cap must be >= 0")
                    nested["socratic"]["cap"] = cap
                else:
                    raise _err(lineno, f"unknown key '{key}' under section 'socratic'")
            else:
                nested["usability"][key] = _strip_quotes(value)
        else:
            raise _err(lineno, f"unparseable facet-meta line: {raw.strip()!r}")

    for key in _REQUIRED_TOP:
        if key not in key_lines:
            raise _err(fence_lineno, f"missing required key '{key}'")

    if scalars.get("schema", "").strip() != "1":
        raise _err(key_lines["schema"], "only facet-meta schema 1 is supported")

    facet_id = scalars["id"].strip()
    if not _ID_RE.match(facet_id):
        raise _err(key_lines["id"], f"id must be lowercase-hyphen, got '{facet_id}'")
    if filename:
        stem = os.path.splitext(os.path.basename(filename))[0]
        if facet_id != stem:
            raise _err(key_lines["id"], f"id '{facet_id}' must equal filename stem '{stem}'")

    try:
        priority = int(scalars["priority"].strip())
    except ValueError:
        raise _err(key_lines["priority"], f"priority must be an integer, got '{scalars['priority']}'")
    if not 1 <= priority <= 10:
        raise _err(key_lines["priority"], f"priority {priority} outside range 1-10")

    applies = tuple(t.lower() for t in lists.get("applies_when", []))
    if not applies:
        raise _err(key_lines["applies_when"], "applies_when must not be empty")

    context = scalars.get("context", "").strip().lower()
    if not context:
        header = "\n".join(lines[:fence_start])
        m = _CONTEXT_HEADER_RE.search(header)
        context = m.group(1).strip().lower() if m else ""

    titles = []
    after = lines[fence_end + 1:]
    for ln in after:
        m = _RULE_TITLE_RE.match(ln)
        if m:
            titles.append(m.group(1))
        if len(titles) >= 3:
            break

    full_text = "\n".join(lines)
    try:
        directives = tuple(parse_directives(full_text))
        playbook = parse_playbook(full_text)
    except PlaybookError as exc:
        raise FacetContractError(f"{where}:{exc.line}: {exc.code}: {str(exc).split(': ', 2)[-1]}")

    socratic = nested["socratic"]
    usability = nested["usability"]
    return FacetContract(
        id=facet_id,
        context=context,
        mode=scalars["mode"].strip().upper(),
        summary=_strip_quotes(scalars["summary"]),
        priority=priority,
        applies_when=applies,
        never_when=tuple(t.lower() for t in lists.get("never_when", [])),
        oracle=tuple(lists.get("oracle", [])),
        socratic_grounding=tuple(socratic.get("grounding", ()) or ()),
        socratic_stems=tuple(socratic.get("stems", ()) or ()),
        socratic_cap=int(socratic.get("cap", 0) or 0),
        seed=str(usability.get("seed", "")),
        example=str(usability.get("example", "")),
        criterion=str(usability.get("criterion", "")),
        directive_titles=tuple(titles),
        directives=directives,
        playbook=playbook,
    )


def load_contracts(facets_dir: str) -> Dict[str, FacetContract]:
    """id -> contract for every fenced facet file under facets_dir.

    Legacy fence-less files are skipped (registry hydration keeps working
    during the retrofit window); fenced-but-invalid files raise.
    """
    contracts: Dict[str, FacetContract] = {}
    if not os.path.isdir(facets_dir):
        return contracts
    paths = []
    for dirpath, _dirnames, filenames in os.walk(facets_dir):
        for fname in sorted(filenames):
            if fname.endswith(".md"):
                paths.append(os.path.join(dirpath, fname))
    for path in sorted(paths):
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except (OSError, IOError):
            continue
        if _FENCE_OPEN not in text:
            continue
        contract = parse_facet_file(text, filename=path)
        if contract.id in contracts:
            raise FacetContractError(f"{path}: duplicate facet id '{contract.id}'")
        contracts[contract.id] = contract
    return contracts


_GIST_STEPS = (110, 70, 44)
_GIST_STEPS_ROOMY = (160,) + _GIST_STEPS   # budgets of 300+ tokens (WINDOW)


def render_compact(contract: FacetContract, budget_tokens: int) -> str:
    """Injected '## Facet Directive' block that fits `budget_tokens`.

    Each rule is emitted as `- NAME: operative clause`, never as a bare title:
    a sub-agent cannot act on a label. Squeeze order, cheapest loss first:
    seed, lazy-tell, cap line, then shorter clauses, then trailing rules.
    Facets are authored most-critical-first, so dropping from the tail keeps
    the rules that matter. Legacy facets without parsed definitions fall back
    to titles.
    """
    if budget_tokens < 40:
        return ""
    from .tokens import estimate_tokens as _est

    header = f"## Facet Directive: {contract.id}"
    cap_line = f"- Socratic cap: {contract.socratic_cap} grounded question(s) per round."
    seed_line = f"- SEED: {contract.seed}" if contract.seed else ""
    tell_line = ""
    pb = contract.playbook
    if pb is not None and pb.tells:
        t = pb.tells[0]
        tell_line = f"- AVOID {t.id}: \"{t.says}\" -> {t.instead}"

    if contract.directives:
        n_all = len(contract.directives)

        def rules(n: int, gist: int):
            return [f"- {d.name}: {d.gist(gist)}" for d in contract.directives[:n]]
        gists = _GIST_STEPS_ROOMY if budget_tokens >= 300 else _GIST_STEPS
    else:
        n_all = min(3, len(contract.directive_titles))

        def rules(n: int, gist: int):
            return [f"- {t}" for t in contract.directive_titles[:n]]
        gists = (0,)

    extras_options = [e for e in ((tell_line, seed_line, cap_line), (tell_line, cap_line),
                                  (cap_line,), ())]
    # Prefer fewer whole rules over many clipped ones: keep every rule at the longest clip
    # that fits, then shrink the clip, and only then drop below 3 rules.
    floor = min(3, n_all)
    plans = [(g, n) for g in gists for n in range(n_all, floor - 1, -1)]
    plans += [(gists[-1], n) for n in range(floor - 1, -1, -1)]
    for gist, n in plans:
        for extras in extras_options:
            text = "\n".join([header] + rules(n, gist) + [e for e in extras if e])
            if _est(text) <= budget_tokens:
                return text
    return ""
