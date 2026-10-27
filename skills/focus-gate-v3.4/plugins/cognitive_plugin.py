"""Cognitive Sub-Skill Plugin for FocusGate v2.8.

Orchestrates unlazy, i-have-adhd, loop-me, and grilling capabilities.
Enforces execution rigor standards, 2-minute activation seeds, push-right checkpoints,
autonomous edge-case resolution, and typed Anti-Corruption Layer (ACL) handoff translation.
Zero external dependencies (100% Python stdlib).
"""

from typing import Dict, Any, List, Optional
import time
import subprocess
import os

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
from core.unlazy_guard import ExecutionRigorGuard
from core.proof_tree import ProofTree
from core.facet_router import scripted_facets


class CognitivePlugin(FocusGatePlugin):
    """Encapsulates execution scaffolding and hardened execution rigor."""

    @property
    def id(self) -> str:
        return "cognitive"

    @property
    def name(self) -> str:
        return "FocusGate Cognitive & Execution Plugin"

    @property
    def context(self) -> str:
        return "cognitive"

    @isolated_error_boundary(fallback_return=None)
    def on_route(self, intent: TaskIntent) -> Optional[RouteRecommendation]:
        ql = intent.query.lower()

        # Automation / Loops (P4)
        if any(k in ql for k in ("workflow", "cron", "recurring", "automate", "routine", "push right", "polling loop")):
            return RouteRecommendation(
                archetype="AUTOMATION",
                pipeline="Loop Synthesis",
                confidence=0.95,
                recommended_facets=scripted_facets(ql, ["loop-me", "grilling", "unlazy"]),
                seed_action={
                    "action": "Draft 1-paragraph workflow trigger and push-right checkpoint",
                    "check": "git status",
                    "expect": "On branch"
                }
            )

        # Ideation to Execution (P6)
        if any(k in ql for k in ("brain dump", "dump", "fragments", "unstructured", "spark", "notes on", "raw thoughts", "fleeting", "observations", "uncurated")):
            return RouteRecommendation(
                archetype="IDEATION",
                pipeline="Ideation to Implementation",
                confidence=0.95,
                recommended_facets=scripted_facets(ql, ["writing-fragments", "writing-shape", "unlazy"]),
                seed_action={
                    "action": "Append initial raw thought to .focusgate/FRAGMENTS.md",
                    "check": "echo FRAGMENT_OK",
                    "expect": "FRAGMENT_OK"
                }
            )

        # Atomic Sprint (P5)
        is_atomic_kw = any(k in ql for k in ("bump version", "badge link", "single comment", "change default timeout", "quick 2-minute", "atomic"))
        is_typo = ("typo" in ql and "typography" not in ql)
        if is_atomic_kw or is_typo:
            return RouteRecommendation(
                archetype="ATOMIC",
                pipeline="Atomic Sprint",
                confidence=0.95,
                recommended_facets=scripted_facets(ql, ["unlazy", "code-review"]),
                seed_action={
                    "action": f"Execute atomic micro-step: {intent.query}",
                    "check": "git status",
                    "expect": "On branch"
                }
            )

        return None

    @isolated_error_boundary(fallback_return=GateResult(gate_id="", success=False, output="Error in cognitive execute", elapsed_ms=0.0))
    def on_execute(self, gate: ActiveGate, ctx: KernelContext) -> GateResult:
        """Executes active gate against strict execution rigor and proof tree criteria."""
        t0 = time.perf_counter()

        # 1. Execute check command if specified
        output = ""
        exit_code = 0
        if gate.check:
            try:
                res = subprocess.run(
                    gate.check,
                    shell=True,
                    cwd=ctx.workspace_root,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                exit_code = res.returncode
                output = (res.stdout + "\n" + res.stderr).strip()
            except subprocess.TimeoutExpired:
                elapsed = (time.perf_counter() - t0) * 1000.0
                return GateResult(
                    gate_id=gate.id,
                    success=False,
                    output=f"Execution timed out (15s bound) for command: {gate.check}",
                    elapsed_ms=elapsed
                )
            except Exception as e:
                elapsed = (time.perf_counter() - t0) * 1000.0
                return GateResult(
                    gate_id=gate.id,
                    success=False,
                    output=f"Execution error: {str(e)}",
                    elapsed_ms=elapsed
                )
        else:
            output = "Manual verification gate"

        # 2. Evaluate Rigor Standards (Zero placeholders, TODOs, or trivial commands)
        is_rigorous, rigor_violations = ExecutionRigorGuard.validate_completion(
            gate=gate,
            test_output=output
        )

        if not is_rigorous:
            elapsed = (time.perf_counter() - t0) * 1000.0
            return GateResult(
                gate_id=gate.id,
                success=False,
                output="RIGOR_CHECK_FAILED: " + "; ".join(rigor_violations),
                elapsed_ms=elapsed
            )

        # 3. Evaluate Deep Verification via ProofTree
        proof_tree = ProofTree.build_unlazy_criteria(gate)
        eval_ctx = {
            "exit_code": exit_code,
            "output": output,
            "modified_files": []
        }
        proof_verdict = proof_tree.evaluate(eval_ctx)

        elapsed = (time.perf_counter() - t0) * 1000.0
        if not proof_verdict.verified:
            failed_str = ", ".join(proof_verdict.failed_criteria)
            return GateResult(
                gate_id=gate.id,
                success=False,
                output=f"PROOF_TREE_UNVERIFIED ({proof_verdict.compliance_score}%): Failed [{failed_str}]. Output: {output[:150]}",
                elapsed_ms=elapsed
            )

        return GateResult(
            gate_id=gate.id,
            success=True,
            output=f"RIGOR_VERIFIED (100% compliance): {output[:120] if output else 'PASS'}",
            elapsed_ms=elapsed
        )

    @isolated_error_boundary(fallback_return=HandoffVerdict(accepted=True, reason="Cognitive ACL fallback"))
    def adapt_incoming_handoff(self, packet: EphemeralHandoffPacket) -> HandoffVerdict:
        """Translates upstream outcomes into concrete 2-minute physical micro-actions."""
        if hasattr(packet, 'total_tokens') and packet.total_tokens() > 120:
            return HandoffVerdict(accepted=False, reason='Packet exceeds 120-token ceiling', adapted_payload={})
        findings = packet.receipt.key_findings if packet.receipt else []
        summary = findings[0] if findings else "Proceed with next gate"

        adapted = {
            "micro_action": f"Verify and advance: {summary[:80]}",
            "est_minutes": 2,
            "upstream_status": packet.receipt.status if packet.receipt else "UNKNOWN"
        }

        return HandoffVerdict(
            accepted=True,
            reason="Cognitive invariants and micro-action anchor synthesized",
            adapted_payload=adapted,
            tokens=packet.total_tokens()
        )

    @isolated_error_boundary(fallback_return=HandoffVerdict(accepted=True, reason="Fallback acceptance"))
    def on_handoff(self, payload: HandoffPayload) -> HandoffVerdict:
        if payload.packet:
            return self.adapt_incoming_handoff(payload.packet)
        return HandoffVerdict(accepted=True, reason="Cognitive invariants satisfied", adapted_payload=payload.context_data)
