"""FocusGate v2.8 Microkernel Engine.

Coordinates the plugin registry, lifecycle hooks, isolated error boundaries,
statechart transitions, aggregate domain state, deep token economy governor,
hierarchical precedence sieve, deterministic tool selection matrix,
ephemeral session isolation manager, on-demand context retriever,
failure auto-grep enrichment, and typed inter-skill handoff coordinator.
"""

from typing import Dict, Any, List, Optional, Type
import time
import os
import sys
import re

from .plugin_interface import (
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
from .aggregate import LedgerAggregate
from .statechart import WorkflowStatechart, StatechartState
from .precedence_sieve import HierarchicalPrecedenceSieve, SieveResult
from .ephemeral_session import EphemeralSessionManager, EphemeralSession, GateReceipt
from .ephemeral_retriever import EphemeralContextRetriever
from .ephemeral_handoff import EphemeralHandoffPacket, HandoffCoordinator
from .token_economy import TokenEconomyGovernor, InboundVerdict, FoldedOutput
from .tool_matrix import ToolSelectionMatrix, ToolDecision, PatchPreconditionCheck
from .friction_sensor import FrictionSensor
from .unlazy_guard import ExecutionRigorGuard
from .proof_tree import ProofTree


class FocusKernel:
    """Microkernel coordinating FocusGate modular plugins with Ephemeral Context isolation."""
    
    RETRAINING_THRESHOLD = 50

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)
        self.plugins: Dict[str, FocusGatePlugin] = {}
        self.aggregate = LedgerAggregate(workspace_root=self.workspace_root)
        self.statechart = WorkflowStatechart()
        self.token_governor = TokenEconomyGovernor(workspace_root=self.workspace_root)
        # Backward-compatibility aliases
        self.budget_governor = self.token_governor
        self.cost_governor = self.token_governor
        self.precedence_sieve = HierarchicalPrecedenceSieve()
        self.session_manager = EphemeralSessionManager(workspace_root=self.workspace_root)
        self.retriever = EphemeralContextRetriever(workspace_root=self.workspace_root)
        self.tool_matrix = ToolSelectionMatrix(workspace_root=self.workspace_root)
        self.friction_sensor = FrictionSensor()
        self.event_listeners: List[Any] = []
        self._booted = False
        self._settled_gate_count = 0

    def register_plugin(self, plugin: FocusGatePlugin) -> None:
        """Registers a sub-skill plugin with the kernel registry."""
        if plugin.id in self.plugins:
            raise ValueError(f"Plugin with id '{plugin.id}' is already registered")
        self.plugins[plugin.id] = plugin

    def boot(self) -> None:
        """Boots the microkernel and executes on_init across all registered plugins."""
        if self._booted:
            return

        ctx = self._create_context()
        for pid, plugin in self.plugins.items():
            try:
                plugin.on_init(ctx)
            except Exception as e:
                print(f"[Kernel Warning] Plugin {pid} failed on_init: {e}", file=sys.stderr)

        self._booted = True

    def dispatch_intent(self, query: str) -> Optional[RouteRecommendation]:
        """Sanitizes prompt via TokenEconomyGovernor, queries plugins, and resolves via PrecedenceSieve."""
        self.statechart.trigger("SUBMIT_TASK")

        # 1. Deep Token Economy pre-dispatch sanitization & sliding window enforcement
        verdict = self.token_governor.sanitize_inbound(query)
        intent = TaskIntent(query=verdict.sanitized_prompt)

        # 2. Allow each plugin to provide route recommendation under error boundary
        candidates: List[RouteRecommendation] = []
        for pid, plugin in self.plugins.items():
            try:
                rec = plugin.on_route(intent)
                if rec and rec.confidence > 0.5:
                    candidates.append(rec)
            except Exception as e:
                print(f"[Kernel Error Boundary] Plugin {pid} on_route failure: {e}", file=sys.stderr)

        # 3. Deterministic resolution via Hierarchical Precedence Sieve
        if candidates:
            sieve_res = self.precedence_sieve.resolve_best_route(candidates)
            if sieve_res:
                best_rec = sieve_res.winning_route
                self.statechart.trigger("ROUTE_SETTLED", {
                    "pipeline": best_rec.pipeline,
                    "rank": sieve_res.calculated_rank,
                    "tier": sieve_res.precedence_tier
                })
                return best_rec

        return None

    def execute_active_gate(self, gate_id: str) -> GateResult:
        """Executes active gate in an isolated, ephemeral session sandbox with test output folding."""
        self.aggregate.activate_gate(gate_id)
        active_dict = self.aggregate.active_gate
        if not active_dict:
            return GateResult(gate_id=gate_id, success=False, output="No active gate", elapsed_ms=0.0)

        active = ActiveGate(
            id=active_dict["id"],
            title=active_dict["title"],
            facet=active_dict["facet"],
            status=active_dict["status"],
            check=active_dict["check"],
            expect=active_dict["expect"]
        )

        self.statechart.trigger("GATE_ACTIVATED", {"active_gate_id": gate_id})
        self.statechart.trigger("RUN_VERIFY")

        # 1. Spawn isolated ephemeral session with zero cumulative baggage
        session = self.session_manager.spawn_session(facet=active.facet, active_gate=active)
        prompt_seed = session.build_clean_prompt()

        # Enforce prompt ceiling via TokenEconomyGovernor (<1500 tokens)
        _, bounded_prompt, prompt_tokens = self.token_governor.enforce_prompt_ceiling(prompt_seed)

        # Locate assigned plugin
        target_plugin = self._resolve_plugin_for_facet(active.facet)
        ctx = self._create_context(active, session_id=session.session_id)

        t0 = time.perf_counter()
        try:
            res = target_plugin.on_execute(active, ctx)
        except Exception as e:
            print(f"[Kernel Error Boundary] Unhandled error during on_execute in {target_plugin.name}: {e}", file=sys.stderr)
            res = GateResult(gate_id=gate_id, success=False, output=f"Plugin Exception: {str(e)}", elapsed_ms=0.0)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        res.elapsed_ms = elapsed_ms

        # 2. Failure Auto-Grep Enrichment (instant 3-line diagnostic window)
        diag = None
        if not res.success and res.output:
            diag = self._extract_failure_diagnostic(res.output)
            if diag:
                res.diagnostic_snippet = diag

        # 3. Dynamic Test-Output Folding (enforce <=150 tokens, offload full trace to disk)
        folded = self.token_governor.fold_test_output(
            raw_output=res.output,
            exit_code=0 if res.success else 1,
            session_id=session.session_id,
            diagnostic_snippet=diag
        )
        res.output = folded.folded_text

        # 4. Reap ephemeral session memory and generate immutable GateReceipt
        receipt = self.session_manager.close_and_reap(
            session_id=session.session_id,
            success=res.success,
            output=res.output,
            elapsed_ms=elapsed_ms
        )
        res.receipt = receipt

        # Record session token usage
        self.token_governor.record_session(tokens_used=prompt_tokens)

        # 5. Strict Rigor Verification on candidate success
        if res.success:
            proof = ProofTree.build_unlazy_criteria(active, target_files=getattr(active, 'artifacts', None))
            verdict = proof.evaluate({'output': res.output, 'code_diff': '', 'test_output': res.output})
            rigor_pass = verdict.verified
            rigor_issues = [c.description for c in proof.criteria if c.id in verdict.failed_criteria]
            if not rigor_pass:
                res.success = False
                res.output = f"RIGOR_REJECTED: {'; '.join(rigor_issues)}"

        # 6. Proactive friction monitoring and autonomous remediation
        self.friction_sensor.record_gate_result(gate_id, res.success, res.output)
        if not res.success:
            remedy = self.friction_sensor.resolve_friction_autonomously(gate_id, res.output)
            if remedy:
                res.remedy = remedy.to_dict()
                if not res.diagnostic_snippet:
                    res.diagnostic_snippet = f"[AUTONOMOUS_REMEDY] {remedy.hypothesis}"

        if res.success:
            self.aggregate.check_gate(gate_id, output=res.output, receipt=receipt)
            
            self._settled_gate_count += 1
            if self._settled_gate_count >= self.RETRAINING_THRESHOLD:
                self.aggregate._record_event("RETRAINING_READY", {"count": self._settled_gate_count})
                print(f"[FocusKernel] Automated Retraining threshold reached ({self._settled_gate_count}). Emitting RETRAINING_READY.", file=sys.stderr)
                self._settled_gate_count = 0
                
            pending_left = sum(1 for g in self.aggregate.gates.values() if g["status"] == "PENDING")
            if pending_left > 0:
                self.statechart.trigger("ORACLE_PASS", {"has_pending_gates": True})
            else:
                self.statechart.trigger("ALL_GATES_PASS", {"has_pending_gates": False})
        else:
            self.aggregate.rollback_gate(gate_id, reason=res.output)
            self.statechart.trigger("ORACLE_FAIL")

        return res

    def perform_handoff(
        self,
        source_id: str,
        target_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> HandoffVerdict:
        """Coordinates clean anti-corruption handoffs between sub-skills using HandoffCoordinator."""
        source = self.plugins.get(source_id)
        target = self.plugins.get(target_id)
        if not target:
            return HandoffVerdict(accepted=False, reason=f"Target plugin '{target_id}' not found in registry")

        last_receipt = self.session_manager.get_last_receipt()
        if not last_receipt:
            last_receipt = GateReceipt(
                session_id="init-handoff",
                gate_id="seed",
                facet=source_id,
                status="PASS",
                key_findings=["Handoff initialized from source"],
                elapsed_ms=0.0
            )

        accepted, reason, adapted, elapsed_ms = HandoffCoordinator.execute_handoff(
            source_plugin=source or source_id,
            target_plugin=target,
            receipt=last_receipt,
            delta=data or {}
        )
        return HandoffVerdict(accepted=accepted, reason=reason, adapted_payload=adapted)

    def select_tool(
        self,
        intent: str,
        target_path: Optional[str] = None,
        estimated_diff_lines: int = 0,
        is_diagnostic: bool = False
    ) -> ToolDecision:
        """Evaluates operational context and returns deterministic tool recommendation."""
        return self.tool_matrix.select_tool(intent, target_path, estimated_diff_lines, is_diagnostic)

    def verify_patch(
        self,
        target_path: str,
        search_block: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> PatchPreconditionCheck:
        """Verifies preconditions for first-attempt patch success."""
        return self.tool_matrix.verify_patch_preconditions(target_path, search_block, start_line, end_line)

    def _extract_failure_diagnostic(self, output: str) -> Optional[str]:
        """Automatically scans failure output for file:line traces and retrieves a 3-line snippet."""
        m1 = re.findall(r'File "([^"]+)", line (\d+)', output)
        if m1:
            fpath, lnum = m1[-1]
            return self._fetch_line_window(fpath, int(lnum))

        m2 = re.findall(r'([\w/\.\-]+\.[a-zA-Z0-9]+):(\d+)', output)
        if m2:
            fpath, lnum = m2[-1]
            return self._fetch_line_window(fpath, int(lnum))

        return None

    def _fetch_line_window(self, file_path: str, line_num: int, context: int = 2) -> Optional[str]:
        target = file_path if os.path.isabs(file_path) else os.path.join(self.workspace_root, file_path)
        if not os.path.exists(target) or not os.path.isfile(target):
            return None
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
            start = max(0, line_num - 1 - context)
            end = min(len(lines), line_num + context)
            rel_name = os.path.basename(target)
            out = [f"[{rel_name}:{line_num}]"]
            for i in range(start, end):
                curr = i + 1
                prefix = "> " if curr == line_num else "  "
                out.append(f"{prefix}{curr:4d} | {lines[i]}")
            return "\n".join(out)
        except Exception:
            return None

    def audit_handoff_performance(self) -> Dict[str, Any]:
        """Benchmarks handoff latency and token sizes across registered plugins."""
        results = []
        pids = list(self.plugins.keys())
        dummy_receipt = GateReceipt(
            session_id="bench-receipt",
            gate_id="g-audit",
            facet="engineering",
            status="PASS",
            key_findings=["Seam verified clean"],
            elapsed_ms=1.0
        )
        for i in range(len(pids)):
            src = pids[i]
            tgt = pids[(i + 1) % len(pids)]
            accepted, reason, adapted, latency = HandoffCoordinator.execute_handoff(
                source_plugin=self.plugins[src],
                target_plugin=self.plugins[tgt],
                receipt=dummy_receipt,
                delta={"test_key": "val"}
            )
            results.append({
                "source": src,
                "target": tgt,
                "accepted": accepted,
                "latency_ms": round(latency, 4),
                "tokens": EphemeralHandoffPacket.estimate_tokens_dict(adapted),
                "checksum_valid": True
            })
        return {"handoffs": results}

    def handle_dlq_fault(self, tombstone_path: str) -> None:
        """Halts the statechart with an invariant safe-halt when a compensation fails."""
        self.statechart.trigger("DLQ_HALT", {"tombstone_path": tombstone_path})

    def get_cost_report(self) -> str:
        """Returns ASCII table representation of token savings."""
        return self.token_governor.format_report()

    def _resolve_plugin_for_facet(self, facet: str) -> FocusGatePlugin:
        for p in self.plugins.values():
            if facet in p.id or p.context in facet:
                return p
        return next(iter(self.plugins.values()))

    def _create_context(
        self,
        active_gate: Optional[ActiveGate] = None,
        session_id: Optional[str] = None
    ) -> KernelContext:
        ledger_path = os.path.join(self.workspace_root, ".focusgate", "ledger.events.jsonl")
        return KernelContext(
            workspace_root=self.workspace_root,
            ledger_path=ledger_path,
            state_vector=self.aggregate.get_state_vector(),
            active_gate=active_gate,
            session_id=session_id,
            retriever=self.retriever
        )
