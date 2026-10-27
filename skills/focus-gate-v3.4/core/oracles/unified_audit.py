"""FocusGate v2.8 — Unified Multi-Oracle Anti-Cliche Audit Engine.

Evaluates files and text content against domain-specific bespoke oracles:
- Markdown/Text -> ProseClicheOracle (anti-sycophancy, anti-throat-clearing, anti-buzzword)
- Python/Code   -> CodeClicheOracle (anti-shotgun suppression, anti-junk-drawer)
- CSS/HTML/JSX  -> ClicheOracle (anti-warm-cream, anti-SaaS card kit)
"""

import os
from typing import Dict, Any, List
from .prose_cliche_oracle import ProseClicheOracle
from .code_cliche_oracle import CodeClicheOracle
from .cliche_oracle import ClicheOracle


class UnifiedAuditOracle:
    """Unified entrypoint for cross-domain anti-cliché auditing."""

    @classmethod
    def audit_text(cls, content: str, file_type: str = "text", filename: str = "") -> Dict[str, Any]:
        """Audit raw text by inferred or explicit file type."""
        file_type = file_type.lower().strip(".")
        
        if file_type in ("md", "markdown", "txt", "text"):
            res = ProseClicheOracle.audit_content(content, filename=filename or "document.md")
            return {
                "clean": res.clean,
                "category": "prose",
                "findings": [f.to_dict() for f in res.findings],
                "summary": f"{len(res.findings)} prose cliché finding(s)"
            }
        elif file_type in ("py", "python", "ts", "typescript", "js", "javascript", "rs", "rust"):
            res = CodeClicheOracle.audit_content(content, filename=filename or f"module.{file_type}")
            return {
                "clean": res.clean,
                "category": "code",
                "findings": [f.to_dict() for f in res.findings],
                "summary": f"{len(res.findings)} code architecture finding(s)"
            }
        elif file_type in ("css", "html", "jsx", "tsx"):
            res = ClicheOracle.audit_content(content, filename=filename or "component.tsx")
            return {
                "clean": res.clean,
                "category": "design",
                "findings": [f.to_dict() for f in res.findings],
                "summary": f"{len(res.findings)} design cliché finding(s)"
            }
        else:
            # Fallback to prose check
            res = ProseClicheOracle.audit_content(content, filename=filename or "unknown.txt")
            return {
                "clean": res.clean,
                "category": "prose",
                "findings": [f.to_dict() for f in res.findings],
                "summary": f"{len(res.findings)} finding(s)"
            }
