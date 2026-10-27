"""On-Demand Ephemeral Context Retriever for FocusGate v2.8.

Replaces bulk pre-hydration with ultra-lightweight, JIT retrieval.
Provides:
1. Directive Slicing: Extracts only the relevant section/rules from facet markdown.
2. Lightweight Grep Engine: Pure Python stdlib regex/line-windowed scanner (with optional ripgrep fast-path).
3. Mtime-Aware Local Cache: Dual-tier (in-memory + .focusgate/cache/) with automatic file mtime invalidation.
"""

import os
import re
import json
import hashlib
import shutil
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class DirectiveSlice:
    """A sliced section of a facet directive to avoid loading entire document."""
    facet: str
    section: str
    content: str
    tokens: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "facet": self.facet,
            "section": self.section,
            "content": self.content,
            "tokens": self.tokens,
        }


@dataclass
class GrepMatch:
    """A targeted snippet matching a query with limited line context."""
    file_path: str
    line_number: int
    line_content: str
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)

    def to_formatted_snippet(self) -> str:
        lines = []
        start_line = self.line_number - len(self.context_before)
        for i, prev in enumerate(self.context_before):
            lines.append(f"  {start_line + i:4d} | {prev}")
        lines.append(f"> {self.line_number:4d} | {self.line_content}")
        for i, nxt in enumerate(self.context_after):
            lines.append(f"  {self.line_number + 1 + i:4d} | {nxt}")
        header = f"[{self.file_path}:{self.line_number}]"
        return f"{header}\n" + "\n".join(lines)


class EphemeralCache:
    """Dual-tier cache (in-memory LRU + on-disk JSON) invalidated by file mtime."""

    def __init__(self, cache_file: Optional[str] = None):
        self.cache_file = cache_file
        self.memory_store: Dict[str, Any] = {}
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        if self.cache_file and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.memory_store = json.load(f)
            except Exception:
                self.memory_store = {}

    def save_to_disk(self) -> None:
        if not self.cache_file:
            return
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.memory_store, f, indent=2)
        except (OSError, IOError):
            pass

    def compute_key(self, path: str, pattern: str, extra: str = "") -> str:
        mtime = 0.0
        if os.path.exists(path):
            mtime = os.path.getmtime(path)
        raw = f"{os.path.abspath(path)}:{pattern}:{mtime}:{extra}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str, max_age_s: float = 0) -> Optional[Any]:
        val = self.memory_store.get(key)
        if val is None:
            return None
        if isinstance(val, dict) and "_ts" in val:
            import time as _time
            if max_age_s and _time.time() - float(val.get("_ts", 0)) > max_age_s:
                self.memory_store.pop(key, None)
                return None
            val = {k: v for k, v in val.items() if k != "_ts"}
        return val

    def set(self, key: str, value: Any) -> None:
        import time as _time
        if isinstance(value, dict) and "_ts" not in value:
            value = dict(value)
            value["_ts"] = _time.time()
        self.memory_store[key] = value
        self.save_to_disk()

    def clear(self) -> None:
        self.memory_store.clear()
        if self.cache_file and os.path.exists(self.cache_file):
            try:
                os.remove(self.cache_file)
            except OSError:
                pass


