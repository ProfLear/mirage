"""Mirage: Ultra-lightweight, browser-less static exporter for Plotly in Python."""

from mirage.core import to_svg, to_image, write_image
from mirage.plotly_hook import register, unregister, patch_plotly, unpatch_plotly

__version__ = "0.1.0"

__all__ = [
    "to_svg",
    "to_image",
    "write_image",
    "register",
    "unregister",
    "patch_plotly",
    "unpatch_plotly",
    "__version__",
]
