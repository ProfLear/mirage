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
    # width/height are layout size; scale multiplies them (Kaleido semantics)
    png_scaled = mirage.to_image(fig, format="png", width=1056, height=816, scale=2)
    img_scaled = Image.open(io.BytesIO(png_scaled))
    assert img_scaled.width == 2112
    assert img_scaled.height == 1632


def test_scale_applies_to_jpeg_and_webp():
    fig = go.Figure(
        data=[go.Scatter(x=[1, 2], y=[3, 4])],
        layout=go.Layout(width=200, height=100),
    )

    jpg = mirage.to_image(fig, format="jpeg", width=200, height=100, scale=2)
    img_jpg = Image.open(io.BytesIO(jpg))
    assert img_jpg.width == 400
    assert img_jpg.height == 200
    assert img_jpg.format == "JPEG"

    webp = mirage.to_image(fig, format="webp", width=200, height=100, scale=2)
    img_webp = Image.open(io.BytesIO(webp))
    assert img_webp.width == 400
    assert img_webp.height == 200
    assert img_webp.format == "WEBP"


def test_svg_ignores_scale():
    """SVG output uses layout size only; scale is ignored (Kaleido-compatible)."""
    import re

    fig = go.Figure(
        data=[go.Scatter(x=[1, 2], y=[3, 4])],
        layout=go.Layout(width=400, height=300),
    )

    svg_1x = mirage.to_image(fig, format="svg", width=400, height=300, scale=1).decode("utf-8")
    svg_2x = mirage.to_image(fig, format="svg", width=400, height=300, scale=2).decode("utf-8")

    def root_tag(svg: str) -> str:
        root = re.search(r"<svg\b[^>]*>", svg)
        assert root is not None
        return root.group(0)

    def root_size(svg: str) -> tuple[str, str]:
        tag = root_tag(svg)
        w = re.search(r'\bwidth="([^"]*)"', tag)
        h = re.search(r'\bheight="([^"]*)"', tag)
        assert w and h
        return w.group(1), h.group(1)

    assert root_size(svg_1x) == ("400", "300")
    assert root_size(svg_2x) == ("400", "300")
    assert "viewBox" not in root_tag(svg_2x)


def test_prepare_svg_sets_scaled_size_and_viewbox():
    import re
    from mirage.raster import _prepare_svg_for_raster

    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"><rect width="100" height="50"/></svg>'
    prepared = _prepare_svg_for_raster(svg, width=100, height=50, scale=2.5)
    root = re.search(r"<svg\b[^>]*>", prepared).group(0)
    assert 'width="250"' in root
    assert 'height="125"' in root
    assert 'viewBox="0 0 100 50"' in root


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
