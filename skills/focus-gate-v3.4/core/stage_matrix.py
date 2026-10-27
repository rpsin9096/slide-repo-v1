"""FocusGate v2.8 — Stage Verification Matrix & Boundary Guard.

Eliminates stage-dropping and stage-amnesia across multi-step pipelines.
Enforces intra-stage verification gateways before frontier advancement.
Zero external dependencies (100% Python stdlib).
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import os
import json
import ast
import hashlib


class StageBoundaryViolationError(Exception):
    """Raised when an agent attempts to advance or execute out-of-stage gates."""
    pass


@dataclass
class StageDefinition:
    """Formal contract for an execution stage within a multi-facet pipeline."""
    stage_id: str
    index: int
    name: str
    facet: str
    gate_ids: List[str]
    depends_on_stages: List[str] = field(default_factory=list)
    branch_id: Optional[str] = None
    barrier_type: str = "ALL_PREDECESSORS"  # ALL_PREDECESSORS | ANY_PREDECESSOR
    required_artifacts: List[str] = field(default_factory=list)
    artifact_schemas: Dict[str, Any] = field(default_factory=dict)
    status: str = "PENDING"  # PENDING, ACTIVE, VERIFIED, FAILED
    receipt_hashes: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "index": self.index,
            "name": self.name,
            "facet": self.facet,
            "gate_ids": self.gate_ids,
            "depends_on_stages": self.depends_on_stages,
            "branch_id": self.branch_id,
            "barrier_type": self.barrier_type,
            "required_artifacts": self.required_artifacts,
            "artifact_schemas": self.artifact_schemas,
            "status": self.status,
            "receipt_hashes": self.receipt_hashes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StageDefinition':
        return cls(
            stage_id=data["stage_id"],
            index=data.get("index", 1),
            name=data.get("name", data["stage_id"]),
            facet=data.get("facet", "engineering"),
            gate_ids=data.get("gate_ids", []),
            depends_on_stages=data.get("depends_on_stages", []),
            branch_id=data.get("branch_id"),
            barrier_type=data.get("barrier_type", "ALL_PREDECESSORS"),
            required_artifacts=data.get("required_artifacts", []),
            artifact_schemas=data.get("artifact_schemas", {}),
            status=data.get("status", "PENDING"),
            receipt_hashes=data.get("receipt_hashes", {})
        )


class StageVerificationMatrix:
    """Evaluates intra-stage exit criteria before releasing the next stage frontier."""

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)

    def compute_stage_frontier(
        self,
        stages: List[StageDefinition],
        aggregate_gates: Dict[str, Dict[str, Any]],
        dlq_dir: Optional[str] = None
    ) -> List[StageDefinition]:
        """Resolves all unblocked (executable) stages in topological dependency order."""
        stage_by_id = {s.stage_id: s for s in stages}
        unblocked: List[StageDefinition] = []

        # Determine if stages use explicit DAG dependencies or linear indices
        has_explicit_dag = any(len(s.depends_on_stages) > 0 for s in stages)

        for stage in sorted(stages, key=lambda s: s.index):
            if stage.status == "VERIFIED":
                continue

            # Linear fallback if no stages declare depends_on_stages
            if not has_explicit_dag:
                priors = [p for p in stages if p.index < stage.index]
                all_priors_done = all(p.status == "VERIFIED" for p in priors)
                if all_priors_done:
                    unblocked.append(stage)
                continue

            # Explicit DAG evaluation
            deps = stage.depends_on_stages
            if not deps:
                # Root stage in DAG
                unblocked.append(stage)
                continue

            # Evaluate dependencies
            dep_stages = [stage_by_id.get(dep_id) for dep_id in deps if dep_id in stage_by_id]
            if stage.barrier_type == "ANY_PREDECESSOR":
                deps_satisfied = any(ds and ds.status == "VERIFIED" for ds in dep_stages)
            else:  # ALL_PREDECESSORS
                deps_satisfied = len(dep_stages) == len(deps) and all(ds and ds.status == "VERIFIED" for ds in dep_stages)

            if deps_satisfied:
                unblocked.append(stage)

        return unblocked

    def get_active_stage(
        self,
        stages: List[StageDefinition],
        aggregate_gates: Dict[str, Dict[str, Any]],
        dlq_dir: Optional[str] = None
    ) -> Optional[StageDefinition]:
        """Resolves the current active (incomplete) stage in sequence."""
        frontier = self.compute_stage_frontier(stages, aggregate_gates, dlq_dir=dlq_dir)
        return frontier[0] if frontier else None

    def verify_stage_completion(
        self,
        stage: StageDefinition,
        aggregate_gates: Dict[str, Dict[str, Any]],
        dlq_dir: Optional[str] = None
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Verifies that all intra-stage requirements are met before advancing.
        
        Evaluates:
        1. Receipt Completeness: All stage gates must be in CHECKED status with proof.
        2. Artifact Contract: All required stage files must exist on disk and be non-empty.
        3. Zero DLQ Tombstones: No unhandled failures for this stage in dead letter queue.
        """
        rejection_reasons = []
        evidence = {
            "checked_gates": [],
            "missing_gates": [],
            "verified_artifacts": [],
            "missing_artifacts": [],
            "dlq_tombstones": 0
        }

        # 1. Receipt Completeness
        for gid in stage.gate_ids:
            gate_data = aggregate_gates.get(gid)
            if not gate_data:
                rejection_reasons.append(f"Gate '{gid}' is missing from aggregate ledger.")
                evidence["missing_gates"].append(gid)
            elif gate_data.get("status") != "CHECKED":
                rejection_reasons.append(f"Prerequisite gate '{gid}' status is '{gate_data.get('status')}' (expected CHECKED).")
                evidence["missing_gates"].append(gid)
            else:
                expected_hash = stage.receipt_hashes.get(gid)
                actual_hash = gate_data.get("receipt_hash")
                if expected_hash and actual_hash != expected_hash:
                    rejection_reasons.append(
                        f"Receipt hash mismatch for gate '{gid}': expected '{expected_hash}', got '{actual_hash}'."
                    )
                    evidence["missing_gates"].append(gid)
                else:
                    evidence["checked_gates"].append(gid)

        # 2. Artifact Contract Verification
        for rel_path in stage.required_artifacts:
            full_path = os.path.join(self.workspace_root, rel_path)
            if not os.path.exists(full_path):
                rejection_reasons.append(f"Declared stage artifact '{rel_path}' does not exist on disk.")
                evidence["missing_artifacts"].append(rel_path)
            elif os.path.getsize(full_path) == 0:
                rejection_reasons.append(f"Declared stage artifact '{rel_path}' is empty (0 bytes).")
                evidence["missing_artifacts"].append(rel_path)
            else:
                schema = stage.artifact_schemas.get(rel_path, {})
                schema_type = schema.get("type", "")

                if schema_type == "json" or rel_path.endswith(".json"):
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            parsed_json = json.load(f)
                        required_keys = schema.get("required_keys", [])
                        if required_keys:
                            if not isinstance(parsed_json, dict):
                                rejection_reasons.append(f"Artifact '{rel_path}' JSON root must be an object/dict")
                                evidence["missing_artifacts"].append(rel_path)
                                continue
                            missing_keys = [k for k in required_keys if k not in parsed_json]
                            if missing_keys:
                                rejection_reasons.append(f"Artifact '{rel_path}' missing required keys: {', '.join(missing_keys)}")
                                evidence["missing_artifacts"].append(rel_path)
                                continue
                    except (OSError, IOError, json.JSONDecodeError, ValueError) as err:
                        rejection_reasons.append(f"Invalid JSON syntax in artifact '{rel_path}': {err}")
                        evidence["missing_artifacts"].append(rel_path)
                        continue

                elif schema_type == "python" or rel_path.endswith(".py"):
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            py_src = f.read()
                        tree = ast.parse(py_src, filename=full_path)
                        required_fns = schema.get("required_functions", [])
                        if required_fns:
                            found_fns = {
                                node.name for node in ast.walk(tree)
                                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                            }
                            missing_fns = [fn for fn in required_fns if fn not in found_fns]
                            if missing_fns:
                                rejection_reasons.append(f"Artifact '{rel_path}' missing required function(s): {', '.join(missing_fns)}")
                                evidence["missing_artifacts"].append(rel_path)
                                continue
                    except SyntaxError as err:
                        rejection_reasons.append(f"Invalid Python AST syntax in artifact '{rel_path}': {err}")
                        evidence["missing_artifacts"].append(rel_path)
                        continue

                evidence["verified_artifacts"].append({
                    "path": rel_path,
                    "size_bytes": os.path.getsize(full_path)
                })

        # 3. DLQ Tombstone Check
        target_dlq = dlq_dir or os.path.join(self.workspace_root, ".focusgate", "dlq")
        if os.path.isdir(target_dlq):
            tombstones = [f for f in os.listdir(target_dlq) if f.endswith(".json")]
            for t_file in tombstones:
                for gid in stage.gate_ids:
                    if gid in t_file:
                        rejection_reasons.append(f"Unresolved DLQ tombstone detected: {t_file}")
                        evidence["dlq_tombstones"] += 1

        is_verified = (len(rejection_reasons) == 0)
        if is_verified:
            stage.status = "VERIFIED"
        else:
            if evidence["dlq_tombstones"] > 0:
                stage.status = "FAILED"
        return is_verified, rejection_reasons, evidence


