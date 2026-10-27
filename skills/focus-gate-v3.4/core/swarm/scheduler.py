"""FocusGate v3.0 — Autonomous Swarm Scheduler & Work Allocator.

Analyzes DAG frontier gates and maps them to specialized swarm actors
(Architect, Coder, Verifier, Remediator) based on task semantics and verification criteria.

Zero external dependencies (100% Python stdlib).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from core.mesh import ActorSpecialty, ActorMeshRouter


@dataclass
class ActorAssignment:
    """An assignment allocating a specific gate or spike to a specialized actor."""
    gate_id: str
    actor_id: str
    specialty: ActorSpecialty
    check_cmd: str = ""
    title: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes assignment to dictionary."""
        return {
            "gate_id": self.gate_id,
            "actor_id": self.actor_id,
            "specialty": self.specialty.value,
            "check_cmd": self.check_cmd,
            "title": self.title,
            "payload": self.payload
        }


class SwarmScheduler:
    """Allocates DAG frontier gates across specialized swarm actors."""

    @classmethod
    def classify_specialty(cls, gate: Any) -> ActorSpecialty:
        """Determines the best actor specialty for a given gate or spike."""
        gid = (getattr(gate, "id", None) or getattr(gate, "gate_id", "") or "").lower()
        title = getattr(gate, "title", "").lower()
        cmd = (getattr(gate, "check_cmd", "") or "").lower()

        # 1. Remediator: healing, failure mitigation
        if "heal" in gid or "heal" in title or "heal" in cmd or "remediat" in title:
            return ActorSpecialty.REMEDIATOR

        # 2. Architect: spikes, exploration, prototypes, schemas, architecture
        if (gid.startswith("spike") or "spike" in gid or "prototype" in title or
                "explore" in title or "schema" in title or "design" in title or "rfc" in title):
            return ActorSpecialty.ARCHITECT

        # 3. Verifier: tests, test runner execution, validation
        if ("verify" in title or "test" in title or "pytest" in cmd or
                "unittest" in cmd or "lint" in cmd or "audit" in cmd or "check" in title):
            return ActorSpecialty.VERIFIER

        # 4. Coder: standard implementation and coding gates
        return ActorSpecialty.CODER

    def find_actor_for_specialty(
        self,
        specialty: ActorSpecialty,
        router: Optional[ActorMeshRouter] = None
    ) -> str:
        """Finds a matching registered actor in the router or returns a canonical ID."""
        if router:
            for actor_id, actor in router.actors.items():
                if actor.specialty == specialty:
                    return actor_id
        return f"actor-{specialty.value.lower()}-01"

    def plan_wave(
        self,
        frontier_gates: List[Any],
        router: Optional[ActorMeshRouter] = None
    ) -> List[ActorAssignment]:
        """Plans a parallel execution wave assigning each frontier gate to an actor."""
        assignments: List[ActorAssignment] = []
        for gate in frontier_gates:
            specialty = self.classify_specialty(gate)
            actor_id = self.find_actor_for_specialty(specialty, router=router)
            assignment = ActorAssignment(
                gate_id=getattr(gate, "id", None) or getattr(gate, "gate_id", ""),
                actor_id=actor_id,
                specialty=specialty,
                check_cmd=getattr(gate, "check_cmd", "") or "",
                title=getattr(gate, "title", "") or "",
                payload=gate.to_dict() if hasattr(gate, "to_dict") else {}
            )
            assignments.append(assignment)
        return assignments
