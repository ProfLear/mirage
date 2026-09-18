"""Benchmark and visual side-by-side comparison generator across all supported 2D chart types."""

import io
import json
import os
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import plotly.graph_objects as go
import mirage

OUTPUT_DIR = Path("/Users/benjaminlear/GitHub/mirage/assets/benchmarks")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Pure-Vector 2D Chart Types
CHARTS = {
    # 1. Core Cartesian
    "scatter_line": {
        "category": "Core Cartesian",
        "title": "Scatter & Line Chart",
        "fig": go.Figure(
            data=[
                go.Scatter(x=[1, 2, 3, 4, 5, 6], y=[10, 15, 13, 17, 22, 19], mode="lines+markers", name="Series A"),
                go.Scatter(x=[1, 2, 3, 4, 5, 6], y=[16, 11, 9, 14, 18, 25], mode="lines+markers", name="Series B"),
            ],
            layout=go.Layout(title="Scatter & Line Chart", width=650, height=450),
        ),
    },
    "bar": {
        "category": "Core Cartesian",
        "title": "Grouped Bar Chart",
        "fig": go.Figure(
            data=[
                go.Bar(name="2025", x=["Product A", "Product B", "Product C", "Product D"], y=[32, 58, 44, 76]),
                go.Bar(name="2026", x=["Product A", "Product B", "Product C", "Product D"], y=[45, 67, 52, 89]),
            ],
            layout=go.Layout(title="Grouped Bar Chart", barmode="group", width=650, height=450),
        ),
    },
    "pie": {
        "category": "Core Cartesian",
        "title": "Donut / Pie Chart",
        "fig": go.Figure(
            data=[go.Pie(labels=["Direct", "Organic Search", "Paid Referral", "Social", "Email"], values=[35, 25, 20, 12, 8], hole=0.3)],
            layout=go.Layout(title="Traffic Distribution (Donut)", width=650, height=450),
        ),
    },
    "box": {
        "category": "Core Cartesian",
        "title": "Box Plot",
        "fig": go.Figure(
            data=[
                go.Box(y=[12, 15, 18, 19, 21, 22, 24, 25, 29, 31, 35], name="Control"),
                go.Box(y=[18, 22, 24, 27, 28, 30, 33, 36, 40, 42, 45], name="Treatment"),
            ],
            layout=go.Layout(title="Box Plot Distribution", width=650, height=450),
        ),
    },
    "violin": {
        "category": "Core Cartesian",
        "title": "Violin Plot",
        "fig": go.Figure(
            data=[
                go.Violin(y=[10, 12, 14, 15, 16, 18, 19, 20, 22, 25, 29, 32], box_visible=True, meanline_visible=True, name="Alpha"),
                go.Violin(y=[16, 18, 20, 21, 22, 24, 25, 26, 28, 30, 35, 38], box_visible=True, meanline_visible=True, name="Beta"),
            ],
            layout=go.Layout(title="Violin Distribution Plot", width=650, height=450),
        ),
    },
    "histogram": {
        "category": "Core Cartesian",
        "title": "Frequency Histogram",
        "fig": go.Figure(
            data=[go.Histogram(x=[1.2, 1.5, 1.8, 2.0, 2.1, 2.2, 2.5, 2.7, 2.9, 3.0, 3.1, 3.2, 3.5, 3.8, 4.0, 4.2, 4.5, 4.8, 5.0], nbinsx=8, name="Sample Set")],
            layout=go.Layout(title="Frequency Histogram", width=650, height=450),
        ),
    },
    "histogram2d": {
        "category": "Core Cartesian",
        "title": "2D Density Histogram",
        "fig": go.Figure(
            data=[go.Histogram2d(x=[1, 1, 2, 2, 2, 3, 3, 3, 3, 4], y=[1, 2, 2, 3, 3, 3, 4, 4, 4, 5], nbinsx=6, nbinsy=6)],
            layout=go.Layout(title="2D Density Histogram", width=650, height=450),
        ),
    },
    "contour": {
        "category": "Core Cartesian",
        "title": "2D Contour Plot",
        "fig": go.Figure(
            data=[go.Contour(z=[[10, 10.6, 12.3, 14.0], [10.6, 12.5, 14.5, 16.2], [12.3, 14.5, 17.1, 19.3], [14.0, 16.2, 19.3, 22.0]], colorscale="Blues")],
            layout=go.Layout(title="2D Contour Plot", width=650, height=450),
        ),
    },
    "heatmap": {
        "category": "Core Cartesian",
        "title": "Performance Heatmap",
        "fig": go.Figure(
            data=[
                go.Heatmap(
                    z=[[10, 25, 30, 45], [20, 35, 55, 65], [30, 45, 70, 85], [40, 60, 80, 95]],
                    x=["Q1", "Q2", "Q3", "Q4"],
                    y=["North", "South", "East", "West"],
                    colorscale="Viridis",
                )
            ],
            layout=go.Layout(title="Performance Heatmap", width=650, height=450),
        ),
    },
    "scatterternary": {
        "category": "Core Cartesian",
        "title": "Ternary Phase Diagram",
        "fig": go.Figure(
            data=[go.Scatterternary(a=[40, 30, 20], b=[30, 50, 60], c=[30, 20, 20], mode="lines+markers", name="Phase")],
            layout=go.Layout(title="Ternary Phase Diagram", width=650, height=450),
        ),
    },

    # 2. Financial & Flow
    "candlestick": {
        "category": "Financial & Business",
        "title": "Candlestick Stock Chart",
        "fig": go.Figure(
            data=[
                go.Candlestick(
                    x=["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
                    open=[100, 105, 103, 108, 107],
                    high=[108, 110, 109, 115, 112],
                    low=[98, 101, 99, 105, 102],
                    close=[105, 103, 108, 107, 111],
                )
            ],
            layout=go.Layout(title="Candlestick Stock Chart", width=650, height=450),
        ),
    },
    "ohlc": {
        "category": "Financial & Business",
        "title": "OHLC Financial Chart",
        "fig": go.Figure(
            data=[
                go.Ohlc(
                    x=["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
                    open=[100, 105, 103, 108, 107],
                    high=[108, 110, 109, 115, 112],
                    low=[98, 101, 99, 105, 102],
                    close=[105, 103, 108, 107, 111],
                )
            ],
            layout=go.Layout(title="OHLC Financial Chart", width=650, height=450),
        ),
    },
    "waterfall": {
        "category": "Financial & Business",
        "title": "Waterfall Profit & Loss",
        "fig": go.Figure(
            data=[
                go.Waterfall(
                    name="2026",
                    orientation="v",
                    measure=["relative", "relative", "total", "relative", "total"],
                    x=["Sales", "Consulting", "Gross Revenue", "Expenses", "Net Profit"],
                    y=[60, 20, 0, -35, 0],
                    connector={"line": {"color": "rgb(63, 63, 63)"}},
                )
            ],
            layout=go.Layout(title="Waterfall Profit & Loss", width=650, height=450),
        ),
    },
    "funnel": {
        "category": "Financial & Business",
        "title": "Sales Conversion Funnel",
        "fig": go.Figure(
            data=[go.Funnel(y=["Website Visit", "Sign Up", "Demo Request", "Purchase"], x=[12000, 5500, 2100, 950])],
            layout=go.Layout(title="Sales Conversion Funnel", width=650, height=450),
        ),
    },
    "funnelarea": {
        "category": "Financial & Business",
        "title": "Funnel Area Analysis",
        "fig": go.Figure(
            data=[go.Funnelarea(values=[10000, 4500, 1800, 800], text=["Visitors", "Leads", "Proposals", "Deals"])],
            layout=go.Layout(title="Funnel Area Analysis", width=650, height=450),
        ),
    },
    "indicator": {
        "category": "Financial & Business",
        "title": "KPI Performance Indicator",
        "fig": go.Figure(
            data=[
                go.Indicator(
                    mode="number+delta+gauge",
                    value=450,
                    delta={"reference": 400, "relative": True},
                    gauge={"axis": {"range": [None, 500]}, "bar": {"color": "#1f77b4"}},
                )
            ],
            layout=go.Layout(title="KPI Performance Indicator", width=650, height=450),
        ),
    },

    # 3. Hierarchical
    "treemap": {
        "category": "Hierarchical",
        "title": "Market Cap Treemap",
        "fig": go.Figure(
            data=[
                go.Treemap(
                    labels=["Market", "Tech", "Finance", "Energy", "Apple", "Microsoft", "JPMorgan", "Chevron"],
                    parents=["", "Market", "Market", "Market", "Tech", "Tech", "Finance", "Energy"],
                    values=[0, 0, 0, 0, 120, 110, 80, 70],
                )
            ],
            layout=go.Layout(title="Market Cap Treemap", width=650, height=450),
        ),
    },
    "sunburst": {
        "category": "Hierarchical",
        "title": "Global Sunburst Hierarchy",
        "fig": go.Figure(
            data=[
                go.Sunburst(
                    labels=["World", "Europe", "Asia", "France", "Germany", "Japan", "China"],
                    parents=["", "World", "World", "Europe", "Europe", "Asia", "Asia"],
                    values=[0, 0, 0, 65, 83, 125, 1400],
                )
            ],
            layout=go.Layout(title="Global Sunburst Hierarchy", width=650, height=450),
        ),
    },
    "icicle": {
        "category": "Hierarchical",
        "title": "Icicle Partition Chart",
        "fig": go.Figure(
            data=[
                go.Icicle(
                    labels=["Root", "Cluster 1", "Cluster 2", "Sub A", "Sub B", "Sub C"],
                    parents=["", "Root", "Root", "Cluster 1", "Cluster 1", "Cluster 2"],
                    values=[0, 0, 0, 10, 20, 35],
                )
            ],
            layout=go.Layout(title="Icicle Partition Chart", width=650, height=450),
        ),
    },

    # 4. Polar / Radial
    "scatterpolar": {
        "category": "Radial & Polar",
        "title": "Radar Performance Comparison",
        "fig": go.Figure(
            data=[
                go.Scatterpolar(r=[80, 90, 70, 85, 95], theta=["Speed", "Power", "Range", "Defense", "Agility"], fill="toself", name="Model X"),
                go.Scatterpolar(r=[65, 75, 90, 80, 70], theta=["Speed", "Power", "Range", "Defense", "Agility"], fill="toself", name="Model Y"),
            ],
            layout=go.Layout(title="Radar Performance Comparison", width=650, height=450),
        ),
    },
    "barpolar": {
        "category": "Radial & Polar",
        "title": "Polar Wind Rose",
        "fig": go.Figure(
            data=[go.Barpolar(r=[3, 4.5, 2, 5, 6, 3, 2, 4], theta=["N", "NE", "E", "SE", "S", "SW", "W", "NW"], name="Wind Force")],
            layout=go.Layout(title="Polar Wind Rose", width=650, height=450),
        ),
    },

    # 5. Specialized Diagrams & Tables
    "sankey": {
        "category": "Specialized Diagrams",
        "title": "Energy Flow Sankey Diagram",
        "fig": go.Figure(
            data=[
                go.Sankey(
                    node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=["Solar", "Wind", "Grid", "Residential", "Industry"]),
                    link=dict(source=[0, 1, 0, 2, 2], target=[2, 2, 3, 3, 4], value=[8, 6, 2, 9, 7]),
                )
            ],
            layout=go.Layout(title="Energy Flow Sankey Diagram", width=650, height=450),
        ),
    },
    "parcats": {
        "category": "Specialized Diagrams",
        "title": "Parallel Categories Diagram",
        "fig": go.Figure(
            data=[
                go.Parcats(
                    dimensions=[
                        dict(label="Hair", values=["Fair", "Brown", "Brown", "Brown", "Fair"]),
                        dict(label="Eye", values=["Blue", "Brown", "Hazel", "Blue", "Green"]),
                        dict(label="Sex", values=["Female", "Male", "Female", "Male", "Female"]),
                    ]
                )
            ],
            layout=go.Layout(title="Parallel Categories Diagram", width=650, height=450),
        ),
    },
    "table": {
        "category": "Specialized Diagrams",
        "title": "Formatted Data Table",
        "fig": go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Item ID", "Category", "Unit Price", "Stock Level"], fill_color="paleturquoise", align="left"),
                    cells=dict(
                        values=[[101, 102, 103, 104], ["Hardware", "Software", "Service", "Hardware"], ["$499", "$120", "$85", "$250"], [45, 120, 800, 12]],
                        fill_color="lavender",
                        align="left",
                    ),
                )
            ],
            layout=go.Layout(title="Formatted Inventory Table", width=650, height=450),
        ),
    },
    "carpet": {
        "category": "Specialized Diagrams",
        "title": "Carpet Coordinate Plot",
        "fig": go.Figure(
            data=[
                go.Carpet(
                    a=[4, 4.5, 5],
                    b=[1, 2, 3],
                    y=[[2, 3.5, 4], [3, 4.5, 5], [5, 5.5, 7]],
                    aaxis=dict(tickprefix="a = ", smoothing=0, minorgridcount=9),
                    baxis=dict(tickprefix="b = ", smoothing=0, minorgridcount=9),
                ),
                go.Scattercarpet(a=[4, 4.5, 5], b=[1.5, 2.5, 1.5], line=dict(shape="spline", smoothing=1, color="crimson")),
            ],
            layout=go.Layout(title="Carpet Coordinate Plot", width=650, height=450),
        ),
    },
}


