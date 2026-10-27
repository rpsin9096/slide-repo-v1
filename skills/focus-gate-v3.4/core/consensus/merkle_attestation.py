"""FocusGate v3.1 Loop 52 — Merkle Proof Verification & State Attestation.

Generates and verifies cryptographic Merkle inclusion proofs and manages
multi-node state root attestations with 2/3 supermajority quorum validation.

Zero external dependencies (100% Python stdlib).
"""

import time
import math
import hmac
import hashlib
from typing import List, Tuple, Dict, Any, Optional, Set


def _hash_pair(left: str, right: str) -> str:
    """Computes SHA-256 hash over concatenated left and right hex hashes."""
    combined = (left + right).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def build_merkle_tree(leaf_hashes: List[str]) -> Tuple[str, List[List[str]]]:
    """Constructs a binary Merkle tree over a list of leaf hashes.

    Returns:
        (merkle_root_hash, levels) where levels[0] is leaves and levels[-1] is [root].
    """
    if not leaf_hashes:
        empty_root = hashlib.sha256(b"").hexdigest()
        return empty_root, [[empty_root]]

    levels: List[List[str]] = [list(leaf_hashes)]
    current = levels[0]

    # Bound loop iterations strictly to prevent infinite loops
    max_depth = max(len(leaf_hashes).bit_length() + 2, 4)
    depth = 0

    while len(current) > 1 and depth < max_depth:
        depth += 1
        next_level: List[str] = []
        n = len(current)
        for i in range(0, n, 2):
            left = current[i]
            right = current[i + 1] if i + 1 < n else current[i]
            next_level.append(_hash_pair(left, right))
        levels.append(next_level)
        current = next_level

    return current[0], levels


def generate_inclusion_proof(leaf_index: int, levels: List[List[str]]) -> List[Dict[str, str]]:
    """Generates an inclusion proof path for a leaf index in the Merkle tree."""
    proof: List[Dict[str, str]] = []
    idx = leaf_index

    # Traverse from bottom up to root level
    for level in levels[:-1]:
        n = len(level)
        if idx % 2 == 0:
            sibling_idx = idx + 1 if idx + 1 < n else idx
            proof.append({"sibling": level[sibling_idx], "direction": "right"})
        else:
            sibling_idx = idx - 1
            proof.append({"sibling": level[sibling_idx], "direction": "left"})
        idx = idx // 2

    return proof


def verify_inclusion_proof(leaf_hash: str, proof: List[Dict[str, str]], expected_root: str) -> bool:
    """Verifies that leaf_hash belongs to the tree with expected_root using proof path."""
    curr = leaf_hash
    for step in proof:
        sibling = step["sibling"]
        direction = step.get("direction", "right")
        if direction == "right":
            curr = _hash_pair(curr, sibling)
        else:
            curr = _hash_pair(sibling, curr)
    return curr.lower() == expected_root.lower()


class StateAttestation:
    """Cryptographic signed attestation for a mesh state root at an epoch."""

    def __init__(
        self,
        epoch: int,
        state_root: str,
        node_id: str,
        timestamp: Optional[float] = None,
        signature: Optional[str] = None,
        secret: str = "",
    ):
        self.epoch = epoch
        self.state_root = state_root
        self.node_id = node_id
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.signature = signature or self._compute_signature(secret)

    def _compute_signature(self, secret: str) -> str:
        payload = f"{self.epoch}:{self.state_root}:{self.node_id}:{self.timestamp:.4f}".encode("utf-8")
        return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    def verify(self, secret: str = "") -> bool:
        """Verifies HMAC signature integrity."""
        expected = self._compute_signature(secret)
        return hmac.compare_digest(self.signature, expected)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes attestation to dictionary."""
        return {
            "epoch": self.epoch,
            "state_root": self.state_root,
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }


class MeshStateAttestor:
    """Collects and validates multi-node state root attestations for epoch quorums."""

    def __init__(self, secret: str = "") -> None:
        self.secret = secret
        # Map: (epoch, state_root) -> set of valid StateAttestations
        self._attestations: Dict[Tuple[int, str], Dict[str, StateAttestation]] = {}

    def create_attestation(
        self,
        epoch: int,
        state_root: str,
        node_id: str,
        timestamp: Optional[float] = None,
    ) -> StateAttestation:
        """Creates and signs a new state attestation."""
        return StateAttestation(
            epoch=epoch,
            state_root=state_root,
            node_id=node_id,
            timestamp=timestamp,
            secret=self.secret,
        )

    def add_attestation(self, attestation: StateAttestation) -> bool:
        """Validates and records a state attestation from a mesh node."""
        if not attestation.verify(self.secret):
            return False

        key = (attestation.epoch, attestation.state_root)
        if key not in self._attestations:
            self._attestations[key] = {}
        self._attestations[key][attestation.node_id] = attestation
        return True

    def has_quorum_attestation(
        self,
        epoch: int,
        state_root: str,
        total_nodes: int,
        quorum_ratio: float = 2.0 / 3.0,
    ) -> bool:
        """Determines if the state root has achieved 2/3 supermajority attestation."""
        if total_nodes <= 0:
            return False

        key = (epoch, state_root)
        node_records = self._attestations.get(key, {})
        valid_node_count = len(node_records)

        threshold = math.ceil(total_nodes * quorum_ratio)
        return valid_node_count >= threshold
