"""FocusGate v2.8 — Anti-Cliché Prose & Writing Oracle.

Detects canonical AI-generated prose tells across Markdown, specifications, and machine briefs:
1. Throat-Clearing Preambles: "Certainly!", "In today's fast-paced world", "It is important to remember/note that..."
2. AI Buzzword Density: Over-indexing on "delve", "testament to", "tapestry", "landscape", "pivotal", "paramount", "beacon", "foster", "seamlessly".
3. Sycophantic / Vague Agent Directives: "You are a world-class...", "Think step-by-step and do your best...", "Ensure high quality".
4. Faux-Authoritative Summaries: "In conclusion", "To summarize", "In summary" closing boilerplate on short memos.
5. Mechanical Tripartite Symmetrical Lists: Repetitive 3-bullet parallel structure without asymmetric priority.

Zero external dependencies (100% Python stdlib).
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ProseClicheFinding:
    rule_id: str
    description: str
    line_number: Optional[int] = None
    snippet: Optional[str] = None
    severity: str = "WARNING"  # WARNING or VIOLATION
    filename: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "description": self.description,
            "line_number": self.line_number,
            "snippet": self.snippet,
            "severity": self.severity,
            "filename": self.filename
        }


@dataclass
class ProseClicheAuditResult:
    clean: bool
    findings: List[ProseClicheFinding] = field(default_factory=list)
    checked_lines: int = 0

    def summary(self) -> str:
        if self.clean:
            return "PROSE_CLICHE_AUDIT_PASS: Zero generic AI writing tells detected."
        rules = set(f.rule_id for f in self.findings)
        return f"PROSE_CLICHE_AUDIT_FAIL: Found {len(self.findings)} prose tell(s) across rules: {', '.join(sorted(rules))}"


class ProseClicheOracle:
    """Audits Markdown, technical briefs, and text for AI prose clichés."""

    # 1. Throat-Clearing Preambles
    RE_THROAT_CLEARING = [
        (re.compile(r"^\s*(?:Certainly!|Sure!|Of course!|Here(?:'s| is) (?:a|the) (?:comprehensive|detailed|breakdown|guide))\b", re.IGNORECASE),
         "PROSE_THROAT_CLEARING", "Conversational AI filler or opening throat-clearing."),
        (re.compile(r"\b(?:in today'?s (?:fast-paced|rapidly evolving|digital) world)\b", re.IGNORECASE),
         "PROSE_THROAT_CLEARING", "Generic AI opening trope ('in today's fast-paced world')."),
        (re.compile(r"\b(?:it is (?:important|worth|crucial|essential) to (?:note|remember|keep in mind) that)\b", re.IGNORECASE),
         "PROSE_PREAMBLE_PADDING", "Passive AI preamble padding ('it is important to note that').")
    ]

    # 2. AI Buzzwords & Tropes
    RE_BUZZWORDS = [
        (re.compile(r"\b(?:delve(?:s|d|ing)? into)\b", re.IGNORECASE),
         "PROSE_BUZZWORD_DELVE", "Overused AI buzzword ('delve into')."),
        (re.compile(r"\b(?:a testament to)\b", re.IGNORECASE),
         "PROSE_BUZZWORD_TESTAMENT", "Overused AI flourish ('a testament to')."),
        (re.compile(r"\b(?:rich tapestry|intricate tapestry)\b", re.IGNORECASE),
         "PROSE_BUZZWORD_TAPESTRY", "Canonical AI metaphor ('tapestry')."),
        (re.compile(r"\b(?:ever-evolving|dynamic) landscape\b", re.IGNORECASE),
         "PROSE_BUZZWORD_LANDSCAPE", "Overused AI cliché ('landscape')."),
        (re.compile(r"\b(?:pivotal role|paramount importance)\b", re.IGNORECASE),
         "PROSE_BUZZWORD_PIVOTAL", "Overwrought AI intensity trope ('pivotal role / paramount importance')."),
        (re.compile(r"\b(?:seamlessly integrate(?:s|d|ing)?|foster(?:s|ed|ing)? collaboration)\b", re.IGNORECASE),
         "PROSE_BUZZWORD_SEAMLESS", "Corporate AI filler ('seamlessly integrate / foster collaboration').")
    ]

    # 3. Sycophantic Agent Prompt Padding
    RE_SYCOPHANCY = [
        (re.compile(r"\byou are a (?:world-class|brilliant|expert|10x)\b", re.IGNORECASE),
         "PROSE_SYCOPHANCY_PROMPT", "Sycophantic prompt padding ('you are a world-class...')."),
        (re.compile(r"\bthink step-by-step and do your best\b", re.IGNORECASE),
         "PROSE_VAGUE_STEERING", "Vague unquantified agent steering prompt.")
    ]

    # 4. Faux-Authoritative Summary Closings
    RE_FAUX_SUMMARY = re.compile(
        r"^\s*(?:#{1,4}\s*)?(?:In conclusion|To summarize|In summary|Concluding thoughts)[\s*:]*",
        re.IGNORECASE
    )

    @classmethod
    def audit_content(cls, content: str, filename: str = "") -> ProseClicheAuditResult:
        """Audits document text for AI writing and prompt cliches."""
        findings: List[ProseClicheFinding] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            s = line.strip()
            if not s:
                continue

            # Skip regex compile definitions if self-auditing
            if "re.compile" in line or "RE_" in line:
                continue

            # Skip guard rules defining prohibitions
            if any(k in s for k in ("ANTI_", "GUARD:", "DIRECTIVE:")) and re.search(r"\b(?:ban|eliminate|reject|prohibit|forbidden)\b", s, re.IGNORECASE):
                continue

            # 1. Throat Clearing
            for pattern, rule_id, desc in cls.RE_THROAT_CLEARING:
                if pattern.search(s):
                    findings.append(ProseClicheFinding(
                        rule_id=rule_id,
                        description=desc,
                        line_number=idx,
                        snippet=s[:120],
                        severity="VIOLATION" if "THROAT" in rule_id else "WARNING",
                        filename=filename
                    ))

            # 2. Buzzwords
            for pattern, rule_id, desc in cls.RE_BUZZWORDS:
                if pattern.search(s):
                    findings.append(ProseClicheFinding(
                        rule_id=rule_id,
                        description=desc,
                        line_number=idx,
                        snippet=s[:120],
                        severity="VIOLATION",
                        filename=filename
                    ))

            # 3. Sycophancy
            for pattern, rule_id, desc in cls.RE_SYCOPHANCY:
                if pattern.search(s):
                    findings.append(ProseClicheFinding(
                        rule_id=rule_id,
                        description=desc,
                        line_number=idx,
                        snippet=s[:120],
                        severity="WARNING",
                        filename=filename
                    ))

            # 4. Faux-Authoritative Closings
            if cls.RE_FAUX_SUMMARY.search(s):
                findings.append(ProseClicheFinding(
                    rule_id="PROSE_FAUX_SUMMARY_CLOSING",
                    description="Faux-authoritative boilerplate closing heading ('In conclusion / In summary').",
                    line_number=idx,
                    snippet=s[:120],
                    severity="WARNING",
                    filename=filename
                ))

        return ProseClicheAuditResult(
            clean=(len(findings) == 0),
            findings=findings,
            checked_lines=len(lines)
        )