def build_side_by_side(mirage_bytes, kaleido_bytes, display_name, mirage_time, kaleido_time, output_path):
    img_m = Image.open(io.BytesIO(mirage_bytes)).convert("RGBA")
    img_k = Image.open(io.BytesIO(kaleido_bytes)).convert("RGBA")

    w, h = img_m.size
    header_h = 70
    banner_w = w * 2 + 30
    banner_h = h + header_h + 30

    combined = Image.new("RGBA", (banner_w, banner_h), (248, 250, 252, 255))
    draw = ImageDraw.Draw(combined)

    # Font setup
    try:
        font_header = ImageFont.truetype("/System/Library/Fonts/Supplemental/Verdana Bold.ttf", 16)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Verdana.ttf", 13)
    except Exception:
        font_header = font_sub = ImageFont.load_default()

    # Left Card (Mirage)
    x_m = 10
    y_top = 10
    draw.rounded_rectangle([x_m, y_top, x_m + w, y_top + header_h - 10], radius=6, fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), width=1)
    draw.text((x_m + 15, y_top + 12), "Mirage (Embedded QuickJS)", fill=(15, 23, 42, 255), font=font_header)
    draw.text((x_m + 15, y_top + 34), f"Latency: {mirage_time * 1000:.1f} ms", fill=(16, 149, 193, 255), font=font_sub)
    combined.paste(img_m, (x_m, y_top + header_h), img_m)

    # Right Card (Kaleido)
    x_k = w + 20
    draw.rounded_rectangle([x_k, y_top, x_k + w, y_top + header_h - 10], radius=6, fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), width=1)
    draw.text((x_k + 15, y_top + 12), "Kaleido (Chromium-based)", fill=(15, 23, 42, 255), font=font_header)
    draw.text((x_k + 15, y_top + 34), f"Latency: {kaleido_time * 1000:.1f} ms", fill=(100, 116, 139, 255), font=font_sub)
    combined.paste(img_k, (x_k, y_top + header_h), img_k)

    # Outlines around images
    draw.rectangle([x_m, y_top + header_h, x_m + w, y_top + header_h + h], outline=(226, 232, 240, 255), width=1)
    draw.rectangle([x_k, y_top + header_h, x_k + w, y_top + header_h + h], outline=(226, 232, 240, 255), width=1)

    combined.save(output_path, "PNG")


