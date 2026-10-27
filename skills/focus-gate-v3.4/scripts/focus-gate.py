#!/usr/bin/env python3
"""FocusGate CLI entry point.

All behavior lives in `core/`: commands in `core/cli/commands/`, the parser in
`core/cli/parser.py`, and the dispatch loop in `core/cli/app.py`. This file only
makes `core` importable and runs `main`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cli.app import main  # noqa: E402
from core.cli.parser import build_parser, print_help  # noqa: E402,F401  (gen_cli_docs and tests read these)
# Backward-compatible re-exports (contract pinned by tests/test_loop22_modular_cli.py).
from core.gates import SpikeGate, SpikeValidator, TracerGate  # noqa: E402,F401
from core.compaction import SmartZoneCompactor  # noqa: E402,F401
from core.grounding import ConceptGroundingLinter, SpecToLedgerCompiler  # noqa: E402,F401

if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError:  # `... | head`: the reader left; not an error
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(0)
