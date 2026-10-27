"""Tests for Loop 26: Autonomous Swarm Scheduler & Parallel Wave Dispatch.

Tests SwarmScheduler frontier assignment to specialized actors,
SwarmWaveDispatcher parallel execution and receipt aggregation,
and CLI flags --swarm-wave and --swarm-run.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import json
import io
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from contextlib import redirect_stdout
from typing import Dict, Any, List

from core.mesh import (
    ActorMeshRouter,
    ActorSpecialty,
    ArchitectActor,
    CoderActor,
    VerifierActor,
    RemediatorActor
)
from core.swarm.scheduler import SwarmScheduler, ActorAssignment
from core.swarm.wave_dispatcher import SwarmWaveDispatcher, WaveResult


class MockGate:
    """Mock FocusGate gate for scheduler testing."""
    def __init__(self, gate_id: str, title: str, check_cmd: str = "", checked: bool = False, deps: List[str] = None):
        self.id = gate_id
        self.title = title
        self.check_cmd = check_cmd
        self.checked = checked
        self.deps = deps or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "check_cmd": self.check_cmd,
            "checked": self.checked,
            "deps": self.deps
        }


class TestSwarmScheduler(unittest.TestCase):
    """Test specialty matching and assignment logic."""

    def setUp(self):
        self.scheduler = SwarmScheduler()

    def test_specialty_classification(self):
        # Spikes / specs -> ARCHITECT
        g_arch = MockGate("spike-1", "Explore API schema hypothesis", "python3 -c 'print(1)'")
        self.assertEqual(self.scheduler.classify_specialty(g_arch), ActorSpecialty.ARCHITECT)

        # Code implementation -> CODER
        g_code = MockGate("gate-code", "Implement authentication backend", "python3 auth.py")
        self.assertEqual(self.scheduler.classify_specialty(g_code), ActorSpecialty.CODER)

        # Verification / test -> VERIFIER
        g_test = MockGate("gate-verify", "Verify unit test suite", "pytest tests/")
        self.assertEqual(self.scheduler.classify_specialty(g_test), ActorSpecialty.VERIFIER)

        # Failure / heal -> REMEDIATOR
        g_heal = MockGate("gate-heal", "Remediate failing circuit breaker", "focus-gate.py --heal g1")
        self.assertEqual(self.scheduler.classify_specialty(g_heal), ActorSpecialty.REMEDIATOR)

    def test_plan_wave_allocates_assignments(self):
        router = ActorMeshRouter()
        router.register(ArchitectActor("arch-01"))
        router.register(CoderActor("coder-01"))
        router.register(VerifierActor("verif-01"))

        gates = [
            MockGate("spike-proto", "Spike prototype UI"),
            MockGate("gate-core", "Implement core engine"),
            MockGate("gate-tests", "Run verification test suite")
        ]

        assignments = self.scheduler.plan_wave(gates, router=router)
        self.assertEqual(len(assignments), 3)

        by_gate = {a.gate_id: a for a in assignments}
        self.assertEqual(by_gate["spike-proto"].actor_id, "arch-01")
        self.assertEqual(by_gate["gate-core"].actor_id, "coder-01")
        self.assertEqual(by_gate["gate-tests"].actor_id, "verif-01")


class TestSwarmWaveDispatcher(unittest.TestCase):
    """Test parallel wave execution and receipt aggregation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_swarm_test_")
        self.router = ActorMeshRouter()
        self.router.register(ArchitectActor("arch-01"))
        self.router.register(CoderActor("coder-01"))
        self.router.register(VerifierActor("verif-01"))
        self.dispatcher = SwarmWaveDispatcher(router=self.router, max_workers=2)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_run_wave_all_pass(self):
        gates = [
            MockGate("gate-1", "Pass gate 1", check_cmd="python3 -c 'print(\"PASS_1\")'"),
            MockGate("gate-2", "Pass gate 2", check_cmd="python3 -c 'print(\"PASS_2\")'")
        ]

        result = self.dispatcher.run_wave(gates, wave_number=1)
        self.assertTrue(result.all_passed)
        self.assertEqual(result.total_gates, 2)
        self.assertEqual(result.passed_gates, 2)
        self.assertEqual(result.failed_gates, 0)
        self.assertEqual(len(result.receipts), 2)
        self.assertTrue(result.receipts[0].passed)
        self.assertTrue(result.receipts[1].passed)

    def test_run_wave_with_failure(self):
        gates = [
            MockGate("gate-ok", "Passing gate", check_cmd="python3 -c 'print(\"OK\")'"),
            MockGate("gate-fail", "Failing gate", check_cmd="python3 -c 'import sys; sys.exit(1)'")
        ]

        result = self.dispatcher.run_wave(gates, wave_number=1)
        self.assertFalse(result.all_passed)
        self.assertEqual(result.passed_gates, 1)
        self.assertEqual(result.failed_gates, 1)


class TestSwarmCLI(unittest.TestCase):
    """Test CLI dispatch for --swarm-wave and --swarm-run."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_swarm_cli_")
        self.ledger_file = os.path.join(self.temp_dir, "GATES.md")
        with open(self.ledger_file, "w", encoding="utf-8") as f:
            f.write("""# FocusGate Ledger
State: [Step 1 of 2] [0/2 gates met]

## 1. Domain Anchors
- **Core**: Engine domain

## 2. Acceptance Gates
- [ ] gate-1: First fast pass
  CHECK: python3 -c 'print("PASS_1")'
  EXPECT: PASS_1
- [ ] gate-2: Second fast pass
  CHECK: python3 -c 'print("PASS_2")'
  EXPECT: PASS_2
""")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_swarm_wave_json(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(swarm_wave=True, swarm_run=None)
        clean_args = ["--swarm-wave", self.ledger_file, "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertIn("wave_number", output)
        self.assertTrue(output["all_passed"])
        self.assertEqual(output["total_gates"], 2)

    def test_cli_swarm_run_json(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(swarm_run=True, swarm_wave=None)
        clean_args = ["--swarm-run", self.ledger_file, "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertTrue(output["converged"])
        self.assertEqual(output["total_gates_met"], 2)


if __name__ == '__main__':
    unittest.main()
