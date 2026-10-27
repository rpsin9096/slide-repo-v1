# FocusGate Production Ledger: {task_name}
State: [Pipeline: {pipeline_name} (1/{total_steps})] [Stage: {active_stage}] [Queue: 1 active, {buffered_count} buffered] [Est: {est_minutes} min] [Depth: L2]

## 1. Domain Anchors (Micro-Glossary, ≤ 5 Terms)
- **{canonical_term}**: {term_definition}
  _Replaces_: {term_replaces}

## 2. Acceptance Gates (Single-Item Active Queue)

### Spikes (Throwaway Explorations)
- [ ] spike-logic-{spike_name}: Test state machine hypothesis
  BRANCH: logic
  QUESTION: {spike_question}
  ARTIFACT: .focusgate/prototypes/{spike_name}.html
  CHECK: python3 {cli_path} --verify-spike .focusgate/prototypes/{spike_name}.html
  EXPECT: VALID_LOGIC_PROTOTYPE

### Production Gates
- [ ] gate-01: {active_gate_title}
  DEPS: []
  CHECK: {gate_01_check}
  EXPECT: {gate_01_expect}

- [ ] gate-02: {buffered_gate_title}
  DEPS: [gate-01]
  CHECK: {gate_02_check}
  EXPECT: {gate_02_expect}

## 3. Micro-ADR Ledger
- **None yet.**
