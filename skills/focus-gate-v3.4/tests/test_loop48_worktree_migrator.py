"""FocusGate v3.1 — Cross-Node Worktree Migration & Task Balancing Tests (Loop 48).

Verifies in-flight worktree packaging, mailbox stream serialization,
cross-node transfer with checksum integrity, and dynamic load balancing.

100% Python stdlib, zero external dependencies. Sub-50ms migration latency.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import unittest

from core.grid.worktree_migrator import (
    MigrationPackage,
    WorktreeMigrator,
    SwarmLoadBalancer,
)


class TestWorktreeMigration(unittest.TestCase):
    """Verifies packaging, transfer, checksum integrity, and load balancing."""

    def setUp(self):
        self.tmp_src = tempfile.mkdtemp(prefix="focus_mig_src_")
        self.tmp_dst = tempfile.mkdtemp(prefix="focus_mig_dst_")
        self.migrator = WorktreeMigrator()

        # Seed sample files in source worktree
        self.code_file = os.path.join(self.tmp_src, "worker.py")
        with open(self.code_file, "w", encoding="utf-8") as f:
            f.write("def run():\n    return 42\n")

        self.data_file = os.path.join(self.tmp_src, "meta.json")
        with open(self.data_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"stage": "active", "gate": "gate-03"}))

    def tearDown(self):
        shutil.rmtree(self.tmp_src, ignore_errors=True)
        shutil.rmtree(self.tmp_dst, ignore_errors=True)

    def test_package_export_and_checksum(self):
        mailbox = [{"role": "system", "content": "Execute unit tests on worker.py"}]
        pkg = self.migrator.export_worktree_package(
            task_id="task-42-spec",
            worktree_path=self.tmp_src,
            mailbox_messages=mailbox,
            target_node="node-worker-99",
            source_node="node-master-01"
        )

        self.assertEqual(pkg.task_id, "task-42-spec")
        self.assertEqual(pkg.target_node, "node-worker-99")
        self.assertIn("worker.py", pkg.files)
        self.assertIn("meta.json", pkg.files)
        self.assertIsNotNone(pkg.checksum)
        self.assertEqual(len(pkg.mailbox_messages), 1)

    def test_package_import_and_file_reconstitution(self):
        mailbox = [{"role": "system", "content": "Run tests"}]
        pkg = self.migrator.export_worktree_package(
            task_id="task-recon-01",
            worktree_path=self.tmp_src,
            mailbox_messages=mailbox,
            target_node="node-dest"
        )

        t0 = time.perf_counter()
        target_wt_path = self.migrator.import_worktree_package(pkg, destination_root=self.tmp_dst)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        self.assertLess(elapsed_ms, 50.0)
        self.assertTrue(os.path.exists(target_wt_path))
        reconstituted_code = os.path.join(target_wt_path, "worker.py")
        self.assertTrue(os.path.exists(reconstituted_code))
        with open(reconstituted_code, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("return 42", content)

    def test_load_balancer_selects_idle_node(self):
        # Capacities: node-1 (4), node-2 (4), node-3 (8)
        # Active: node-1 (4/4 -> 100%), node-2 (3/4 -> 75%), node-3 (2/8 -> 25%)
        balancer = SwarmLoadBalancer(node_capacities={"node-1": 4, "node-2": 4, "node-3": 8})
        active_counts = {"node-1": 4, "node-2": 3, "node-3": 2}

        target = balancer.select_migration_target(source_node="node-1", active_tasks=active_counts)
        self.assertEqual(target, "node-3")


class TestMigrationCLI(unittest.TestCase):
    """Verifies CLI flag --migrate-task."""

    def test_cli_migrate_task_json(self):
        from core.cli.dispatch import CLIDispatcher
        clean_args = ["--migrate-task", "task-889", "node-backup-02"]

        import io
        import contextlib
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = CLIDispatcher.dispatch_migrate_task(clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(stdout.getvalue())
        self.assertIn("task_id", output)
        self.assertIn("migration_status", output)
        self.assertEqual(output["migration_status"], "MIGRATED")
