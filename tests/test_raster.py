import io
import os
import tempfile
import plotly.graph_objects as go
from PIL import Image
import mirage


def test_raster_scaling_and_sizing():
    fig = go.Figure(
        data=[go.Scatter(x=[1, 2], y=[3, 4])],
        layout=go.Layout(width=400, height=300),
    )

    # Test scale=2
    png_2x = mirage.to_image(fig, format="png", scale=2.0)
    img_2x = Image.open(io.BytesIO(png_2x))
    assert img_2x.width == 800
    assert img_2x.height == 600

    # Test width and height override
    png_custom = mirage.to_image(fig, format="png", width=600, height=450)
    img_custom = Image.open(io.BytesIO(png_custom))
    assert img_custom.width == 600
    assert img_custom.height == 450


def test_file_writing_formats():
    fig = go.Figure(
        data=[go.Bar(x=["A", "B"], y=[1, 2])],
        layout=go.Layout(width=300, height=200),
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        # SVG
        svg_path = os.path.join(tmpdir, "chart.svg")
        mirage.write_image(fig, svg_path)
        assert os.path.exists(svg_path)
        with open(svg_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert content.startswith("<svg")

        # PNG
        png_path = os.path.join(tmpdir, "chart.png")
        mirage.write_image(fig, png_path)
        assert os.path.exists(png_path)
        with open(png_path, "rb") as f:
            assert f.read().startswith(b"\x89PNG")

        # JPEG
        jpg_path = os.path.join(tmpdir, "chart.jpg")
        mirage.write_image(fig, jpg_path)
        assert os.path.exists(jpg_path)
        img_jpg = Image.open(jpg_path)
        assert img_jpg.format == "JPEG"

        # WEBP
        webp_path = os.path.join(tmpdir, "chart.webp")
        mirage.write_image(fig, webp_path)
        assert os.path.exists(webp_path)
        img_webp = Image.open(webp_path)
        assert img_webp.format == "WEBP"
