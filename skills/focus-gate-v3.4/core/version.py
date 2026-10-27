"""The single source of truth for the FocusGate release identity.

v3.2 Loop 65 (AUDIT F17). Before this module the version was repeated
string literals in a dozen files, and the `--version` handler alone
emitted FOUR mutually inconsistent answers:

    {"version": "3.0", "release": "FocusGate v3.0-PREVIEW-1", "status": "preview"}
    "FocusGate v2.8 / v3.0 (Autonomous Distributed Cognitive Swarm OS - Preview 1)"

A machine consumer reading `--json` and a human reading the banner
disagreed about what was running. One constant, read by every surface, is
the only shape in which those two cannot diverge again.

`VERSION` is the bare version. `RELEASE_LABEL` is the human-facing
`v3.1-PROD` form the documentation uses, and it is the string claim C05
compares across SKILL.md, SPEC.md and `--version` — so it lives here
rather than being typed three times.
"""

VERSION = "3.4"
RELEASE_LABEL = "v3.4-PROD"
STATUS = "prod"

__version__ = VERSION

__all__ = ["VERSION", "RELEASE_LABEL", "STATUS", "__version__"]
