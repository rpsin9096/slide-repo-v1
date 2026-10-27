"""FocusGate v3.0 — Polyglot Actor SDK & Client Subsystem.

Provides zero-dependency protocol specifications, Python client connectors,
and shell bridges for cross-language mesh integration.
"""

from core.sdk.protocol_spec import (
    get_protocol_schema,
    validate_rpc_message,
    export_typescript_definitions,
    export_rust_definitions
)
from core.sdk.shell_actor_bridge import FocusGateClient, ClientConnectionError, ShellActorBridge

__all__ = [
    "get_protocol_schema",
    "validate_rpc_message",
    "export_typescript_definitions",
    "export_rust_definitions",
    "FocusGateClient",
    "ClientConnectionError",
    "ShellActorBridge"
]
