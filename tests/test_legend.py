import plotly.graph_objects as go
import mirage


def test_legend_rendering():
    fig = go.Figure(
        data=[
            go.Scatter(x=[1, 2, 3], y=[10, 20, 30], name="First Series", mode="lines+markers"),
            go.Scatter(x=[1, 2, 3], y=[20, 15, 10], name="Second Series", mode="lines+markers"),
        ],
        layout=go.Layout(
            title="Multi-Series Legend Test",
            showlegend=True,
            width=600,
            height=400,
        ),
    )

    svg = mirage.to_svg(fig)
    assert "First Series" in svg
    assert "Second Series" in svg
    assert "infolayer" in svg
    assert "Multi-Series Legend Test" in svg

    png = mirage.to_image(fig, format="png")
    assert png.startswith(b"\x89PNG")
