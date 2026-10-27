"""FocusGate v2.8 — AgentBrief and AgentReceiptBundle contracts.

The delegation unit for the Master Orchestrator.
AgentBrief encodes a single gate's task as a complete LLM system prompt
for dispatch to an external AI session (not a shell subprocess).
AgentReceiptBundle is the immutable proof package returned by the sub-agent.
"""
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timezone


@dataclass
class AgentBrief:
    """Typed delegation contract for one external AI sub-agent session."""
    brief_id: str
    gate_id: str
    facet: str
    task_summary: str          # <= 80 tokens — single executable sentence
    acceptance_criteria: List[str]  # CHECK: / EXPECT: pairs from TracerGate
    upstream_receipts: List[Dict[str, Any]]  # Serialized GateReceipts from dependencies
    context_delta_hash: str    # SHA-256 of SharedContextBus snapshot at dispatch time
    spawn_mode: str = "ai_session"  # Always "ai_session" for external LLM sessions
    max_context_tokens: int = 400  # Max tokens the orchestrator injects (not total prompt)
    timeout_s: float = 300.0   # Hard wall; breach triggers FrictionSensor
    stage_context: Optional[Dict[str, Any]] = None  # e.g. {"stage_index": 2, "total_stages": 4, "stage_name": "Tokens"}
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    delta_resolver: Optional[Callable[[str], Optional[str]]] = None  # Dereferences @delta_id pointers to <=80-token summaries (v2.8 Part 3); never serialized.

    @classmethod
    def create(
        cls,
        gate_id: str,
        facet: str,
        task_summary: str,
        acceptance_criteria: List[str],
        upstream_receipts: Optional[List[Dict[str, Any]]] = None,
        context_delta_hash: str = "",
        spawn_mode: str = "ai_session",
        max_context_tokens: int = 400,
        timeout_s: float = 300.0,
        stage_context: Optional[Dict[str, Any]] = None,
        delta_resolver: Optional[Callable[[str], Optional[str]]] = None,
    ) -> 'AgentBrief':
        return cls(
            brief_id=str(uuid.uuid4()),
            gate_id=gate_id,
            facet=facet,
            task_summary=task_summary,
            acceptance_criteria=acceptance_criteria or [],
            upstream_receipts=upstream_receipts or [],
            context_delta_hash=context_delta_hash,
            spawn_mode=spawn_mode,
            max_context_tokens=max_context_tokens,
            timeout_s=timeout_s,
            stage_context=stage_context,
            delta_resolver=delta_resolver,
        )

    def to_prompt(self) -> str:
        """Render a complete LLM system prompt for the external AI sub-agent session.
        
        The rendered prompt contains:
        - The active gate contract (task + acceptance criteria)
        - Upstream receipts (key findings only, not full outputs)
        - Stage Progress Anchor preventing stage-dropping
        - Mandatory 4-Pass Implementation Rigor Directive (/unlazy hardening)
        - Context bus snapshot hash for cache coherence
        - Strict ephemeral session instructions
        """
        lines = [
            f"# FocusGate Sub-Agent Brief [{self.brief_id[:8]}]",
            f"\n## Gate Contract",
            f"gate_id: {self.gate_id}",
            f"facet: {self.facet}",
        ]

        if self.stage_context:
            cur = self.stage_context.get("stage_index", 1)
            tot = self.stage_context.get("total_stages", 1)
            name = self.stage_context.get("stage_name", "Execution")
            lines.append(f"\n## Stage Progress Anchor")
            lines.append(f"[STAGE MATRIX: Stage {cur} of {tot} — {name}] (Do NOT drop or confuse active stage)")

        lines += [
            f"\n## Task",
            self.task_summary,
            f"\n## Acceptance Criteria",
        ]
        for criterion in self.acceptance_criteria:
            lines.append(f"- {criterion}")

        if self.upstream_receipts:
            from .tokens import estimate_tokens as _estimate_tokens
            header = "## Upstream Context (from dependency gates)"
            lines.append(f"\n{header}")
            try:
                from .context_policy import brief_budget as _budget
                budget = _budget(self.facet)
            except Exception:
                budget = 400
            used = _estimate_tokens(header)

            def _clip(text: str, max_tokens: int) -> str:
                if _estimate_tokens(text) <= max_tokens:
                    return text
                cut = text[:max(0, max_tokens * 4)]
                sp = cut.rfind(" ")
                if sp > 0:
                    cut = cut[:sp]
                return cut.rstrip() + "…"

            for r in self.upstream_receipts:
                gate = r.get('gate_id', '?')
                status = r.get('status', '?')
                delta_id = r.get('delta_id', '')
                findings = r.get('key_findings', []) or []
                body = None
                if delta_id and self.delta_resolver:
                    try:
                        body = self.delta_resolver(delta_id)
                    except Exception:
                        body = None
                if not body:
                    body = "; ".join(findings[:2])
                if not body:
                    body = f"(upstream {gate} settled; no summary available)"
                ref = f" (ref @{delta_id[:8]})" if delta_id else ""
                entry = f"- {gate} [{status}]: {body}{ref}"
                remaining = budget - used
                if _estimate_tokens(entry) > remaining:
                    if remaining < 12:
                        break
                    entry = _clip(entry, remaining)
                lines.append(entry)
                used += _estimate_tokens(entry)
                if used >= budget:
                    break

        from . import brief_composer as _bc
        from .tokens import estimate_tokens as _est
        from .context_policy import brief_budget as _bb
        _sec_start = next((i for i, l in enumerate(lines) if l.lstrip().startswith("## Upstream Context")), None)
        _used_up = _est("\n".join(lines[_sec_start:])) if _sec_start is not None else 0
        facet_section_text = _bc.facet_section(self.facet, min(_bb(self.facet), 400) - _used_up)
        if facet_section_text:
            lines.append(f"\n{facet_section_text}")
        lines += _bc.rigor_block(self.facet)
        lines += _bc.fallback_block(self.facet, bool(facet_section_text))
        lines += _bc.evidence_block(self.gate_id, self.acceptance_criteria)

        lines += [
            f"\n## Ephemeral Session Rules",
            "- Complete the gate contract above. Do not attempt work outside it.",
            "- Report output as a JSON AgentReceiptBundle when done.",
            f"- Context bus hash at dispatch: {self.context_delta_hash[:16] or 'none'}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "briefId": self.brief_id,
            "gateId": self.gate_id,
            "facet": self.facet,
            "taskSummary": self.task_summary,
            "acceptanceCriteria": self.acceptance_criteria,
            "upstreamReceipts": self.upstream_receipts,
            "contextDeltaHash": self.context_delta_hash,
            "spawnMode": self.spawn_mode,
            "maxContextTokens": self.max_context_tokens,
            "timeoutS": self.timeout_s,
            "createdAt": self.created_at,
        }


