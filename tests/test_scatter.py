import io
import plotly.graph_objects as go
import mirage


def test_scatter_to_svg():
    fig = go.Figure(
        data=[
            go.Scatter(
                x=[1, 2, 3, 4],
                y=[10, 15, 13, 17],
                mode="lines+markers",
                name="Test Scatter",
            )
        ],
        layout=go.Layout(title="Scatter Plot Test", width=500, height=350),
    )

    svg = mirage.to_svg(fig)
    assert isinstance(svg, str)
    assert svg.startswith("<svg")
    assert "</svg>" in svg
    assert "Scatter Plot Test" in svg
    assert 'class="point"' in svg
    assert 'class="js-line"' in svg


def test_scatter_to_png():
    fig = go.Figure(
        data=[go.Scatter(x=[1, 2, 3], y=[4, 5, 6], mode="markers")],
        layout=go.Layout(width=400, height=300),
    )

    png_bytes = mirage.to_image(fig, format="png")
    assert isinstance(png_bytes, bytes)
    # Check PNG magic header
    assert png_bytes[:4] == b"\x89PNG"
    assert len(png_bytes) > 1000
