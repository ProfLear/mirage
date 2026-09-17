"""Engine lifecycle and QuickJS execution manager for Mirage."""

from __future__ import annotations

import base64
import io
import json
import os
import re
import threading
from typing import Any, Dict, List, Optional
from PIL import Image, ImageColor, ImageDraw
import quickjs

from mirage.fonts import get_default_font_manager


_JS_DIR = os.path.join(os.path.dirname(__file__), "js")
_MICRO_DOM_PATH = os.path.join(_JS_DIR, "micro_dom.js")
_PLOTLY_COMPREHENSIVE_PATH = os.path.join(_JS_DIR, "plotly_comprehensive_2d.js")
_PLOTLY_CARTESIAN_PATH = os.path.join(_JS_DIR, "plotly_cartesian.js")
_PLOTLY_BASIC_PATH = os.path.join(_JS_DIR, "plotly_basic.js")

if os.path.exists(_PLOTLY_COMPREHENSIVE_PATH):
    _BUNDLE_PATH = _PLOTLY_COMPREHENSIVE_PATH
elif os.path.exists(_PLOTLY_CARTESIAN_PATH):
    _BUNDLE_PATH = _PLOTLY_CARTESIAN_PATH
else:
    _BUNDLE_PATH = _PLOTLY_BASIC_PATH

_ENGINE_THREAD_LOCAL = threading.local()


def _parse_color(c: str) -> tuple[int, int, int, int] | tuple[int, int, int]:
    if not c:
        return (0, 0, 0, 0)
    c = c.strip()
    m = re.match(r"rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\s*\)", c, re.I)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        a = int(float(m.group(4)) * 255) if m.group(4) is not None else 255
        return (r, g, b, a)
    try:
        return ImageColor.getrgb(c)
    except Exception:
        return (0, 0, 0, 255)


def _encode_canvas_to_png(width: int, height: int, commands_json: str) -> str:
    w = max(1, int(width))
    h = max(1, int(height))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        commands = json.loads(commands_json)
    except Exception:
        commands = []

    for cmd in commands:
        op = cmd.get("op")
        if op == "fillRect":
            x = cmd.get("x", 0)
            y = cmd.get("y", 0)
            cw = cmd.get("w", 0)
            ch = cmd.get("h", 0)
            fill = _parse_color(cmd.get("fill", "#000000"))
            draw.rectangle([x, y, x + cw, y + ch], fill=fill)
        elif op == "clearRect":
            x = cmd.get("x", 0)
            y = cmd.get("y", 0)
            cw = cmd.get("w", 0)
            ch = cmd.get("h", 0)
            draw.rectangle([x, y, x + cw, y + ch], fill=(0, 0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


class MirageEngine:
    """Manages an embedded QuickJS runtime with micro-DOM and Plotly.js."""

    def __init__(self) -> None:
        self.font_manager = get_default_font_manager()
        self.context = quickjs.Context()
        self.context.set_max_stack_size(10 * 1024 * 1024)

        # Register callbacks
        self.context.add_callable("_measureTextRaw", self.font_manager.measure_raw)
        self.context.add_callable("_encodeCanvasToPNG", _encode_canvas_to_png)

        # Load JavaScript assets
        with open(_MICRO_DOM_PATH, "r", encoding="utf-8") as f:
            micro_dom_js = f.read()

        with open(_BUNDLE_PATH, "r", encoding="utf-8") as f:
            plotly_js = f.read()

        self.context.eval(micro_dom_js)
        self.context.eval(plotly_js)

        # Define render helper
        self.context.eval("""
        function mirageRender(dataJson, layoutJson) {
            var data = JSON.parse(dataJson);
            var layout = JSON.parse(layoutJson);

            var w = layout.width || 600;
            var h = layout.height || 400;

            var container = document.createElement('div');
            container.id = 'mirage-plot-' + Math.random().toString(36).slice(2);
            container.clientWidth = w;
            container.clientHeight = h;
            container.offsetWidth = w;
            container.offsetHeight = h;
            container.getBoundingClientRect = function() {
                return { left: 0, top: 0, right: w, bottom: h, width: w, height: h };
            };
            document.body.appendChild(container);

            try {
                Plotly.newPlot(container, data, layout, { staticPlot: true });
                var res = null;
                if (Plotly.Snapshot && typeof Plotly.Snapshot.toSVG === 'function') {
                    try {
                        res = Plotly.Snapshot.toSVG(container, 'svg');
                    } catch(snapErr) {
                        // fallback to manual extraction if snapshot fails
                    }
                }
                if (!res) {
                    var svgs = container.querySelectorAll('svg');
                    if (svgs.length === 0) {
                        document.body.removeChild(container);
                        return null;
                    }
                    var mainSvg = svgs[0];
                    for (var s = 1; s < svgs.length; s++) {
                        var otherSvg = svgs[s];
                        var kids = otherSvg.childNodes.slice();
                        for (var k = 0; k < kids.length; k++) {
                            var kid = kids[k];
                            if (kid.nodeType === 1 && kid.classList && kid.classList.contains('hoverlayer')) continue;
                            mainSvg.appendChild(kid);
                        }
                    }
                    res = mainSvg.outerHTML;
                }
                if (res) {
                    res = res.replace(/TOBESTRIPPED/g, "'");
                }
                document.body.removeChild(container);
                return res;
            } catch(e) {
                try { document.body.removeChild(container); } catch(ignore) {}
                throw new Error("Plotly render failed: " + e.message + "\\n" + e.stack);
            }
        }
        """)

    def render_svg(
        self,
        data: List[Dict[str, Any]],
        layout: Dict[str, Any],
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> str:
        """Render Plotly traces and layout to a clean SVG XML string."""
        layout_copy = dict(layout) if layout else {}
        if width is not None:
            layout_copy["width"] = width
        if height is not None:
            layout_copy["height"] = height

        data_json = json.dumps(data)
        layout_json = json.dumps(layout_copy)

        # Call mirageRender inside QuickJS
        self.context.eval(f"var __mirage_data = {json.dumps(data_json)};")
        self.context.eval(f"var __mirage_layout = {json.dumps(layout_json)};")
        svg = self.context.eval("mirageRender(__mirage_data, __mirage_layout);")
        if not svg:
            raise RuntimeError("Mirage rendering failed: No SVG element was generated by Plotly.")
        return svg


def get_engine() -> MirageEngine:
    """Get or create the thread-local Mirage engine instance."""
    if not hasattr(_ENGINE_THREAD_LOCAL, "engine"):
        _ENGINE_THREAD_LOCAL.engine = MirageEngine()
    return _ENGINE_THREAD_LOCAL.engine
