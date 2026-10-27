"""FocusGate v3.0 — Actor Mesh Router & Message Dispatcher.

Manages the registration, point-to-point routing, topic broadcast, and
dead-letter tracking across the autonomous swarm actor mesh.

Zero external dependencies (100% Python standard library).
"""

import threading
from typing import Dict, Any, Optional, List
from core.mesh.actor import SwarmActor
from core.mesh.mailbox import ActorMessage


class ActorMeshRouter:
    """Thread-safe routing hub managing actor registry and message dispatch."""

    def __init__(self):
        self._actors: Dict[str, SwarmActor] = {}
        self._lock = threading.Lock()
        self.dead_letters: List[ActorMessage] = []

    @property
    def actors(self) -> Dict[str, SwarmActor]:
        """Returns a snapshot dictionary of registered actors."""
        with self._lock:
            return dict(self._actors)

    def register(self, actor: SwarmActor):
        """Registers a swarm actor with the routing mesh."""
        with self._lock:
            self._actors[actor.actor_id] = actor

    def unregister(self, actor_id: str) -> Optional[SwarmActor]:
        """Unregisters an actor by ID."""
        with self._lock:
            return self._actors.pop(actor_id, None)

    def get_actor(self, actor_id: str) -> Optional[SwarmActor]:
        """Retrieves a registered actor by ID."""
        with self._lock:
            return self._actors.get(actor_id)

    def list_actors(self) -> List[SwarmActor]:
        """Returns snapshot of all registered actors."""
        with self._lock:
            return list(self._actors.values())

    def send(self, message: ActorMessage) -> bool:
        """Routes a point-to-point message to its destination actor."""
        if message.target == "broadcast":
            return self.broadcast(message) > 0

        with self._lock:
            actor = self._actors.get(message.target)

        if actor is not None:
            return actor.post(message)
        else:
            with self._lock:
                self.dead_letters.append(message)
            return False

    def broadcast(self, message: ActorMessage) -> int:
        """Broadcasts a message to all registered peers except the sender."""
        with self._lock:
            peers = [a for aid, a in self._actors.items() if aid != message.source]

        delivered = 0
        for peer in peers:
            if peer.post(message):
                delivered += 1
        return delivered

    def get_status(self) -> Dict[str, Any]:
        """Returns observable telemetry on the actor mesh."""
        with self._lock:
            actors_data = [a.to_dict() for a in self._actors.values()]
            dead_count = len(self.dead_letters)

        return {
            "total_registered": len(actors_data),
            "total_active": sum(1 for a in actors_data if a["state"] == "ACTIVE"),
            "actors": actors_data,
            "dead_letter_count": dead_count
        }

    def shutdown(self):
        """Stops all registered actors and clears registry."""
        with self._lock:
            actors = list(self._actors.values())
            self._actors.clear()

        for a in actors:
            a.stop()
