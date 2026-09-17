import os
import tempfile
import plotly.graph_objects as go
import mirage


def test_plotly_register_integration():
    # Register Mirage into plotly
    mirage.register()

    fig = go.Figure(
        data=[go.Scatter(x=[1, 2, 3], y=[10, 20, 30])],
        layout=go.Layout(title="Patched Export", width=400, height=300),
    )

    # Calling fig.to_image() directly without engine specified
    img_bytes = fig.to_image(format="png")
    assert img_bytes.startswith(b"\x89PNG")

    # Calling fig.write_image()
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "test.png")
        fig.write_image(out_file)
        assert os.path.exists(out_file)
        with open(out_file, "rb") as f:
            assert f.read().startswith(b"\x89PNG")

    # Unregister to clean up
    mirage.unregister()
