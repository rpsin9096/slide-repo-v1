<!-- ARCHIVED. This document describes FocusGate v2.4 and is SUPERSEDED: v2.8 and then v3.0. Its bounded contexts no longer match `core/`.
     Moved here by FocusGate v3.2 Loop 65 (AUDIT F18). Kept, not deleted, so the
     decision is on the record. Do not implement against it; read SPEC.md,
     ROADMAP.md and SKILL.md instead. -->

# FocusGate v2.4: Bounded Context Map & Distributed Topologies
## Resilient Subsystems, Governance Boundaries & Fault Recovery

**Context Map Version:** 2.4.0  

---

## 1. Context Relationship Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                   FOCUSGATE v2.4 RESILIENT KERNEL                      │
│        (Budget Governor, Precedence Sieve, Resilient Saga)             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                         Internal Event Ledger & DLQ
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
┌──────────────┐             ┌──────────────┐             ┌──────────────┐
│  Cognitive   │             │ Engineering  │             │    Design    │
│    Plugin    │             │    Plugin    │             │    Plugin    │
│  [Upstream]  │             │  [Upstream]  │             │  [Upstream]  │
└──────┬───────┘             └──────┬───────┘             └──────┬───────┘
       │                            │                            │
       └────────────────────────────┼────────────────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Writing Plugin     │
                         │     [Downstream]     │
                         │ (Anti-Corruption ACL)│
                         └──────────────────────┘
```

---

## 2. Bounded Context Definitions

1. **Budget Governance Context**: Houses the `ContextBudgetGovernor` and input sanitization filters, establishing a protective boundary against prompt bloat before intent dispatch.
2. **Deterministic Precedence Context**: Contains the `HierarchicalPrecedenceSieve` and operational tier weighting rules that resolve competing route recommendations.
3. **Resilient Recovery Context**: Manages `ResilientSagaCoordinator`, compensation execution, and persistent `.focusgate/dlq/` tombstones.
4. **State Exploration Context**: Encapsulates `SessionBranchDAG`, immutable checkpoint trees, and the `EphemeralBranchPruner`.
5. **Execution Plugins**: Modular sub-skills communicating over typed interfaces with isolated error boundaries.
