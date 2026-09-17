# Mirage 🪄

> **Ultra-lightweight, browser-less static image exporter for Plotly in Python.**  
> *Zero Chrome. Zero Chromium. Zero Playwright. 100% Vector & Raster Fidelity.*

---

## The Problem with Kaleido & Headless Browsers

Historically, exporting static images (`.svg`, `.png`, `.jpg`, `.webp`) from Plotly in Python relied on **Kaleido**:
* **Kaleido v0.1/v0.2** bundled a custom, monolithic Chromium build that frequently froze, deadlocked, or failed to install across various Linux distributions and architectures (like ARM64 / Apple Silicon).
* **Kaleido v1+** transitioned to requiring a full installation of Google Chrome or downloading ~150MB+ Playwright browser binaries.
* In **Docker containers, AWS Lambda, minimal Linux (Alpine), and CI/CD pipelines**, installing Chrome or WebKit pulls in hundreds of megabytes of system packages (`libglib`, `libgtk`, `libnss`, `Xvfb`), making deployments slow, fragile, and bloated.

---

## How Mirage Works

Plotly's Python figures are JSON specifications. The actual layout math, coordinate scaling, D3 curves, and SVG construction live inside `plotly.js`.

**Mirage executes Plotly's official chart engine without a browser:**

```
┌───────────────────────────────┐
│     fig = go.Figure(...)      │
└──────────────┬────────────────┘
               │ fig.to_dict()
               ▼
┌────────────────────────────────────────────────────────┐
│  Mirage Engine (Embedded QuickJS Runtime)               │
│                                                        │
│  1. Micro-DOM (~400 lines JS):                         │
│     - Minimal SVG/HTML element tree                    │
│     - D3 selector & attribute managers                 │
│  2. Pillow Font Engine:                                │
│     - Answers getBBox() text measurements via PIL      │
│  3. Plotly 2D Engine:                                  │
│     - Computes layout & renders vector chart           │
│  4. Extracts clean, standalone <svg>                   │
└──────────────────────────────┬─────────────────────────┘
                               │ Pure SVG Vector Output
                               ▼
               ┌───────────────────────────────┐
               │    resvg-py (Rust Wheel)      │
               │    Instant SVG ➔ PNG / JPEG   │
               └───────────────────────────────┘
```

1. **Embedded QuickJS Engine**: Runs the official `plotly.js` bundle inside an embedded C JavaScript runtime (~1.5 MB wheel).
2. **Micro-DOM**: Implements the precise subset of DOM and SVG APIs that D3 and Plotly require to build the SVG scene graph.
3. **Pillow Font Engine**: When Plotly asks for text bounding boxes (`getBBox()`), Mirage queries Python's `PIL.ImageFont` to measure text dimensions, ensuring clean margins, titles, and tick placements without overlaps.
4. **Rust Vector Rasterization (`resvg-py`)**: Converts SVG directly into crisp PNG, JPEG, or WEBP bytes in milliseconds with zero C++ system dependencies.

---

## Performance Benchmark

| Metric | Kaleido (Chrome / Playwright) | **Mirage** | Speedup |
| :--- | :--- | :--- | :--- |
| **Download / Install Size** | 150MB – 300MB | **~12MB** | **~25x smaller** |
| **Cold Startup Time** | 2.5s – 4.0s | **~130ms** | **~20x faster** |
| **Per-Plot Render Time** | 1,500ms – 3,000ms | **~28ms** | **~50x–100x faster** |
| **System Dependencies** | Chrome / GTK / X11 / Xvfb | **Zero** (Pure wheels) | Complete portability |

---

## Installation

### From GitHub (Pre-PyPI / Development)
```bash
pip install git+https://github.com/ProfLear/mirage.git
```
Or for local development:
```bash
pip install -e .
```

### From PyPI (Upcoming)
```bash
pip install plotly-mirage
```

Works out-of-the-box on **macOS (Intel & Apple Silicon), Linux (Ubuntu, Debian, Fedora, Alpine/musl), and Windows 10/11**.

---

## Quickstart

### 1. Direct API

```python
import plotly.express as px
import mirage

fig = px.scatter(x=[1, 2, 3, 4], y=[10, 11, 12, 13], title="Sales Growth")

# Export to SVG string or file
svg_str = mirage.to_svg(fig)
mirage.write_image(fig, "sales.svg")

# Export to PNG / JPEG / WEBP
png_bytes = mirage.to_image(fig, format="png", scale=2.0)
mirage.write_image(fig, "sales.png", scale=2.0)
mirage.write_image(fig, "sales.jpg")
mirage.write_image(fig, "sales.webp")
```

### 2. Drop-in Replacement for Kaleido (`mirage.register()`)

If you have existing code using Plotly's native `fig.write_image()` or `fig.to_image()`:

```python
import plotly.express as px
import mirage

# Patch Plotly to use Mirage
mirage.register()

fig = px.bar(x=["A", "B", "C"], y=[1, 3, 2])

# These now run instantly via Mirage without Chrome or Kaleido!
fig.write_image("chart.png")
fig.write_image("chart.svg")
png_data = fig.to_image(format="png")
```

---

## Supported Chart Types

Mirage currently supports all standard 2D Cartesian and Polar Plotly charts:
* Scatter & Line plots (`px.scatter`, `px.line`)
* Bar charts (`px.bar`, grouped & stacked)
* Histograms (`px.histogram`)
* Box & Violin plots (`px.box`, `px.violin`)
* Pie & Donut charts (`px.pie`)
* Heatmaps (`px.density_heatmap`, `go.Heatmap`)
* Multi-series legends, titles, annotations, and axis styling

*(Note: 3D/WebGL plots like `scatter3d` and `surface` require an OpenGL GPU context and are not currently supported).*

---

## License

MIT License. Copyright (c) 2026 Benjamin Lear.
