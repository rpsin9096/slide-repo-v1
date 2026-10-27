# FocusGate Production Ledger: {task_name}
State: [Pipeline: {pipeline_name} (1/{total_steps})] [Stage: {active_stage}] [Queue: 1 active, {buffered_count} buffered] [Est: {est_minutes} min]

## 1. Domain Anchors (Micro-Glossary, ≤ 5 Terms)
- **{CanonicalTerm}**: {Clear definition of core domain concept.}
  _Avoid_: {Misleading or generic terms to avoid.}

## 2. Acceptance Gates (Single-Item Active Queue)

### Production Gates
- [ ] gate-01: {active_gate_title}
  DEPS: []
  CHECK: {executable_command_or_test_case}
  EXPECT: {expected_output_pattern}

- [ ] gate-02: {buffered_gate_title}
  DEPS: [gate-01]
  CHECK: {executable_command_or_test_case}
  EXPECT: {expected_output_pattern}

## 3. Micro-ADR Ledger
- **[ADR-001] {decision_title}**: Context: {context}. Decision: {decision}. Consequences: {consequences}.
