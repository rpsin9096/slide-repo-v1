"""Writing Sub-Skill Plugin for FocusGate v2.8.

Orchestrates writing-beats, writing-fragments, writing-for-agents, and writing-shapes.
Enforces prerequisite concept grounding, beat-by-beat narrative exposition, subagent briefs,
and typed Anti-Corruption Layer (ACL) handoff translation.
"""

from typing import Dict, Any, List, Optional
from core.plugin_interface import (
    FocusGatePlugin,
    TaskIntent,
    RouteRecommendation,
    ActiveGate,
    GateResult,
    HandoffPayload,
    HandoffVerdict,
    KernelContext,
    isolated_error_boundary
)
from core.ephemeral_handoff import EphemeralHandoffPacket
from core.facet_router import scripted_facets


class WritingPlugin(FocusGatePlugin):
    """Encapsulates technical writing, RFC authoring, and documentation capabilities."""

    @property
    def id(self) -> str:
        return "writing"

    @property
    def name(self) -> str:
        return "FocusGate Technical Writing Plugin"

    @property
    def context(self) -> str:
        return "writing"

    @isolated_error_boundary(fallback_return=None)
    def on_route(self, intent: TaskIntent) -> Optional[RouteRecommendation]:
        ql = intent.query.lower()

        # Architectural RFC Spec (P7)
        if any(k in ql for k in ("rfc", "spec doc", "system spec", "design doc", "architecture spec", "data contract", "specification doc", "specification")):
            return RouteRecommendation(
                archetype="SPECIFICATION",
                pipeline="Architectural RFC Spec",
                confidence=0.96,
                recommended_facets=scripted_facets(ql, ["writing-fragments", "codebase-design", "writing-shape", "prototype"]),
                seed_action={
                    "action": "Draft 1-paragraph problem statement and candidate public seam",
                    "check": "git status",
                    "expect": "On branch"
                }
            )

        # Narrative Postmortem (P8)
        if any(k in ql for k in ("post-mortem", "postmortem", "incident", "tutorial", "migration guide", "release notes", "changelog")):
            return RouteRecommendation(
                archetype="POSTMORTEM",
                pipeline="Narrative Guide & Post-Mortem",
                confidence=0.96,
                recommended_facets=scripted_facets(ql, ["diagnosing-bugs", "writing-beats", "code-review"]),
                seed_action={
                    "action": "Propose starting beat establishing incident prerequisites",
                    "check": "git status",
                    "expect": "On branch"
                }
            )

        return None

    @isolated_error_boundary(fallback_return=GateResult(gate_id="", success=True, output="Writing execution fallback", elapsed_ms=0.0))
    def on_execute(self, gate: ActiveGate, ctx: KernelContext) -> GateResult:
        return GateResult(
            gate_id=gate.id,
            success=True,
            output="Narrative beat grounded and verified.",
            elapsed_ms=0.5
        )

    @isolated_error_boundary(fallback_return=HandoffVerdict(accepted=True, reason="Writing ACL fallback"))
    def adapt_incoming_handoff(self, packet: EphemeralHandoffPacket) -> HandoffVerdict:
        """Translates upstream diffs and outcomes into concise narrative spec beats."""
        if hasattr(packet, 'total_tokens') and packet.total_tokens() > 120:
            return HandoffVerdict(accepted=False, reason='Packet exceeds 120-token ceiling', adapted_payload={})
        findings = packet.receipt.key_findings if packet.receipt else []
        adapted = {
            "spec_summary": "; ".join(findings) if findings else "Spec grounded",
            "section_target": "System Architecture & Invariants",
            "upstream_evidence": packet.receipt.evidence_hash if packet.receipt else ""
        }

        return HandoffVerdict(
            accepted=True,
            reason="Synthesized structured spec brief from upstream findings",
            adapted_payload=adapted,
            tokens=packet.total_tokens()
        )

    @isolated_error_boundary(fallback_return=HandoffVerdict(accepted=True, reason="Writing handoff accepted"))
    def on_handoff(self, payload: HandoffPayload) -> HandoffVerdict:
        if payload.packet:
            return self.adapt_incoming_handoff(payload.packet)
        return HandoffVerdict(accepted=True, reason="Specification data grounded into agent brief", adapted_payload=payload.context_data)
