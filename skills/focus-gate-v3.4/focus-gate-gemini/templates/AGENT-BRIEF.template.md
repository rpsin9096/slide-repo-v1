# Agent Brief: {task_title}

**Assignee:** Subagent Swarm Worker  
**Facet Contract:** {facet_name}  
**Isolation Target:** Isolated worktree or modular file  

## 1. Objective & Scope
{task_summary_and_boundaries}

## 2. Context Pointers (Authoritative Seams)
- `{target_file}`: Implement changes strictly behind this interface contract.
- Invariants: {key_architectural_invariants_and_rules}

## 3. Checkable Completion Criteria
- [ ] `{gate_id}`:
  - Command: `{check_cmd}`
  - Expect: `{expect_pattern}`
  - Timeout: {timeout_sec}s
