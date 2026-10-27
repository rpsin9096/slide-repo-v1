"""Facet body grammar: directives (tier 1) and Playbook (tier 2).

A facet file is `facet-meta` fence + `## Invariant Directives` + `## Playbook`.
The directive tier is what gets injected into sub-agent briefs under a token
ceiling; the playbook tier is the on-demand depth: ordered phases with
observable exits, the named lazy shortcuts and how to detect them, gate
templates the evidence linter accepts, and the handoff to the next facet.

Grammar (one record per line, `|` separates fields, pure stdlib):

    ## Invariant Directives
    1. NAME: one-sentence rule, operative clause first.

    ## Playbook
    ### Phases
    1. Name | DO: action | EXIT: observable result
    ### Lazy Tells
    - TELL_ID | SAYS: "the shortcut" | DETECT: observable | INSTEAD: counter-move
    ### Gate Templates
    ```gate
    - [ ] id: behavior
      CHECK: command with {placeholders}
      EXPECT: regex
    ```
    ### Handoff
    - NEXT: facet-id | WHEN: condition
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

_DIRECTIVE_RE = re.compile(r"^\s*\d+\.\s+([A-Z][A-Z0-9_]*):\s*(.+?)\s*$")
_PHASE_RE = re.compile(r"^\s*\d+\.\s+(.+?)\s*$")
_FIELD_RE = re.compile(r"^([A-Z]+):\s*(.*)$")
_GATE_HEAD_RE = re.compile(r"^-\s*\[[ xX]\]\s*([A-Za-z0-9._-]+):\s*(.*)$")
_TELL_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


class PlaybookError(ValueError):
    """`line N: CODE: message`; CODE is the lint code the catalog reports."""

    def __init__(self, code: str, line: int, message: str):
        super().__init__(f"line {line}: {code}: {message}")
        self.code = code
        self.line = line


@dataclass(frozen=True)
class Directive:
    name: str
    definition: str

    def gist(self, max_chars: int) -> str:
        """Operative clause: text up to the first sentence end, clipped on a word.

        Semicolons do not end a clause: the half after one is often the half that matters."""
        first = re.split(r"(?<=\.)\s", self.definition, maxsplit=1)[0].rstrip(".")
        if len(first) <= max_chars:
            return first
        cut = first[:max_chars].rsplit(" ", 1)[0].rstrip(",:;-")
        return cut + "…"


@dataclass(frozen=True)
class Phase:
    name: str
    do: str
    exit: str


@dataclass(frozen=True)
class LazyTell:
    id: str
    says: str
    detect: str
    instead: str


@dataclass(frozen=True)
class GateTemplate:
    gate_id: str
    behavior: str
    check: str
    expect: str


@dataclass(frozen=True)
class Handoff:
    next: str
    when: str


@dataclass(frozen=True)
class Playbook:
    phases: Tuple[Phase, ...]
    tells: Tuple[LazyTell, ...]
    templates: Tuple[GateTemplate, ...]
    handoffs: Tuple[Handoff, ...]


def _section(lines: List[str], heading: str, level: int) -> Tuple[int, List[Tuple[int, str]]]:
    """(start_index, [(lineno, text)]) of the body under `heading`, or (-1, [])."""
    mark = "#" * level + " "
    start = next((i for i, ln in enumerate(lines) if ln.strip() == f"{mark}{heading}"), -1)
    if start == -1:
        return -1, []
    body = []
    for i in range(start + 1, len(lines)):
        ln = lines[i]
        if ln.startswith("#") and re.match(r"^#{1,%d} " % level, ln):
            break
        body.append((i + 1, ln))
    return start, body


def parse_directives(text: str) -> List[Directive]:
    lines = (text or "").replace("\r\n", "\n").split("\n")
    _, body = _section(lines, "Invariant Directives", 2)
    out = []
    for _no, ln in body:
        m = _DIRECTIVE_RE.match(ln)
        if m:
            out.append(Directive(m.group(1), m.group(2)))
    return out


def _fields(rest: List[str]) -> dict:
    out = {}
    for part in rest:
        m = _FIELD_RE.match(part.strip())
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def _subsection(body: List[Tuple[int, str]], name: str) -> List[Tuple[int, str]]:
    out, on = [], False
    for no, ln in body:
        if ln.startswith("### "):
            on = ln.strip() == f"### {name}"
            continue
        if on:
            out.append((no, ln))
    return out


def _parse_phases(rows) -> List[Phase]:
    phases = []
    for no, ln in rows:
        m = _PHASE_RE.match(ln)
        if not m:
            continue
        parts = [p.strip() for p in m.group(1).split(" | ")]
        f = _fields(parts[1:])
        if not f.get("DO"):
            raise PlaybookError("PHASE_NO_DO", no, f"phase '{parts[0]}' has no DO:")
        if not f.get("EXIT"):
            raise PlaybookError("PHASE_NO_EXIT", no, f"phase '{parts[0]}' has no EXIT:")
        phases.append(Phase(parts[0], f["DO"], f["EXIT"]))
    return phases


def _parse_tells(rows) -> List[LazyTell]:
    tells = []
    for no, ln in rows:
        s = ln.strip()
        if not s.startswith("- "):
            continue
        parts = [p.strip() for p in s[2:].split(" | ")]
        if not _TELL_ID_RE.match(parts[0]):
            raise PlaybookError("TELL_BAD_ID", no, f"'{parts[0]}' is not an UPPER_SNAKE id")
        f = _fields(parts[1:])
        for key, code in (("SAYS", "TELL_NO_SAYS"), ("DETECT", "TELL_NO_DETECT"), ("INSTEAD", "TELL_NO_INSTEAD")):
            if not f.get(key):
                raise PlaybookError(code, no, f"tell '{parts[0]}' has no {key}:")
        tells.append(LazyTell(parts[0], f["SAYS"].strip('"'), f["DETECT"], f["INSTEAD"]))
    return tells


def _parse_templates(rows) -> List[GateTemplate]:
    out, in_fence, block, start = [], False, [], 0
    for no, ln in rows:
        if ln.strip().startswith("```gate"):
            in_fence, block, start = True, [], no
            continue
        if in_fence and ln.strip() == "```":
            in_fence = False
            out.extend(_gates_in(block, start))
            continue
        if in_fence:
            block.append(ln)
    return out


def _gates_in(block: List[str], start: int) -> List[GateTemplate]:
    gates, cur = [], None
    for ln in block + ["- [ ] __end__: x"]:
        m = _GATE_HEAD_RE.match(ln.strip())
        if m:
            if cur is not None:
                if not cur.get("CHECK") or not cur.get("EXPECT"):
                    raise PlaybookError("TEMPLATE_BAD", start, f"gate '{cur['id']}' needs CHECK and EXPECT")
                gates.append(GateTemplate(cur["id"], cur["behavior"], cur["CHECK"], cur["EXPECT"]))
            cur = {"id": m.group(1), "behavior": m.group(2)}
            continue
        k = _FIELD_RE.match(ln.strip())
        if k and cur is not None and k.group(1) in ("CHECK", "EXPECT"):
            cur[k.group(1)] = k.group(2).strip()
    return gates


def _parse_handoffs(rows) -> List[Handoff]:
    out = []
    for no, ln in rows:
        s = ln.strip()
        if not s.startswith("- "):
            continue
        f = _fields([p.strip() for p in s[2:].split(" | ")])
        if not f.get("NEXT") or not f.get("WHEN"):
            raise PlaybookError("HANDOFF_BAD", no, "handoff needs NEXT: and WHEN:")
        out.append(Handoff(f["NEXT"], f["WHEN"]))
    return out


def parse_playbook(text: str) -> Optional[Playbook]:
    """Playbook of a facet body, or None when the facet has no `## Playbook`."""
    lines = (text or "").replace("\r\n", "\n").split("\n")
    start, body = _section(lines, "Playbook", 2)
    if start == -1:
        return None
    return Playbook(
        phases=tuple(_parse_phases(_subsection(body, "Phases"))),
        tells=tuple(_parse_tells(_subsection(body, "Lazy Tells"))),
        templates=tuple(_parse_templates(_subsection(body, "Gate Templates"))),
        handoffs=tuple(_parse_handoffs(_subsection(body, "Handoff"))),
    )
