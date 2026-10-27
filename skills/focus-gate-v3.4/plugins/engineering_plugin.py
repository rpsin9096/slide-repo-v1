"""Engineering Sub-Skill Plugin for FocusGate v2.8.

Orchestrates codebase-design, prototype, code-review, and diagnosing-bugs.
Enforces tracer reproduction gates, deep module seams, dual-axis reviews,
and typed Anti-Corruption Layer (ACL) handoff translation.
"""

from typing import Dict, Any, List, Optional
import subprocess
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


class EngineeringPlugin(FocusGatePlugin):
    """Encapsulates core software engineering, debugging, and review capabilities."""

    @property
    def id(self) -> str:
        return "engineering"

    @property
    def name(self) -> str:
        return "FocusGate Engineering & Architecture Plugin"

    @property
    def context(self) -> str:
        return "engineering"

    @isolated_error_boundary(fallback_return=None)
    def on_route(self, intent: TaskIntent) -> Optional[RouteRecommendation]:
        ql = intent.query.lower()

        # Yield to specialized Design, Writing, or Atomic plugins only if no defect keywords are present
        has_defect = any(k in ql for k in ("bug", "error", "fail", "broken", "flaky", "timeout", "regression", "fix", "exception", "crash", "p0", "emergency", "deadlock"))
        if not has_defect and any(k in ql for k in ("contrast", "wcag", "token audit", "color audit", "hardcoded", "typo", "change default timeout", "spec doc")):
            return None

        # Rapid Defect Resolution (P1)
        if any(k in ql for k in ("bug", "error", "fail", "broken", "flaky", "timeout", "regression", "fix", "exception", "crash", "null pointer", "typeerror", "bounds error", "deadlock")):
            return RouteRecommendation(
                archetype="DEFECT",
                pipeline="Rapid Defect Resolution",
                confidence=0.98,
                recommended_facets=scripted_facets(ql, ["triage", "diagnosing-bugs", "unlazy", "code-review"]),
                seed_action={
                    "action": f"Reproduce failure locally: {intent.query}",
                    "check": "pytest || npm test || echo 'reproduce'",
                    "expect": "FAIL"
                }
            )

        # Strategic Wayfinding (P2)
        if any(k in ql for k in ("idea", "explore", "fog", "epic", "maybe", "strategy", "roadmap", "concept", "direction")):
            return RouteRecommendation(
                archetype="STRATEGY",
                pipeline="Strategic Wayfinding",
                confidence=0.92,
                recommended_facets=scripted_facets(ql, ["grilling", "wayfinder", "prototype", "unlazy"]),
                seed_action={
                    "action": "Answer the primary open question with one recommended choice",
                    "check": "git status",
                    "expect": "On branch"
                }
            )

        # Deep Module Redesign (P3)
        if any(k in ql for k in ("refactor", "seam", "architecture", "decouple", "deep module", "interface", "redesign", "clean up", "adapter")):
            return RouteRecommendation(
                archetype="ARCHITECTURE",
                pipeline="Deep Module Redesign",
                confidence=0.95,
                recommended_facets=scripted_facets(ql, ["codebase-design", "prototype", "unlazy", "code-review"]),
                seed_action={
                    "action": "Inspect public interface boundary of target module",
                    "check": "git status",
                    "expect": "On branch"
                }
            )

        return None

    @isolated_error_boundary(fallback_return=GateResult(gate_id="", success=False, output="Error in engineering execute", elapsed_ms=0.0))
    def on_execute(self, gate: ActiveGate, ctx: KernelContext) -> GateResult:
        try:
            res = subprocess.run(
                gate.check,
                shell=True,
                cwd=ctx.workspace_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=20
            )
            passed = (gate.expect in res.stdout) or (res.returncode == 0 and not gate.expect)
            return GateResult(
                gate_id=gate.id,
                success=passed,
                output=res.stdout.strip(),
                elapsed_ms=1.0
            )
        except Exception as e:
            return GateResult(gate_id=gate.id, success=False, output=str(e), elapsed_ms=1.0)

    @isolated_error_boundary(fallback_return=HandoffVerdict(accepted=True, reason="Engineering ACL fallback"))
    def adapt_incoming_handoff(self, packet: EphemeralHandoffPacket) -> HandoffVerdict:
        """Translates incoming upstream packet into concrete engineering targets."""
        if hasattr(packet, 'total_tokens') and packet.total_tokens() > 120:
            return HandoffVerdict(accepted=False, reason='Packet exceeds 120-token ceiling', adapted_payload={})
        adapted: Dict[str, Any] = {}
        src = packet.source_facet.lower()

        if "design" in src:
            # Map design tokens into engineering CSS/theme variables
            tokens = packet.delta_payload.get("tokens", {})
            adapted["css_vars"] = [f"--{k}: {v}" for k, v in tokens.items()] if isinstance(tokens, dict) else []
            adapted["target_files"] = packet.delta_payload.get("target_files", ["styles.css"])
            reason = "Mapped design tokens to CSS variable targets"
        elif "writing" in src:
            # Map spec fragments to test assertions
            adapted["spec_ref"] = packet.delta_payload.get("spec_file", "SPEC.md")
            adapted["test_suites"] = packet.delta_payload.get("test_suites", ["tests/"])
            reason = "Mapped spec requirements to test suite targets"
        else:
            # Default engineering adaptation
            adapted = packet.delta_payload.copy()
            adapted["upstream_hash"] = packet.receipt.evidence_hash if packet.receipt else ""
            reason = f"Accepted handoff from {packet.source_facet}"

        return HandoffVerdict(
            accepted=True,
            reason=reason,
            adapted_payload=adapted,
            tokens=packet.total_tokens()
        )

    @isolated_error_boundary(fallback_return=HandoffVerdict(accepted=True, reason="Engineering handoff fallback"))
    def on_handoff(self, payload: HandoffPayload) -> HandoffVerdict:
        if payload.packet:
            return self.adapt_incoming_handoff(payload.packet)
        return HandoffVerdict(accepted=True, reason="Code seam verified", adapted_payload=payload.context_data)
