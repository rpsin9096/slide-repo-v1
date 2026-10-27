"""FocusGate v3.1 — Episodic Immune Memory & Token-Efficient Retrieval Tests (Loop 41).

Verifies pure-Python TF-IDF episodic memory store, semantic gotcha retrieval,
token-bounded prompt inoculation (<= 120 tokens), and CLI dispatch.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import json
import time
import unittest

from core.memory.episodic_cache import (
    EpisodicRecord,
    EpisodicMemoryStore,
    ImmuneMemoryRetriever
)


class TestEpisodicMemoryStore(unittest.TestCase):
    """Verifies TF-IDF indexing, cosine similarity scoring, and trajectory ingestion."""

    def setUp(self):
        self.store = EpisodicMemoryStore()
        self.record1 = EpisodicRecord(
            record_id="rec-001",
            task_query="Run database schema migration for user accounts",
            failure_mode="SQLite lock timeout on unindexed column migration",
            resolution="Wrap schema alter in exclusive transaction and create index first",
            domain="database"
        )
        self.record2 = EpisodicRecord(
            record_id="rec-002",
            task_query="Verify path jail boundaries on macOS tempfile",
            failure_mode="Path normalization mismatch between /var and /private/var symlink",
            resolution="Use os.path.realpath() on sandbox root path before assertion",
            domain="security"
        )
        self.store.index_record(self.record1)
        self.store.index_record(self.record2)

    def test_store_size_and_indexing(self):
        self.assertEqual(self.store.size(), 2)

    def test_semantic_search_matches_relevant_domain(self):
        # Query about database indexing
        results = self.store.search("database migration index failure", limit=1)
        self.assertEqual(len(results), 1)
        score, rec = results[0]
        self.assertGreater(score, 0.2)
        self.assertEqual(rec.record_id, "rec-001")
        self.assertEqual(rec.domain, "database")

    def test_semantic_search_matches_macos_symlink(self):
        # Query about macOS path jail
        results = self.store.search("macOS path jail symlink /private/var", limit=1)
        self.assertEqual(len(results), 1)
        score, rec = results[0]
        self.assertGreater(score, 0.2)
        self.assertEqual(rec.record_id, "rec-002")

    def test_ingest_trajectory_record(self):
        trajectory = {
            "trajectory_id": "traj-fail-01",
            "task": "AST loop termination check",
            "verification_status": "FAILED",
            "error_message": "Infinite loop detected in tight spin while True",
            "remediation_applied": "Inject time.sleep cooperative yield or termination counter"
        }
        rec = self.store.index_trajectory(trajectory)
        self.assertIsNotNone(rec)
        self.assertEqual(self.store.size(), 3)
        self.assertIn("loop", rec.failure_mode.lower())


class TestImmuneMemoryRetriever(unittest.TestCase):
    """Verifies fast-path retrieval, token bounding (<=120 tokens), and prompt inoculation."""

    def setUp(self):
        self.store = EpisodicMemoryStore()
        self.store.index_record(EpisodicRecord(
            record_id="rec-001",
            task_query="Postgres SQL table index migration",
            failure_mode="Deadlock on uncommitted schema migration lock",
            resolution="Execute migration with lock_timeout set to 2s and retry",
            domain="database"
        ))
        self.retriever = ImmuneMemoryRetriever(store=self.store, max_tokens=120)

    def test_sub_5ms_retrieval_speed(self):
        t0 = time.perf_counter()
        inoculation = self.retriever.get_immune_inoculation("Postgres SQL table migration")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        self.assertLess(elapsed_ms, 5.0)
        self.assertIn("Immune Memory", inoculation)
        self.assertIn("Deadlock", inoculation)

    def test_token_bounding_strict_ceiling(self):
        inoculation = self.retriever.get_immune_inoculation("Postgres SQL table migration")
        # 1 token is ~4 chars in English text
        est_tokens = len(inoculation.split()) * 1.3
        self.assertLessEqual(est_tokens, 120)

    def test_inoculate_brief_injection(self):
        base_prompt = "You are a specialized CoderActor.\n\nTask: Migrate user table."
        inoculated = self.retriever.inoculate_brief(base_prompt, "Migrate user table SQL")
        self.assertIn("Immune Memory", inoculated)
        self.assertIn("You are a specialized CoderActor", inoculated)
        self.assertIn("Deadlock on uncommitted schema", inoculated)


class TestMemoryCLI(unittest.TestCase):
    """Verifies CLI flag --memory-search."""

    def test_cli_memory_search_json(self):
        from core.cli.dispatch import CLIDispatcher
        clean_args = ["--memory-search", "database schema migration deadlock"]

        import io
        import contextlib
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = CLIDispatcher.dispatch_memory_search(clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(stdout.getvalue())
        self.assertIn("query", output)
        self.assertIn("matches", output)
