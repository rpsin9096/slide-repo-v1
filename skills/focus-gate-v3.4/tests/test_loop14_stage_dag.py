"""Tests for FocusGate v2.8.5 — Milestone 11 (Loop 14: Branching Stage DAG Matrix).

Covers:
1. StageDefinition DAG fields and serialization.
2. Topological stage frontier resolution (linear fallback & diamond fork-join).
3. Barrier synchronization (ALL_PREDECESSORS vs ANY_PREDECESSOR).
4. StageBoundaryGuard with DAG dependency evaluation.
5. Structural artifact schema verification (JSON required keys and Python AST).
"""

import unittest
import os
import tempfile
import shutil
import json

from core.stage_matrix import (
    StageDefinition,
    StageVerificationMatrix,
    StageBoundaryGuard,
    StageBoundaryViolationError
)


class TestStageDefinitionDAGFields(unittest.TestCase):
    """Verifies StageDefinition model evolution with DAG attributes."""

    def test_stage_definition_dag_defaults(self):
        s = StageDefinition(
            stage_id="stage-1",
            index=1,
            name="Decomposition",
            facet="navigation",
            gate_ids=["g1"]
        )
        self.assertEqual(s.depends_on_stages, [])
        self.assertIsNone(s.branch_id)
        self.assertEqual(s.barrier_type, "ALL_PREDECESSORS")
        self.assertEqual(s.artifact_schemas, {})

    def test_to_dict_and_from_dict_roundtrip(self):
        s = StageDefinition(
            stage_id="stage-2a",
            index=2,
            name="Frontend Build",
            facet="design",
            gate_ids=["g-fe-1", "g-fe-2"],
            depends_on_stages=["stage-1"],
            branch_id="frontend",
            barrier_type="ALL_PREDECESSORS",
            required_artifacts=["ui/tokens.json"],
            artifact_schemas={"ui/tokens.json": {"type": "json", "required_keys": ["colors", "spacing"]}},
            status="ACTIVE",
            receipt_hashes={"g-fe-1": "sha256-abc"}
        )
        d = s.to_dict()
        self.assertEqual(d["depends_on_stages"], ["stage-1"])
        self.assertEqual(d["branch_id"], "frontend")
        self.assertEqual(d["artifact_schemas"]["ui/tokens.json"]["required_keys"], ["colors", "spacing"])

        s2 = StageDefinition.from_dict(d)
        self.assertEqual(s2.stage_id, "stage-2a")
        self.assertEqual(s2.depends_on_stages, ["stage-1"])
        self.assertEqual(s2.branch_id, "frontend")
        self.assertEqual(s2.artifact_schemas, s.artifact_schemas)


class TestTopologicalStageFrontier(unittest.TestCase):
    """Verifies topological frontier computation for concurrent fork-join DAGs."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.matrix = StageVerificationMatrix(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_linear_stage_frontier_fallback(self):
        s1 = StageDefinition("s1", 1, "Plan", "cognitive", ["g1"], status="PENDING")
        s2 = StageDefinition("s2", 2, "Code", "engineering", ["g2"], status="PENDING")
        s3 = StageDefinition("s3", 3, "Review", "engineering", ["g3"], status="PENDING")
        stages = [s1, s2, s3]

        # Initially, only s1 is in the frontier
        gates = {
            "g1": {"status": "PENDING"},
            "g2": {"status": "PENDING"},
            "g3": {"status": "PENDING"}
        }
        frontier = self.matrix.compute_stage_frontier(stages, gates)
        self.assertEqual([s.stage_id for s in frontier], ["s1"])

        # Mark s1 complete
        gates["g1"]["status"] = "CHECKED"
        s1.status = "VERIFIED"
        frontier = self.matrix.compute_stage_frontier(stages, gates)
        self.assertEqual([s.stage_id for s in frontier], ["s2"])

    def test_fork_join_diamond_dag_frontier(self):
        # Topology:
        #        s1 (Root)
        #       /  \
        #    s2a    s2b (Parallel Swarm Branches)
        #       \  /
        #        s3 (Join Barrier)
        s1 = StageDefinition("s1", 1, "Decompose", "navigation", ["g1"], status="PENDING")
        s2a = StageDefinition("s2a", 2, "Frontend", "design", ["g2a"], depends_on_stages=["s1"], branch_id="fe", status="PENDING")
        s2b = StageDefinition("s2b", 2, "Backend", "engineering", ["g2b"], depends_on_stages=["s1"], branch_id="be", status="PENDING")
        s3 = StageDefinition("s3", 3, "Integration", "engineering", ["g3"], depends_on_stages=["s2a", "s2b"], barrier_type="ALL_PREDECESSORS", status="PENDING")
        stages = [s1, s2a, s2b, s3]

        gates = {
            "g1": {"status": "PENDING"},
            "g2a": {"status": "PENDING"},
            "g2b": {"status": "PENDING"},
            "g3": {"status": "PENDING"}
        }

        # Step 1: Only s1 unblocked
        frontier = self.matrix.compute_stage_frontier(stages, gates)
        self.assertEqual([s.stage_id for s in frontier], ["s1"])

        # Step 2: s1 VERIFIED -> both s2a and s2b unblock concurrently
        gates["g1"]["status"] = "CHECKED"
        s1.status = "VERIFIED"
        frontier = self.matrix.compute_stage_frontier(stages, gates)
        frontier_ids = sorted([s.stage_id for s in frontier])
        self.assertEqual(frontier_ids, ["s2a", "s2b"])

        # Step 3: s2a completes, s2b still pending -> s3 remains blocked
        gates["g2a"]["status"] = "CHECKED"
        s2a.status = "VERIFIED"
        frontier = self.matrix.compute_stage_frontier(stages, gates)
        self.assertEqual([s.stage_id for s in frontier], ["s2b"])

        # Step 4: s2b completes -> s3 join barrier unlocks
        gates["g2b"]["status"] = "CHECKED"
        s2b.status = "VERIFIED"
        frontier = self.matrix.compute_stage_frontier(stages, gates)
        self.assertEqual([s.stage_id for s in frontier], ["s3"])

    def test_any_predecessor_barrier(self):
        s1a = StageDefinition("s1a", 1, "Quick Path", "engineering", ["g1a"], status="PENDING")
        s1b = StageDefinition("s1b", 1, "Thorough Path", "engineering", ["g1b"], status="PENDING")
        s2 = StageDefinition("s2", 2, "Followup", "writing", ["g2"], depends_on_stages=["s1a", "s1b"], barrier_type="ANY_PREDECESSOR", status="PENDING")
        stages = [s1a, s1b, s2]

        gates = {
            "g1a": {"status": "CHECKED"},
            "g1b": {"status": "PENDING"},
            "g2": {"status": "PENDING"}
        }
        s1a.status = "VERIFIED"

        frontier = self.matrix.compute_stage_frontier(stages, gates)
        frontier_ids = [s.stage_id for s in frontier]
        self.assertIn("s2", frontier_ids, "ANY_PREDECESSOR should unlock when one predecessor completes.")


class TestStageBoundaryGuardWithDAG(unittest.TestCase):
    """Verifies that StageBoundaryGuard respects DAG dependencies."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.matrix = StageVerificationMatrix(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_dag_boundary_guard_blocks_unmet_dependencies(self):
        s1 = StageDefinition("s1", 1, "Plan", "navigation", ["g1"], status="VERIFIED")
        s2 = StageDefinition("s2", 2, "Build", "engineering", ["g2"], depends_on_stages=["s1"], status="PENDING")
        s3 = StageDefinition("s3", 3, "Deploy", "engineering", ["g3"], depends_on_stages=["s2"], status="PENDING")
        stages = [s1, s2, s3]

        gates = {
            "g1": {"status": "CHECKED"},
            "g2": {"status": "PENDING"},
            "g3": {"status": "PENDING"}
        }

        # Trying to activate g3 before s2 is verified should raise StageBoundaryViolationError
        with self.assertRaises(StageBoundaryViolationError):
            StageBoundaryGuard.assert_can_activate_gate("g3", stages, gates, self.matrix)

        # Activating g2 is permitted because s1 is verified
        try:
            StageBoundaryGuard.assert_can_activate_gate("g2", stages, gates, self.matrix)
        except StageBoundaryViolationError:
            self.fail("Activating g2 should be permitted when predecessor s1 is VERIFIED.")


