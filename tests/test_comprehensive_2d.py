"""Tests for comprehensive 2D chart types in Mirage."""

import pytest
import plotly.graph_objects as go
import mirage


@pytest.mark.parametrize(
    "name,fig",
    [
        ("candlestick", go.Figure(data=[go.Candlestick(x=["2026-01-01", "2026-01-02"], open=[100, 105], high=[110, 108], low=[95, 101], close=[105, 102])])),
        ("ohlc", go.Figure(data=[go.Ohlc(x=["2026-01-01", "2026-01-02"], open=[100, 105], high=[110, 108], low=[95, 101], close=[105, 102])])),
        ("waterfall", go.Figure(data=[go.Waterfall(x=["A", "B", "Total"], y=[10, -5, 0], measure=["relative", "relative", "total"])])),
        ("funnel", go.Figure(data=[go.Funnel(y=["Step 1", "Step 2"], x=[100, 50])])),
        ("funnelarea", go.Figure(data=[go.Funnelarea(values=[100, 50], labels=["Step 1", "Step 2"])])),
        ("indicator", go.Figure(data=[go.Indicator(mode="number+delta", value=120, delta={"reference": 100})])),
        ("treemap", go.Figure(data=[go.Treemap(labels=["A", "B", "C"], parents=["", "A", "A"])])),
        ("sunburst", go.Figure(data=[go.Sunburst(labels=["A", "B", "C"], parents=["", "A", "A"])])),
        ("icicle", go.Figure(data=[go.Icicle(labels=["A", "B", "C"], parents=["", "A", "A"])])),
        ("scatterpolar", go.Figure(data=[go.Scatterpolar(r=[1, 2, 3], theta=["0", "90", "180"], fill="toself")])),
        ("barpolar", go.Figure(data=[go.Barpolar(r=[1, 2, 3], theta=["0", "90", "180"])])),
        ("sankey", go.Figure(data=[go.Sankey(node=dict(label=["A", "B"]), link=dict(source=[0], target=[1], value=[5]))])),
        ("parcats", go.Figure(data=[go.Parcats(dimensions=[dict(label="A", values=["x", "y"]), dict(label="B", values=["p", "q"])])])),
        ("parcoords", go.Figure(data=[go.Parcoords(dimensions=[dict(label="A", values=[1, 2]), dict(label="B", values=[3, 4])])])),
        ("table", go.Figure(data=[go.Table(header=dict(values=["Col A", "Col B"]), cells=dict(values=[[1, 2], [3, 4]]))])),
        ("scatterternary", go.Figure(data=[go.Scatterternary(a=[1, 2], b=[2, 3], c=[3, 1])])),
        ("carpet", go.Figure(data=[go.Carpet(a=[1, 2], b=[1, 2], y=[[1, 2], [3, 4]])])),
        ("scattercarpet", go.Figure(data=[
            go.Carpet(a=[4, 4.5, 5], b=[1, 2, 3], y=[[2, 3.5, 4], [3, 4.5, 5], [5, 5.5, 7]]),
            go.Scattercarpet(a=[4, 4.5, 5], b=[1.5, 2.5, 1.5])
        ])),
        ("contourcarpet", go.Figure(data=[
            go.Carpet(a=[4, 4.5, 5], b=[1, 2, 3], y=[[2, 3.5, 4], [3, 4.5, 5], [5, 5.5, 7]]),
            go.Contourcarpet(a=[4, 4.5, 5], b=[1, 2, 3], z=[[1, 2, 3], [2, 4, 5], [3, 2, 9]])
        ])),
    ],
)
def test_comprehensive_2d_charts(name, fig):
    svg = mirage.to_svg(fig)
    assert "<svg" in svg
    png = mirage.to_image(fig, format="png")
    assert png.startswith(b"\x89PNG")
    assert len(png) > 1000
