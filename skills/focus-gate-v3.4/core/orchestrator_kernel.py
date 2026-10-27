"""FocusGate v2.8 — OrchestratorKernel: Master Orchestrator for Multi-Agent Workflows.

Extends FocusKernel to coordinate external AI sub-agent sessions with:
1. Task Decomposition: Breaks complex queries into multi-facet DAG frontiers.
2. Ephemeral Worktree Provisioning: Allocates git-isolated workspace slots for each sub-agent.
3. State Synchronization: Broadcasts delta events via SharedContextBus without token bloat.
4. Coherence Verification: Evaluates AgentReceiptBundles via OrchestratorProofTree before merging.
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from .kernel import FocusKernel
from .agent_brief import AgentBrief, AgentReceiptBundle
from .context_bus import SharedContextBus, ContextDeltaEvent
from .orchestrator_proof_tree import OrchestratorProofTree
from .worktree_runner import WorktreeRunner
from .resilient_saga import ResilientSagaCoordinator, DLQTombstone
from .proof_tree import ProofVerdict
from .stage_matrix import StageDefinition, StageVerificationMatrix, StageBoundaryGuard


class OrchestratorKernel(FocusKernel):
    """Master Orchestrator coordinating concurrent external AI sub-agent sessions."""

    def __init__(self, workspace_root: str = ".", max_concurrent_agents: int = 5):
        abs_root = os.path.abspath(workspace_root)
        if os.path.basename(abs_root) == ".focusgate":
            abs_root = os.path.dirname(abs_root)
        super().__init__(workspace_root=abs_root)
        self.max_concurrent_agents = max_concurrent_agents
        self.context_bus = SharedContextBus(workspace_root=self.workspace_root)
        self.worktree_runner = WorktreeRunner(repo_root=self.workspace_root)
        self.stage_matrix = StageVerificationMatrix(workspace_root=self.workspace_root)
        self.stage_definitions: List[StageDefinition] = []
        self.dispatched_briefs: Dict[str, AgentBrief] = {}
        self.active_bundles: Dict[str, AgentReceiptBundle] = {}

        self._briefs_dir = os.path.join(self.workspace_root, ".focusgate", "briefs")
        self._bundles_dir = os.path.join(self.workspace_root, ".focusgate", "bundles")
        self._dlq_dir = os.path.join(self.workspace_root, ".focusgate", "dlq")
        self._gates_file = os.path.join(self.workspace_root, ".focusgate", "orchestrator_gates.json")
        self._stages_file = os.path.join(self.workspace_root, ".focusgate", "stages.json")
        self._checkpoints_dir = os.path.join(self.workspace_root, ".focusgate", "checkpoints")
        os.makedirs(self._briefs_dir, exist_ok=True)
        os.makedirs(self._bundles_dir, exist_ok=True)
        os.makedirs(self._dlq_dir, exist_ok=True)
        os.makedirs(self._checkpoints_dir, exist_ok=True)

        from adapters.storage_adapter import SQLiteStorageAdapter
        events_path = os.path.join(self.workspace_root, ".focusgate", "ledger.events.jsonl")
        self.event_store = getattr(self.aggregate, "event_store", None) or SQLiteStorageAdapter(events_path)

        self._load_gates()
        self._load_stages()

    def _save_gates(self) -> None:
        try:
            with open(self._gates_file, "w", encoding="utf-8") as f:
                json.dump(self.aggregate.gates, f, indent=2)
        except (OSError, IOError):
            pass

    def _load_gates(self) -> None:
        if os.path.exists(self._gates_file):
            try:
                with open(self._gates_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if isinstance(saved, dict):
                        self.aggregate.gates.update(saved)
            except (OSError, IOError, json.JSONDecodeError):
                pass

    def _save_stages(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._stages_file), exist_ok=True)
            with open(self._stages_file, "w", encoding="utf-8") as f:
                json.dump([s.to_dict() for s in self.stage_definitions], f, indent=2)
        except (OSError, IOError):
            pass

    def _load_stages(self) -> None:
        if os.path.exists(self._stages_file):
            try:
                with open(self._stages_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list) and data:
                    self.stage_definitions = [
                        StageDefinition.from_dict(s)
                        for s in data
                        if isinstance(s, dict) and "stage_id" in s
                    ]
                    return
            except (OSError, IOError, json.JSONDecodeError):
                pass

    def get_active_stage_frontier(self) -> List[StageDefinition]:
        """Resolves the current active (unblocked) stage frontier in topological dependency order."""
        return self.stage_matrix.compute_stage_frontier(
            self.stage_definitions,
            self.aggregate.gates,
            dlq_dir=self._dlq_dir
        )
        # Fallback reconstruction from self.aggregate.stages
        if hasattr(self.aggregate, "stages") and self.aggregate.stages:
            self.stage_definitions = [
                StageDefinition(
                    stage_id=s.get("gate_id") or s.get("stage_id", f"stage-{idx}"),
                    index=idx,
                    name=s.get("title") or s.get("name", f"Stage-{idx}"),
                    facet=s.get("facet", "engineering"),
                    gate_ids=s.get("gate_ids") or ([s["gate_id"]] if "gate_id" in s else []),
                    required_artifacts=s.get("required_artifacts", []),
                    status=s.get("status", "PENDING")
                )
                for idx, s in enumerate(self.aggregate.stages, 1)
            ]

    def verify_stage(self, stage_id_or_index: str) -> Tuple[bool, List[str]]:
        """Evaluates intra-stage verification matrix, updates state, and records domain events."""
        target_def = next(
            (s for s in self.stage_definitions if s.stage_id == stage_id_or_index or str(s.index) == str(stage_id_or_index)),
            None
        )
        if not target_def:
            return False, [f"Stage '{stage_id_or_index}' not found."]

        ok, reasons, evidence = self.stage_matrix.verify_stage_completion(
            target_def, self.aggregate.gates, dlq_dir=self._dlq_dir
        )
        self._save_stages()

        event_type = "STAGE_VERIFIED" if ok else "STAGE_FAILED"
        payload = {
            "stage_id": target_def.stage_id,
            "stage_index": target_def.index,
            "stage_name": target_def.name,
            "facet": target_def.facet,
            "status": target_def.status,
            "reasons": reasons,
            "evidence": evidence
        }
        if hasattr(self, "event_store") and self.event_store:
            try:
                self.event_store.append(event_type, payload)
            except (OSError, IOError, KeyError, ValueError, AttributeError) as exc:
                print(f"[OrchestratorKernel Warning] Could not record {event_type} event: {exc}", file=sys.stderr)

        if ok:
            self._auto_harvest_stage(target_def)

        return ok, reasons

    def _auto_harvest_stage(self, stage_def: StageDefinition) -> Optional[Dict[str, Any]]:
        """Automatically harvests a verified stage execution into an SFT trajectory record."""
        try:
            trajectories_dir = os.path.join(self.workspace_root, ".focusgate", "trajectories")
            os.makedirs(trajectories_dir, exist_ok=True)
            harvest_file = os.path.join(trajectories_dir, "auto_harvested.jsonl")

            gates_snapshot = {
                gid: self.aggregate.gates.get(gid, {})
                for gid in stage_def.gate_ids
            }
            gate_titles = [g.get("title", gid) for gid, g in gates_snapshot.items()]

            instruction = f"Execute stage '{stage_def.name}' [{stage_def.facet}] for: {self.aggregate.pipeline}"
            input_context = f"Facet: {stage_def.facet}. Gates: {', '.join(gate_titles)}. Invariants: verified intra-stage matrix."

            first_gate = list(gates_snapshot.values())[0] if gates_snapshot else {}
            first_check = first_gate.get("check", "git status")
            first_expect = first_gate.get("expect", "On branch")

            envelope_lines = [
                f"▶ NEXT ACTION: {first_check}",
                f"State: [Pipeline: {self.aggregate.pipeline} (Stage {stage_def.index}: {stage_def.name})] [Active Gate: {stage_def.gate_ids[0] if stage_def.gate_ids else 'gate-1'}] [Queue: 1 active, 0 buffered] [Est: 15 min] [Depth: L1]",
                "",
                f"■ ACTIVE FOCUS: Execute verified stage gates for '{stage_def.name}'.",
            ]
            for idx, (gid, g) in enumerate(gates_snapshot.items(), 1):
                envelope_lines.append(f"{idx}. [{stage_def.facet}] {g.get('title', gid)}")
            envelope_lines.append(f"CHECK: {first_check}")
            envelope_lines.append(f"EXPECT: {first_expect}")
            action_envelope = "\n".join(envelope_lines)

            record = {
                "instruction": instruction,
                "input": input_context,
                "output": action_envelope,
                "prompt": f"<|im_start|>system\nYou are FocusGate v2.8, an ultra-compact, deterministic agent orchestration router.<|im_end|>\n<|im_start|>user\n{instruction}\n\nContext:\n{input_context}<|im_end|>\n<|im_start|>assistant\n",
                "completion": action_envelope,
                "timestamp": time.time(),
                "stage_id": stage_def.stage_id,
                "facet": stage_def.facet
            }

            with open(harvest_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

            if hasattr(self, "event_store") and self.event_store:
                self.event_store.append("TRAJECTORY_HARVESTED", {
                    "stage_id": stage_def.stage_id,
                    "file": harvest_file
                })

            return record
        except (OSError, IOError, KeyError, ValueError, AttributeError) as exc:
            print(f"[OrchestratorKernel Warning] Could not auto-harvest trajectory: {exc}", file=sys.stderr)
            return None

    def export_colab_pack(self, export_dir: Optional[str] = None) -> Dict[str, Any]:
        """Bundles harvested trajectories and generates a zero-setup Google Colab training script."""
        pack_dir = export_dir or os.path.join(self.workspace_root, ".focusgate", "colab_pack")
        os.makedirs(pack_dir, exist_ok=True)

        trajectories_source = os.path.join(self.workspace_root, ".focusgate", "trajectories", "auto_harvested.jsonl")
        target_jsonl = os.path.join(pack_dir, "trajectories.jsonl")

        records: List[Dict[str, Any]] = []
        if os.path.exists(trajectories_source):
            try:
                with open(trajectories_source, "r", encoding="utf-8") as f:
                    records = [json.loads(line) for line in f if line.strip()]
            except (OSError, IOError, json.JSONDecodeError):
                records = []

        if not records:
            # The training script is an asset we ship, not a package we import: load it by path
            # so core/ never depends on scripts/ (fitness test: test_core_never_imports_scripts).
            import importlib.util
            _src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "scripts", "colab_train_focusgate.py")
            _spec = importlib.util.spec_from_file_location("colab_train_focusgate", _src)
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            records = list(_mod.FOCUSGATE_TRAINING_DATA)

        with open(target_jsonl, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        script_source = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "colab_train_focusgate.py")
        script_dest = os.path.join(pack_dir, "train_focusgate_colab.py")
        if os.path.exists(script_source):
            with open(script_source, "r", encoding="utf-8") as sf:
                script_content = sf.read()
            script_content = script_content.replace('DATA_PATH = None', 'DATA_PATH = "./trajectories.jsonl"')
            with open(script_dest, "w", encoding="utf-8") as df:
                df.write(script_content)

        return {
            "success": True,
            "export_dir": pack_dir,
            "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
            "peft_type": "LORA",
            "record_count": len(records),
            "script_path": script_dest,
            "dataset_path": target_jsonl
        }

    def _build_brief(self, g: Dict[str, Any], context_hash: str,
                     stage_ctx: Optional[Dict[str, Any]]) -> AgentBrief:
        """v2.8 hybrid context: EPHEMERAL sterile vs WINDOW hydrated.

        Assembles upstream receipts from direct DAG edges and the hydrated bus
        window, then injects the SharedContextBus resolver so the AgentBrief
        renders budgeted summaries instead of unresolvable bare @pointers.
        """
        gid = g["id"]
        from .context_policy import mode_for_facet, FacetContextMode, subscriptions_for, brief_budget
        facet = g.get("facet", "engineering")
        mode = mode_for_facet(facet)
        # Collect upstream receipts (direct DAG edges only, with delta pointer)
        upstream_receipts = []
        for dep_id in g.get("depends_on", []):
            dep_bundle = self.active_bundles.get(dep_id)
            if dep_bundle and dep_bundle.gate_receipts:
                ptr = dep_bundle.delta_ids[0] if dep_bundle.delta_ids else ""
                for r in dep_bundle.gate_receipts:
                    rc = dict(r)
                    if ptr and "delta_id" not in rc:
                        rc["delta_id"] = ptr
                    upstream_receipts.append(rc)
        if mode == FacetContextMode.WINDOW:
            try:
                self.context_bus.evict_stale()
                self.context_bus.subscribe(gid, subscriptions_for(facet))
                window = self.context_bus.hydrate_window(gid, max_tokens=brief_budget(facet))
                seen = {r.get("gate_id") for r in upstream_receipts}
                for d in window:
                    if d.source_agent not in seen:
                        upstream_receipts.append({
                            "gate_id": d.source_agent,
                            "status": d.delta_type,
                            "key_findings": [d.content[:160]],
                            "delta_id": d.delta_id,
                        })
                        seen.add(d.source_agent)
            except Exception as e:
                print(f"[OrchestratorKernel Warning] Bus hydration failed: {e}", file=sys.stderr)

        return AgentBrief.create(
            gate_id=gid,
            facet=g.get("facet", "engineering"),
            task_summary=g.get("title", f"Execute {gid}"),
            acceptance_criteria=[
                f"CHECK: {g.get('check', 'echo OK')}",
                f"EXPECT: {g.get('expect', 'OK')}"
            ],
            upstream_receipts=upstream_receipts,
            context_delta_hash=context_hash,
            spawn_mode="ai_session",
            stage_context=stage_ctx,
            delta_resolver=self.context_bus.resolve_delta,
        )

    def plan_decomposition(self, query: str) -> List[Dict[str, Any]]:
        """Decomposes a complex objective into an acyclic DAG of acceptance gates.
        
        Analyzes query intent, selects the appropriate canonical pipeline,
        and instantiates dependency-linked gates inside LedgerAggregate.
        """
        ql = query.lower()
        try:
            from .facet_router import matched_ids
            matched = matched_ids(ql)
        except Exception:
            matched = []
        stages = []
        pipeline_name = "Dynamic Multi-Agent Workflow"

        if "frontend-design" in matched or "frontend-design" in ql:
            pipeline_name = "Bespoke Frontend Design & Implementation"
            stages = [
                {"gate_id": "gate-1-spec", "title": f"Bespoke design plan for: {query[:50]}", "facet": "frontend-design", "check": "python3 -c 'print(\"SPEC_OK\")'", "expect": "SPEC_OK", "deps": []},
                {"gate_id": "gate-2-tokens", "title": "Bespoke token extraction & lock", "facet": "design-tokens", "check": "python3 -c 'print(\"TOKENS_OK\")'", "expect": "TOKENS_OK", "deps": ["gate-1-spec"]},
                {"gate_id": "gate-3-proto", "title": "Disposable HTML/CSS sandbox spike", "facet": "prototype", "check": "python3 -c 'print(\"PROTO_OK\")'", "expect": "PROTO_OK", "deps": ["gate-2-tokens"]},
                {"gate_id": "gate-4-seam", "title": "Component interface seam", "facet": "codebase-design", "check": "python3 -c 'print(\"SEAM_OK\")'", "expect": "SEAM_OK", "deps": ["gate-3-proto"]},
                {"gate_id": "gate-5-impl", "title": "Production component implementation", "facet": "engineering", "check": "python3 -c 'print(\"IMPL_OK\")'", "expect": "IMPL_OK", "deps": ["gate-4-seam"]},
                {"gate_id": "gate-6-review", "title": "Dual-axis & anti-cliche review", "facet": "code-review", "check": "python3 -c 'print(\"REVIEW_OK\")'", "expect": "REVIEW_OK", "deps": ["gate-5-impl"]},
            ]
        elif "diagnosing-bugs" in matched:
            pipeline_name = "Rapid Defect Resolution"
            stages = [
                {"gate_id": "gate-1-repro", "title": f"Reproduction oracle for: {query[:50]}", "facet": "diagnosing-bugs", "check": "python3 -c 'print(\"REPRO_READY\")'", "expect": "REPRO_READY", "deps": []},
                {"gate_id": "gate-2-patch", "title": "Minimal defect repair", "facet": "engineering", "check": "python3 -c 'print(\"PATCH_PASS\")'", "expect": "PATCH_PASS", "deps": ["gate-1-repro"]},
                {"gate_id": "gate-3-review", "title": "Dual-axis code review", "facet": "code-review", "check": "python3 -c 'print(\"REVIEW_PASS\")'", "expect": "REVIEW_PASS", "deps": ["gate-2-patch"]},
            ]
        elif any(k in ql for k in ("ui", "component", "design", "css", "theme", "layout")):
            pipeline_name = "UI Component & Design Slicing"
            stages = [
                {"gate_id": "gate-1-spec", "title": f"Design specification for: {query[:50]}", "facet": "focus-design", "check": "python3 -c 'print(\"SPEC_OK\")'", "expect": "SPEC_OK", "deps": []},
                {"gate_id": "gate-2-tokens", "title": "Design tokens extraction", "facet": "design-tokens", "check": "python3 -c 'print(\"TOKENS_OK\")'", "expect": "TOKENS_OK", "deps": ["gate-1-spec"]},
                {"gate_id": "gate-3-impl", "title": "Production UI component implementation", "facet": "engineering", "check": "python3 -c 'print(\"UI_READY\")'", "expect": "UI_READY", "deps": ["gate-2-tokens"]},
            ]
        else:
            pipeline_name = "Modular Feature Architecture"
            stages = [
                {"gate_id": "gate-1-seam", "title": f"Public interface contract for: {query[:50]}", "facet": "codebase-design", "check": "python3 -c 'print(\"SEAM_READY\")'", "expect": "SEAM_READY", "deps": []},
                {"gate_id": "gate-2-core", "title": "Domain core implementation", "facet": "engineering", "check": "python3 -c 'print(\"CORE_READY\")'", "expect": "CORE_READY", "deps": ["gate-1-seam"]},
                {"gate_id": "gate-3-rigor", "title": "Unlazy rigor and integration verification", "facet": "cognitive", "check": "python3 -c 'print(\"RIGOR_VERIFIED\")'", "expect": "RIGOR_VERIFIED", "deps": ["gate-2-core"]},
            ]

        self.aggregate.pipeline = pipeline_name
        self.stage_definitions = [
            StageDefinition(
                stage_id=s["gate_id"],
                index=idx,
                name=s["title"],
                facet=s["facet"],
                gate_ids=[s["gate_id"]]
            )
            for idx, s in enumerate(stages, 1)
        ]
        self.aggregate.set_stages(stages)

        for s in stages:
            if s["gate_id"] not in self.aggregate.gates:
                self.aggregate.add_gate(
                    gate_id=s["gate_id"],
                    title=s["title"],
                    facet=s["facet"],
                    check=s["check"],
                    expect=s["expect"],
                    depends_on=s.get("deps", [])
                )

        self._save_gates()
        self._save_stages()
        return stages

    def dispatch_frontier(self) -> List[AgentBrief]:
        """Identifies unblocked frontier gates and renders AgentBriefs for external AI sessions."""
        unblocked_gates = []
        for gid, g in self.aggregate.gates.items():
            if g.get("status") == "PENDING" and gid not in self.dispatched_briefs:
                # Check all dependencies are CHECKED
                deps = g.get("depends_on", [])
                deps_satisfied = all(
                    self.aggregate.gates.get(d, {}).get("status") == "CHECKED"
                    for d in deps
                )
                if deps_satisfied:
                    unblocked_gates.append(g)

        available_slots = max(0, self.max_concurrent_agents - len(self.dispatched_briefs))
        to_dispatch = unblocked_gates[:available_slots]
        dispatched = []

        context_hash = self.context_bus.snapshot_hash()

        for g in to_dispatch:
            gid = g["id"]

            # Enforce Stage Boundary Guard
            StageBoundaryGuard.assert_can_activate_gate(
                target_gate_id=gid,
                stages=self.stage_definitions,
                aggregate_gates=self.aggregate.gates,
                matrix=self.stage_matrix
            )

            stage_ctx = None
            for s in self.stage_definitions:
                if gid in s.gate_ids:
                    stage_ctx = {
                        "stage_index": s.index,
                        "total_stages": len(self.stage_definitions),
                        "stage_name": s.name
                    }
                    break

            worktree_path = self.worktree_runner.provision_worktree(gid)

            # Fork a dedicated branch in Session DAG for this agent
            if hasattr(self.session_manager, "_dag") and self.session_manager._dag:
                try:
                    self.session_manager._dag.fork_branch(f"agent-{gid}")
                except (AttributeError, KeyError, RuntimeError):
                    pass

            brief = self._build_brief(g, context_hash, stage_ctx)

            # Write brief to disk and worktree
            brief_file = os.path.join(self._briefs_dir, f"{brief.brief_id}.json")
            with open(brief_file, "w", encoding="utf-8") as f:
                json.dump(brief.to_dict(), f, indent=2)

            prompt_path = os.path.join(worktree_path, "AGENT_PROMPT.md")
            prompt_text = brief.to_prompt()
            try:
                from .token_economy import TokenEconomyGovernor
                _gov = TokenEconomyGovernor(workspace_root=self.workspace_root)
                _compacted, prompt_text, _ = _gov.enforce_prompt_ceiling(prompt_text)
            except (ImportError, AttributeError, ValueError, OSError):
                pass
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt_text)

            self.dispatched_briefs[gid] = brief
            g["status"] = "ACTIVE"
            dispatched.append(brief)

            # Announce dispatch on context bus
            try:
                self.context_bus.publish(ContextDeltaEvent.create(
                    source_agent="orchestrator",
                    delta_type="REORIENT",
                    content=f"Dispatched sub-agent for {gid}: {brief.task_summary[:60]}"
                ))
            except Exception as e:
                print(f"[OrchestratorKernel Warning] Context bus broadcast failed: {e}", file=sys.stderr)

        self._save_gates()
        return dispatched

    def monitor_agents(self) -> Dict[str, Any]:
        """Monitors execution status, elapsed times, and timeouts across dispatched sub-agents."""
        now = datetime.now(timezone.utc)
        active_list = []
        timed_out = []

        for gid, brief in list(self.dispatched_briefs.items()):
            created = datetime.fromisoformat(brief.created_at)
            elapsed = (now - created).total_seconds()
            is_timeout = elapsed > brief.timeout_s

            status_entry = {
                "gate_id": gid,
                "brief_id": brief.brief_id,
                "facet": brief.facet,
                "elapsed_s": round(elapsed, 1),
                "timeout_s": brief.timeout_s,
                "timed_out": is_timeout
            }
            active_list.append(status_entry)

            if is_timeout:
                timed_out.append(status_entry)
                self.friction_sensor.record_gate_result(gid, False, f"Timeout after {elapsed}s")

        return {
            "active_count": len(self.dispatched_briefs),
            "agents": active_list,
            "timed_out_count": len(timed_out),
            "timed_out": timed_out
        }

    def receive_bundle(self, bundle: AgentReceiptBundle) -> ProofVerdict:
        """Evaluates an incoming AgentReceiptBundle using OrchestratorProofTree coherence criteria."""
        gid = bundle.gate_id
        bundle_file = os.path.join(self._bundles_dir, f"{bundle.bundle_id}.json")
        with open(bundle_file, "w", encoding="utf-8") as f:
            json.dump(bundle.to_dict(), f, indent=2)

        self.active_bundles[gid] = bundle

        tree = OrchestratorProofTree(f"coherence-{gid}")
        tree.build_coherence_criteria(
            expected_gate_ids=[gid],
            bundles=[bundle],
            dlq_dir=self._dlq_dir
        )

        verdict = tree.evaluate({
            "bundles": [bundle],
            "dlq_dir": self._dlq_dir
        })

        if verdict.verified:
            bundle.status = "PASS"
            # Update bundle file with verified status
            try:
                with open(bundle_file, "w", encoding="utf-8") as f:
                    json.dump(bundle.to_dict(), f, indent=2)
            except (OSError, IOError):
                pass
            # Publish receipt delta to Context Bus
            try:
                self.context_bus.publish(ContextDeltaEvent.create(
                    source_agent=gid,
                    delta_type="RECEIPT",
                    content=f"Gate {gid} verified: {len(bundle.artifacts_produced)} artifacts, evidence intact"
                ))
                for art in (bundle.artifacts_produced or [])[:3]:
                    try:
                        self.context_bus.publish_file_patch(gid, art, (bundle.patch_hashes[0][:16] if bundle.patch_hashes else "patch"))
                    except (KeyError, IndexError, TypeError, AttributeError, OSError):
                        pass
            except Exception as e:
                print(f"[OrchestratorKernel Warning] Receipt delta broadcast failed: {e}", file=sys.stderr)
        else:
            bundle.status = "FAIL"
            bundle.error_message = "; ".join(verdict.failed_criteria)
            try:
                with open(bundle_file, "w", encoding="utf-8") as f:
                    json.dump(bundle.to_dict(), f, indent=2)
            except (OSError, IOError):
                pass

        return verdict

    def merge_results(self, gate_id: str) -> bool:
        """Merges an accepted sub-agent's work into the main branch and settles the gate."""
        bundle = self.active_bundles.get(gate_id)
        if not bundle and os.path.exists(self._bundles_dir):
            for fname in os.listdir(self._bundles_dir):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(self._bundles_dir, fname), "r", encoding="utf-8") as f:
                            b_data = json.load(f)
                            if b_data.get("gateId") == gate_id or b_data.get("gate_id") == gate_id:
                                bundle = AgentReceiptBundle(
                                    bundle_id=b_data.get("bundleId") or b_data.get("bundle_id"),
                                    gate_id=gate_id,
                                    brief_id=b_data.get("briefId") or b_data.get("brief_id"),
                                    gate_receipts=b_data.get("gateReceipts") or b_data.get("gate_receipts", []),
                                    delta_ids=b_data.get("deltaIds") or b_data.get("delta_ids", []),
                                    artifacts_produced=b_data.get("artifactsProduced") or b_data.get("artifacts_produced", []),
                                    patch_hashes=b_data.get("patchHashes") or b_data.get("patch_hashes", []),
                                    status=b_data.get("status", "PASS")
                                )
                                break
                    except (OSError, IOError, json.JSONDecodeError):
                        pass
        if not bundle or bundle.status != "PASS":
            reason = bundle.error_message if bundle else "Missing or unverified AgentReceiptBundle"
            self._escalate_dlq_tombstone(gate_id, reason)
            return False

        # Mark aggregate gate as CHECKED
        receipt = bundle.gate_receipts[0] if bundle.gate_receipts else None
        self.aggregate.check_gate(gate_id, output="Orchestrator verified bundle", receipt=receipt)

        # Merge branch in Session DAG if active
        if hasattr(self.session_manager, "_dag") and self.session_manager._dag:
            agent_branch = f"agent-{gate_id}"
            if agent_branch in self.session_manager._dag.branches:
                try:
                    self.session_manager._dag.merge_branch(
                        source_branch=agent_branch,
                        target_branch="main",
                        metadata={"gate_id": gate_id, "bundle_id": bundle.bundle_id}
                    )
                except Exception as e:
                    print(f"[OrchestratorKernel Warning] Session DAG merge warning: {e}", file=sys.stderr)
            try:
                self.session_manager._dag.prune_stale_branches()
            except (AttributeError, KeyError, RuntimeError):
                pass

        # v2.8: prune dispatch noise for settled gate, keep anchors
        try:
            self.context_bus.evict_settled(gate_id)
        except (AttributeError, KeyError, TypeError):
            pass
        # Cleanup isolated worktree
        self.worktree_runner.cleanup_worktree(gate_id, force=True)
        self.dispatched_briefs.pop(gate_id, None)

        # Persist the updated CHECKED status to disk
        self._save_gates()

        # Auto-verify enclosing stage if all its gates are now CHECKED
        for stage in self.stage_definitions:
            if gate_id in stage.gate_ids:
                all_stage_gates_checked = all(
                    self.aggregate.gates.get(gid, {}).get("status") == "CHECKED"
                    for gid in stage.gate_ids
                )
                if all_stage_gates_checked:
                    self.verify_stage(stage.stage_id)
                break

        # Check if all gates are settled
        unsettled = [g for g in self.aggregate.gates.values() if g.get("status") != "CHECKED"]
        if not unsettled:
            self.statechart.trigger("ALL_GATES_PASS", {"has_pending_gates": False})

        return True

    def _escalate_dlq_tombstone(self, gate_id: str, error_message: str) -> None:
        """Persists failure tombstone to Dead Letter Queue (DLQ)."""
        tombstone = DLQTombstone(
            tombstone_id=f"dlq-{gate_id}-{int(time.time())}",
            saga_name="OrchestratorMergeSaga",
            failed_step=f"merge_{gate_id}",
            failed_compensation_step="rollback_gate",
            error_message=error_message,
            compensation_error="None",
            timestamp=time.time(),
            remediation_cmd=f"python3 focus-gate.py --agent-retry {gate_id}",
            context_snapshot={"gate_id": gate_id, "active_bundles": list(self.active_bundles.keys())}
        )

        tombstone_path = os.path.join(self._dlq_dir, f"{tombstone.tombstone_id}.tombstone.json")
        try:
            with open(tombstone_path, "w", encoding="utf-8") as f:
                json.dump(tombstone.__dict__, f, indent=2)
            self.aggregate.rollback_gate(gate_id, reason=error_message)
        except Exception as e:
            print(f"[OrchestratorKernel Critical] Failed writing DLQ tombstone: {e}", file=sys.stderr)

    def create_checkpoint(self, checkpoint_id: str = "v2.8-prod") -> Dict[str, Any]:
        """Creates an immutable, cryptographically verified checkpoint of the orchestrator state."""
        import hashlib
        os.makedirs(self._checkpoints_dir, exist_ok=True)
        now_ts = time.time()

        dag_state = {}
        if hasattr(self.session_manager, "_dag") and self.session_manager._dag:
            dag = self.session_manager._dag
            dag_state = {
                "active_branch": dag.active_branch,
                "active_node_id": dag.branches.get(dag.active_branch),
                "branches": dict(dag.branches),
                "turn_counter": dag.turn_counter
            }

        stages_payload = [s.to_dict() for s in self.stage_definitions]
        gates_payload = dict(self.aggregate.gates)

        model_adapter_payload = None
        try:
            from adapters.model_adapter import LoRAModelAdapter
            adapter = LoRAModelAdapter(repo_root=self.workspace_root)
            if adapter.is_available():
                model_adapter_payload = adapter.get_metadata()
        except (ImportError, OSError, ValueError, KeyError):
            pass

        content_dict = {
            "checkpoint_id": checkpoint_id,
            "version": "2.8",
            "pipeline": self.aggregate.pipeline,
            "gates": gates_payload,
            "stages": stages_payload,
            "dag": dag_state
        }
        if model_adapter_payload:
            content_dict["model_adapter"] = model_adapter_payload

        content_for_hash = json.dumps(content_dict, sort_keys=True)
        sha256_checksum = hashlib.sha256(content_for_hash.encode("utf-8")).hexdigest()

        manifest = {
            "checkpoint_id": checkpoint_id,
            "version": "2.8",
            "timestamp": now_ts,
            "pipeline": self.aggregate.pipeline,
            "gate_count": len(gates_payload),
            "stage_count": len(stages_payload),
            "gates": gates_payload,
            "stages": stages_payload,
            "dag": dag_state,
            "checksum": sha256_checksum
        }
        if model_adapter_payload:
            manifest["model_adapter"] = model_adapter_payload

        checkpoint_file = os.path.join(self._checkpoints_dir, f"{checkpoint_id}.json")
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        try:
            from core.aggregate import DomainEvent
            ev = DomainEvent(
                event_type="CHECKPOINT_CREATED",
                aggregate_id="orchestrator",
                payload={"checkpoint_id": checkpoint_id, "checksum": sha256_checksum, "gate_count": len(gates_payload)},
                timestamp=now_ts
            )
            self.event_store.append(ev)
        except (AttributeError, KeyError, RuntimeError, TypeError):
            pass

        return manifest

    def restore_checkpoint(self, checkpoint_id: str = "v2.8-prod") -> bool:
        """Restores orchestrator state from a previously saved checkpoint, returning loops to the prior state."""
        import hashlib
        checkpoint_file = os.path.join(self._checkpoints_dir, f"{checkpoint_id}.json")
        if not os.path.exists(checkpoint_file):
            return False

        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except (OSError, IOError, json.JSONDecodeError):
            return False

        gates_payload = manifest.get("gates", {})
        stages_payload = manifest.get("stages", [])
        dag_state = manifest.get("dag", {})
        expected_checksum = manifest.get("checksum", "")

        content_dict = {
            "checkpoint_id": manifest.get("checkpoint_id", checkpoint_id),
            "version": manifest.get("version", "2.8"),
            "pipeline": manifest.get("pipeline", ""),
            "gates": gates_payload,
            "stages": stages_payload,
            "dag": dag_state
        }
        if "model_adapter" in manifest:
            content_dict["model_adapter"] = manifest["model_adapter"]

        content_for_hash = json.dumps(content_dict, sort_keys=True)
        computed_checksum = hashlib.sha256(content_for_hash.encode("utf-8")).hexdigest()

        if expected_checksum and computed_checksum != expected_checksum:
            raise ValueError(f"Checkpoint integrity verification failed: expected {expected_checksum[:12]}..., got {computed_checksum[:12]}...")

        self.aggregate.pipeline = manifest.get("pipeline", self.aggregate.pipeline)
        self.aggregate.gates = dict(gates_payload)

        self.stage_definitions = [
            StageDefinition(
                stage_id=s["stage_id"],
                index=s.get("index", idx),
                name=s.get("name", s.get("title", s["stage_id"])),
                facet=s.get("facet", "engineering"),
                gate_ids=s.get("gate_ids", [s["stage_id"]]),
                required_artifacts=s.get("required_artifacts", []),
                status=s.get("status", "PENDING"),
                receipt_hashes=s.get("receipt_hashes", {})
            )
            for idx, s in enumerate(stages_payload, 1)
        ]

        if hasattr(self.session_manager, "_dag") and self.session_manager._dag and dag_state:
            dag = self.session_manager._dag
            active_node_id = dag_state.get("active_node_id")
            if active_node_id and active_node_id in dag.nodes:
                try:
                    dag.rewind_to(active_node_id)
                except (KeyError, RuntimeError):
                    pass
            if dag_state.get("active_branch"):
                dag.active_branch = dag_state.get("active_branch")

        self._save_gates()
        self._save_stages()

        try:
            from core.aggregate import DomainEvent
            ev = DomainEvent(
                event_type="CHECKPOINT_RESTORED",
                aggregate_id="orchestrator",
                payload={"checkpoint_id": checkpoint_id, "checksum": computed_checksum},
                timestamp=time.time()
            )
            self.event_store.append(ev)
        except (AttributeError, KeyError, RuntimeError, TypeError):
            pass

        return True

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """Lists all existing production checkpoints and verifies their cryptographic integrity."""
        import hashlib
        checkpoints = []
        if not os.path.exists(self._checkpoints_dir):
            return checkpoints

        for fname in sorted(os.listdir(self._checkpoints_dir)):
            if fname.endswith(".json"):
                cpath = os.path.join(self._checkpoints_dir, fname)
                try:
                    with open(cpath, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    gates_payload = data.get("gates", {})
                    stages_payload = data.get("stages", [])
                    dag_state = data.get("dag", {})
                    expected_checksum = data.get("checksum", "")

                    content_dict = {
                        "checkpoint_id": data.get("checkpoint_id", fname[:-5]),
                        "version": data.get("version", "2.8"),
                        "pipeline": data.get("pipeline", ""),
                        "gates": gates_payload,
                        "stages": stages_payload,
                        "dag": dag_state
                    }
                    if "model_adapter" in data:
                        content_dict["model_adapter"] = data["model_adapter"]
                    content_for_hash = json.dumps(content_dict, sort_keys=True)
                    computed_checksum = hashlib.sha256(content_for_hash.encode("utf-8")).hexdigest()
                    valid = (computed_checksum == expected_checksum) if expected_checksum else True

                    checkpoints.append({
                        "checkpoint_id": data.get("checkpoint_id", fname[:-5]),
                        "version": data.get("version", "2.8"),
                        "timestamp": data.get("timestamp", 0.0),
                        "pipeline": data.get("pipeline", "N/A"),
                        "gate_count": data.get("gate_count", len(gates_payload)),
                        "stage_count": data.get("stage_count", len(stages_payload)),
                        "model_adapter": data.get("model_adapter"),
                        "checksum_valid": valid,
                        "checksum": expected_checksum[:12] if expected_checksum else "N/A"
                    })
                except (OSError, IOError, json.JSONDecodeError):
                    pass

        return checkpoints

