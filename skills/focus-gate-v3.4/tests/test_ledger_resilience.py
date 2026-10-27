#!/usr/bin/env python3
"""TDD regression: ledger loader must survive corrupt non-UTF8 bytes."""

import os
import sys
import tempfile
import unittest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
V271_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))
if V271_ROOT not in sys.path:
    sys.path.insert(0, V271_ROOT)

from adapters.storage_adapter import SQLiteStorageAdapter


class TestLedgerResilience(unittest.TestCase):
    def test_01_corrupt_jsonl_does_not_crash_loader(self):
        with tempfile.TemporaryDirectory() as td:
            bad_path = os.path.join(td, "ledger.events.jsonl")
            with open(bad_path, "wb") as f:
                f.write(b'{"valid": 1}\n')
                f.write(b'\x99\xff binary garbage \x99\n')
                f.write(b'{"valid": 2}\n')
            try:
                store = SQLiteStorageAdapter(bad_path)
            except UnicodeDecodeError as e:
                self.fail(f"Loader crashed on corrupt bytes: {e}")
            self.assertIsNotNone(store.events)


if __name__ == "__main__":
    unittest.main()
