"""Session Branch DAG Engine for FocusGate v2.8.

Provides non-linear state exploration, immutable checkpoints, branch forking,
time-travel rewind, branch merging, and ephemeral branch garbage collection
to prevent branch sprawl during high-friction or executive dysfunction episodes.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import time
import uuid


@dataclass(frozen=True)
class DAGNode:
    """An immutable checkpoint in the session execution tree."""
    node_id: str
    parent_id: Optional[str]
    branch: str
    state_payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionBranchDAG:
    """Directed Acyclic Graph managing branching session execution contexts."""

    def __init__(self, root_state: Optional[Dict[str, Any]] = None, context_bus=None):
        self.nodes: Dict[str, DAGNode] = {}
        self.branches: Dict[str, str] = {}  # branch_name -> head_node_id
        self.active_branch: str = "main"
        self.turn_counter: int = 0
        self.branch_last_active: Dict[str, int] = {"main": 0}
        self._context_bus = context_bus

        # Initialize root node
        initial_payload = root_state or {"phase": "INITIAL", "status": "PENDING"}
        root_node = DAGNode(
            node_id="root-0",
            parent_id=None,
            branch="main",
            state_payload=initial_payload,
            timestamp=time.time(),
            metadata={"description": "Root session origin"}
        )
        self.nodes[root_node.node_id] = root_node
        self.branches["main"] = root_node.node_id

    def _tick_turn(self) -> None:
        self.turn_counter += 1
        self.branch_last_active[self.active_branch] = self.turn_counter

    def checkpoint(self, state: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> DAGNode:
        """Records an immutable state checkpoint on the active branch."""
        self._tick_turn()
        parent_id = self.branches.get(self.active_branch)
        node_id = f"snap-{uuid.uuid4().hex[:8]}"

        node = DAGNode(
            node_id=node_id,
            parent_id=parent_id,
            branch=self.active_branch,
            state_payload=dict(state),
            timestamp=time.time(),
            metadata=dict(metadata or {})
        )
        self.nodes[node_id] = node
        self.branches[self.active_branch] = node_id
        return node

    def fork_branch(self, branch_name: str, from_node_id: Optional[str] = None) -> DAGNode:
        """Forks a new speculative branch from a specified checkpoint (or branch head)."""
        if branch_name in self.branches:
            raise ValueError(f"Branch '{branch_name}' already exists.")

        self._tick_turn()
        base_node_id = from_node_id or self.branches[self.active_branch]
        if base_node_id not in self.nodes:
            raise KeyError(f"Source node '{base_node_id}' does not exist.")

        base_node = self.nodes[base_node_id]
        fork_node_id = f"fork-{uuid.uuid4().hex[:8]}"

        fork_node = DAGNode(
            node_id=fork_node_id,
            parent_id=base_node_id,
            branch=branch_name,
            state_payload=dict(base_node.state_payload),
            timestamp=time.time(),
            metadata={"forked_from": base_node_id, "source_branch": base_node.branch}
        )
        self.nodes[fork_node_id] = fork_node
        self.branches[branch_name] = fork_node_id
        self.active_branch = branch_name
        self.branch_last_active[branch_name] = self.turn_counter
        return fork_node

    def switch_branch(self, branch_name: str) -> DAGNode:
        """Switches the active branch pointer."""
        if branch_name not in self.branches:
            raise KeyError(f"Branch '{branch_name}' does not exist.")
        self.active_branch = branch_name
        self._tick_turn()
        return self.nodes[self.branches[branch_name]]

    def rewind_to(self, node_id: str) -> DAGNode:
        """Rewinds the active branch head pointer to a historic checkpoint."""
        if node_id not in self.nodes:
            raise KeyError(f"Target node '{node_id}' does not exist.")
        self._tick_turn()
        target_node = self.nodes[node_id]
        self.branches[self.active_branch] = node_id
        return target_node

    def merge_branch(
        self,
        source_branch: str,
        target_branch: str = "main",
        metadata: Optional[Dict[str, Any]] = None
    ) -> DAGNode:
        """Merges a source branch's active state into the target branch."""
        if source_branch not in self.branches:
            raise KeyError(f"Source branch '{source_branch}' does not exist.")
        if target_branch not in self.branches:
            raise KeyError(f"Target branch '{target_branch}' does not exist.")

        self._tick_turn()
        source_head = self.nodes[self.branches[source_branch]]
        target_head = self.nodes[self.branches[target_branch]]

        merge_node_id = f"merge-{uuid.uuid4().hex[:8]}"
        merged_payload = dict(target_head.state_payload)
        # Update with source branch modifications
        merged_payload.update(source_head.state_payload)

        merge_meta = {
            "merged_from_branch": source_branch,
            "merged_from_node": source_head.node_id,
            "target_prior_node": target_head.node_id
        }
        if metadata:
            merge_meta.update(metadata)

        merge_node = DAGNode(
            node_id=merge_node_id,
            parent_id=target_head.node_id,
            branch=target_branch,
            state_payload=merged_payload,
            timestamp=time.time(),
            metadata=merge_meta
        )
        self.nodes[merge_node_id] = merge_node
        self.branches[target_branch] = merge_node_id
        self.active_branch = target_branch
        self.branch_last_active[target_branch] = self.turn_counter
        
        if self._context_bus is not None:
            try:
                from .context_bus import ContextDeltaEvent
                content = f"branch '{source_branch}' merged into '{target_branch}'"
                if metadata:
                    gate_id = metadata.get('gate_id', '')
                    if gate_id:
                        content += f" (gate: {gate_id})"
                content = content[:320]
                delta = ContextDeltaEvent.create(
                    source_agent=source_branch,
                    delta_type="DOMAIN_ANCHOR",
                    content=content,
                )
                self._context_bus.publish(delta)
            except Exception as e:
                import sys
                print(f"[FocusGate] Bus publish (merge) failed: {e}", file=sys.stderr)
                
        return merge_node

    def prune_stale_branches(self, max_idle_turns: int = 3) -> List[str]:
        """Reaps abandoned speculative branches that have been idle for >= max_idle_turns.
        
        Never prunes 'main' or the currently active branch.
        """
        pruned: List[str] = []
        for branch, head_id in list(self.branches.items()):
            if branch == "main" or branch == self.active_branch:
                continue
            last_active = self.branch_last_active.get(branch, 0)
            idle_turns = self.turn_counter - last_active
            if idle_turns >= max_idle_turns:
                del self.branches[branch]
                if branch in self.branch_last_active:
                    del self.branch_last_active[branch]
                pruned.append(branch)
                
                orphaned_nodes = [node_id for node_id, node in self.nodes.items() if node.branch == branch]
                for n_id in orphaned_nodes:
                    del self.nodes[n_id]
        return pruned

    def get_active_node(self) -> DAGNode:
        """Returns the active head node of the current active branch."""
        head_id = self.branches[self.active_branch]
        return self.nodes[head_id]

    def get_history(self, branch: Optional[str] = None) -> List[DAGNode]:
        """Returns the sequential ancestry path from root to the branch head."""
        target_branch = branch or self.active_branch
        if target_branch not in self.branches:
            raise KeyError(f"Branch '{target_branch}' does not exist.")

        curr_id: Optional[str] = self.branches[target_branch]
        trail: List[DAGNode] = []
        visited = set()

        while curr_id and curr_id not in visited:
            node = self.nodes[curr_id]
            trail.append(node)
            visited.add(curr_id)
            curr_id = node.parent_id

        trail.reverse()
        return trail
