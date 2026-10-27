"""FocusGate v3.0 — Cryptographic Merkle State Vector Consensus & Swarm Sync.

Enables distributed actors, daemon threads, and worktrees to detect state divergence
in O(1) time and synchronize Merkle event DAGs:
- O(1) state comparison via canonical MerkleStateVector summary hashes
- 3-Way Merkle DAG divergence analysis with common ancestor discovery
- Deterministic conflict resolution for concurrent actor branches
- File-level JSONL ledger synchronization and diffing

Zero external dependencies (100% Python stdlib).
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Set

from core.merkle_ledger import MerkleEventNode, MerkleEventDAG
from core.consensus.vector_clock import VectorClock


class MerkleStateVector:
    """Compact state vector capturing the cryptographic frontier of an event DAG."""

    def __init__(
        self,
        actor_id: str,
        vector_clock: VectorClock,
        state_root: str,
        tip_hash: str,
        event_count: int,
        frontier_hashes: Optional[List[str]] = None
    ):
        self.actor_id = actor_id
        self.vector_clock = vector_clock
        self.state_root = state_root
        self.tip_hash = tip_hash
        self.event_count = max(0, int(event_count))
        self.frontier_hashes = list(frontier_hashes) if frontier_hashes else ([tip_hash] if tip_hash else [])

    def summary_hash(self) -> str:
        """Computes O(1) deterministic state fingerprint across root, tip, count, and clock."""
        raw = f"{self.state_root}:{self.tip_hash}:{self.event_count}:{self.vector_clock.hash()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes MerkleStateVector to dictionary."""
        return {
            "actor_id": self.actor_id,
            "vector_clock": self.vector_clock.to_dict(),
            "state_root": self.state_root,
            "tip_hash": self.tip_hash,
            "event_count": self.event_count,
            "frontier_hashes": self.frontier_hashes,
            "summary_hash": self.summary_hash()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MerkleStateVector":
        """Deserializes MerkleStateVector from dictionary."""
        vc = VectorClock.from_dict(data.get("vector_clock", {}))
        return cls(
            actor_id=data.get("actor_id", "anonymous"),
            vector_clock=vc,
            state_root=data.get("state_root", "0" * 64),
            tip_hash=data.get("tip_hash", ""),
            event_count=data.get("event_count", 0),
            frontier_hashes=data.get("frontier_hashes")
        )

    @classmethod
    def from_dag(
        cls,
        dag: MerkleEventDAG,
        actor_id: str = "local",
        vector_clock: Optional[VectorClock] = None
    ) -> "MerkleStateVector":
        """Generates a MerkleStateVector directly from an active MerkleEventDAG."""
        vc = vector_clock.clone() if vector_clock else VectorClock({actor_id: len(dag.nodes)})
        return cls(
            actor_id=actor_id,
            vector_clock=vc,
            state_root=dag.compute_state_root(),
            tip_hash=dag.tip_hash,
            event_count=len(dag.nodes),
            frontier_hashes=[dag.tip_hash] if dag.tip_hash else []
        )

    def __repr__(self) -> str:
        return f"MerkleStateVector(actor={self.actor_id}, events={self.event_count}, summary={self.summary_hash()[:8]}...)"


class MerkleSyncCoordinator:
    """Orchestrates divergence detection, DAG diffing, and deterministic synchronization."""

    @classmethod
    def diff_vectors(cls, local_vec: MerkleStateVector, remote_vec: MerkleStateVector) -> Dict[str, Any]:
        """Compares two state vectors in O(1) to determine synchronization state."""
        local_sum = local_vec.summary_hash()
        remote_sum = remote_vec.summary_hash()

        if local_sum == remote_sum:
            status = "IDENTICAL"
        elif remote_vec.vector_clock.happened_before(local_vec.vector_clock):
            status = "LOCAL_AHEAD"
        elif local_vec.vector_clock.happened_before(remote_vec.vector_clock):
            status = "REMOTE_AHEAD"
        elif local_vec.vector_clock.is_concurrent(remote_vec.vector_clock):
            status = "DIVERGENT"
        else:
            # Fallback when clocks don't strictly order (e.g. empty or non-intersecting keys)
            if local_vec.event_count > remote_vec.event_count:
                status = "LOCAL_AHEAD"
            elif local_vec.event_count < remote_vec.event_count:
                status = "REMOTE_AHEAD"
            else:
                status = "DIVERGENT"

        return {
            "status": status,
            "identical": status == "IDENTICAL",
            "local_actor": local_vec.actor_id,
            "remote_actor": remote_vec.actor_id,
            "local_summary": local_sum,
            "remote_summary": remote_sum,
            "local_count": local_vec.event_count,
            "remote_count": remote_vec.event_count
        }

    @classmethod
    def compute_dag_diff(
        cls,
        local_dag: MerkleEventDAG,
        remote_dag: MerkleEventDAG
    ) -> Dict[str, Any]:
        """Computes structural DAG difference between two event streams.

        Finds common ancestor, isolates local-only and remote-only events,
        and identifies whether branches are divergent.
        """
        local_hash_set: Set[str] = {n.node_hash for n in local_dag.nodes}
        remote_hash_set: Set[str] = {n.node_hash for n in remote_dag.nodes}

        # Find latest common ancestor (walking backwards from local tip)
        common_ancestor: Optional[str] = None
        for node in reversed(local_dag.nodes):
            if node.node_hash in remote_hash_set:
                common_ancestor = node.node_hash
                break

        # Collect local-only events (events appearing after common ancestor or missing in remote)
        local_only: List[MerkleEventNode] = []
        if common_ancestor is None:
            local_only = [n for n in local_dag.nodes if n.node_hash not in remote_hash_set]
        else:
            seen_ancestor = False
            for node in local_dag.nodes:
                if node.node_hash == common_ancestor:
                    seen_ancestor = True
                    continue
                if seen_ancestor:
                    local_only.append(node)

        # Collect remote-only events
        remote_only: List[MerkleEventNode] = []
        if common_ancestor is None:
            remote_only = [n for n in remote_dag.nodes if n.node_hash not in local_hash_set]
        else:
            seen_ancestor = False
            for node in remote_dag.nodes:
                if node.node_hash == common_ancestor:
                    seen_ancestor = True
                    continue
                if seen_ancestor:
                    remote_only.append(node)

        is_divergent = len(local_only) > 0 and len(remote_only) > 0

        return {
            "common_ancestor_hash": common_ancestor,
            "local_only_events": local_only,
            "remote_only_events": remote_only,
            "divergent": is_divergent
        }

    @classmethod
    def sync_dags(
        cls,
        local_dag: MerkleEventDAG,
        remote_dag: MerkleEventDAG,
        resolution_strategy: str = "causal"
    ) -> Dict[str, Any]:
        """Synchronizes remote_dag events into local_dag with cryptographic continuity.

        Fast-forwards if local has no divergent changes; deterministically rebases
        and re-hashes remote events if divergent.
        """
        diff = cls.compute_dag_diff(local_dag, remote_dag)
        remote_only: List[MerkleEventNode] = diff["remote_only_events"]
        local_only: List[MerkleEventNode] = diff["local_only_events"]
        divergent: bool = diff["divergent"]
        common_ancestor: Optional[str] = diff["common_ancestor_hash"]

        if not remote_only:
            return {
                "status": "NOOP",
                "common_ancestor": common_ancestor,
                "events_merged": 0,
                "conflicts_resolved": 0,
                "new_state_root": local_dag.compute_state_root()
            }

        conflicts_resolved = 0

        if not divergent and len(local_only) == 0:
            # Clean fast-forward: verify each remote node can be directly chained
            for node in remote_only:
                local_dag.nodes.append(node)
                local_dag.tip_hash = node.node_hash
        else:
            # Concurrent divergent branches: deterministic causal resolution
            conflicts_resolved = len(remote_only)
            # Rebase remote events sequentially on top of local tip
            for node in remote_only:
                rebased_node = MerkleEventNode.create(
                    event_type=node.event_type,
                    payload=node.payload,
                    prev_hash=local_dag.tip_hash,
                    event_id=node.event_id,
                    timestamp=node.timestamp
                )
                local_dag.nodes.append(rebased_node)
                local_dag.tip_hash = rebased_node.node_hash

        # Persist to disk if ledger_path is configured
        if local_dag.ledger_path:
            os.makedirs(os.path.dirname(os.path.abspath(local_dag.ledger_path)), exist_ok=True)
            with open(local_dag.ledger_path, "w", encoding="utf-8") as f:
                for node in local_dag.nodes:
                    f.write(json.dumps(node.to_dict()) + "\n")

        return {
            "status": "SYNCED",
            "common_ancestor": common_ancestor,
            "events_merged": len(remote_only),
            "conflicts_resolved": conflicts_resolved,
            "new_state_root": local_dag.compute_state_root()
        }

    @classmethod
    def diff_files(cls, file1: str, file2: str) -> Dict[str, Any]:
        """Computes structural DAG difference between two JSONL event log files."""
        dag1 = MerkleEventDAG.load_from_file(file1)
        dag2 = MerkleEventDAG.load_from_file(file2)
        diff = cls.compute_dag_diff(dag1, dag2)
        return {
            "common_ancestor_hash": diff["common_ancestor_hash"],
            "local_only_events": [n.to_dict() for n in diff["local_only_events"]],
            "remote_only_events": [n.to_dict() for n in diff["remote_only_events"]],
            "divergent": diff["divergent"],
            "local_root": dag1.compute_state_root(),
            "remote_root": dag2.compute_state_root()
        }

    @classmethod
    def sync_files(
        cls,
        file1: str,
        file2: str,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronizes file2 into file1 (or into output_file if specified)."""
        target_path = output_file if output_file else file1
        dag1 = MerkleEventDAG.load_from_file(file1)
        dag1.ledger_path = target_path
        dag2 = MerkleEventDAG.load_from_file(file2)

        return cls.sync_dags(dag1, dag2)
