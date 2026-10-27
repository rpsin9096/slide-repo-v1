"""Document collection for grounding lints (moved out of the CLI script in v3.4)."""
import os

_DOC_EXTS = (".md", ".markdown", ".txt", ".rst")

# Directories that hold machine-scored fixture data rather than prose a human
# reads. `evals/` is the important one: each case names the exact phrases the
# prose oracle must detect, so auditing it reports the oracle's own test data
# as cliches. Editing the fixture to satisfy the oracle would delete the
# evidence (v3.2 Loop 66, AUDIT F21).
_DOC_SKIP_DIRS = ("evals",)


def collect_documents(target):
    """Every document under `target`, recursively, sorted for determinism.

    Shared by --lint-grounding, --audit-safe-zone and --audit-prose-cliche so
    every flag agrees on what "a directory" contains. Sorted because an audit
    that lists files in filesystem order is not reproducible run to run.

    Note `_DOC_EXTS` deliberately excludes `.json`: a `.json` under the tree is
    machine data, and the prose/design oracles score human-readable documents.
    """
    if os.path.isfile(target):
        return [target]
    found = []
    for root, dirs, files in os.walk(target):
        dirs[:] = sorted(d for d in dirs
                         if d not in (".git", "__pycache__", ".focusgate",
                                      "node_modules", ".venv") + _DOC_SKIP_DIRS)
        for fn in sorted(files):
            if fn.lower().endswith(_DOC_EXTS):
                found.append(os.path.join(root, fn))
    return found
