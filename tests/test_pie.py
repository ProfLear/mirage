import plotly.graph_objects as go
import mirage


def test_pie_chart():
    fig = go.Figure(
        data=[go.Pie(labels=["Oxygen", "Hydrogen", "Carbon_Dioxide", "Nitrogen"], values=[4500, 2500, 1053, 500])],
        layout=go.Layout(title="Pie Chart", width=450, height=350),
    )

    svg = mirage.to_svg(fig)
    assert "<svg" in svg
    assert "Pie Chart" in svg
    assert "Oxygen" in svg

    png = mirage.to_image(fig, format="png")
    assert png.startswith(b"\x89PNG")
