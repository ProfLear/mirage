import io
import plotly.graph_objects as go
from PIL import Image
import mirage


def test_default_white_background():
    fig = go.Figure(
        data=[go.Scatter(x=[1, 2], y=[10, 20])],
        layout=go.Layout(width=400, height=300),
    )
    svg = mirage.to_svg(fig)
    # Background rect with fill should be inserted
    assert '<rect x="0" y="0" width="400" height="300"' in svg
    assert "fill: rgb(255, 255, 255)" in svg

    png = mirage.to_image(fig, format="png")
    im = Image.open(io.BytesIO(png))
    # Corner pixel should be opaque white
    assert im.getpixel((0, 0)) == (255, 255, 255, 255)


def test_transparent_background():
    fig = go.Figure(
        data=[go.Scatter(x=[1, 2], y=[10, 20])],
        layout=go.Layout(width=400, height=300, paper_bgcolor="rgba(0,0,0,0)"),
    )
    png = mirage.to_image(fig, format="png")
    im = Image.open(io.BytesIO(png))
    # Corner pixel alpha should be 0 (transparent)
    assert im.getpixel((0, 0))[3] == 0


def test_custom_color_background():
    fig = go.Figure(
        data=[go.Scatter(x=[1, 2], y=[10, 20])],
        layout=go.Layout(width=400, height=300, paper_bgcolor="#ff0000"),
    )
    svg = mirage.to_svg(fig)
    assert "fill: rgb(255, 0, 0)" in svg

    png = mirage.to_image(fig, format="png")
    im = Image.open(io.BytesIO(png))
    assert im.getpixel((0, 0)) == (255, 0, 0, 255)
