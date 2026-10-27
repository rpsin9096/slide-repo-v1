#!/usr/bin/env python3
"""3-Layer Design Token Synchronizer and Token Allowlist Auditor.

Pure Python standard library implementation with zero external dependencies.
Audits CSS/TSX/HTML source code against token allowlists and generates
3-layer (primitive -> semantic -> component) design tokens CSS/JSON from brand guidelines.
"""

import os
import re
import json
from typing import Dict, Any, List


class DesignTokenEngine:
    """Audits source files for hardcoded design values and syncs brand rules
    into 3-layer token files (primitive -> semantic -> component)."""

    HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
    COLOR_FUNC_RE = re.compile(r"\b((?:rgba?|hsla?|oklch|oklab|color-mix)\([^)]*\))")
    FONT_RE = re.compile(r"font-family\s*:\s*([^;}{]+)")
    TOKEN_DEF_RE = re.compile(r"^\s*--[\w-]+\s*:")
    VAR_RE = re.compile(r"var\(\s*--[^)]+\)")
    BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
    HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

    @classmethod
    def _strip_comments(cls, text: str) -> str:
        def blank(match):
            return "\n" * match.group(0).count("\n")
        text = cls.BLOCK_COMMENT_RE.sub(blank, text)
        return cls.HTML_COMMENT_RE.sub(blank, text)

    @classmethod
    def audit(cls, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            content = cls._strip_comments(f.read())
        violations = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            if cls.TOKEN_DEF_RE.match(line):
                continue
            code = cls.VAR_RE.sub("", line)
            for match in cls.HEX_RE.finditer(code):
                violations.append({"line": lineno, "match": match.group(0), "kind": "hardcoded-hex"})
            for match in cls.COLOR_FUNC_RE.finditer(code):
                func = match.group(1).split("(")[0].lower()
                if func.startswith("rgb"):
                    kind = "hardcoded-rgb"
                elif func.startswith("hsl"):
                    kind = "hardcoded-hsl"
                else:
                    kind = f"hardcoded-{func}"
                violations.append({"line": lineno, "match": match.group(1), "kind": kind})
            font = cls.FONT_RE.search(line)
            if font and "var(--" not in font.group(1):
                violations.append({"line": lineno, "match": font.group(1).strip(), "kind": "hardcoded-font"})
        return {"path": path, "violations": violations, "passed": not violations}

    @classmethod
    def sync(cls, brand_md_path: str, out_dir: str) -> Dict[str, Any]:
        with open(brand_md_path, "r", encoding="utf-8") as f:
            brand = f.read()
        seen = []
        for match in cls.HEX_RE.finditer(brand):
            color = cls._normalize_hex(match.group(0))
            if color not in seen:
                seen.append(color)
        if not seen:
            raise ValueError(f"No brand colors found in {brand_md_path}")
        os.makedirs(out_dir, exist_ok=True)
        primitive = {f"color-primitive-{i + 1}": c for i, c in enumerate(seen)}
        semantic = {"color-primary": "{primitive.color-primitive-1}"}
        if len(seen) > 1:
            semantic["color-accent"] = "{primitive.color-primitive-2}"
        semantic["color-neutral-strong"] = "#0f172a"
        semantic["color-neutral-soft"] = "#f8fafc"
        component = {
            "button-bg": "{semantic.color-primary}",
            "button-fg": "#ffffff",
            "card-bg": "#ffffff",
        }
        data = {"primitive": primitive, "semantic": semantic, "component": component}
        json_path = os.path.join(out_dir, "design-tokens.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        css_lines = [":root {"]
        for name, value in primitive.items():
            css_lines.append(f"  --{name}: {value};")
        ref = re.compile(r"\{([^}]+)\}")
        def _ref_to_var(match):
            parts = match.group(1).split(".")
            return f"var(--{'-'.join(parts[1:])})"
        for name, value in list(semantic.items()) + list(component.items()):
            css_value = ref.sub(_ref_to_var, value)
            css_lines.append(f"  --{name}: {css_value};")
        css_lines.append("}")
        css_path = os.path.join(out_dir, "design-tokens.css")
        with open(css_path, "w", encoding="utf-8") as f:
            f.write("\n".join(css_lines) + "\n")
        return {"json": json_path, "css": css_path, "colors": seen}

    @staticmethod
    def _normalize_hex(color: str) -> str:
        h = color.lstrip("#").lower()
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        return f"#{h}"
