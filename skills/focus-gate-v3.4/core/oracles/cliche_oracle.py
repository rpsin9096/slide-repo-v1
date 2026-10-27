"""FocusGate v2.8 — Anti-Cliché Design Oracle.

Detects common AI-generated design tells across CSS, HTML, and JSX/TSX:
1. Warm cream (#F4F1EA) + terracotta (#D97757) Anthropic tell.
2. Near-black (#0B0B0B / #111) + bright acid-green / vermilion.
3. SaaS-card kit: identical rounded cards with uniform rgba(0,0,0,.1) shadows.
4. AI template chrome:
   - Tracked all-caps eyebrows.
   - Middle-dot joined metadata strings ('A · B · C').
   - Spaced em-dash labels ('WORD — fragment').
   - Unwarranted button arrow markers ('→').
5. Headline single-word accenting (accenting just one word in a title).

Zero external dependencies (100% Python stdlib).
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ClicheFinding:
    rule_id: str
    description: str
    line_number: Optional[int] = None
    snippet: Optional[str] = None
    severity: str = "WARNING"  # WARNING or VIOLATION
    # Added in v3.2 Loop 63. `audit_content` already took a `filename` and
    # every caller passed one, but the finding dropped it — so the CLI printed
    # "line 369" with no file, and a location like that cannot be acted on.
    # It also made finding IDENTITY impossible to compare between --audit-all
    # and --audit-design-cliche, which is the only honest way to assert the
    # aggregate is not weaker than its parts. Optional and last, so every
    # positional construction in the wild keeps working.
    filename: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "description": self.description,
            "line_number": self.line_number,
            "snippet": self.snippet,
            "severity": self.severity,
            "filename": self.filename,
        }


@dataclass
class ClicheAuditResult:
    clean: bool
    findings: List[ClicheFinding] = field(default_factory=list)
    checked_lines: int = 0

    def summary(self) -> str:
        if self.clean:
            return "CLICHE_AUDIT_PASS: Zero generic AI design tells detected."
        rules = set(f.rule_id for f in self.findings)
        return f"CLICHE_AUDIT_FAIL: Found {len(self.findings)} tell(s) across rules: {', '.join(rules)}"


class ClicheOracle:
    """Audits visual artifacts against the 5 canonical AI design templates."""

    # Color tells
    RE_TERRACOTTA = re.compile(r"#(?:d97757|f4f1ea|f5f2eb|e87a5a)\b", re.IGNORECASE)
    RE_ACID_GREEN = re.compile(r"#(?:39ff14|00ff66|ff3300|e34234)\b", re.IGNORECASE)
    RE_NEAR_BLACK = re.compile(r"#(?:0b0b0b|111111|121212)\b", re.IGNORECASE)

    # Chrome tells
    RE_MIDDLE_DOT = re.compile(r"\b[A-Za-z0-9]+\s+[·•]\s+[A-Za-z0-9]+")
    # An ALL-CAPS label, an em dash, then a word. Rewritten in Loop 66 (F21)
    # for two reasons, both proven by fault injection:
    #
    # 1. It never matched inside markup. The original had no allowance for a
    #    closing tag between the label and the dash, so `<span>PRO</span> -
    #    Upgrade` was invisible while bare `FREE - Start` was caught. The rule
    #    was disarmed against the actual thing it exists to catch.
    # 2. It fired on ordinary markdown. `**Preview 1 (DELIVERED & SEALED -
    #    Loops 39-44)**` matched, so auditing the workspace flagged the
    #    project's own ROADMAP with two findings.
    #
    # The discriminator is the tail: a chrome label em-dashes to a standalone
    # word, a release range em-dashes to a span containing digits. The negative
    # lookahead rejects a number within the following 40 characters. Verified on
    # 8 cases — 4 chrome tells caught, 4 numeric ranges allowed through.
    RE_EM_DASH_LABEL = re.compile(
        r"(?:<[^>]{0,40}>\s*)?\b[A-Z]{3,}\s*(?:</[^>]{0,40}>\s*)?\u2014\s*"
        r"(?:<[^>]{0,40}>\s*)?[A-Za-z]+\b(?![^\n]{0,40}?\d)")
    RE_BUTTON_ARROW = re.compile(r"(?:>|\b)(?:[A-Za-z\s]+)\s+(?:→|&rarr;|->)(?:<|\b)")
    RE_CARD_SHADOW = re.compile(r"rgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*0?\.1\s*\)")

    # Typographic tells
    RE_HEADLINE_SINGLE_ACCENT = re.compile(
        r"<h[1-3][^>]*>[^<]*<(?:span|em|strong|b)\s+class=[\"'][^\"']*accent[^\"']*[\"']>[^<]+<\/(?:span|em|strong|b)>[^<]*<\/h[1-3]>",
        re.IGNORECASE
    )
    RE_TRACKED_ALL_CAPS = re.compile(
        r"(?:letter-spacing:\s*(?:0\.[1-9]|1|2|3)em;?\s*text-transform:\s*uppercase|text-transform:\s*uppercase;?\s*letter-spacing:\s*(?:0\.[1-9]|1|2|3)em)",
        re.IGNORECASE
    )

    @classmethod
    def audit_content(cls, content: str, filename: str = "") -> ClicheAuditResult:
        """Audits CSS/HTML/TSX source content for template tells."""
        findings: List[ClicheFinding] = []
        lines = content.splitlines()

        has_cream_or_terracotta = False
        has_acid_green_or_near_black = False

        for idx, line in enumerate(lines, 1):
            s = line.strip()

            # Ignore pattern definitions inside scanner itself
            if "RE_" in line or "re.compile" in line:
                continue

            # 1. Palette Tells
            if cls.RE_TERRACOTTA.search(s):
                has_cream_or_terracotta = True
                findings.append(ClicheFinding(
                    rule_id="CLICHE_PALETTE_TERRACOTTA",
                    description="Detected AI-archetype warm cream or terracotta palette tell.",
                    line_number=idx,
                    snippet=s,
                    severity="VIOLATION"
                ))

            if cls.RE_ACID_GREEN.search(s) or (cls.RE_NEAR_BLACK.search(s) and ("green" in s.lower() or "accent" in s.lower())):
                findings.append(ClicheFinding(
                    rule_id="CLICHE_PALETTE_ACID_DARK",
                    description="Detected AI-archetype near-black with bright acid accent.",
                    line_number=idx,
                    snippet=s,
                    severity="WARNING"
                ))

            # 2. Chrome Tells
            if cls.RE_MIDDLE_DOT.search(s):
                findings.append(ClicheFinding(
                    rule_id="CLICHE_CHROME_MIDDLE_DOT",
                    description="Metadata string joined with middle dot template tell ('A · B · C').",
                    line_number=idx,
                    snippet=s,
                    severity="WARNING"
                ))

            if cls.RE_EM_DASH_LABEL.search(s):
                findings.append(ClicheFinding(
                    rule_id="CLICHE_CHROME_EM_DASH",
                    description="Template label built as 'WORD — fragment' with spaced em dash.",
                    line_number=idx,
                    snippet=s,
                    severity="WARNING"
                ))

            if cls.RE_BUTTON_ARROW.search(s):
                findings.append(ClicheFinding(
                    rule_id="CLICHE_CHROME_BUTTON_ARROW",
                    description="Gratuitous '→' arrow appended to button or link text.",
                    line_number=idx,
                    snippet=s,
                    severity="WARNING"
                ))

            if cls.RE_TRACKED_ALL_CAPS.search(s) or ("eyebrow" in s.lower() and "uppercase" in s.lower()):
                findings.append(ClicheFinding(
                    rule_id="CLICHE_CHROME_TRACKED_EYEBROW",
                    description="Tracked ALL-CAPS eyebrow label above heading.",
                    line_number=idx,
                    snippet=s,
                    severity="VIOLATION"
                ))

            # 3. Layout Tells
            if cls.RE_CARD_SHADOW.search(s):
                findings.append(ClicheFinding(
                    rule_id="CLICHE_LAYOUT_SAAS_CARD_SHADOW",
                    description="SaaS-card kit boilerplate shadow: rgba(0,0,0,0.1).",
                    line_number=idx,
                    snippet=s,
                    severity="WARNING"
                ))

        # Check full-document multi-line patterns
        for match in cls.RE_HEADLINE_SINGLE_ACCENT.finditer(content):
            snippet = match.group(0).strip().replace("\n", " ")
            findings.append(ClicheFinding(
                rule_id="CLICHE_TYPO_SINGLE_WORD_ACCENT",
                description="Accenting just a single word in a headline (common generated tell).",
                snippet=snippet[:100],
                severity="VIOLATION"
            ))

        # v3.2 Loop 63: stamp the source file on every finding here rather than
        # at eight construction sites. The dataclass field defaults to None, so
        # a finding built without a filename still works — it just stays
        # unattributed, exactly as before.
        for _f in findings:
            if _f.filename is None:
                _f.filename = filename or None

        return ClicheAuditResult(
            clean=(len(findings) == 0),
            findings=findings,
            checked_lines=len(lines)
        )
