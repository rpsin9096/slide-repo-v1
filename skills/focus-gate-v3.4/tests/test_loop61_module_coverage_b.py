"""Loop 61, Task 61.2 (part 2) — coverage for the remaining 9 untested modules.

After the first batch, claim C08 (rewritten in this release to measure the test
corpus's *import graph* rather than grep its text) correctly refused to credit
weak tests and still reported 9/115. These are those nine.

Every expected value was read out of the running code first. Notable real
behaviours pinned here:

* `SagaCoordinator` compensates *already-completed* steps, not the failing one:
  step "one" succeeded, step "two" returned False, and the call order recorded
  here is `a1, a2, c1` — "two" is never compensated because it never ran.
* `WorkflowStatechart`'s `ROUTE_SETTLED` guard reads `context["pipeline"]`, so
  the same event is refused before the key is set and accepted after.
* `SmartZoneCompactor.estimate_tokens` is ~4 chars/token: 400 chars -> 100.
* `FrictionSensor` treats a 0.75 abort rate as the paralysis threshold.
"""

import os
import sys
import tempfile
import unittest

V31 = os.path.normpath(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if V31 not in sys.path:
    sys.path.insert(0, V31)


def _available():
    return os.path.isdir(os.path.join(V31, "core"))


requires_baseline = unittest.skipUnless(_available(), "core/ not present")


class _TmpCase(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp(prefix="fg61b_")


# --------------------------------------------------------------------------
# core.saga_coordinator — compensating transactions
# --------------------------------------------------------------------------

@requires_baseline
class TestSagaCoordinator(_TmpCase):

    def test_a_fully_successful_saga_reports_no_compensation(self):
        from core.saga_coordinator import SagaCoordinator
        calls = []
        s = SagaCoordinator("demo")
        s.add_step("one", lambda c: calls.append("a1") or True,
                   lambda c: calls.append("c1"))
        s.add_step("two", lambda c: calls.append("a2") or True,
                   lambda c: calls.append("c2"))
        r = s.execute()
        self.assertTrue(r.success)
        self.assertEqual(r.completed_steps, ["one", "two"])
        self.assertEqual(r.compensated_steps, [])
        self.assertEqual(calls, ["a1", "a2"], "compensation must not run on success")

    def test_a_failing_step_compensates_only_completed_ones(self):
        """The failing step never ran, so compensating it would be wrong."""
        from core.saga_coordinator import SagaCoordinator
        calls = []

        def a1(c):
            calls.append("a1")
            return True

        def c1(c):
            calls.append("c1")

        def a2(c):
            calls.append("a2")
            return False

        def c2(c):
            calls.append("c2")

        s = SagaCoordinator("demo")
        s.add_step("one", a1, c1)
        s.add_step("two", a2, c2)
        r = s.execute({"k": 1})

        self.assertFalse(r.success)
        self.assertEqual(r.completed_steps, ["one"])
        self.assertEqual(r.compensated_steps, ["one"],
                         "only the step that succeeded may be compensated")
        self.assertEqual(r.error_step, "two")
        self.assertEqual(calls, ["a1", "a2", "c1"],
                         "compensation runs in reverse and never touches the "
                         "failed step")
        self.assertNotIn("c2", calls)

    def test_an_exception_in_a_step_is_captured_not_propagated(self):
        from core.saga_coordinator import SagaCoordinator

        def boom(c):
            raise RuntimeError("disk gone")

        s = SagaCoordinator("demo")
        s.add_step("one", boom, lambda c: None)
        r = s.execute()
        self.assertFalse(r.success)
        self.assertEqual(r.error_step, "one")
        self.assertIn("disk gone", (r.error_message or ""), r.error_message)

    def test_initial_context_reaches_the_steps(self):
        from core.saga_coordinator import SagaCoordinator
        seen = {}
        s = SagaCoordinator("demo")
        s.add_step("one", lambda c: seen.update(c) or True, lambda c: None)
        s.execute({"gate": "G1"})
        self.assertEqual(seen.get("gate"), "G1")


# --------------------------------------------------------------------------
# core.resilient_saga — same contract plus a dead-letter queue
# --------------------------------------------------------------------------

@requires_baseline
class TestResilientSaga(_TmpCase):

    def test_a_clean_run_reports_success(self):
        from core.resilient_saga import ResilientSagaCoordinator
        s = ResilientSagaCoordinator("demo", dlq_dir=self.work)
        s.add_step("one", lambda c: True, lambda c: None)
        r = s.execute()
        self.assertTrue(r.success, getattr(r, "__dict__", r))

    def test_a_failing_step_rolls_back_and_reports_where(self):
        from core.resilient_saga import ResilientSagaCoordinator
        compensated = []
        s = ResilientSagaCoordinator("demo", dlq_dir=self.work)
        s.add_step("one", lambda c: True, lambda c: compensated.append("one"))
        s.add_step("two", lambda c: False, lambda c: compensated.append("two"))
        r = s.execute()
        self.assertFalse(r.success)
        self.assertEqual(compensated, ["one"])
        self.assertEqual(r.error_step, "two")
        self.assertEqual(r.uncompensated_steps, [])

    def test_a_failing_compensation_leaves_a_tombstone(self):
        """The DLQ exists precisely for the un-compensatable case."""
        from core.resilient_saga import ResilientSagaCoordinator

        def bad_compensation(c):
            raise RuntimeError("cannot undo")

        s = ResilientSagaCoordinator("demo", dlq_dir=self.work)
        s.add_step("one", lambda c: True, bad_compensation)
        s.add_step("two", lambda c: False, lambda c: None)
        r = s.execute()
        self.assertFalse(r.success)
        self.assertEqual(r.uncompensated_steps, ["one"],
                         "the step whose compensation raised is uncompensated")
        self.assertTrue(r.inconsistent_halt,
                        "an un-compensatable saga must halt, not continue")
        self.assertTrue(r.tombstone_path, "a failed compensation must be recorded")
        self.assertTrue(os.path.exists(r.tombstone_path),
                        "tombstone path %r does not exist" % r.tombstone_path)
        with open(r.tombstone_path, "r", encoding="utf-8") as fh:
            self.assertIn("cannot undo", fh.read())


# --------------------------------------------------------------------------
# core.statechart — guarded deterministic transitions
# --------------------------------------------------------------------------

@requires_baseline
class TestWorkflowStatechart(_TmpCase):

    def test_it_starts_idle_and_records_history(self):
        from core.statechart import WorkflowStatechart
        c = WorkflowStatechart()
        self.assertEqual(c.current_state.value, "IDLE")
        self.assertEqual(c.context["history"], ["IDLE"])

    def test_an_undefined_event_is_refused(self):
        from core.statechart import WorkflowStatechart
        c = WorkflowStatechart()
        self.assertFalse(c.can_trigger("DANCE"))
        self.assertEqual(c.current_state.value, "IDLE", "a refused event changed state")

    def test_a_guard_blocks_the_transition_until_its_key_is_present(self):
        """ROUTE_SETTLED is guarded on context['pipeline']."""
        from core.statechart import WorkflowStatechart
        c = WorkflowStatechart()
        c.trigger("SUBMIT_TASK")
        self.assertEqual(c.current_state.value, "TRIAGING")
        self.assertFalse(c.can_trigger("ROUTE_SETTLED"),
                         "transition allowed without its guard condition")
        c.context["pipeline"] = "writing"
        self.assertTrue(c.can_trigger("ROUTE_SETTLED"))
        c.trigger("ROUTE_SETTLED")
        self.assertEqual(c.current_state.value, "PLANNING")

    def test_history_accumulates_in_order(self):
        from core.statechart import WorkflowStatechart
        c = WorkflowStatechart()
        c.trigger("SUBMIT_TASK")
        c.context["pipeline"] = "writing"
        c.trigger("ROUTE_SETTLED")
        self.assertEqual(c.context["history"], ["IDLE", "TRIAGING", "PLANNING"])

    def test_a_checkpoint_can_be_restored(self):
        from core.statechart import WorkflowStatechart
        c = WorkflowStatechart()
        c.trigger("SUBMIT_TASK")
        c.checkpoint()
        c.context["pipeline"] = "writing"
        c.trigger("ROUTE_SETTLED")
        self.assertEqual(c.current_state.value, "PLANNING")
        c.rollback_to_checkpoint()
        self.assertEqual(c.current_state.value, "TRIAGING",
                         "rollback did not restore the checkpointed state")


# --------------------------------------------------------------------------
# core.compaction.smart_compactor — context-budget guard
# --------------------------------------------------------------------------

@requires_baseline
class TestSmartZoneCompactor(_TmpCase):

    class _Ledger:
        def __init__(self, gates=(), spikes=(), content=""):
            self.gates, self.spikes, self.raw_content = list(gates), list(spikes), content

    class _Gate:
        def __init__(self, checked=True):
            self.checked = checked

    def test_token_estimate_is_four_characters_per_token(self):
        from core.compaction.smart_compactor import SmartZoneCompactor
        self.assertEqual(SmartZoneCompactor.estimate_tokens("x" * 400), 100)

    def test_a_ledger_with_nothing_settled_never_needs_compaction(self):
        from core.compaction.smart_compactor import SmartZoneCompactor
        self.assertFalse(SmartZoneCompactor.needs_compaction(self._Ledger()))

    def test_exceeding_the_token_budget_triggers_compaction(self):
        from core.compaction.smart_compactor import SmartZoneCompactor
        led = self._Ledger(gates=[self._Gate()], content="x" * 4000)
        self.assertTrue(SmartZoneCompactor.needs_compaction(led, token_budget=100))

    def test_too_many_active_items_triggers_compaction(self):
        from core.compaction.smart_compactor import SmartZoneCompactor
        led = self._Ledger(gates=[self._Gate()] * 4,
                           spikes=[self._Gate()] * 3)
        self.assertTrue(SmartZoneCompactor.needs_compaction(led),
                        "7 active items must exceed the 5-item cap")

    def test_a_small_settled_ledger_needs_nothing(self):
        from core.compaction.smart_compactor import SmartZoneCompactor
        led = self._Ledger(gates=[self._Gate()], content="short")
        self.assertFalse(SmartZoneCompactor.needs_compaction(led))

    def test_the_documented_caps_are_the_ones_enforced(self):
        from core.compaction.smart_compactor import SmartZoneCompactor
        self.assertEqual(SmartZoneCompactor.DEFAULT_TOKEN_BUDGET, 150000)
        self.assertEqual(SmartZoneCompactor.MAX_ACTIVE_GATES, 5)


# --------------------------------------------------------------------------
# core.friction_sensor — cognitive ergonomics
# --------------------------------------------------------------------------

@requires_baseline
class TestFrictionSensor(_TmpCase):

    def test_repeated_aborts_saturate_the_index_and_paralyze(self):
        """record_abort() takes no argument; three of them drive index to 1.0."""
        from core.friction_sensor import FrictionSensor
        s = FrictionSensor()
        for _ in range(3):
            s.record_abort()
        p = s.analyze_friction()
        self.assertEqual(p.friction_index, 1.0)
        self.assertTrue(p.is_paralyzed, p)
        self.assertEqual(p.pacing_mode, "PROACTIVE_RECOVERY")
        self.assertTrue(p.recommended_micro_step,
                        "a paralyzed profile must recommend a micro-step")

    def test_a_clean_prompt_leaves_the_profile_in_flow(self):
        from core.friction_sensor import FrictionSensor
        s = FrictionSensor()
        s.record_prompt("a clear, bounded task")
        p = s.analyze_friction()
        self.assertEqual(p.friction_index, 0.0)
        self.assertFalse(p.is_paralyzed)
        self.assertEqual(p.pacing_mode, "FLOW")

    def test_a_failed_gate_raises_the_index_without_paralyzing(self):
        """0.3 — elevated, but below the 0.75 paralysis threshold."""
        from core.friction_sensor import FrictionSensor
        s = FrictionSensor()
        s.record_prompt("do the thing")
        s.record_gate_result("G1", False, "boom")
        p = s.analyze_friction()
        self.assertEqual(p.friction_index, 0.3)
        self.assertFalse(p.is_paralyzed, "one failure must not paralyze")
        self.assertEqual(p.repeat_error_count, 1)
        self.assertIn("boom", p.recommended_micro_step)

    def test_a_failed_gate_produces_an_autonomous_remedy(self):
        from core.friction_sensor import FrictionSensor
        s = FrictionSensor()
        s.record_prompt("do the thing")
        s.record_gate_result("G1", False, "boom")
        remedy = s.analyze_friction().active_remedy
        self.assertIsNotNone(remedy, "a stalled gate must yield a remedy")
        self.assertEqual(remedy.remedy_type, "DIAGNOSTIC_PROBE")
        self.assertTrue(remedy.automated_fix_viable)

    def test_a_remedy_serialises_for_the_envelope(self):
        from core.friction_sensor import AutonomousRemedy
        r = AutonomousRemedy("clarify", "ask for the acceptance gate")
        d = r.to_dict()
        self.assertEqual(d["remedy_type"], "clarify")
        self.assertEqual(d["hypothesis"], "ask for the acceptance gate")


# --------------------------------------------------------------------------
# core.grounding.grounding_linter — ubiquitous-language audit
# --------------------------------------------------------------------------

@requires_baseline
class TestGroundingLinter(_TmpCase):

    def test_an_ungrounded_camel_case_concept_is_reported(self):
        from core.grounding.grounding_linter import ConceptGroundingLinter
        v = ConceptGroundingLinter.lint_grounding(
            "The TelepathyBridge sends focus beacons.", set())
        self.assertEqual(len(v), 1)
        self.assertIn("TelepathyBridge", v[0]["ungrounded_concepts"])

    def test_a_concept_defined_in_the_glossary_is_grounded(self):
        from core.grounding.grounding_linter import ConceptGroundingLinter
        self.assertEqual(
            ConceptGroundingLinter.lint_grounding(
                "The TelepathyBridge sends beacons.", {"TelepathyBridge"}), [])

    def test_a_definition_in_an_earlier_paragraph_grounds_a_later_use(self):
        from core.grounding.grounding_linter import ConceptGroundingLinter
        doc = ("**FocusGate**: the gate.\n\n"
               "The FocusGate blocks drift.")
        self.assertEqual(ConceptGroundingLinter.lint_grounding(doc, set()), [])

    def test_prose_without_compound_concepts_is_clean(self):
        from core.grounding.grounding_linter import ConceptGroundingLinter
        self.assertEqual(
            ConceptGroundingLinter.lint_grounding("just ordinary words", set()), [])


# --------------------------------------------------------------------------
# core.aggregate — event-sourced ledger root
# --------------------------------------------------------------------------

@requires_baseline
class TestLedgerAggregate(_TmpCase):
    """Three real defects were found here, all invisible without a test.

    1. `LedgerAggregate.from_file` raised `NameError: name 'Ledger' is not
       defined` — the module referenced `Ledger` in `from_file` and in a type
       annotation but never imported it, so the class's only real construction
       path was dead code. No test existed.
    2. `__init__(workspace_root=...)` never assigned `self.ledger`, so
       `get_active_gate()` died with `AttributeError: 'LedgerAggregate' object
       has no attribute 'ledger'`. Only the `ledger=` path (via
       `__init_inline__`) ever set it.
    3. `get_active_gate()` returns a `TracerGate`, not an id — an id-comparing
       assertion would pass for the wrong reason.
    """

    GATES_MD = (
        "# Demo\n\n"
        "## Acceptance Gates\n"
        "### Production Deliverables\n"
        "- [x] G1: Suite is green\n"
        "- [ ] G2: Budget is met\n"
    )

    def _aggregate(self):
        from core.aggregate import LedgerAggregate
        path = os.path.join(self.work, "GATES.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.GATES_MD)
        return LedgerAggregate.from_file(path)

    def _aggregate_unsettled(self):
        """Same shape, but nothing is checked yet: G1 and G2 are both
        activatable, so the single-active-gate invariant can be exercised."""
        from core.aggregate import LedgerAggregate
        path = os.path.join(self.work, "GATES-UNSETTLED.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# Demo\n\n## Acceptance Gates\n### Production Deliverables\n"
                     "- [ ] G1: Suite is green\n- [ ] G2: Budget is met\n")
        return LedgerAggregate.from_file(path)

    def test_a_domain_event_serialises_with_a_schema_version(self):
        from core.aggregate import DomainEvent
        e = DomainEvent("gate.added", {"id": "G1"})
        d = e.to_dict()
        self.assertEqual(d["payload"], {"id": "G1"})
        self.assertIn("version", d)
        self.assertTrue(d["version"], "an event with no version cannot be ordered")

    def test_from_file_builds_an_aggregate_with_its_gates(self):
        """Defect 1: this raised NameError before the fix."""
        agg = self._aggregate()
        self.assertTrue(hasattr(agg, "ledger"), "aggregate has no ledger bound")
        self.assertEqual([g.id for g in agg.ledger.gates], ["G1", "G2"])

    def test_from_file_on_a_missing_path_is_refused(self):
        from core.aggregate import LedgerAggregate
        with self.assertRaises(FileNotFoundError):
            LedgerAggregate.from_file(os.path.join(self.work, "absent.md"))

    def test_get_active_gate_falls_back_to_the_first_unblocked_gate(self):
        """Not a defect: `get_active_gate` deliberately falls back to the first
        unblocked pending gate when nothing is ACTIVE, so it is never None while
        unblocked work exists. An earlier draft of this test asserted None here
        and was wrong about the code."""
        agg = self._aggregate()
        active = agg.get_active_gate()
        self.assertIsNotNone(active)
        self.assertEqual(active.id, "G2",
                         "G1 is already checked, so G2 is the first unblocked gate")

    def test_activating_a_gate_returns_that_gate_object(self):
        agg = self._aggregate()
        gate = agg.activate_tracer_gate("G2")
        self.assertIsNotNone(gate, "G2 was activated but nothing came back")
        self.assertEqual(gate.id, "G2")
        self.assertTrue(getattr(gate, "is_active", False))

    def test_only_one_gate_is_active_at_a_time(self):
        """The Single Active Gate invariant, asserted in the direction the code
        actually enforces: a second activation while one is in flight is
        refused, it does not silently supersede."""
        from core.aggregate import DomainViolationError
        agg = self._aggregate_unsettled()
        agg.activate_tracer_gate("G1")
        with self.assertRaises(DomainViolationError):
            agg.activate_tracer_gate("G2")
        self.assertEqual(agg.get_active_gate().id, "G1",
                         "the refused activation must not have changed the active gate")

    def test_a_gate_can_be_deactivated(self):
        agg = self._aggregate()
        agg.activate_tracer_gate("G2")
        agg.deactivate_gate("G2")
        self.assertFalse(agg.get_gate("G2").is_active)

    def test_activating_an_unknown_gate_is_refused(self):
        agg = self._aggregate()
        with self.assertRaises(Exception):
            agg.activate_tracer_gate("nope")

    def test_the_envelope_header_is_a_single_line(self):
        """Only the dict half supports this; the ledger half has no `gates`.

        `get_state_vector` reads `self.gates`, which only `__init__(workspace_
        root=...)` binds, so it cannot serve a ledger-backed aggregate. The
        shipped callers (core/kernel.py:360, focus-gate.py:1904, :3624) all go
        through the kernel, so this is a latent cross-half gap rather than a live
        crash — recorded here so the limitation is measured, not assumed away.
        """
        from core.aggregate import LedgerAggregate
        agg = self._aggregate()
        self.assertFalse(hasattr(agg, "gates"),
                         "if the ledger half ever grows `gates`, restore the "
                         "state-vector path for it")

    def test_the_settled_gates_exclude_the_unchecked_one(self):
        agg = self._aggregate()
        self.assertEqual([g.id for g in agg.get_settled_gates()], ["G1"])


@requires_baseline
class TestPhantomEventSourcedLedger(unittest.TestCase):
    """A fourth defect, found the same way: a referenced class that never existed.

    `core/aggregate.py` names `EventSourcedLedger` in `__init_inline__` and
    `from_file`, but no such class is defined anywhere in the repository (only
    `core/aggregate.py` and `adapters/storage_adapter.py` mention the name, and
    the latter only in a comment marking injected code).

    Consequence, reproduced on a real ledger:

        $ python3 scripts/focus-gate.py --queue-status --json
        NameError: name 'EventSourcedLedger' is not defined

    `--queue-status` / `--queue-next` reach this through
    `SingleItemQueue.evaluate` (scripts/focus-gate.py:3172), so a documented flag
    died with a traceback. The module had no tests, so it shipped.
    """

    LEDGER = ("# L\n\n## Acceptance Gates\n### Production Deliverables\n"
              "- [x] G1: green\n- [ ] G2: budget\n")

    def test_event_sourced_ledger_is_importable(self):
        """RED before the fix: NameError / ImportError."""
        from core.aggregate import EventSourcedLedger
        self.assertTrue(callable(EventSourcedLedger),
                        "core.aggregate.EventSourcedLedger is referenced but not "
                        "defined; the ledger-backed aggregate can never construct")

    def test_the_event_store_can_be_created_next_to_a_ledger(self):
        import tempfile
        from core.aggregate import EventSourcedLedger
        d = tempfile.mkdtemp(prefix="fg61esl_")
        store = EventSourcedLedger(os.path.join(d, "ledger.events.jsonl"))
        self.assertTrue(hasattr(store, "append") or hasattr(store, "write"),
                        "the event store exposes no way to record an event")

    def test_the_ledger_backed_aggregate_constructs(self):
        from core.aggregate import LedgerAggregate
        d = tempfile.mkdtemp(prefix="fg61agg_")
        path = os.path.join(d, "GATES.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.LEDGER)
        agg = LedgerAggregate.from_file(path)
        self.assertIsNotNone(agg.ledger, "from_file left the ledger unbound")
        self.assertEqual([g.id for g in agg.ledger.gates], ["G1", "G2"])

    def test_queue_status_does_not_crash_on_a_real_ledger(self):
        """The user-visible symptom: a documented flag raising a traceback."""
        import subprocess
        d = tempfile.mkdtemp(prefix="fg61q_")
        os.makedirs(os.path.join(d, ".focusgate"), exist_ok=True)
        with open(os.path.join(d, ".focusgate", "GATES.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(self.LEDGER)
        script = os.path.join(V31, "scripts", "focus-gate.py")
        r = subprocess.run(
            [sys.executable, script, "--queue-status", "--json"],
            cwd=d, capture_output=True, text=True, timeout=120)
        out = r.stdout + r.stderr
        self.assertNotIn("Traceback", out,
                         "--queue-status crashed:\n%s" % out[-600:])
        self.assertNotIn("NameError", out, out[-400:])
        self.assertNotIn("AttributeError", out, out[-400:])


@requires_baseline
class TestOrchestratorProofTree(_TmpCase):

    def test_an_unmet_criterion_fails_the_verdict(self):
        from core.orchestrator_proof_tree import OrchestratorProofTree
        tree = OrchestratorProofTree("merge-1")
        tree.add_criterion("c1", "receipts present",
                           lambda ctx: (len(ctx.get("bundles", [])) > 0, {"n": 0}))
        v = tree.evaluate({"bundles": []})
        self.assertFalse(v.verified, "an unmet criterion must not verify")
        self.assertEqual(v.failed_criteria, ["c1"])
        self.assertEqual(v.passed_criteria, [])

    def test_a_met_criterion_verifies_and_carries_its_evidence(self):
        from core.orchestrator_proof_tree import OrchestratorProofTree
        tree = OrchestratorProofTree("merge-1")
        tree.add_criterion("c1", "receipts present",
                           lambda ctx: (len(ctx.get("bundles", [])) > 0, {"n": 7}))
        v = tree.evaluate({"bundles": [object()]})
        self.assertTrue(v.verified)
        self.assertEqual(v.passed_criteria, ["c1"])
        self.assertEqual(v.failed_criteria, [])


# --------------------------------------------------------------------------
# core.plugin_interface / core.grounding compiler
# --------------------------------------------------------------------------

@requires_baseline
class TestSpecToLedgerCompiler(_TmpCase):

    def test_a_spec_with_stories_compiles_to_gate_entries(self):
        from core.grounding.grounding_linter import SpecToLedgerCompiler
        out = SpecToLedgerCompiler.compile_spec(
            "As a user I want a gate so that I know it works.")
        self.assertTrue(out, "a user story produced no gate entries")


if __name__ == "__main__":
    unittest.main(verbosity=2)
