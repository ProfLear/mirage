"""Font metrics and measurement engine using Pillow for Mirage."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, Tuple
from PIL import ImageFont


# Common fallback fonts across platforms
CANDIDATE_FONTS = [
    # macOS
    "/System/Library/Fonts/Supplemental/Verdana.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/SFNSText.ttf",
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    # Windows
    "C:\\Windows\\Fonts\\arial.ttf",
    "C:\\Windows\\Fonts\\segoeui.ttf",
]


class FontManager:
    """Manages font resolution, caching, and measurement."""

    def __init__(self) -> None:
        self._font_cache: Dict[Tuple[str, int, str], ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}
        self._measurement_cache: Dict[Tuple[str, str, int, str], Tuple[float, float, float, float]] = {}
        self._default_system_font_path = self._find_first_available_font()

    def _find_first_available_font(self) -> str | None:
        for path in CANDIDATE_FONTS:
            if os.path.exists(path):
                return path
        return None

    def get_font(self, family: str, size: float, weight: str = "") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        int_size = max(1, round(size))
        cache_key = (family.lower().strip(), int_size, weight.lower().strip())
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        font = None
        # Walk candidate family stack (e.g. "'Open Sans', verdana, arial, sans-serif")
        for raw_name in family.split(","):
            clean_name = raw_name.strip().strip("\"'").lower()
            if not clean_name or clean_name in ("sans-serif", "serif", "monospace"):
                continue

            for test_name in (clean_name.title(), clean_name.capitalize(), clean_name):
                try:
                    font = ImageFont.truetype(test_name, size=int_size)
                    if font:
                        break
                except Exception:
                    pass
            if font:
                break

            for font_path in CANDIDATE_FONTS:
                base = os.path.basename(font_path).lower()
                if base.startswith(clean_name) and os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, size=int_size)
                        if font:
                            break
                    except Exception:
                        pass
            if font:
                break

        if font is None and self._default_system_font_path:
            try:
                font = ImageFont.truetype(self._default_system_font_path, size=int_size)
            except Exception:
                pass

        if font is None:
            try:
                font = ImageFont.load_default(size=int_size)
            except TypeError:
                font = ImageFont.load_default()

        self._font_cache[cache_key] = font
        return font

    def measure(self, text: str, family: str, size: float, weight: str = "") -> Tuple[float, float, float, float]:
        """Returns (width, height, ascent, descent)."""
        int_size = max(1, round(size))
        cache_key = (text, family.lower().strip(), int_size, weight.lower().strip())
        if cache_key in self._measurement_cache:
            return self._measurement_cache[cache_key]

        if not text:
            res = (0.0, float(int_size), float(int_size), 0.0)
            self._measurement_cache[cache_key] = res
            return res

        font = self.get_font(family, size, weight)
        try:
            length = float(font.getlength(text))
        except Exception:
            length = float(len(text) * int_size * 0.6)

        try:
            bbox = font.getbbox(text)
            if bbox:
                w = max(length, float(bbox[2] - bbox[0]))
                h = max(float(int_size), float(bbox[3] - bbox[1]))
                ascent = float(-bbox[1]) if bbox[1] < 0 else float(int_size * 0.8)
                descent = float(bbox[3] - int_size * 0.8) if bbox[3] > int_size * 0.8 else 0.0
            else:
                w, h = length, float(int_size * 1.2)
                ascent, descent = float(int_size * 0.8), float(int_size * 0.2)
        except Exception:
            w, h = length, float(int_size * 1.2)
            ascent, descent = float(int_size * 0.8), float(int_size * 0.2)

        res = (round(w, 2), round(h, 2), round(ascent, 2), round(descent, 2))
        self._measurement_cache[cache_key] = res
        return res

    def measure_raw(self, text: str, family: str, size_str: str, weight: str = "") -> str:
        """String interface formatted as 'w,h,ascent,descent' for QuickJS FFI."""
        try:
            size = float(size_str)
        except (ValueError, TypeError):
            size = 12.0
        w, h, a, d = self.measure(text, family, size, weight)
        return f"{w},{h},{a},{d}"


_DEFAULT_FONT_MANAGER = FontManager()


def get_default_font_manager() -> FontManager:
    return _DEFAULT_FONT_MANAGER
