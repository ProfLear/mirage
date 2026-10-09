"""Tests for figure values that are not natively JSON-serializable."""

import datetime as dt
import decimal

import plotly.graph_objects as go
import pytest

import mirage

CASES = [
    (
        "datetime",
        go.Figure(
            data=[
                go.Scatter(
                    x=[dt.datetime(2024, 1, 1), dt.datetime(2024, 1, 2), dt.datetime(2024, 1, 3)], y=[1, 2, 3]
                )
            ],
            layout=go.Layout(
                title="Datetime",
                width=500,
                height=350,
                xaxis={"range": [dt.datetime(2024, 1, 1), dt.datetime(2024, 1, 4)]},
            ),
        ),
    ),
    (
        "date",
        go.Figure(
            data=[go.Scatter(x=[dt.date(2024, 1, 1), dt.date(2024, 1, 2), dt.date(2024, 1, 3)], y=[1, 2, 3])],
            layout=go.Layout(title="Date", width=500, height=350),
        ),
    ),
    (
        "time",
        go.Figure(
            data=[go.Scatter(x=[dt.time(1, 0), dt.time(2, 0), dt.time(3, 0)], y=[1, 2, 3])],
            layout=go.Layout(title="Time", width=500, height=350),
        ),
    ),
    (
        "decimal",
        go.Figure(
            data=[
                go.Scatter(
                    x=[decimal.Decimal("1.5"), decimal.Decimal("2.5"), decimal.Decimal("3.5")],
                    y=[decimal.Decimal("10"), decimal.Decimal("20"), decimal.Decimal("30")],
                )
            ],
            layout=go.Layout(
                title="Decimal",
                width=500,
                height=350,
                annotations=[
                    {"x": decimal.Decimal("2.5"), "y": decimal.Decimal("20"), "text": "note", "showarrow": False}
                ],
                xaxis={
                    "tickvals": [decimal.Decimal("1.5"), decimal.Decimal("2.5"), decimal.Decimal("3.5")],
                    "ticktext": ["a", "b", "c"],
                },
            ),
        ),
    ),
]

try:
    import numpy as np

    CASES.extend(
        [
            (
                "numpy-datetime64",
                go.Figure(
                    data=[
                        go.Scatter(
                            x=np.array(["2024-01-01", "2024-01-02", "2024-01-03"], dtype="datetime64[D]"),
                            y=np.array([1, 2, 3]),
                        )
                    ],
                    layout=go.Layout(title="Numpy datetime64", width=500, height=350),
                ),
            ),
            (
                "numpy-object-array",
                go.Figure(
                    data=[
                        go.Bar(
                            x=np.array(["alpha", "beta", "gamma"], dtype=object),
                            y=np.array(
                                [decimal.Decimal("1.5"), decimal.Decimal("2.5"), decimal.Decimal("4")], dtype=object
                            ),
                        )
                    ],
                    layout=go.Layout(title="Numpy object array", width=500, height=350),
                ),
            ),
        ]
    )
except ImportError:
    pass

try:
    import pandas as pd

    CASES.extend(
        [
            (
                "pandas-timestamp",
                go.Figure(
                    data=[go.Scatter(x=[pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02"), pd.NaT], y=[1, 2, 3])],
                    layout=go.Layout(
                        title="Timestamp",
                        width=500,
                        height=350,
                        xaxis={"range": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-05")]},
                    ),
                ),
            ),
            (
                "pandas-timestamp-series",
                go.Figure(
                    data=[go.Scatter(x=pd.Series(pd.date_range("2024-01-01", periods=3)), y=pd.Series([1, 2, 3]))],
                    layout=go.Layout(title="Timestamp series", width=500, height=350),
                ),
            ),
            (
                "pandas-timedelta",
                go.Figure(
                    data=[go.Scatter(x=[pd.Timedelta(days=1), pd.Timedelta(days=2), pd.Timedelta(days=3)], y=[1, 2, 3])],
                    layout=go.Layout(title="Timedelta", width=500, height=350),
                ),
            ),
            (
                "pandas-na",
                go.Figure(
                    data=[go.Scatter(x=[1, 2, 3, 4], y=[1, pd.NA, 3, pd.NA])],
                    layout=go.Layout(title="Pandas NA", width=500, height=350),
                ),
            ),
        ]
    )
except ImportError:
    pass


@pytest.mark.parametrize("name,fig", CASES)
def test_non_json_values_render(name, fig):
    svg = mirage.to_svg(fig)
    assert "<svg" in svg
    png = mirage.to_image(fig, format="png")
    assert png.startswith(b"\x89PNG")


def test_hooked_to_image_with_decimal_values():
    mirage.register()

    fig = go.Figure(
        data=[
            go.Scatter(
                x=[decimal.Decimal("1"), decimal.Decimal("2"), decimal.Decimal("3")],
                y=[decimal.Decimal("4"), decimal.Decimal("5"), decimal.Decimal("6")],
            )
        ],
        layout=go.Layout(title="Hooked decimal", width=400, height=300),
    )

    img_bytes = fig.to_image(format="png")
    assert img_bytes.startswith(b"\x89PNG")

    mirage.unregister()