class TestArtifactStructuralSchemaGate(unittest.TestCase):
    """Verifies intra-stage verification matrix artifact schema enforcement."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.matrix = StageVerificationMatrix(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_json_artifact_schema_validation_passes(self):
        json_path = os.path.join(self.tmp_dir, "manifest.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"name": "test", "version": "1.0", "active": True}, f)

        stage = StageDefinition(
            stage_id="s1",
            index=1,
            name="Artifact Stage",
            facet="engineering",
            gate_ids=["g1"],
            required_artifacts=["manifest.json"],
            artifact_schemas={
                "manifest.json": {
                    "type": "json",
                    "required_keys": ["name", "version"]
                }
            }
        )
        gates = {"g1": {"status": "CHECKED"}}
        ok, reasons, evidence = self.matrix.verify_stage_completion(stage, gates)
        self.assertTrue(ok, f"Verification failed unexpectedly: {reasons}")
        self.assertEqual(len(evidence["verified_artifacts"]), 1)

    def test_json_artifact_schema_validation_fails_on_missing_keys(self):
        json_path = os.path.join(self.tmp_dir, "manifest.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"name": "test"}, f)  # missing 'version'

        stage = StageDefinition(
            stage_id="s1",
            index=1,
            name="Artifact Stage",
            facet="engineering",
            gate_ids=["g1"],
            required_artifacts=["manifest.json"],
            artifact_schemas={
                "manifest.json": {
                    "type": "json",
                    "required_keys": ["name", "version"]
                }
            }
        )
        gates = {"g1": {"status": "CHECKED"}}
        ok, reasons, evidence = self.matrix.verify_stage_completion(stage, gates)
        self.assertFalse(ok)
        self.assertTrue(any("missing required keys" in r for r in reasons))

    def test_python_artifact_schema_validation(self):
        py_path = os.path.join(self.tmp_dir, "service.py")
        with open(py_path, "w", encoding="utf-8") as f:
            f.write("def start_service():\n    return True\n")

        stage = StageDefinition(
            stage_id="s1",
            index=1,
            name="Service Stage",
            facet="engineering",
            gate_ids=["g1"],
            required_artifacts=["service.py"],
            artifact_schemas={
                "service.py": {
                    "type": "python",
                    "required_functions": ["start_service"]
                }
            }
        )
        gates = {"g1": {"status": "CHECKED"}}
        ok, reasons, _ = self.matrix.verify_stage_completion(stage, gates)
        self.assertTrue(ok)

        # Now test with missing function
        stage.artifact_schemas["service.py"]["required_functions"] = ["stop_service"]
        ok, reasons, _ = self.matrix.verify_stage_completion(stage, gates)
        self.assertFalse(ok)
        self.assertTrue(any("missing required function" in r for r in reasons))


if __name__ == "__main__":
    unittest.main()
