"""FocusGate v3.0 — Polyglot Protocol Specification.

Defines the JSON-RPC over Unix domain socket / line-delimited message protocol,
including machine-readable JSON Schema, TypeScript definitions, and Rust type models.

100% Python stdlib, zero external dependencies.
"""

from typing import Dict, Any, Tuple, Optional, List

PROTOCOL_VERSION = "3.0.0"

SUPPORTED_METHODS = [
    "ping",
    "status",
    "get_events",
    "eval_gate",
    "stop"
]


def get_protocol_schema() -> Dict[str, Any]:
    """Generates a complete JSON Schema (Draft 2020-12) for FocusGate IPC messages."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "FocusGateIPCMessage",
        "description": f"FocusGate v{PROTOCOL_VERSION} Polyglot Line-Delimited IPC Specification",
        "type": "object",
        "required": ["method"],
        "properties": {
            "method": {
                "type": "string",
                "enum": SUPPORTED_METHODS,
                "description": "RPC method identifier to invoke on the FocusGate supervisor"
            },
            "params": {
                "type": "object",
                "description": "Optional parameters payload for the method invocation",
                "default": {}
            },
            "id": {
                "type": ["string", "integer", "null"],
                "description": "Optional correlation identifier for matching requests with responses"
            }
        },
        "additionalProperties": False,
        "definitions": {
            "StreamEvent": {
                "type": "object",
                "required": ["event_id", "event_type", "payload", "timestamp"],
                "properties": {
                    "event_id": {"type": "string"},
                    "event_type": {"type": "string"},
                    "payload": {"type": "object"},
                    "timestamp": {"type": "number"}
                }
            },
            "SupervisorStatus": {
                "type": "object",
                "required": ["running", "socket_path", "workspace_root", "tracked_files"],
                "properties": {
                    "running": {"type": "boolean"},
                    "uptime_seconds": {"type": "number"},
                    "socket_path": {"type": "string"},
                    "workspace_root": {"type": "string"},
                    "tracked_files": {"type": "integer"},
                    "events_buffered": {"type": "integer"},
                    "actors": {
                        "type": "array",
                        "items": {"type": "object"}
                    }
                }
            }
        }
    }


def validate_rpc_message(msg: Any) -> Tuple[bool, Optional[str]]:
    """Validates an incoming RPC message against the protocol specification."""
    if not isinstance(msg, dict):
        return False, "Message must be a JSON object"

    if "method" not in msg:
        return False, "Missing required field: 'method'"

    method = msg["method"]
    if not isinstance(method, str) or not method.strip():
        return False, "Field 'method' must be a non-empty string"

    if method not in SUPPORTED_METHODS:
        return False, f"Unsupported method '{method}'. Supported methods: {', '.join(SUPPORTED_METHODS)}"

    if "params" in msg and not isinstance(msg["params"], dict):
        return False, "Field 'params' must be an object if present"

    return True, None


def export_typescript_definitions() -> str:
    """Exports TypeScript types and interfaces for external actors."""
    return f"""// FocusGate v{PROTOCOL_VERSION} — Polyglot TypeScript SDK Definitions
// Generated automatically by FocusGate Protocol Spec Engine.

export type FocusGateMethod = "ping" | "status" | "get_events" | "eval_gate" | "stop";

export interface FocusGateMessage {{
  method: FocusGateMethod;
  params?: Record<string, unknown>;
  id?: string | number;
}}

export interface FocusGateResponse<T = unknown> {{
  result?: T;
  error?: string;
  id?: string | number;
}}

export interface SupervisorStatus {{
  running: boolean;
  uptime_seconds: number;
  socket_path: string;
  workspace_root: string;
  tracked_files: number;
  events_buffered: number;
  actors: Array<Record<string, unknown>>;
}}

export interface StreamEvent {{
  event_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  timestamp: number;
}}
"""


def export_rust_definitions() -> str:
    """Exports Rust serde definitions for native external actors."""
    return f"""// FocusGate v{PROTOCOL_VERSION} — Polyglot Rust SDK Definitions
// Generated automatically by FocusGate Protocol Spec Engine.

use serde::{{Deserialize, Serialize}};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum FocusGateMethod {{
    Ping,
    Status,
    GetEvents,
    EvalGate,
    Stop,
}}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FocusGateMessage {{
    pub method: FocusGateMethod,
    #[serde(default)]
    pub params: Option<serde_json::Value>,
    #[serde(default)]
    pub id: Option<String>,
}}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SupervisorStatus {{
    pub running: bool,
    pub uptime_seconds: f64,
    pub socket_path: String,
    pub workspace_root: String,
    pub tracked_files: usize,
    pub events_buffered: usize,
    pub actors: Vec<serde_json::Value>,
}}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StreamEvent {{
    pub event_id: String,
    pub event_type: String,
    pub payload: serde_json::Value,
    pub timestamp: f64,
}}
"""