@dataclass
class AgentReceiptBundle:
    """Immutable proof package returned by a sub-agent to the orchestrator.
    
    Contains all evidence produced during an external AI session.
    The orchestrator feeds this into OrchestratorProofTree for tier-4
    coherence verification before merging to the main branch.
    """
    bundle_id: str
    gate_id: str
    brief_id: str                      # Links back to the dispatching AgentBrief
    gate_receipts: List[Dict[str, Any]] # Serialized GateReceipts
    delta_ids: List[str]               # ContextBus delta IDs emitted by this agent
    artifacts_produced: List[str]      # Absolute file paths written
    patch_hashes: List[str]            # SHA-256(patch content) per artifact, for collision detection
    status: str = "PENDING"            # PENDING | PASS | FAIL | DLQ
    error_message: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(
        cls,
        gate_id: str,
        brief_id: str,
        gate_receipts: Optional[List[Dict[str, Any]]] = None,
        delta_ids: Optional[List[str]] = None,
        artifacts_produced: Optional[List[str]] = None,
        patch_contents: Optional[List[str]] = None,  # Raw content for hashing
    ) -> 'AgentReceiptBundle':
        patch_hashes = [
            hashlib.sha256(p.encode()).hexdigest()
            for p in (patch_contents or [])
        ]
        return cls(
            bundle_id=str(uuid.uuid4()),
            gate_id=gate_id,
            brief_id=brief_id,
            gate_receipts=gate_receipts or [],
            delta_ids=delta_ids or [],
            artifacts_produced=artifacts_produced or [],
            patch_hashes=patch_hashes,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bundleId": self.bundle_id,
            "gateId": self.gate_id,
            "briefId": self.brief_id,
            "gateReceipts": self.gate_receipts,
            "deltaIds": self.delta_ids,
            "artifactsProduced": self.artifacts_produced,
            "patchHashes": self.patch_hashes,
            "status": self.status,
            "errorMessage": self.error_message,
            "createdAt": self.created_at,
        }
