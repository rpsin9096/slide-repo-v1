"""FocusGate v2.8.5 — Filesystem Template Engine.

Loads, caches, and renders scaffolding templates from disk (templates/).
Replaces inline Python string literals with single-source-of-truth templates.
100% Python standard library compatibility (zero external dependencies).
"""

import os
from typing import Dict, List, Optional, Any


class TemplateEngine:
    """Discovers, caches, and formats workspace templates from disk."""

    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir:
            self.templates_dir = os.path.abspath(templates_dir)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.templates_dir = os.path.join(base_dir, "templates")

        self._cache: Dict[str, str] = {}

    def list_templates(self) -> List[str]:
        """Returns names of all registered template files on disk."""
        if not os.path.isdir(self.templates_dir):
            return []
        try:
            return sorted([
                f for f in os.listdir(self.templates_dir)
                if not f.startswith(".") and os.path.isfile(os.path.join(self.templates_dir, f))
            ])
        except (OSError, PermissionError):
            return []

    def get_template(self, name: str) -> str:
        """Loads and caches the raw template string from disk."""
        if name in self._cache:
            return self._cache[name]

        path = os.path.join(self.templates_dir, name)
        if not os.path.isfile(path):
            # Try appending .template.md or .template.html if bare name given
            for suffix in [".template.md", ".template.html", ".template.json", ".template.css"]:
                candidate = os.path.join(self.templates_dir, name + suffix)
                if os.path.isfile(candidate):
                    path = candidate
                    break

        if not os.path.isfile(path):
            raise FileNotFoundError(f"Template '{name}' not found in '{self.templates_dir}'")

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        self._cache[name] = content
        return content

    def render(self, name: str, **kwargs: Any) -> str:
        """Loads and formats a template with keyword substitutions."""
        raw = self.get_template(name)
        try:
            return raw.format(**kwargs)
        except KeyError:
            # Fallback for templates with nested braces (e.g. CSS, JSON, HTML)
            # Use safe token replacement for provided kwargs
            rendered = raw
            for k, v in kwargs.items():
                rendered = rendered.replace(f"{{{k}}}", str(v))
            return rendered

    def clear_cache(self) -> None:
        """Clears the in-memory template cache."""
        self._cache.clear()
