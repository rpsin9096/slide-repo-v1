"""FocusGate v3.0 — Mesh Chaos Engine.

Injects synthetic packet loss, message poisoning, latency, and actor failure
scenarios into the in-process actor message mesh to evaluate zero-day fault tolerance.

100% Python stdlib, zero external dependencies.
"""

import time
import random
from dataclasses import dataclass, field
from typing import Dict, Any, List, Set, Optional

from core.mesh import ActorMeshRouter, ActorMessage


@dataclass
class ChaosConfig:
    """Configuration governing failure injection probabilities."""
    drop_rate: float = 0.0
    latency_ms: float = 0.0
    poison_rate: float = 0.0


class ChaosMeshInjector:
    """Intercepts and injects adversarial faults into actor message routing."""

    def __init__(self, router: ActorMeshRouter, config: Optional[ChaosConfig] = None):
        self.router = router
        self.config = config or ChaosConfig()
        self.dropped_messages: List[ActorMessage] = []
        self.poisoned_messages: List[ActorMessage] = []
        self.crashed_actors: Set[str] = set()

    def route(self, message: ActorMessage) -> bool:
        """Evaluates chaos rules and dispatches or faults message."""
        # 1. Packet Loss Drop Injection
        if self.config.drop_rate > 0.0 and (self.config.drop_rate >= 1.0 or random.random() < self.config.drop_rate):
            self.dropped_messages.append(message)
            return False

        # 2. Crashed Target Node Check
        if message.target in self.crashed_actors:
            self.dropped_messages.append(message)
            return False

        # 3. Latency Injection
        if self.config.latency_ms > 0.0:
            time.sleep(self.config.latency_ms / 1000.0)

        # 4. Message Poisoning Injection
        if self.config.poison_rate > 0.0 and (self.config.poison_rate >= 1.0 or random.random() < self.config.poison_rate):
            corrupted_payload = dict(message.payload)
            corrupted_payload["_CHAOS_CORRUPTED"] = "CHAOS_CORRUPTED_PAYLOAD_SIGNATURE"
            corrupted_msg = ActorMessage(
                message_id=f"poison-{message.message_id}",
                priority=message.priority,
                source=message.source,
                target=message.target,
                topic=message.topic,
                payload=corrupted_payload,
                timestamp=message.timestamp
            )
            self.poisoned_messages.append(corrupted_msg)
            return self.router.send(corrupted_msg)

        # Normal routing
        return self.router.send(message)

    def simulate_actor_crash(self, actor_id: str) -> None:
        """Simulates immediate crash of an actor node."""
        self.crashed_actors.add(actor_id)
        actor = self.router.get_actor(actor_id)
        if actor:
            actor.state = "STOPPED"

    def is_crashed(self, actor_id: str) -> bool:
        """Checks if actor is in crashed state."""
        return actor_id in self.crashed_actors
