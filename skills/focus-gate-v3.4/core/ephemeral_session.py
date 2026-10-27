"""Ephemeral Session Isolation Engine for FocusGate v2.8.

Enforces zero-waste, ephemeral session boundaries for sub-skills.
Each sub-skill starts with a pristine context containing only the active gate
contract, scoped domain anchors, and a compact upstream receipt (<= 150 tokens).
Upon completion, working memory is reaped and only an immutable GateReceipt is persisted.
"""

import uuid
import hashlib
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from .session_dag import SessionBranchDAG


@dataclass
class GateReceipt:
    """Immutable, compact proof receipt produced upon ephemeral session completion."""
    session_id: str
    gate_id: str
    facet: str
    status: str  # "PASS" | "FAIL"
    key_findings: List[str] = field(default_factory=list)
    artifacts_produced: List[str] = field(default_factory=list)
    evidence_hash: str = ""
    elapsed_ms: float = 0.0
    tokens_used: int = 0

    def __post_init__(self):
        # Enforce strict 3-item ceiling on findings to prevent receipt bloat
        if len(self.key_findings) > 3:
            self.key_findings = self.key_findings[:3]
        if not self.evidence_hash:
            payload = f"{self.session_id}:{self.gate_id}:{self.status}:{','.join(self.artifacts_produced)}"
            self.evidence_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def estimate_tokens(self) -> int:
        """Heuristic token estimation (~4 chars/token). Enforces <= 150 tokens."""
        text = f"{self.session_id} {self.gate_id} {self.facet} {self.status} " + " ".join(self.key_findings) + " " + " ".join(self.artifacts_produced)
        from .tokens import estimate_tokens as _estimate_tokens
        return _estimate_tokens(text)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "gate_id": self.gate_id,
            "facet": self.facet,
            "status": self.status,
            "key_findings": self.key_findings,
            "artifacts_produced": self.artifacts_produced,
            "evidence_hash": self.evidence_hash,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "tokens_used": self.tokens_used,
        }


@dataclass
class EphemeralSessionContext:
    """Isolated context seed provided to a sub-skill execution sandbox."""
    session_id: str
    facet: str
    gate_contract: Dict[str, Any]
    upstream_receipt: Optional[GateReceipt] = None
    scoped_anchors: Dict[str, str] = field(default_factory=dict)
    max_prompt_tokens: int = 1500
    transient_memory: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class EphemeralSession:
    """Encapsulates a single ephemeral sub-skill session with clean context boundaries."""

    def __init__(self, ctx: EphemeralSessionContext):
        self.ctx = ctx
        self._is_reaped = False

    @property
    def session_id(self) -> str:
        return self.ctx.session_id

    @property
    def facet(self) -> str:
        return self.ctx.facet

    def build_clean_prompt(self) -> str:
        """Constructs a minimal, self-contained prompt bounded under max_prompt_tokens."""
        if self._is_reaped:
            raise RuntimeError(f"Cannot build prompt for reaped session {self.session_id}")

        gc = self.ctx.gate_contract
        lines = [
            f"▶ ACTIVE CONTRACT: [Gate: {gc.get('id', 'unknown')}] [Facet: {self.ctx.facet}] [Est: {gc.get('est_minutes', 15)}m]",
            f"Check: {gc.get('check', 'N/A')} | Expect: {gc.get('expect', 'N/A')}",
            f"■ SCOPED GOAL: {gc.get('title', 'Execute active gate')}",
        ]

        # Inject upstream receipt if present (strictly bounded)
        if self.ctx.upstream_receipt:
            rec = self.ctx.upstream_receipt
            findings_str = "; ".join(rec.key_findings) if rec.key_findings else "None"
            lines.append(f"Upstream Receipt ({rec.facet}): [{rec.status}] Findings: {findings_str}")

        # Inject scoped domain anchors (only relevant terms, no global dictionary dumps)
        if self.ctx.scoped_anchors:
            anchor_defs = [f"{k}: {v}" for k, v in self.ctx.scoped_anchors.items()]
            lines.append(f"Domain Anchors: {', '.join(anchor_defs)}")

        lines.append("Next: Perform isolated verification and emit observable command output.")
        prompt = "\n".join(lines)
        return prompt

    def reap(
        self,
        success: bool,
        output: str,
        artifacts: Optional[List[str]] = None,
        key_findings: Optional[List[str]] = None,
        elapsed_ms: float = 0.0,
    ) -> GateReceipt:
        """Purges transient working memory and extracts an immutable GateReceipt."""
        if self._is_reaped:
            raise RuntimeError(f"Session {self.session_id} has already been reaped.")

        findings = key_findings or []
        if not findings and output:
            # Extract first line or clean summary
            first_line = output.strip().splitlines()[0] if output.strip() else "Execution finished"
            findings = [first_line[:120]]

        from .tokens import estimate_tokens as _estimate_tokens
        receipt = GateReceipt(
            session_id=self.session_id,
            gate_id=self.ctx.gate_contract.get("id", "unknown"),
            facet=self.ctx.facet,
            status="PASS" if success else "FAIL",
            key_findings=findings,
            artifacts_produced=artifacts or [],
            elapsed_ms=elapsed_ms,
            tokens_used=_estimate_tokens(self.build_clean_prompt())
        )

        # Clear transient working memory completely
        self.ctx.transient_memory.clear()
        self._is_reaped = True
        return receipt


