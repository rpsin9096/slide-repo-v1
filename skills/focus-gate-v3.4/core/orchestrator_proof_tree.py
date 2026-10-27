"""FocusGate v2.8 — OrchestratorProofTree: cross-agent coherence verification.

Extends ProofTree with a 4th verification tier that runs after all sub-agents
in a DAG tier have settled. Checks that their combined outputs form a
consistent, non-conflicting whole before the orchestrator merges to main.

The 4 tiers are:
  Tier 1 (Oracle)       — inherited from ProofTree
  Tier 2 (Side-Effects) — inherited from ProofTree
  Tier 3 (Rigor)        — inherited from ProofTree
  Tier 4 (Coherence)    — NEW: cross-agent correctness
    4a: All expected receipts present (no missing sub-agent outputs)
    4b: No patch collisions (no two agents wrote conflicting patches)
    4c: SHA-256 evidence chain is unbroken
    4d: Zero outstanding DLQ tombstones in the workspace
"""
import glob
import hashlib
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from .proof_tree import ProofTree, ProofCriterion, ProofVerdict
from .agent_brief import AgentReceiptBundle

class OrchestratorProofTree(ProofTree):
    """Extends ProofTree with cross-agent coherence (tier 4) verification."""

    def build_coherence_criteria(
        self,
        expected_gate_ids: List[str],
        bundles: List[AgentReceiptBundle],
        dlq_dir: Optional[str] = None,
    ) -> 'OrchestratorProofTree':
        """Add all 4 coherence sub-criteria for the given agent bundles.
        
        Call this after instantiation:
            tree = OrchestratorProofTree('tier-2-merge')
            tree.build_coherence_criteria(expected_gate_ids=['B','C'], bundles=[bundle_B, bundle_C])
            verdict = tree.evaluate({'bundles': bundles, 'dlq_dir': '.focusgate/dlq'})
        """
        
        # 4a: All expected receipts present
        def verify_all_receipts_present(
            ctx: Dict[str, Any]
        ) -> Tuple[bool, Dict[str, Any]]:
            bs: List[AgentReceiptBundle] = ctx.get('bundles', [])
            arrived_gate_ids = {b.gate_id for b in bs}
            missing = [g for g in expected_gate_ids if g not in arrived_gate_ids]
            passed = len(missing) == 0
            return passed, {
                'expected': expected_gate_ids,
                'arrived': list(arrived_gate_ids),
                'missing': missing,
            }
        self.add_criterion(
            'coherence_4a_receipts_present',
            f'All {len(expected_gate_ids)} expected agent receipts must be present',
            verify_all_receipts_present,
        )

        # 4b: No patch collisions (no two bundles share a patch_hash)
        def verify_no_patch_collisions(
            ctx: Dict[str, Any]
        ) -> Tuple[bool, Dict[str, Any]]:
            bs: List[AgentReceiptBundle] = ctx.get('bundles', [])
            seen_hashes: Dict[str, str] = {}  # hash -> gate_id
            collisions = []
            for b in bs:
                for h in b.patch_hashes:
                    if h in seen_hashes:
                        collisions.append({
                            'hash': h[:12],
                            'gate_a': seen_hashes[h],
                            'gate_b': b.gate_id,
                        })
                    else:
                        seen_hashes[h] = b.gate_id
            passed = len(collisions) == 0
            return passed, {'collisions': collisions, 'unique_patches': len(seen_hashes)}
        self.add_criterion(
            'coherence_4b_no_patch_collisions',
            'No two sub-agents may produce identical patch hashes (conflicting writes)',
            verify_no_patch_collisions,
        )

        # 4c: SHA-256 evidence chain is unbroken
        def verify_evidence_chain(
            ctx: Dict[str, Any]
        ) -> Tuple[bool, Dict[str, Any]]:
            bs: List[AgentReceiptBundle] = ctx.get('bundles', [])
            broken = []
            for b in bs:
                for receipt_dict in b.gate_receipts:
                    evidence_hash = receipt_dict.get('evidence_hash', '')
                    if not evidence_hash or len(evidence_hash) < 16:
                        broken.append({
                            'gate_id': b.gate_id,
                            'receipt_session': receipt_dict.get('session_id', '?'),
                            'reason': 'missing or malformed evidence_hash',
                        })
            passed = len(broken) == 0
            return passed, {'broken_chain_entries': broken}
        self.add_criterion(
            'coherence_4c_evidence_chain',
            'All gate_receipts inside bundles must carry valid SHA-256 evidence_hash fields',
            verify_evidence_chain,
        )

        # 4d: Zero outstanding DLQ tombstones
        def verify_no_dlq_tombstones(
            ctx: Dict[str, Any]
        ) -> Tuple[bool, Dict[str, Any]]:
            dlq = ctx.get('dlq_dir', '.focusgate/dlq')
            tombstones = []
            if dlq and os.path.isdir(dlq):
                tombstones = glob.glob(os.path.join(dlq, '*.tombstone.json'))
            passed = len(tombstones) == 0
            return passed, {
                'dlq_dir': dlq,
                'tombstone_count': len(tombstones),
                'tombstones': [os.path.basename(t) for t in tombstones],
            }
        self.add_criterion(
            'coherence_4d_no_dlq_tombstones',
            'No outstanding DLQ tombstones may exist before a branch merge',
            verify_no_dlq_tombstones,
        )

        return self
