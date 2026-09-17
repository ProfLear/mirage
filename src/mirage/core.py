"""Core user-facing rendering API for Mirage."""

from __future__ import annotations

import os
from typing import Any, BinaryIO, Dict, List, Optional, Union

from mirage.engine import get_engine
from mirage.raster import svg_to_png, svg_to_jpeg, svg_to_webp, write_raster


def _extract_figure_spec(fig: Any) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Extract (data, layout) dictionaries from a Figure or dict."""
    if hasattr(fig, "to_dict"):
        d = fig.to_dict()
    elif isinstance(fig, dict):
        d = fig
    else:
        raise TypeError(f"Expected plotly.graph_objects.Figure or dict, got {type(fig).__name__}")

    data = d.get("data", [])
    layout = d.get("layout", {})
    return data, layout


def to_svg(
    fig: Any,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> str:
    """Render a Plotly figure to an SVG XML string.

    Parameters
    ----------
    fig : plotly.graph_objects.Figure or dict
        The Plotly figure to render.
    width : int, optional
        The width of the output image in pixels.
    height : int, optional
        The height of the output image in pixels.

    Returns
    -------
    str
        The SVG XML document string.
    """
    data, layout = _extract_figure_spec(fig)
    engine = get_engine()
    return engine.render_svg(data, layout, width=width, height=height)


def to_image(
    fig: Any,
    format: str = "png",
    width: Optional[int] = None,
    height: Optional[int] = None,
    scale: float = 1.0,
) -> bytes:
    """Render a Plotly figure to image bytes.

    Parameters
    ----------
    fig : plotly.graph_objects.Figure or dict
        The Plotly figure to render.
    format : str, default 'png'
        The image format: 'svg', 'png', 'jpeg' (or 'jpg'), 'webp'.
    width : int, optional
        The width of the output image in pixels.
    height : int, optional
        The height of the output image in pixels.
    scale : float, default 1.0
        The scale factor to apply to the output image.

    Returns
    -------
    bytes
        The raw image bytes.
    """
    fmt = format.lower().strip()
    svg = to_svg(fig, width=width, height=height)

    if fmt == "svg":
        return svg.encode("utf-8")
    elif fmt == "png":
        return svg_to_png(svg, width=width, height=height, scale=scale)
    elif fmt in ("jpg", "jpeg"):
        return svg_to_jpeg(svg, width=width, height=height, scale=scale)
    elif fmt == "webp":
        return svg_to_webp(svg, width=width, height=height, scale=scale)
    else:
        raise ValueError(f"Unsupported format: {format}. Supported: 'svg', 'png', 'jpeg', 'webp'")


def write_image(
    fig: Any,
    file: Union[str, os.PathLike, BinaryIO],
    format: Optional[str] = None,
    scale: float = 1.0,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> None:
    """Save a Plotly figure to an image file.

    Parameters
    ----------
    fig : plotly.graph_objects.Figure or dict
        The Plotly figure to render.
    file : str, PathLike, or binary file object
        The destination filepath or open binary file.
    format : str, optional
        The image format. Inferred from filepath extension if omitted.
    scale : float, default 1.0
        The scale factor for the output image.
    width : int, optional
        The width in pixels.
    height : int, optional
        The height in pixels.
    """
    if format is None:
        if isinstance(file, (str, os.PathLike)):
            ext = os.path.splitext(str(file))[1].lower().lstrip(".")
            if ext:
                format = ext
            else:
                format = "png"
        else:
            format = "png"

    fmt = format.lower().strip()
    if fmt == "svg":
        svg_str = to_svg(fig, width=width, height=height)
        if isinstance(file, (str, os.PathLike)):
            with open(file, "w", encoding="utf-8") as f:
                f.write(svg_str)
        else:
            file.write(svg_str.encode("utf-8"))
    else:
        svg_str = to_svg(fig, width=width, height=height)
        write_raster(svg_str, file, format=fmt, width=width, height=height, scale=scale)
