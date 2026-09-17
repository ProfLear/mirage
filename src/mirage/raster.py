"""Rasterization module for Mirage converting SVG to PNG, JPEG, and PDF."""

from __future__ import annotations

import io
from typing import Union, BinaryIO
import resvg_py
from PIL import Image


def svg_to_png(
    svg: str,
    width: int | None = None,
    height: int | None = None,
    scale: float = 1.0,
) -> bytes:
    """Rasterize an SVG string into PNG bytes using resvg-py."""
    # resvg_py expects SVG bytes or string
    # Let's inspect resvg_py.svg_to_bytes options or pillow resizing if needed
    png_bytes = resvg_py.svg_to_bytes(svg)
    if scale != 1.0 or width is not None or height is not None:
        img = Image.open(io.BytesIO(png_bytes))
        target_w = width if width is not None else int(round(img.width * scale))
        target_h = height if height is not None else int(round(img.height * scale))
        if target_w != img.width or target_h != img.height:
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
    return png_bytes


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
