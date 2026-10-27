"""FocusGate v3.1 — Episodic Immune Memory & Token-Efficient Retrieval (Loop 41).

Pure Python TF-IDF memory store, semantic gotcha retrieval, token-bounded
prompt inoculation (<= 120 tokens), and trajectory ingestion.

100% Python stdlib, zero external dependencies. Sub-5ms retrieval latency.
"""

import os
import re
import json
import math
import time
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import Counter


def _stem(word: str) -> str:
    """Ultra-lightweight suffix stemmer for token matching."""
    word = word.lower()
    for suffix in ("ations", "ation", "tions", "tion", "ating", "ated", "ates", "ate", "ments", "ment", "ing", "ies", "es", "ed", "ly", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[:-len(suffix)]
            break
    if word.endswith("e") and len(word) >= 4:
        word = word[:-1]
    return word


def tokenize(text: str) -> List[str]:
    """Tokenizes text into words and stemmed variants."""
    raw_tokens = re.findall(r'[a-zA-Z0-9_\-\./]+', text.lower())
    tokens: List[str] = []
    for tok in raw_tokens:
        clean = tok.strip(".-_/")
        if not clean:
            continue
        # Split on slashes/dots if compound path
        sub_parts = re.split(r'[/.\-_]', clean)
        tokens.append(clean)
        stemmed = _stem(clean)
        if stemmed != clean:
            tokens.append(stemmed)
        for part in sub_parts:
            if part and part != clean:
                tokens.append(part)
                part_stem = _stem(part)
                if part_stem != part:
                    tokens.append(part_stem)
    return tokens


@dataclass
class EpisodicRecord:
    """An episodic memory unit capturing a past failure mode and its verified resolution."""
    record_id: str
    task_query: str
    failure_mode: str
    resolution: str
    domain: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "task_query": self.task_query,
            "failure_mode": self.failure_mode,
            "resolution": self.resolution,
            "domain": self.domain,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpisodicRecord":
        return cls(
            record_id=data.get("record_id", "rec-unknown"),
            task_query=data.get("task_query", ""),
            failure_mode=data.get("failure_mode", ""),
            resolution=data.get("resolution", ""),
            domain=data.get("domain", "general"),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", time.time()),
        )


class EpisodicMemoryStore:
    """Pure-Python TF-IDF memory store for episodic failure modes and immune gotchas."""

    DEFAULT_GOTCHAS = [
        {
            "record_id": "rec-seed-db01",
            "task_query": "Run database schema migration for user accounts deadlock",
            "failure_mode": "Deadlock on uncommitted schema migration lock",
            "resolution": "Execute migration with lock_timeout set to 2s and retry in exclusive transaction",
            "domain": "database"
        },
        {
            "record_id": "rec-seed-sec01",
            "task_query": "Verify path jail boundaries on macOS tempfile symlink",
            "failure_mode": "Path normalization mismatch between /var and /private/var symlink",
            "resolution": "Use os.path.realpath() on sandbox root path before assertion",
            "domain": "security"
        },
        {
            "record_id": "rec-seed-loop01",
            "task_query": "AST loop termination check infinite spin",
            "failure_mode": "Infinite loop detected in tight spin while True",
            "resolution": "Inject cooperative yield time.sleep or explicit iteration counter",
            "domain": "governance"
        },
        {
            "record_id": "rec-seed-net01",
            "task_query": "Distributed grid node socket port bind",
            "failure_mode": "Address already in use errno 98 / 48 on TCP server restart",
            "resolution": "Set socket.SO_REUSEADDR on socket prior to bind",
            "domain": "networking"
        }
    ]

    def __init__(self, persistence_path: Optional[str] = None):
        self.persistence_path = persistence_path
        self.records: Dict[str, EpisodicRecord] = {}
        self.doc_tokens: Dict[str, List[str]] = {}
        self.doc_freq: Counter = Counter()
        self.doc_weights: Dict[str, Dict[str, float]] = {}
        self.doc_norms: Dict[str, float] = {}
        self._load_from_disk()

    def size(self) -> int:
        return len(self.records)

    def seed_defaults_if_empty(self) -> None:
        """Seeds standard operational gotchas if the store is completely empty."""
        if not self.records:
            for gotcha in self.DEFAULT_GOTCHAS:
                self.index_record(EpisodicRecord.from_dict(gotcha))

    def index_record(self, record: EpisodicRecord) -> None:
        """Indexes an episodic record into the TF-IDF space."""
        self.records[record.record_id] = record

        # Combine text fields, weighting domain and key terms
        text_corpus = f"{record.task_query} {record.failure_mode} {record.resolution} {record.domain} {record.domain}"
        tokens = tokenize(text_corpus)
        self.doc_tokens[record.record_id] = tokens

        # Recompute frequencies and vectors across all docs
        self._rebuild_index()
        self._save_to_disk()

    def _rebuild_index(self) -> None:
        """Recomputes DF, TF-IDF weights, and vector norms across indexed records."""
        self.doc_freq = Counter()
        n_docs = len(self.records)
        if n_docs == 0:
            return

        for rec_id, tokens in self.doc_tokens.items():
            unique_terms = set(tokens)
            for term in unique_terms:
                self.doc_freq[term] += 1

        self.doc_weights.clear()
        self.doc_norms.clear()

        for rec_id, tokens in self.doc_tokens.items():
            tf_counts = Counter(tokens)
            weights: Dict[str, float] = {}
            for term, count in tf_counts.items():
                df = self.doc_freq.get(term, 1)
                idf = math.log((1.0 + n_docs) / (1.0 + df)) + 1.0
                tf = 1.0 + math.log(count)
                weights[term] = tf * idf
            
            norm_sq = sum(w * w for w in weights.values())
            self.doc_weights[rec_id] = weights
            self.doc_norms[rec_id] = math.sqrt(norm_sq) if norm_sq > 0 else 1.0

    def search(self, query: str, limit: int = 5) -> List[Tuple[float, EpisodicRecord]]:
        """Searches memory store using TF-IDF cosine similarity."""
        if not self.records:
            return []

        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        q_counts = Counter(q_tokens)
        n_docs = len(self.records)

        q_weights: Dict[str, float] = {}
        for term, count in q_counts.items():
            df = self.doc_freq.get(term, 0)
            idf = math.log((1.0 + n_docs) / (1.0 + df)) + 1.0
            tf = 1.0 + math.log(count)
            q_weights[term] = tf * idf

        q_norm_sq = sum(w * w for w in q_weights.values())
        if q_norm_sq <= 0:
            return []
        q_norm = math.sqrt(q_norm_sq)

        scored: List[Tuple[float, EpisodicRecord]] = []
        for rec_id, rec in self.records.items():
            doc_w = self.doc_weights.get(rec_id, {})
            doc_norm = self.doc_norms.get(rec_id, 1.0)

            dot_product = 0.0
            for term, q_w in q_weights.items():
                if term in doc_w:
                    dot_product += q_w * doc_w[term]

            if dot_product > 0:
                score = dot_product / (q_norm * doc_norm)
                scored.append((score, rec))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:limit]

    def index_trajectory(self, trajectory: Dict[str, Any]) -> EpisodicRecord:
        """Ingests an agent execution trajectory record into episodic memory."""
        rec_id = trajectory.get("trajectory_id", f"traj-{len(self.records) + 1}")
        task_query = trajectory.get("task", "")
        failure_mode = trajectory.get("error_message", "")
        resolution = trajectory.get("remediation_applied", "")
        domain = trajectory.get("domain", "trajectory")

        rec = EpisodicRecord(
            record_id=rec_id,
            task_query=task_query,
            failure_mode=failure_mode,
            resolution=resolution,
            domain=domain,
            metadata=trajectory,
        )
        self.index_record(rec)
        return rec

    def _load_from_disk(self) -> None:
        if not self.persistence_path or not os.path.exists(self.persistence_path):
            return
        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                rec = EpisodicRecord.from_dict(item)
                self.records[rec.record_id] = rec
                text_corpus = f"{rec.task_query} {rec.failure_mode} {rec.resolution} {rec.domain} {rec.domain}"
                self.doc_tokens[rec.record_id] = tokenize(text_corpus)
            self._rebuild_index()
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            # Corrupted or unreadable persistence file; keep in-memory records
            return

    def _save_to_disk(self) -> None:
        if not self.persistence_path:
            return
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.persistence_path)), exist_ok=True)
            data = [rec.to_dict() for rec in self.records.values()]
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except (OSError, TypeError):
            # Filesystem write error; abort persistence cleanly
            return


