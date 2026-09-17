"""Benchmark and visual comparison suite for Plotly Mirage vs Kaleido across 7 plot types."""

import gc
import json
import os
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import plotly.graph_objects as go
import kaleido

import mirage

ARTIFACT_DIR = Path("/Users/benjaminlear/.gemini/antigravity-ide/brain/0ea3274f-ce49-4966-84b8-fb596f6374ae")

PLOTS = {
    "scatter_line": (
        "Scatter & Line Chart",
        go.Figure(
            data=[
                go.Scatter(x=[1, 2, 3, 4, 5, 6], y=[10, 15, 13, 17, 22, 19], mode="lines+markers", name="Series A"),
                go.Scatter(x=[1, 2, 3, 4, 5, 6], y=[16, 11, 9, 14, 18, 25], mode="lines+markers", name="Series B"),
            ],
            layout=go.Layout(title="Scatter & Line Chart", width=650, height=450),
        ),
    ),
    "bar": (
        "Bar Chart (Grouped)",
        go.Figure(
            data=[
                go.Bar(name="2025", x=["Product A", "Product B", "Product C", "Product D"], y=[32, 58, 44, 76]),
                go.Bar(name="2026", x=["Product A", "Product B", "Product C", "Product D"], y=[45, 67, 52, 89]),
            ],
            layout=go.Layout(title="Grouped Bar Chart", barmode="group", width=650, height=450),
        ),
    ),
    "pie": (
        "Pie / Donut Chart",
        go.Figure(
            data=[
                go.Pie(labels=["Direct", "Organic Search", "Paid Referral", "Social", "Email"], values=[35, 25, 20, 12, 8], hole=0.3)
            ],
            layout=go.Layout(title="Traffic Distribution (Donut)", width=650, height=450),
        ),
    ),
    "box": (
        "Box Plot",
        go.Figure(
            data=[
                go.Box(y=[12, 15, 18, 19, 21, 22, 24, 25, 29, 31, 35], name="Control"),
                go.Box(y=[18, 22, 24, 27, 28, 30, 33, 36, 40, 42, 45], name="Treatment"),
            ],
            layout=go.Layout(title="Box Plot Distribution", width=650, height=450),
        ),
    ),
    "violin": (
        "Violin Plot",
        go.Figure(
            data=[
                go.Violin(y=[10, 12, 14, 15, 16, 18, 19, 20, 22, 25, 29, 32], box_visible=True, meanline_visible=True, name="Alpha"),
                go.Violin(y=[16, 18, 20, 21, 22, 24, 25, 26, 28, 30, 35, 38], box_visible=True, meanline_visible=True, name="Beta"),
            ],
            layout=go.Layout(title="Violin Distribution Plot", width=650, height=450),
        ),
    ),
    "histogram": (
        "Histogram",
        go.Figure(
            data=[
                go.Histogram(x=[1.2, 1.5, 1.8, 2.0, 2.1, 2.2, 2.5, 2.7, 2.9, 3.0, 3.1, 3.2, 3.5, 3.8, 4.0, 4.2, 4.5, 4.8, 5.0], nbinsx=8, name="Sample Set")
            ],
            layout=go.Layout(title="Frequency Histogram", width=650, height=450),
        ),
    ),
    "heatmap": (
        "Heatmap",
        go.Figure(
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
    ),
}


def build_side_by_side(mirage_img_path, kaleido_img_path, title, mirage_time, kaleido_time, output_path):
    img_m = Image.open(mirage_img_path).convert("RGBA")
    img_k = Image.open(kaleido_img_path).convert("RGBA")

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
        font_badge = ImageFont.truetype("/System/Library/Fonts/Supplemental/Verdana Bold.ttf", 12)
    except Exception:
        font_header = font_sub = font_badge = ImageFont.load_default()

    # Left Card (Mirage)
    x_m = 10
    y_top = 10
    draw.rounded_rectangle([x_m, y_top, x_m + w, y_top + header_h - 10], radius=6, fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), width=1)
    draw.text((x_m + 15, y_top + 12), "Mirage (Embedded QuickJS)", fill=(15, 23, 42, 255), font=font_header)
    speedup = f"Latency: {mirage_time * 1000:.1f} ms"
    draw.text((x_m + 15, y_top + 34), speedup, fill=(16, 149, 193, 255), font=font_sub)
    combined.paste(img_m, (x_m, y_top + header_h), img_m)

    # Right Card (Kaleido)
    x_k = w + 20
    draw.rounded_rectangle([x_k, y_top, x_k + w, y_top + header_h - 10], radius=6, fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), width=1)
    draw.text((x_k + 15, y_top + 12), "Kaleido (Chromium-based)", fill=(15, 23, 42, 255), font=font_header)
    draw.text((x_k + 15, y_top + 34), f"Latency: {kaleido_time * 1000:.1f} ms", fill=(100, 116, 139, 255), font=font_sub)
    combined.paste(img_k, (x_k, y_top + header_h), img_k)

    # Outline around images
    draw.rectangle([x_m, y_top + header_h, x_m + w, y_top + header_h + h], outline=(226, 232, 240, 255), width=1)
    draw.rectangle([x_k, y_top + header_h, x_k + w, y_top + header_h + h], outline=(226, 232, 240, 255), width=1)

    combined.save(output_path, "PNG")
    print(f"Saved side-by-side: {output_path}")


def main():
    results = []

    # Warmup engines
    dummy = go.Figure(data=[go.Scatter(x=[1], y=[1])])
    mirage.to_image(dummy, format="png")
    dummy.to_image(format="png")

    N_ROUNDS = 5

    print(f"{'Plot Type':<25} | {'Mirage (avg)':<14} | {'Kaleido (avg)':<14} | {'Speedup':<10}")
    print("-" * 72)

    for key, (display_name, fig) in PLOTS.items():
        # Benchmark Mirage
        m_times = []
        for _ in range(N_ROUNDS):
            t0 = time.perf_counter()
            png_m = mirage.to_image(fig, format="png")
            m_times.append(time.perf_counter() - t0)
        avg_m = sum(m_times) / len(m_times)

        # Benchmark Kaleido
        k_times = []
        for _ in range(N_ROUNDS):
            t0 = time.perf_counter()
            png_k = fig.to_image(format="png")
            k_times.append(time.perf_counter() - t0)
        avg_k = sum(k_times) / len(k_times)

        speedup = avg_k / avg_m if avg_m > 0 else 0
        print(f"{display_name:<25} | {avg_m*1000:>9.2f} ms | {avg_k*1000:>9.2f} ms | {speedup:>8.1f}x")

        # Save individual images
        mirage_file = ARTIFACT_DIR / f"{key}_mirage.png"
        kaleido_file = ARTIFACT_DIR / f"{key}_kaleido.png"
        mirage_file.write_bytes(png_m)
        kaleido_file.write_bytes(png_k)

        # Save combined side-by-side
        compare_file = ARTIFACT_DIR / f"compare_{key}.png"
        build_side_by_side(mirage_file, kaleido_file, display_name, avg_m, avg_k, compare_file)

        results.append({
            "key": key,
            "display_name": display_name,
            "mirage_ms": avg_m * 1000,
            "kaleido_ms": avg_k * 1000,
            "speedup": speedup,
            "mirage_bytes": len(png_m),
            "kaleido_bytes": len(png_k),
            "compare_file": str(compare_file),
        })

    # Save benchmark json
    summary_path = ARTIFACT_DIR / "benchmark_7plots.json"
    summary_path.write_text(json.dumps(results, indent=2))
    print(f"\nBenchmark results written to {summary_path}")


if __name__ == "__main__":
    main()
