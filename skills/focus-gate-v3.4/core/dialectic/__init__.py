"""FocusGate v3.0 — Dialectic & Socratic Peer Review Package."""

from core.dialectic.socratic_mesh import SocraticMeshProtocol, DialecticResult, DialecticRound
from core.dialectic.peer_review import CoherenceReceipt, CoherenceRegistry, AutonomousPeerReviewer

__all__ = [
    "SocraticMeshProtocol",
    "DialecticResult",
    "DialecticRound",
    "CoherenceReceipt",
    "CoherenceRegistry",
    "AutonomousPeerReviewer"
]
