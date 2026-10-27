"""FocusGate v3.1 — Dynamic Adaptive Actor Persona Synthesizer.

Analyzes task objectives, code AST, and domain ontologies to dynamically synthesize
specialized actor personas with scoped tool affinities and custom verification invariants.

100% Python stdlib, zero external dependencies.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set

from core.mesh.mailbox import ActorMessage, MessagePriority
from core.mesh.actor import SwarmActor, ActorState, ActorSpecialty
from core.mesh.router import ActorMeshRouter


@dataclass
class ActorPersona:
    """Specialized actor persona defining behavioral directives, tool affinities, and invariants."""
    role_id: str
    domain: str
    description: str
    system_prompt: str
    tool_affinity: List[str] = field(default_factory=list)
    verification_invariants: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "domain": self.domain,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "tool_affinity": list(self.tool_affinity),
            "verification_invariants": list(self.verification_invariants)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActorPersona":
        return cls(
            role_id=data.get("role_id", "actor-custom"),
            domain=data.get("domain", "general"),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            tool_affinity=data.get("tool_affinity", []),
            verification_invariants=data.get("verification_invariants", [])
        )


class PersonaSynthesizer:
    """Synthesizes domain-specialized personas from task descriptions and code hints."""

    DOMAIN_ONTOLOGY: Dict[str, Dict[str, Any]] = {
        "database": {
            "keywords": ["database", "table", "schema", "migration", "sql", "postgres", "sqlite", "query", "index", "orm"],
            "tool_affinity": ["sql_query", "schema_inspect", "migrate", "explain_plan", "schema"],
            "system_prompt": "Ensure transactional ACID guarantees, parameterized queries, and idempotent schema migrations.",
            "invariants": ["All queries parameterized", "Migration rollback defined", "Index efficiency verified"]
        },
        "security": {
            "keywords": ["security", "token", "auth", "password", "crypto", "sanitize", "vulnerability", "jail", "injection", "permission", "rbac"],
            "tool_affinity": ["taint_analysis", "sandbox_exec", "crypto_verify", "sanitize"],
            "system_prompt": "Enforce zero-trust boundaries, input sanitization, and principle of least privilege.",
            "invariants": ["Zero untrusted execution", "No hardcoded credentials", "Sanitized input validation"]
        },
        "frontend": {
            "keywords": ["css", "html", "dom", "component", "layout", "accessible", "ui", "style", "view", "react", "tailwind"],
            "tool_affinity": ["dom_inspect", "style_lint", "render_test", "dom"],
            "system_prompt": "Ensure accessible WCAG 2.1 compliance, responsive CSS layouts, and semantic HTML DOM components.",
            "invariants": ["Accessible color contrast", "Semantic DOM hierarchy", "Zero overflow bugs"]
        },
        "performance": {
            "keywords": ["performance", "throughput", "latency", "benchmark", "cpu", "cache", "ring buffer", "optimize", "sub-millisecond", "memory"],
            "tool_affinity": ["perf_profile", "memory_audit", "bench_run", "benchmark"],
            "system_prompt": "Enforce sub-millisecond execution, lock-free concurrency, and bounded memory allocations.",
            "invariants": ["Sub-millisecond latency floor", "Zero memory leak", "Cooperative yielding"]
        }
    }

    def __init__(self):
        self._counter: int = 0

    def synthesize(
        self,
        task_description: str,
        target_files: Optional[List[str]] = None,
        ast_code: Optional[str] = None
    ) -> ActorPersona:
        """Determines best-matching domain and generates a tailored ActorPersona."""
        self._counter += 1
        text = (task_description or "").lower()
        if target_files:
            text += " " + " ".join(target_files).lower()
        if ast_code:
            text += " " + ast_code.lower()

        matched_domain = "general"
        highest_score = 0

        for dom, config in self.DOMAIN_ONTOLOGY.items():
            score = sum(1 for kw in config["keywords"] if re.search(r"\b" + re.escape(kw) + r"\b", text))
            if score > highest_score:
                highest_score = score
                matched_domain = dom

        if matched_domain in self.DOMAIN_ONTOLOGY:
            cfg = self.DOMAIN_ONTOLOGY[matched_domain]
            return ActorPersona(
                role_id=f"actor-{matched_domain}-{self._counter:02d}",
                domain=matched_domain,
                description=f"Specialized {matched_domain} persona for: {task_description[:60]}",
                system_prompt=cfg["system_prompt"],
                tool_affinity=list(cfg["tool_affinity"]),
                verification_invariants=list(cfg["invariants"])
            )

        # Fallback general persona
        return ActorPersona(
            role_id=f"actor-general-{self._counter:02d}",
            domain="general",
            description=f"General engineering persona for: {task_description[:60]}",
            system_prompt="Preserve clean architecture, modular cohesion, and 100% test coverage.",
            tool_affinity=["code_search", "ast_edit", "unit_test", "lint"],
            verification_invariants=["Zero code cliché", "Clean test pass"]
        )


class DynamicSwarmActor(SwarmActor):
    """A specialized SwarmActor configured dynamically from an ActorPersona."""

    def __init__(self, persona: ActorPersona, mailbox_size: int = 100):
        super().__init__(actor_id=persona.role_id, specialty=ActorSpecialty.CODER, mailbox_size=mailbox_size)
        self.persona = persona

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Checks if a tool name is permitted under the persona tool affinity."""
        if not tool_name:
            return True
        for aff in self.persona.tool_affinity:
            if aff in tool_name or tool_name in aff:
                return True
        return False

    def handle_message(self, message: ActorMessage) -> Optional[ActorMessage]:
        """Processes an incoming task message respecting persona boundaries."""
        tool = message.payload.get("tool")
        if tool and not self.is_tool_allowed(tool):
            return ActorMessage(
                source=self.actor_id,
                target=message.source,
                topic="TOOL_REJECTED",
                payload={
                    "success": False,
                    "error": f"Tool '{tool}' not permitted under persona affinity: {self.persona.tool_affinity}"
                }
            )

        # Process and return completed receipt
        return ActorMessage(
            source=self.actor_id,
            target=message.source,
            topic="TASK_COMPLETED",
            payload={
                "success": True,
                "task": message.payload.get("task"),
                "actor_id": self.actor_id,
                "domain": self.persona.domain
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["domain"] = self.persona.domain
        d["persona"] = self.persona.to_dict()
        return d


class PersonaRegistry:
    """Manages active dynamic personas and registers them with the ActorMeshRouter."""

    def __init__(self, router: Optional[ActorMeshRouter] = None):
        self.router = router
        self.actors: Dict[str, DynamicSwarmActor] = {}

    def register_persona(self, persona: ActorPersona) -> DynamicSwarmActor:
        """Creates a DynamicSwarmActor, stores it, and attaches it to the mesh router."""
        actor = DynamicSwarmActor(persona)
        self.actors[persona.role_id] = actor
        if self.router:
            self.router.register(actor)
        return actor


    def get_actor(self, actor_id: str) -> Optional[DynamicSwarmActor]:
        """Retrieves a registered dynamic actor."""
        return self.actors.get(actor_id)

    def list_personas(self) -> List[Dict[str, Any]]:
        """Returns metadata for all registered dynamic personas."""
        return [act.persona.to_dict() for act in self.actors.values()]
