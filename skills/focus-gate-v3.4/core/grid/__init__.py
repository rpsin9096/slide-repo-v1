"""FocusGate v3.1 — Adaptive Swarm Grid & Self-Refining Mesh.

Provides dynamic actor persona synthesis, distributed Merkle CRDT networking,
and speculative wave scheduling.
"""

from core.grid.persona_synthesizer import (
    ActorPersona,
    PersonaSynthesizer,
    DynamicSwarmActor,
    PersonaRegistry
)
from core.grid.crdt_mesh import (
    GridNode,
    MerkleCRDTReplicator,
    GridMessage
)
from core.grid.speculative_scheduler import (
    SpeculativeBranch,
    SpeculativeWaveScheduler,
)
from core.grid.byzantine_consensus import (
    QuorumVote,
    ByzantineDetector,
    QuorumVoteCollector,
)
from core.grid.worktree_migrator import (
    MigrationPackage,
    WorktreeMigrator,
    SwarmLoadBalancer,
)

__all__ = [
    "ActorPersona",
    "PersonaSynthesizer",
    "DynamicSwarmActor",
    "PersonaRegistry",
    "GridNode",
    "MerkleCRDTReplicator",
    "GridMessage",
    "SpeculativeBranch",
    "SpeculativeWaveScheduler",
    "QuorumVote",
    "ByzantineDetector",
    "QuorumVoteCollector",
    "MigrationPackage",
    "WorktreeMigrator",
    "SwarmLoadBalancer",
]