def main():
    import io

    # Warmup
    dummy = go.Figure(data=[go.Scatter(x=[1], y=[1])])
    mirage.to_image(dummy, format="png")
    dummy.to_image(format="png")

    N_ROUNDS = 3
    results = []

    print(f"{'Category':<22} | {'Chart Type':<26} | {'Mirage':<10} | {'Kaleido':<11} | {'Speedup':<8}")
    print("-" * 86)

    for key, info in CHARTS.items():
        category = info["category"]
        title = info["title"]
        fig = info["fig"]

        # Benchmark Mirage
        m_times = []
        png_m = None
        for _ in range(N_ROUNDS):
            t0 = time.perf_counter()
            png_m = mirage.to_image(fig, format="png")
            m_times.append(time.perf_counter() - t0)
        avg_m = sum(m_times) / len(m_times)

        # Benchmark Kaleido
        k_times = []
        png_k = None
        for _ in range(N_ROUNDS):
            t0 = time.perf_counter()
            png_k = fig.to_image(format="png")
            k_times.append(time.perf_counter() - t0)
        avg_k = sum(k_times) / len(k_times)

        speedup = avg_k / avg_m if avg_m > 0 else 0
        print(f"{category:<22} | {title:<26} | {avg_m*1000:>7.1f} ms | {avg_k*1000:>7.1f} ms | {speedup:>6.1f}x")

        # Create side-by-side comparison image
        compare_path = OUTPUT_DIR / f"compare_{key}.png"
        build_side_by_side(png_m, png_k, title, avg_m, avg_k, compare_path)

        results.append({
            "key": key,
            "category": category,
            "title": title,
            "mirage_ms": round(avg_m * 1000, 1),
            "kaleido_ms": round(avg_k * 1000, 1),
            "speedup": round(speedup, 1),
            "image_filename": f"compare_{key}.png"
        })

    summary_file = OUTPUT_DIR / "benchmark_summary.json"
    summary_file.write_text(json.dumps(results, indent=2))
    print(f"\nAll {len(results)} comparison images generated in {OUTPUT_DIR}")
    print(f"Summary saved to {summary_file}")


if __name__ == "__main__":
    main()