class StageBoundaryGuard:
    """Prevents out-of-order stage dispatch and guards execution state vectors."""

    @staticmethod
    def assert_can_activate_gate(
        target_gate_id: str,
        stages: List[StageDefinition],
        aggregate_gates: Dict[str, Dict[str, Any]],
        matrix: StageVerificationMatrix
    ) -> None:
        """Raises StageBoundaryViolationError if target gate belongs to a blocked stage."""
        # Find which stage owns target_gate_id
        target_stage: Optional[StageDefinition] = None
        for s in stages:
            if target_gate_id in s.gate_ids:
                target_stage = s
                break

        if not target_stage:
            return  # Gate is not bound to a formal stage, allow standard DAG checks

        stage_by_id = {s.stage_id: s for s in stages}

        # Check explicit DAG dependencies
        if target_stage.depends_on_stages:
            for dep_id in target_stage.depends_on_stages:
                dep_stage = stage_by_id.get(dep_id)
                if not dep_stage or dep_stage.status != "VERIFIED":
                    verified = False
                    reasons = ["predecessor stage incomplete"]
                    if dep_stage:
                        verified, reasons, _ = matrix.verify_stage_completion(dep_stage, aggregate_gates)
                    if not verified:
                        raise StageBoundaryViolationError(
                            f"Stage Boundary Violation: Cannot execute '{target_gate_id}' in Stage '{target_stage.stage_id}' ({target_stage.name}). "
                            f"Prerequisite Stage '{dep_id}' is incomplete: {'; '.join(reasons)}"
                        )
                    else:
                        dep_stage.status = "VERIFIED"
            return

        # Check all prior stages are verified (linear fallback)
        for prior_stage in stages:
            if prior_stage.index < target_stage.index:
                if prior_stage.status != "VERIFIED":
                    verified, reasons, _ = matrix.verify_stage_completion(prior_stage, aggregate_gates)
                    if not verified:
                        raise StageBoundaryViolationError(
                            f"Stage Boundary Violation: Cannot execute '{target_gate_id}' in Stage {target_stage.index} ({target_stage.name}). "
                            f"Prior Stage {prior_stage.index} ({prior_stage.name}) is incomplete: {'; '.join(reasons)}"
                        )
                    else:
                        prior_stage.status = "VERIFIED"
