import plotly.graph_objects as go
import mirage


def test_bar_chart():
    fig = go.Figure(
        data=[
            go.Bar(name="SF", x=["Apples", "Oranges"], y=[10, 20]),
            go.Bar(name="Montreal", x=["Apples", "Oranges"], y=[15, 25]),
        ],
        layout=go.Layout(barmode="group", width=500, height=350, title="Bar Chart"),
    )

    svg = mirage.to_svg(fig)
    assert "<svg" in svg
    assert "Bar Chart" in svg
    assert "Apples" in svg
    assert "Oranges" in svg

    png = mirage.to_image(fig, format="png")
    assert png.startswith(b"\x89PNG")
