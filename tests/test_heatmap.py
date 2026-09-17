import plotly.graph_objects as go
import mirage


def test_heatmap():
    fig = go.Figure(
        data=go.Heatmap(
            z=[[1, None, 30, 50, 1], [20, 1, 60, 80, 30], [30, 60, 1, -10, 20]],
            x=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            y=["Morning", "Afternoon", "Evening"],
        ),
        layout=go.Layout(title="Heatmap Test", width=550, height=350),
    )

    svg = mirage.to_svg(fig)
    assert "<svg" in svg
    assert "Heatmap Test" in svg
    assert "Monday" in svg

    png = mirage.to_image(fig, format="png")
    assert png.startswith(b"\x89PNG")
