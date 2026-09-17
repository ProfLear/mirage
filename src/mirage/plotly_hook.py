"""Plotly integration hook for Mirage."""

from __future__ import annotations

import functools
import sys
from typing import Any, BinaryIO, Optional, Union

import mirage.core as core


_ORIGINAL_TO_IMAGE = None
_ORIGINAL_WRITE_IMAGE = None
_IS_PATCHED = False


def _patched_to_image(
    fig: Any,
    format: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    scale: Optional[float] = None,
    validate: bool = True,
    **kwargs: Any,
) -> bytes:
    fmt = format or "png"
    return core.to_image(
        fig,
        format=fmt,
        width=width,
        height=height,
        scale=scale or 1.0,
    )


def _patched_write_image(
    fig: Any,
    file: Union[str, BinaryIO],
    format: Optional[str] = None,
    scale: Optional[float] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    validate: bool = True,
    **kwargs: Any,
) -> None:
    core.write_image(
        fig,
        file=file,
        format=format,
        scale=scale or 1.0,
        width=width,
        height=height,
    )


def register() -> None:
    """Patch Plotly's static image export functions to use Mirage.

    After calling `mirage.register()`, all calls to `fig.write_image()`,
    `fig.to_image()`, `plotly.io.write_image()`, and `plotly.io.to_image()`
    will automatically be rendered by Mirage with zero browser dependencies.
    """
    global _ORIGINAL_TO_IMAGE, _ORIGINAL_WRITE_IMAGE, _IS_PATCHED
    if _IS_PATCHED:
        return

    try:
        import plotly.io as pio
        import plotly.graph_objects as go

        _ORIGINAL_TO_IMAGE = pio.to_image
        _ORIGINAL_WRITE_IMAGE = pio.write_image

        pio.to_image = _patched_to_image
        pio.write_image = _patched_write_image

        # Also patch Figure methods directly
        go.Figure.to_image = _patched_to_image
        go.Figure.write_image = _patched_write_image

        _IS_PATCHED = True
    except ImportError:
        pass


def unregister() -> None:
    """Restore Plotly's original static export functions."""
    global _ORIGINAL_TO_IMAGE, _ORIGINAL_WRITE_IMAGE, _IS_PATCHED
    if not _IS_PATCHED:
        return

    try:
        import plotly.io as pio
        import plotly.graph_objects as go

        if _ORIGINAL_TO_IMAGE:
            pio.to_image = _ORIGINAL_TO_IMAGE
            go.Figure.to_image = _ORIGINAL_TO_IMAGE

        if _ORIGINAL_WRITE_IMAGE:
            pio.write_image = _ORIGINAL_WRITE_IMAGE
            go.Figure.write_image = _ORIGINAL_WRITE_IMAGE

        _IS_PATCHED = False
    except ImportError:
        pass


# Alias for convenience
patch_plotly = register
unpatch_plotly = unregister
