"""Rasterization module for Mirage converting SVG to PNG, JPEG, and PDF."""

from __future__ import annotations

import io
import os
import re
from typing import Union, BinaryIO
import resvg_py
from PIL import Image

SYSTEM_FONT_DIRS = [
    "/System/Library/Fonts/Supplemental",
    "/Library/Fonts",
    "/System/Library/Fonts",
    "/usr/share/fonts",
    "/usr/local/share/fonts",
]
EXISTING_FONT_DIRS = [d for d in SYSTEM_FONT_DIRS if os.path.isdir(d)]

COMMON_FONT_NAMES = [
    "verdana",
    "arial",
    "tahoma",
    "trebuchet ms",
    "helvetica",
    "times new roman",
    "courier new",
    "georgia",
]


_SVG_ROOT_RE = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)
_ATTR_RE = re.compile(r"([^\s=]+)\s*=\s*(\"([^\"]*)\"|'([^']*)')")
_LENGTH_RE = re.compile(r"^([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*[a-z%]*$", re.IGNORECASE)


def _normalize_svg_fonts(svg: str) -> str:
    """Normalize font-family names to match case-sensitive font db lookups."""
    def _cap(m: re.Match) -> str:
        val = m.group(0)
        for name in COMMON_FONT_NAMES:
            val = re.sub(r"\b" + re.escape(name) + r"\b", name.title(), val, flags=re.IGNORECASE)
        return val

    return re.sub(r"font-family:\s*[^;\"}]+", _cap, svg)


def _parse_length(value: str | None) -> float | None:
    if value is None:
        return None
    m = _LENGTH_RE.match(value.strip())
    if not m:
        return None
    return float(m.group(1))


def _parse_svg_layout_size(svg: str) -> tuple[float, float]:
    root = _SVG_ROOT_RE.search(svg)
    if not root:
        raise ValueError("SVG root element not found")

    attrs = {
        m.group(1).lower(): (m.group(3) if m.group(3) is not None else m.group(4))
        for m in _ATTR_RE.finditer(root.group(0))
    }

    width = _parse_length(attrs.get("width"))
    height = _parse_length(attrs.get("height"))

    if (width is None or height is None) and "viewbox" in attrs:
        parts = attrs["viewbox"].replace(",", " ").split()
        if len(parts) == 4:
            if width is None:
                width = float(parts[2])
            if height is None:
                height = float(parts[3])

    if width is None or height is None:
        raise ValueError("Could not determine SVG layout width/height")
    return width, height


def _prepare_svg_for_raster(
    svg: str,
    width: int | None = None,
    height: int | None = None,
    scale: float = 1.0,
) -> str:
    layout_w, layout_h = _parse_svg_layout_size(svg)
    if width is not None:
        layout_w = float(width)
    if height is not None:
        layout_h = float(height)

    out_w = max(1, int(round(layout_w * scale)))
    out_h = max(1, int(round(layout_h * scale)))

    root = _SVG_ROOT_RE.search(svg)
    if not root:
        raise ValueError("SVG root element not found")

    tag = root.group(0)
    existing = {m.group(1).lower() for m in _ATTR_RE.finditer(tag)}

    def _set_attr(tag_str: str, name: str, value: str) -> str:
        pattern = rf'({re.escape(name)}\s*=\s*)("([^"]*)"|\'([^\']*)\')'
        if re.search(pattern, tag_str, flags=re.IGNORECASE):
            return re.sub(pattern, rf'\1"{value}"', tag_str, count=1, flags=re.IGNORECASE)
        return re.sub(r"\s*>$", f' {name}="{value}">', tag_str, count=1)

    new_tag = tag
    new_tag = _set_attr(new_tag, "width", str(out_w))
    new_tag = _set_attr(new_tag, "height", str(out_h))
    if "viewbox" not in existing:
        vb_w = int(layout_w) if layout_w == int(layout_w) else layout_w
        vb_h = int(layout_h) if layout_h == int(layout_h) else layout_h
        new_tag = _set_attr(new_tag, "viewBox", f"0 0 {vb_w} {vb_h}")

    return svg[: root.start()] + new_tag + svg[root.end() :]


def svg_to_png(
    svg: str,
    width: int | None = None,
    height: int | None = None,
    scale: float = 1.0,
) -> bytes:
    """Rasterize an SVG string into PNG bytes using resvg-py."""
    normalized_svg = _normalize_svg_fonts(svg)
    prepared = _prepare_svg_for_raster(normalized_svg, width=width, height=height, scale=scale)
    if EXISTING_FONT_DIRS:
        return resvg_py.svg_to_bytes(prepared, font_dirs=EXISTING_FONT_DIRS)
    return resvg_py.svg_to_bytes(prepared)


def svg_to_jpeg(
    svg: str,
    width: int | None = None,
    height: int | None = None,
    scale: float = 1.0,
    quality: int = 90,
) -> bytes:
    """Rasterize an SVG string into JPEG bytes."""
    png_bytes = svg_to_png(svg, width=width, height=height, scale=scale)
    img = Image.open(io.BytesIO(png_bytes))
    if img.mode in ("RGBA", "LA", "P"):
        # Composite against white background
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = bg
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def svg_to_webp(
    svg: str,
    width: int | None = None,
    height: int | None = None,
    scale: float = 1.0,
    quality: int = 90,
) -> bytes:
    """Rasterize an SVG string into WEBP bytes."""
    png_bytes = svg_to_png(svg, width=width, height=height, scale=scale)
    img = Image.open(io.BytesIO(png_bytes))
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=quality)
    return buf.getvalue()


def write_raster(
    svg: str,
    target: Union[str, BinaryIO],
    format: str = "png",
    width: int | None = None,
    height: int | None = None,
    scale: float = 1.0,
) -> None:
    """Save an SVG string into an image file or file-like object."""
    fmt = format.lower().strip()
    if fmt == "png":
        data = svg_to_png(svg, width=width, height=height, scale=scale)
    elif fmt in ("jpg", "jpeg"):
        data = svg_to_jpeg(svg, width=width, height=height, scale=scale)
    elif fmt == "webp":
        data = svg_to_webp(svg, width=width, height=height, scale=scale)
    else:
        raise ValueError(f"Unsupported raster format: {format}. Supported: 'png', 'jpeg', 'webp'")

    if isinstance(target, str):
        with open(target, "wb") as f:
            f.write(data)
    else:
        target.write(data)