class ImmuneMemoryRetriever:
    """Token-bounded prompt inoculation engine for sub-5ms immune memory retrieval."""

    def __init__(self, store: Optional[EpisodicMemoryStore] = None, max_tokens: int = 120):
        self.store = store if store is not None else EpisodicMemoryStore()
        self.max_tokens = max_tokens

    def get_immune_inoculation(self, query: str, min_score: float = 0.05) -> str:
        """Retrieves matching failure modes and formats a token-bounded prompt warning block."""
        results = self.store.search(query, limit=2)
        matches = [rec for score, rec in results if score >= min_score]
        if not matches:
            return ""

        lines = ["### Immune Memory Prior Gotchas:"]
        for rec in matches:
            lines.append(f"- [{rec.domain.upper()}] Gotcha: {rec.failure_mode}")
            lines.append(f"  Fix: {rec.resolution}")

        inoculation = "\n".join(lines)

        # Enforce strict token ceiling: words * 1.3 <= max_tokens
        words = inoculation.split()
        if len(words) * 1.3 > self.max_tokens:
            max_words = max(1, int(self.max_tokens / 1.3))
            inoculation = " ".join(words[:max_words]) + "..."

        return inoculation

    def inoculate_brief(self, base_prompt: str, task_query: str) -> str:
        """Injects relevant immune memory gotchas into an agent task brief."""
        inoculation = self.get_immune_inoculation(task_query)
        if not inoculation:
            return base_prompt
        return f"{base_prompt}\n\n{inoculation}"
