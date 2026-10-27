"""FocusGate v2.8 Core Module Namespace."""

from .kernel import FocusKernel
from .orchestrator_kernel import OrchestratorKernel
from .token_economy import TokenEconomyGovernor, InboundVerdict, FoldedOutput, ContextBudgetGovernor, EphemeralCostGovernor
from .tokens import estimate_tokens
from .tool_matrix import ToolSelectionMatrix, ToolDecision, PatchPreconditionCheck, RecommendedTool
from .ephemeral_session import EphemeralSessionManager, EphemeralSession, GateReceipt
from .ephemeral_handoff import EphemeralHandoffPacket, HandoffCoordinator
from .ephemeral_retriever import EphemeralContextRetriever
from .plugin_interface import FocusGatePlugin, ActiveGate, GateResult, TaskIntent, RouteRecommendation
from .unlazy_guard import ExecutionRigorGuard, RigorInspectionResult, RigorViolation
from .proof_tree import ProofTree, ProofCriterion, ProofVerdict
from .orchestrator_proof_tree import OrchestratorProofTree
from .agent_brief import AgentBrief, AgentReceiptBundle
from .friction_sensor import FrictionSensor, FrictionProfile, AutonomousRemedy
from .session_dag import SessionBranchDAG, DAGNode
from .resilient_saga import ResilientSagaCoordinator, ResilientSagaResult, DLQTombstone
from .statechart import WorkflowStatechart, StatechartState
from .aggregate import LedgerAggregate, DomainEvent
from .oracles import ContrastOracle, SafeZoneValidator, DesignTokenEngine
from .context_bus import SharedContextBus, ContextDeltaEvent, ContextDeltaOverflowError
from .worktree_runner import WorktreeRunner, WorktreeResult, TransactionalMergeResult
from .template_engine import TemplateEngine
from .tool_matrix import ASTSyntaxPreflightGuard

__all__ = [
    "FocusKernel",
    "OrchestratorKernel",
    "TokenEconomyGovernor", "InboundVerdict", "FoldedOutput", "ContextBudgetGovernor", "EphemeralCostGovernor",
    "estimate_tokens",
    "ToolSelectionMatrix", "ToolDecision", "PatchPreconditionCheck", "RecommendedTool", "ASTSyntaxPreflightGuard",
    "EphemeralSessionManager", "EphemeralSession", "GateReceipt",
    "EphemeralHandoffPacket", "HandoffCoordinator",
    "EphemeralContextRetriever",
    "FocusGatePlugin", "ActiveGate", "GateResult", "TaskIntent", "RouteRecommendation",
    "ExecutionRigorGuard", "RigorInspectionResult", "RigorViolation",
    "ProofTree", "ProofCriterion", "ProofVerdict",
    "OrchestratorProofTree", "AgentBrief", "AgentReceiptBundle",
    "FrictionSensor", "FrictionProfile", "AutonomousRemedy",
    "SessionBranchDAG", "DAGNode",
    "ResilientSagaCoordinator", "ResilientSagaResult", "DLQTombstone",
    "WorkflowStatechart", "StatechartState",
    "LedgerAggregate", "DomainEvent",
    "ContrastOracle", "SafeZoneValidator", "DesignTokenEngine",
    "SharedContextBus", "ContextDeltaEvent", "ContextDeltaOverflowError",
    "WorktreeRunner", "WorktreeResult", "TransactionalMergeResult",
    "TemplateEngine"
]
