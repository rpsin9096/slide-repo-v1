#!/usr/bin/env python3
"""Multi-Platform Banner Aspect Ratio and Central 70% Safe-Zone Validator.

Pure Python standard library implementation with zero external dependencies.
Validates canvas aspect ratios and verifies that critical visual bounding boxes
reside inside the central 70% safe zone across common platform aspect ratios.
"""

import os
import re
from typing import Tuple, Dict, Any


class SafeZoneValidator:
    """Multi-platform banner aspect and central safe-zone verifier.
    Safe zone is the central 70% rect (15% margin on each side)."""

    PLATFORMS = {
        "landscape-16x9": 16 / 9,
        "portrait-9x16": 9 / 16,
        "square-1x1": 1.0,
        "portrait-4x5": 4 / 5,
        "landscape-3x2": 3 / 2,
    }
    MARGIN = 0.15
    TOLERANCE = 0.02
    DIMS_RE = re.compile(r"^\s*(\d+)\s*[xX×]\s*(\d+)\s*$")
    # Anchored on the two separators that follow min-x and min-y. The previous
    # pattern used a leading `[\d.\-+\s]+`, which greedily consumed "0 0 1200"
    # and left group(1) == "0" — so every SVG parsed as width 0.0 and
    # `--audit-safe-zone file.svg` validated a zero-width canvas. Found by the
    # Loop 61 coverage tests; this module previously had none.
    VIEWBOX_RE = re.compile(
        r"viewBox\s*=\s*[\"']\s*[-+0-9.eE]+\s+[-+0-9.eE]+\s+"
        r"([0-9.]+)\s+([0-9.]+)\s*[\"']")

    @classmethod
    def check(cls, width: float, height: float, platform: str) -> Dict[str, Any]:
        if platform not in cls.PLATFORMS:
            raise ValueError(f"Unknown platform: {platform!r} (known: {sorted(cls.PLATFORMS)})")
        expected = cls.PLATFORMS[platform]
        aspect = width / height
        mx = round(width * cls.MARGIN)
        my = round(height * cls.MARGIN)
        rect = {"x": mx, "y": my, "w": width - 2 * mx, "h": height - 2 * my}
        return {
            "platform": platform, "width": width, "height": height,
            "aspect": round(aspect, 4), "expected_aspect": round(expected, 4),
            "pass": abs(aspect - expected) <= cls.TOLERANCE,
            "safe_rect": rect,
        }

    @classmethod
    def contains(cls, width: float, height: float, platform: str, box: Dict[str, Any]) -> bool:
        rect = cls.check(width, height, platform)["safe_rect"]
        return (box["x"] >= rect["x"] and box["y"] >= rect["y"]
                and box["x"] + box["w"] <= rect["x"] + rect["w"]
                and box["y"] + box["h"] <= rect["y"] + rect["h"])

    @classmethod
    def parse_dims(cls, spec: str) -> Tuple[float, float]:
        match = cls.DIMS_RE.match(spec)
        if match:
            return float(match.group(1)), float(match.group(2))
        if os.path.exists(spec) and spec.lower().endswith(".svg"):
            with open(spec, "r", encoding="utf-8") as f:
                content = f.read()
            vb = cls.VIEWBOX_RE.search(content)
            if vb:
                return float(vb.group(1)), float(vb.group(2))
            raise ValueError(f"No viewBox found in {spec}")
        raise ValueError(f"Cannot parse dimensions from {spec!r} (expected WxH or .svg path)")
