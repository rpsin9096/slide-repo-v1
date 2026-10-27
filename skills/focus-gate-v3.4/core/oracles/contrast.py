#!/usr/bin/env python3
"""WCAG 2.1 Relative Luminance and Contrast Ratio Oracle.

Pure Python standard library implementation with zero external dependencies.
Calculates exact relative luminance and evaluates against WCAG 2.1 AA / AAA standards.
"""

import re
from typing import Tuple, Dict, Any


class ContrastOracle:
    """Evaluates WCAG 2.1 relative luminance and contrast ratios between color pairs."""

    @staticmethod
    def parse_hex_color(hex_str: str) -> Tuple[float, float, float]:
        """Parses #RGB or #RRGGBB into normalized [0.0, 1.0] sRGB floats."""
        s = hex_str.strip().lstrip('#')
        if len(s) == 3:
            s = ''.join(c * 2 for c in s)
        if len(s) != 6 or not re.match(r'^[0-9a-fA-F]{6}$', s):
            raise ValueError(f"Invalid hex color: '{hex_str}'")
        r = int(s[0:2], 16) / 255.0
        g = int(s[2:4], 16) / 255.0
        b = int(s[4:6], 16) / 255.0
        return r, g, b

    @classmethod
    def channel_luminance(cls, val: float) -> float:
        """Converts sRGB channel to linear luminance per WCAG 2.1 spec."""
        if val <= 0.04045:
            return val / 12.92
        return ((val + 0.055) / 1.055) ** 2.4

    @classmethod
    def relative_luminance(cls, r: float, g: float, b: float) -> float:
        """Calculates relative luminance L = 0.2126*R + 0.7152*G + 0.0722*B."""
        lr = cls.channel_luminance(r)
        lg = cls.channel_luminance(g)
        lb = cls.channel_luminance(b)
        return 0.2126 * lr + 0.7152 * lg + 0.0722 * lb

    @classmethod
    def calculate_ratio(cls, hex1: str, hex2: str) -> float:
        """Calculates contrast ratio (L1 + 0.05) / (L2 + 0.05) where L1 > L2."""
        r1, g1, b1 = cls.parse_hex_color(hex1)
        r2, g2, b2 = cls.parse_hex_color(hex2)
        l1 = cls.relative_luminance(r1, g1, b1)
        l2 = cls.relative_luminance(r2, g2, b2)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    @classmethod
    def evaluate_contrast(cls, fg_hex: str, bg_hex: str) -> Dict[str, Any]:
        """Evaluates contrast ratio and AA / AAA compliance."""
        ratio = cls.calculate_ratio(fg_hex, bg_hex)
        return {
            "fg": fg_hex,
            "bg": bg_hex,
            "ratio": round(ratio, 2),
            "aa_normal_text": ratio >= 4.5,
            "aa_large_text": ratio >= 3.0,
            "aaa_normal_text": ratio >= 7.0,
            "aaa_large_text": ratio >= 4.5,
            "verdict": "CONTRAST_PASS_AA" if ratio >= 4.5 else "CONTRAST_FAIL_AA"
        }
