# Orchestrator Brief: {objective_title}

**Role:** Master Orchestrator (FocusGate v2.6.1)  
**Pipeline:** {pipeline_name}  
**Bus Snapshot:** `{context_delta_hash}`  

## 1. Multi-Agent DAG Plan
- Total Stages: {stage_count}
- Frontier Slots: {max_concurrent_agents} max concurrent external AI sessions
- State Bus: `.focusgate/context_bus.jsonl`

### Acceptance Gate Hierarchy
{planned_gates_tree}

## 2. Shared Context Bus Subscriptions
- **RECEIPT**: Broadcasts completed sub-agent deliverables (<=80 tokens each)
- **DOMAIN_ANCHOR**: Broadcasts merged state vectors after coherence verification
- **REORIENT**: Coordinates dynamic re-routing upon friction detection

## 3. Sub-Agent Handoff & Coherence Protocol
1. **Dispatch**: Sub-agent receives isolated brief (`.focusgate/worktrees/agent-{gate_id}/AGENT_PROMPT.md`)
2. **Execution**: Sub-agent operates strictly within assigned facet without global context bloat (<=400 tokens)
3. **Settle**: Sub-agent yields `AgentReceiptBundle` containing `GateReceipt` + evidence hash
4. **Intake**: Orchestrator evaluates 4-tier criteria via `OrchestratorProofTree` (Oracle, Side-Effects, Rigor, Coherence)
5. **Merge**: Validated bundle merged to main branch; downstream DAG frontier unlocked