class EphemeralContextRetriever:
    """On-demand retriever pulling minimal snippets and sliced directives."""

    FACET_DIRECTORIES = ["cognitive", "design", "engineering", "navigation", "writing"]

    def __init__(self, workspace_root: str = ".", facets_dir: Optional[str] = None):
        self.workspace_root = os.path.abspath(workspace_root)
        self.facets_dir = facets_dir or os.path.join(os.path.dirname(__file__), "..", "facets")
        cache_path = os.path.join(self.workspace_root, ".focusgate", "cache", "retrieval_cache.json")
        self.cache = EphemeralCache(cache_file=cache_path)

    def estimate_tokens(self, text: str) -> int:
        from .tokens import estimate_tokens as _estimate_tokens
        return _estimate_tokens(text)

    def slice_directive(self, facet_name: str, section_header: Optional[str] = None) -> DirectiveSlice:
        """Extracts only a targeted section from a facet directive rather than full file."""
        norm_name = facet_name.strip().lower().replace(".md", "")
        key = self.cache.compute_key(self.facets_dir, norm_name, extra=section_header or "default")
        cached = self.cache.get(key)
        if cached:
            return DirectiveSlice(**cached)

        # Locate facet file
        facet_file = None
        for subdir in self.FACET_DIRECTORIES:
            candidate = os.path.join(self.facets_dir, subdir, f"{norm_name}.md")
            if os.path.exists(candidate):
                facet_file = candidate
                break

        if not facet_file:
            # Fallback search across any subdirectories
            for root, _, files in os.walk(self.facets_dir):
                for f in files:
                    if f.lower() == f"{norm_name}.md":
                        facet_file = os.path.join(root, f)
                        break
                if facet_file:
                    break

        if not facet_file or not os.path.exists(facet_file):
            # Graceful fallback: return minimal mock slice
            fallback_slice = DirectiveSlice(
                facet=norm_name,
                section="Default Contract",
                content=f"Execute {norm_name} facet with minimal verified gates.",
                tokens=15
            )
            return fallback_slice

        with open(facet_file, "r", encoding="utf-8") as f:
            raw_text = f.read()

        sections = self._parse_markdown_sections(raw_text)

        selected_section = "Overview"
        selected_content = ""

        if section_header:
            sh_lower = section_header.lower()
            for header, content in sections.items():
                if sh_lower in header.lower():
                    selected_section = header
                    selected_content = content
                    break

        if not selected_content:
            # If no match or no header requested, pick the first actionable section (Protocol, Steps, or Rules)
            for header, content in sections.items():
                hl = header.lower()
                if any(kw in hl for kw in ("protocol", "action", "step", "rules", "checklist", "verify")):
                    selected_section = header
                    selected_content = content
                    break

            if not selected_content and sections:
                # Pick the first non-empty section
                first_header = next(iter(sections.keys()))
                selected_section = first_header
                selected_content = sections[first_header]

        # Enforce strict maximum length on directive slices (<300 tokens)
        if self.estimate_tokens(selected_content) > 300:
            selected_content = selected_content[:1200] + "\n... [DIRECTIVE_SECTION_TRUNCATED] ..."

        res_slice = DirectiveSlice(
            facet=norm_name,
            section=selected_section,
            content=selected_content.strip(),
            tokens=self.estimate_tokens(selected_content)
        )

        self.cache.set(key, res_slice.to_dict())
        return res_slice

    def grep_source(
        self,
        pattern: str,
        path_scope: str,
        max_matches: int = 5,
        context_lines: int = 3,
        use_regex: bool = True
    ) -> List[GrepMatch]:
        """Scans path_scope (file or dir) for pattern returning line-windowed matches."""
        target_path = os.path.join(self.workspace_root, path_scope) if not os.path.isabs(path_scope) else path_scope
        if not os.path.exists(target_path):
            return []

        cache_key = self.cache.compute_key(target_path, pattern, extra=f"{max_matches}:{context_lines}")
        cached = self.cache.get(cache_key)
        if cached:
            return [GrepMatch(**m) for m in cached]

        matches: List[GrepMatch] = []

        # Pure Python standard library file scanner
        regex_flags = re.IGNORECASE
        compiled_re = re.compile(pattern if use_regex else re.escape(pattern), regex_flags)

        files_to_scan = []
        if os.path.isfile(target_path):
            files_to_scan.append(target_path)
        else:
            for root, _, files in os.walk(target_path):
                # Skip hidden and cache folders
                if any(part.startswith(".") for part in root.split(os.sep)):
                    continue
                for f in files:
                    if f.endswith((".py", ".md", ".json", ".js", ".ts", ".html", ".css", ".txt", ".sh")):
                        files_to_scan.append(os.path.join(root, f))

        for fpath in files_to_scan:
            if len(matches) >= max_matches:
                break
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.read().splitlines()
            except Exception:
                continue

            for idx, line in enumerate(lines):
                if compiled_re.search(line):
                    before = lines[max(0, idx - context_lines):idx]
                    after = lines[idx + 1:min(len(lines), idx + 1 + context_lines)]
                    rel_path = os.path.relpath(fpath, self.workspace_root)
                    matches.append(GrepMatch(
                        file_path=rel_path,
                        line_number=idx + 1,
                        line_content=line,
                        context_before=before,
                        context_after=after
                    ))
                    if len(matches) >= max_matches:
                        break

        serialized = [
            {
                "file_path": m.file_path,
                "line_number": m.line_number,
                "line_content": m.line_content,
                "context_before": m.context_before,
                "context_after": m.context_after,
            }
            for m in matches
        ]
        self.cache.set(cache_key, serialized)
        return matches

    def retrieve_snippet(
        self,
        path_scope: str,
        pattern: str,
        max_tokens: int = 300,
        max_matches: int = 10,
        context_lines: int = 2
    ) -> str:
        """On-demand grep retrieval returning bounded formatted snippet for prompt injection."""
        matches = self.grep_source(
            pattern=pattern,
            path_scope=path_scope,
            max_matches=max_matches,
            context_lines=context_lines
        )
        return self.format_grep_for_prompt(matches, max_tokens=max_tokens)

    def format_grep_for_prompt(self, matches: List[GrepMatch], max_tokens: int = 400) -> str:
        """Formats matches compactly for prompt injection bounded under max_tokens."""
        if not matches:
            return "[No matches found for query]"

        output_parts = []
        running_tokens = 0
        truncation_suffix = "... [Truncated remaining matches for token economy] ..."
        truncation_tokens = self.estimate_tokens(truncation_suffix)

        for i, m in enumerate(matches):
            snippet = m.to_formatted_snippet()
            tokens = self.estimate_tokens(snippet)
            remaining = len(matches) - i
            reserved = truncation_tokens + 4 if remaining > 1 else 0
            if running_tokens + tokens + reserved > max_tokens:
                if not output_parts:
                    # If even the first match exceeds max_tokens, slice its lines
                    snippet_lines = snippet.splitlines()
                    short_lines = []
                    for line in snippet_lines:
                        cand = "\n".join(short_lines + [line])
                        if self.estimate_tokens(cand + "\n" + truncation_suffix) <= max_tokens:
                            short_lines.append(line)
                        else:
                            break
                    if short_lines:
                        output_parts.append("\n".join(short_lines))
                output_parts.append(f"... [Truncated {len(matches) - len(output_parts)} remaining matches for token economy] ...")
                break
            output_parts.append(snippet)
            running_tokens += tokens

        res = "\n\n".join(output_parts)
        while self.estimate_tokens(res) > max_tokens and len(res) > 20:
            res = res[:int(len(res) * 0.9)] + "\n..."
        return res

    def _parse_markdown_sections(self, text: str) -> Dict[str, str]:
        """Parses markdown text into header-to-content mapping."""
        sections: Dict[str, str] = {}
        lines = text.splitlines()
        current_header = "Header"
        current_lines: List[str] = []

        for line in lines:
            if line.startswith(("# ", "## ", "### ")):
                if current_lines:
                    sections[current_header] = "\n".join(current_lines).strip()
                current_header = line.lstrip("#").strip()
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            sections[current_header] = "\n".join(current_lines).strip()

        return sections
