# Agent Brief: {task_title}

**Assignee:** Subagent / Worktree Swarm Worker  
**Isolation Target:** `.focusgate/worktrees/{gate_id}`  

## 1. Objective & Scope
{task_summary}

## 2. Context Pointers (Authoritative Seams)
- `{target_file}`: Implement changes strictly behind this interface.
- Consult `{reference_doc}` for architectural invariants.

## 3. Checkable Completion Criteria
- [ ] `{gate_id}`:
  - Command: `{check_cmd}`
  - Expect: `{expect_pattern}`
  - Timeout: {timeout_sec}s
