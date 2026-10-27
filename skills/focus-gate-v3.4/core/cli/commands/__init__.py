"""Command modules. Importing this package registers every command.

Rules (enforced by tests/test_v33_architecture.py):
  - a module never imports a sibling module; share through `core/`;
  - a handler returns an exit code and never calls sys.exit.
"""
from . import (  # noqa: F401
    audits,
    distributed,
    economy,
    evidence,
    facets,
    focus,
    history,
    ledger_views,
    orchestration,
    routing,
    scaffold,
    spikes,
    swarm_ops,
    verification,
    writing,
)