class EphemeralSessionManager:
    """Manages the lifecycle of ephemeral sub-skill sessions and receipt chains."""

    def __init__(self, workspace_root: str = ".", context_bus=None):
        self.workspace_root = workspace_root
        self.active_sessions: Dict[str, EphemeralSession] = {}
        self.receipt_ledger: List[GateReceipt] = []
        self._dag = SessionBranchDAG()
        self._context_bus = context_bus

    def spawn_session(
        self,
        facet: str,
        active_gate: Any,
        upstream_receipt: Optional[GateReceipt] = None,
        scoped_anchors: Optional[Dict[str, str]] = None,
    ) -> EphemeralSession:
        """Spawns an isolated session with clean context and zero baggage."""
        session_id = f"eph-{uuid.uuid4().hex[:8]}"

        gate_contract = {
            "id": getattr(active_gate, "id", str(active_gate.get("id", "gate-0") if isinstance(active_gate, dict) else active_gate)),
            "title": getattr(active_gate, "title", str(active_gate.get("title", "") if isinstance(active_gate, dict) else "")),
            "check": getattr(active_gate, "check", str(active_gate.get("check", "") if isinstance(active_gate, dict) else "")),
            "expect": getattr(active_gate, "expect", str(active_gate.get("expect", "") if isinstance(active_gate, dict) else "")),
            "est_minutes": getattr(active_gate, "est_minutes", 15 if not isinstance(active_gate, dict) else active_gate.get("est_minutes", 15)),
        }

        # v2.8: no implicit fallback — unrelated gates start sterile.
        # Only explicit upstream_receipt (direct DAG edge) propagates state.

        ctx = EphemeralSessionContext(
            session_id=session_id,
            facet=facet,
            gate_contract=gate_contract,
            upstream_receipt=upstream_receipt,
            scoped_anchors=scoped_anchors or {},
        )

        session = EphemeralSession(ctx)
        self.active_sessions[session_id] = session
        self._dag.checkpoint({'session_id': session.session_id, 'facet': facet, 'gate_id': active_gate.id if hasattr(active_gate, 'id') else str(active_gate)})
        return session

    def close_and_reap(
        self,
        session_id: str,
        success: bool,
        output: str,
        artifacts: Optional[List[str]] = None,
        key_findings: Optional[List[str]] = None,
        elapsed_ms: float = 0.0,
    ) -> GateReceipt:
        """Reaps the session memory and persists the receipt to ledger."""
        session = self.active_sessions.pop(session_id, None)
        if not session:
            raise KeyError(f"No active ephemeral session with ID {session_id}")

        receipt = session.reap(
            success=success,
            output=output,
            artifacts=artifacts,
            key_findings=key_findings,
            elapsed_ms=elapsed_ms,
        )
        self.receipt_ledger.append(receipt)
        self._dag.checkpoint({'session_id': session_id, 'status': 'PASS' if success else 'FAIL', 'receipt_hash': receipt.evidence_hash})

        if self._context_bus is not None:
            try:
                from .context_bus import ContextDeltaEvent, CONTEXT_DELTA_MAX_TOKENS
                findings_str = '; '.join((receipt.key_findings or [])[:2])
                content = f"{receipt.gate_id} [{receipt.status}]: {findings_str}"
                content = content[:CONTEXT_DELTA_MAX_TOKENS * 4]
                delta = ContextDeltaEvent.create(
                    source_agent=receipt.gate_id,
                    delta_type="RECEIPT",
                    content=content,
                )
                self._context_bus.publish(delta)
            except Exception as e:
                import sys
                print(f"[FocusGate] Bus publish failed: {e}", file=sys.stderr)

        return receipt

    def get_last_receipt(self) -> Optional[GateReceipt]:
        return self.receipt_ledger[-1] if self.receipt_ledger else None

    def cleanup_expired_sessions(self, max_age_hours: float = 24.0) -> List[str]:
        """Reaps and evicts expired or abandoned ephemeral sessions exceeding max_age_hours."""
        now = time.time()
        max_age_s = max_age_hours * 3600.0
        expired_ids = []
        for sid, sess in list(self.active_sessions.items()):
            age = now - sess.ctx.created_at
            if age > max_age_s:
                try:
                    sess.ctx.transient_memory.clear()
                    sess._is_reaped = True
                except (AttributeError, KeyError):
                    pass
                del self.active_sessions[sid]
                expired_ids.append(sid)

        if hasattr(self, "_dag") and self._dag:
            try:
                self._dag.prune_stale_branches()
            except (AttributeError, KeyError, RuntimeError):
                pass

        return expired_ids

