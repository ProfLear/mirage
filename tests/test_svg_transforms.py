"""Regression tests for SVG transform-aware getBBox / automargin."""

from __future__ import annotations

import json
import os
import re

import plotly.graph_objects as go
import pytest
import quickjs

import mirage

_MICRO_DOM = os.path.join(os.path.dirname(__file__), "..", "src", "mirage", "js", "micro_dom.js")


def _micro_dom_context() -> quickjs.Context:
    ctx = quickjs.Context()
    ctx.set_max_stack_size(10 * 1024 * 1024)
    with open(_MICRO_DOM, encoding="utf-8") as f:
        ctx.eval(f.read())
    return ctx


def _plot_margins(svg: str, width: float = 500, height: float = 400) -> dict[str, float]:
    for rect in re.findall(r"<rect\b[^>]*>", svg):
        if 'class="bg"' not in rect:
            continue
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', rect))
        x, y, w, h = map(float, (attrs["x"], attrs["y"], attrs["width"], attrs["height"]))
        return {
            "l": x,
            "t": y,
            "r": width - (x + w),
            "b": height - (y + h),
        }
    raise AssertionError("plot background rect not found")


def test_get_bbox_applies_child_rotate():
    ctx = _micro_dom_context()
    raw = ctx.eval(
        r"""
        (function() {
            var NS = 'http://www.w3.org/2000/svg';
            var text = document.createElementNS(NS, 'text');
            text.setAttribute('x', '0');
            text.setAttribute('y', '0');
            text.style.setProperty('font-size', '10');
            text.textContent = 'HelloWorld';

            var g0 = document.createElementNS(NS, 'g');
            g0.appendChild(text.cloneNode(true));
            var unrotated = g0.getBBox();

            var t = text.cloneNode(true);
            t.setAttribute('transform', 'rotate(90)');
            var g90 = document.createElementNS(NS, 'g');
            g90.appendChild(t);
            var rotated = g90.getBBox();

            // Element's own getBBox ignores its transform (SVG spec).
            var own = t.getBBox();

            return JSON.stringify({
                unrotated: {w: unrotated.width, h: unrotated.height},
                rotated: {w: rotated.width, h: rotated.height},
                own: {w: own.width, h: own.height}
            });
        })()
        """
    )
    data = json.loads(raw)
    assert data["unrotated"]["w"] > data["unrotated"]["h"]
    assert data["rotated"]["h"] > data["rotated"]["w"]
    assert data["own"]["w"] == pytest.approx(data["unrotated"]["w"])
    assert data["own"]["h"] == pytest.approx(data["unrotated"]["h"])


def test_get_bounding_client_rect_includes_rotate():
    ctx = _micro_dom_context()
    raw = ctx.eval(
        r"""
        (function() {
            var NS = 'http://www.w3.org/2000/svg';
            var text = document.createElementNS(NS, 'text');
            text.setAttribute('x', '0');
            text.setAttribute('y', '0');
            text.style.setProperty('font-size', '10');
            text.textContent = 'HelloWorld';
            text.setAttribute('transform', 'rotate(90)');
            var r = text.getBoundingClientRect();
            var bb = text.getBBox();
            return JSON.stringify({
                gbr: {w: r.width, h: r.height},
                bbox: {w: bb.width, h: bb.height}
            });
        })()
        """
    )
    data = json.loads(raw)
    assert data["bbox"]["w"] > data["bbox"]["h"]
    assert data["gbr"]["h"] > data["gbr"]["w"]


def test_transform_order_and_rotate_around_point():
    """SVG applies transforms left-to-right; rotate(a,cx,cy) is supported."""
    ctx = _micro_dom_context()
    raw = ctx.eval(
        r"""
        (function() {
            var NS = 'http://www.w3.org/2000/svg';
            function makeText(transform) {
                var g = document.createElementNS(NS, 'g');
                var t = document.createElementNS(NS, 'text');
                t.setAttribute('x', '0');
                t.setAttribute('y', '0');
                t.style.setProperty('font-size', '10');
                t.textContent = 'X';
                t.setAttribute('transform', transform);
                g.appendChild(t);
                var bb = g.getBBox();
                return {x: bb.x, y: bb.y, w: bb.width, h: bb.height};
            }
            return JSON.stringify({
                translateThenRotate: makeText('translate(100,0) rotate(90)'),
                rotateAround: makeText('rotate(90, 10, 20)'),
                scale: makeText('scale(2, 3)'),
                matrix: makeText('matrix(1,0,0,1,15,25)')
            });
        })()
        """
    )
    data = json.loads(raw)
    # SVG post-multiplies left→right, so rotate applies before translate:
    # translate(100,0) rotate(90) → bbox near x=100.
    assert data["translateThenRotate"]["x"] == pytest.approx(100, abs=10)
    assert abs(data["translateThenRotate"]["y"]) < 20
    # matrix(1,0,0,1,15,25) is a pure translate
    assert data["matrix"]["x"] == pytest.approx(15, abs=1)
    assert data["matrix"]["y"] == pytest.approx(25 - 8, abs=2)  # baseline offset
    # scale enlarges the text bbox
    assert data["scale"]["w"] == pytest.approx(2 * 6, abs=1)
    assert data["scale"]["h"] == pytest.approx(3 * 12, abs=1)
    # rotate(90, 10, 20) moves the unrotated origin into the neighborhood of the pivot
    assert data["rotateAround"]["x"] == pytest.approx(26, abs=5)
    assert data["rotateAround"]["y"] == pytest.approx(10, abs=5)


@pytest.mark.parametrize("tickangle", [45, 90, -90])
def test_rotated_tick_labels_expand_bottom_margin(tickangle):
    """automargin must grow the bottom margin for rotated x ticks, not the left."""
    labels = ["Category A", "Category B", "Category C", "Category D"]

    def make_fig(angle):
        return go.Figure(
            data=[go.Bar(x=labels, y=[1, 2, 3, 4])],
            layout=go.Layout(
                template="plotly",
                width=500,
                height=400,
                xaxis=dict(tickangle=angle, title="X Axis Title", automargin=True),
                yaxis=dict(title="Y"),
                title="Tickangle",
            ),
        )

    base = _plot_margins(mirage.to_svg(make_fig(0)))
    rotated = _plot_margins(mirage.to_svg(make_fig(tickangle)))

    assert rotated["b"] > base["b"] + 5
    # -90 previously inflated the left margin because only translate() was parsed.
    assert rotated["l"] == pytest.approx(base["l"], abs=1)
