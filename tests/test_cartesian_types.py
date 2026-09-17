import plotly.graph_objects as go
import mirage


def test_box_plot():
    fig = go.Figure(
        data=go.Box(y=[1, 2, 3, 4, 4, 5, 6, 7, 8, 9], name="Sample"),
        layout=go.Layout(title="Box Plot Test", width=500, height=350),
    )
    svg = mirage.to_svg(fig)
    assert "<svg" in svg
    assert "Box Plot Test" in svg
    assert "box" in svg.lower()
    png = mirage.to_image(fig, format="png")
    assert png.startswith(b"\x89PNG")


def test_violin_plot():
    fig = go.Figure(
        data=go.Violin(y=[1, 2, 3, 4, 4, 5, 6, 7, 8, 9], box_visible=True, name="Distribution"),
        layout=go.Layout(title="Violin Plot Test", width=500, height=350),
    )
    svg = mirage.to_svg(fig)
    assert "<svg" in svg
    assert "Violin Plot Test" in svg
    assert "violin" in svg.lower()
    png = mirage.to_image(fig, format="png")
    assert png.startswith(b"\x89PNG")


def test_histogram():
    fig = go.Figure(
        data=go.Histogram(x=[1, 2, 2, 3, 3, 3, 4, 4, 5], nbinsx=5),
        layout=go.Layout(title="Histogram Test", width=500, height=350),
    )
    svg = mirage.to_svg(fig)
    assert "<svg" in svg
    assert "Histogram Test" in svg
    png = mirage.to_image(fig, format="png")
    assert png.startswith(b"\x89PNG")
