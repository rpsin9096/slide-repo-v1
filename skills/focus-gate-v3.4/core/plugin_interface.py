"""FocusGate v2.8 Plugin Interface & Lifecycle Contract.

Defines the abstract base class and context contracts for decoupled sub-skills.
Includes isolated error boundary wrappers, ephemeral context isolation hooks,
and typed Anti-Corruption Layer (ACL) handoff adapters.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
import functools
import sys

from .ephemeral_session import GateReceipt
from .ephemeral_handoff import EphemeralHandoffPacket


@dataclass
class TaskIntent:
    query: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteRecommendation:
    archetype: str
    pipeline: str
    confidence: float
    recommended_facets: List[str]
    seed_action: Dict[str, str]


@dataclass
class ActiveGate:
    id: str
    title: str
    facet: str
    status: str
    check: str
    expect: str
    est_minutes: int = 15


@dataclass
class GateResult:
    gate_id: str
    success: bool
    output: str
    elapsed_ms: float
    next_gate_id: Optional[str] = None
    receipt: Optional[GateReceipt] = None
    diagnostic_snippet: Optional[str] = None
    remedy: Optional[Dict[str, Any]] = None


@dataclass
class HandoffPayload:
    source_plugin: str
    target_plugin: str
    context_data: Dict[str, Any]
    packet: Optional[EphemeralHandoffPacket] = None


@dataclass
class HandoffVerdict:
    accepted: bool
    reason: str
    adapted_payload: Dict[str, Any] = field(default_factory=dict)
    tokens: int = 0


@dataclass
class KernelContext:
    workspace_root: str
    ledger_path: str
    state_vector: Dict[str, Any]
    active_gate: Optional[ActiveGate] = None
    session_id: Optional[str] = None
    retriever: Optional[Any] = None


def isolated_error_boundary(fallback_return: Any = None, is_critical: bool = False):
    """Decorator shielding the kernel from unhandled exceptions in plugin hooks."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                plugin_name = getattr(self, "name", self.__class__.__name__)
                err_msg = f"[Plugin Error Boundary] Exception in {plugin_name}.{func.__name__}: {str(e)}"
                print(err_msg, file=sys.stderr)
                if is_critical:
                    raise RuntimeError(f"Critical failure in {plugin_name}: {str(e)}") from e
                return fallback_return
        return wrapper
    return decorator


class FocusGatePlugin(ABC):
    """Abstract Base Class for all FocusGate v2.8 sub-skill plugins."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique plugin identifier (e.g. 'cognitive', 'engineering', 'design', 'writing')."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable plugin name."""
        pass

    @property
    @abstractmethod
    def context(self) -> str:
        """Bounded context name ('cognitive' | 'navigation' | 'engineering' | 'writing' | 'design')."""
        pass

    @property
    def version(self) -> str:
        return "2.8"

    def on_init(self, context: KernelContext) -> None:
        """Called once during kernel boot to initialize local resources."""
        pass

    def on_route(self, intent: TaskIntent) -> Optional[RouteRecommendation]:
        """Evaluates query intent and returns a routing recommendation if matching."""
        return None

    def on_execute(self, gate: ActiveGate, ctx: KernelContext) -> GateResult:
        """Executes verification or operations associated with an active gate."""
        return GateResult(gate_id=gate.id, success=True, output="Default PASS", elapsed_ms=0.0)

    def on_ephemeral_seed(self, gate: ActiveGate) -> Dict[str, Any]:
        """Provides minimal scoped seed data for an ephemeral session prompt."""
        return {}

    def adapt_incoming_handoff(self, packet: EphemeralHandoffPacket) -> HandoffVerdict:
        """Anti-Corruption Layer (ACL): Translates foreign domain packet into local domain format."""
        return HandoffVerdict(
            accepted=True,
            reason="Default passthrough",
            adapted_payload=packet.delta_payload,
            tokens=packet.total_tokens()
        )

    def on_handoff(self, payload: HandoffPayload) -> HandoffVerdict:
        """Legacy handoff adapter fallback."""
        return HandoffVerdict(accepted=True, reason="Handoff accepted without adaptation")

    def on_teardown(self) -> None:
        """Called when kernel shuts down or task concludes."""
        pass
