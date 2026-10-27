"""FocusGate v3.0 — Base Swarm Actor & Domain Roles.

Defines the core SwarmActor execution machine and specialized domain actors
(ArchitectActor, CoderActor, VerifierActor, RemediatorActor).

Zero external dependencies (100% Python standard library).
"""

import threading
import time
import subprocess
from enum import Enum
from typing import Dict, Any, Optional, List
from core.mesh.mailbox import ActorMailbox, ActorMessage, MessagePriority


class ActorState(str, Enum):
    """Lifecycle states for swarm actors."""
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    STOPPED = "STOPPED"


class ActorSpecialty(str, Enum):
    """Specialized cognitive roles within the swarm mesh."""
    ARCHITECT = "ARCHITECT"
    CODER = "CODER"
    VERIFIER = "VERIFIER"
    REMEDIATOR = "REMEDIATOR"


class SwarmActor:
    """Base decoupled swarm actor executing tasks via priority mailbox."""

    def __init__(self, actor_id: str, specialty: ActorSpecialty, mailbox_size: int = 100):
        self.actor_id = actor_id
        self.specialty = specialty
        self.state = ActorState.IDLE
        self.mailbox = ActorMailbox(maxsize=mailbox_size)
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self.messages_processed = 0
        self.last_heartbeat = time.time()

    def start(self):
        """Starts the background worker thread for this actor."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, name=f"actor-{self.actor_id}", daemon=True)
        self._thread.start()

    def stop(self):
        """Signals the actor to terminate and wait for thread exit."""
        self._running = False
        self.state = ActorState.STOPPED
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)

    def post(self, message: ActorMessage) -> bool:
        """Enqueues an incoming message into the actor's mailbox."""
        return self.mailbox.put(message)

    def _run_loop(self):
        """Internal execution loop popping and processing mailbox messages."""
        while self._running:
            self.last_heartbeat = time.time()
            msg = self.mailbox.get(timeout=0.1)
            if msg is not None:
                self.state = ActorState.ACTIVE
                try:
                    self.handle_message(msg)
                    self.messages_processed += 1
                except (ValueError, TypeError, RuntimeError, OSError, KeyError):
                    pass
                finally:
                    if self._running:
                        self.state = ActorState.IDLE

    def handle_message(self, message: ActorMessage):
        """Override in subclasses to implement domain logic."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "specialty": self.specialty.value if isinstance(self.specialty, ActorSpecialty) else str(self.specialty),
            "state": self.state.value if isinstance(self.state, ActorState) else str(self.state),
            "queue_depth": self.mailbox.qsize(),
            "messages_processed": self.messages_processed,
            "last_heartbeat": self.last_heartbeat
        }


class ArchitectActor(SwarmActor):
    """Decomposes goals into acceptance gate DAGs and specifications."""

    def __init__(self, actor_id: str = "actor-architect-01"):
        super().__init__(actor_id=actor_id, specialty=ActorSpecialty.ARCHITECT)

    def plan_task(self, query: str) -> Dict[str, Any]:
        """Plans decomposition for a task description."""
        from core.grounding.grounding_linter import SpecToLedgerCompiler
        rendered = SpecToLedgerCompiler.compile_spec(f"# {query}\n1. As system, I want implementation, so that goal succeeds.")
        return {"query": query, "rendered_ledger": rendered}


class CoderActor(SwarmActor):
    """Synthesizes code edits and patches for active acceptance gates."""

    def __init__(self, actor_id: str = "actor-coder-01"):
        super().__init__(actor_id=actor_id, specialty=ActorSpecialty.CODER)


class VerifierActor(SwarmActor):
    """Evaluates acceptance gate checks and test verification invariants."""

    def __init__(self, actor_id: str = "actor-verifier-01"):
        super().__init__(actor_id=actor_id, specialty=ActorSpecialty.VERIFIER)

    def evaluate_gate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executes verification check command for a gate."""
        gate_id = payload.get("gate_id", "gate-unknown")
        cmd = payload.get("check_cmd", "python3 -c 'sys.exit(0)'")
        cwd = payload.get("cwd", ".")

        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return {
            "gate_id": gate_id,
            "passed": proc.returncode == 0,
            "returncode": proc.returncode,
            "output": proc.stdout or proc.stderr
        }


class RemediatorActor(SwarmActor):
    """Diagnoses verification failures and synthesizes prescriptive repairs."""

    def __init__(self, actor_id: str = "actor-remediator-01"):
        super().__init__(actor_id=actor_id, specialty=ActorSpecialty.REMEDIATOR)

    def diagnose_error(self, error_output: str, code: str = "", filename: str = ""):
        """Diagnoses failure traceback against code cliche oracle and AST syntax."""
        from core.self_healing import SelfHealingCoordinator
        coordinator = SelfHealingCoordinator()
        return coordinator.diagnose_failure(error_output, code_content=code, filename=filename)
