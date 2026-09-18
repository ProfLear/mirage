# Mirage 🪄

> **Ultra-lightweight, browser-less static image exporter for Plotly in Python.**  
> *Zero Chrome. Zero Chromium. Zero Playwright. 100% Vector & Raster Fidelity.*

---

## Why Mirage?

Historically, exporting static images (`.svg`, `.png`, `.jpg`, `.webp`) from Plotly in Python required **Kaleido**:
* **Kaleido v0.1/v0.2** bundled an unmaintained, monolithic Chromium binary that frequently deadlocked, crashed on ARM64 / Apple Silicon, or failed on modern Linux distributions.
* **Kaleido v1+** transitioned to requiring a full installation of Google Chrome or downloading ~150MB–300MB Playwright browser binaries.
* In **Docker containers, AWS Lambda, lightweight Linux (Alpine), and CI/CD pipelines**, installing Chrome pulls in hundreds of megabytes of system packages (`libglib`, `libgtk`, `libnss`, `Xvfb`), making deployments bloated and fragile.

**Mirage eliminates all browser dependencies entirely.** It executes Plotly's official SVG engine inside an embedded QuickJS JavaScript runtime, measures fonts using Pillow, and rasterizes pixel-perfect images via high-performance Rust (`resvg-py`).

---

## How Mirage Works

Plotly Python figures are JSON specifications. The actual layout math, coordinate scaling, D3 curves, and SVG construction live inside `plotly.js`.

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
│  3. Comprehensive 2D Plotly Engine:                    │
│     - Computes layout & renders 29 pure-vector traces  │
│  4. Extracts clean, standalone <svg>                   │
└──────────────────────────────┬─────────────────────────┘
                               │ Pure SVG Vector Output
                               ▼
                ┌───────────────────────────────┐
                │    resvg-py (Rust Wheel)      │
                │    Instant SVG ➔ PNG / JPEG   │
                └───────────────────────────────┘
```

1. **Embedded QuickJS Engine**: Runs the official `plotly.js` bundle inside an embedded C JavaScript runtime (~1.8 MB bundle).
2. **Micro-DOM**: Implements the precise subset of DOM and SVG APIs that D3 and Plotly require to build the SVG scene graph.
3. **Pillow Font Engine**: When Plotly asks for text bounding boxes (`getBBox()`), Mirage queries Python's `PIL.ImageFont` to measure text dimensions, ensuring clean margins, titles, and tick placements without overlaps.
4. **Rust Vector Rasterization (`resvg-py`)**: Converts SVG directly into crisp PNG, JPEG, or WEBP bytes in milliseconds with zero C++ system dependencies.

---

## Installation

```bash
pip install plotly-mirage
```

Or install the latest development version directly from GitHub:
```bash
pip install git+https://github.com/ProfLear/mirage.git
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

# Patch Plotly to use Mirage instead of Kaleido
mirage.register()

fig = px.bar(x=["A", "B", "C"], y=[1, 3, 2])

# These now run instantly via Mirage without Chrome or Kaleido!
fig.write_image("chart.png")
fig.write_image("chart.svg")
png_data = fig.to_image(format="png")
```

---

## Performance Benchmarks across 25 Chart Types

Below is an empirical benchmark comparing **Mirage** against **Kaleido** across 25 standard Plotly chart types (tested on Apple Silicon, measuring average per-image export latency after engine warmup):

| Category | Chart Type | Mirage Latency | Kaleido Latency | Speedup |
| :--- | :--- | :---: | :---: | :---: |
| **Core Cartesian** | Scatter & Line Chart | **55.9 ms** | 1074.0 ms | **19.2x** |
| **Core Cartesian** | Grouped Bar Chart | **51.2 ms** | 1023.1 ms | **20.0x** |
| **Core Cartesian** | Donut / Pie Chart | **51.4 ms** | 1147.8 ms | **22.3x** |
| **Core Cartesian** | Box Plot | **56.2 ms** | 1171.2 ms | **20.8x** |
| **Core Cartesian** | Violin Plot | **54.4 ms** | 1165.4 ms | **21.4x** |
| **Core Cartesian** | Frequency Histogram | **39.9 ms** | 1098.7 ms | **27.5x** |
| **Core Cartesian** | 2D Density Histogram | **63.5 ms** | 1092.7 ms | **17.2x** |
| **Core Cartesian** | 2D Contour Plot | **74.1 ms** | 1097.0 ms | **14.8x** |
| **Core Cartesian** | Performance Heatmap | **58.2 ms** | 1078.1 ms | **18.5x** |
| **Core Cartesian** | Ternary Phase Diagram | **58.8 ms** | 1071.9 ms | **18.2x** |
| **Financial & Business** | Candlestick Stock Chart | **85.2 ms** | 1126.1 ms | **13.2x** |
| **Financial & Business** | OHLC Financial Chart | **77.9 ms** | 1096.7 ms | **14.1x** |
| **Financial & Business** | Waterfall Profit & Loss | **42.4 ms** | 1075.7 ms | **25.4x** |
| **Financial & Business** | Sales Conversion Funnel | **59.7 ms** | 1116.3 ms | **18.7x** |
| **Financial & Business** | Funnel Area Analysis | **45.8 ms** | 1094.3 ms | **23.9x** |
| **Financial & Business** | KPI Performance Indicator | **37.8 ms** | 1033.5 ms | **27.3x** |
| **Hierarchical** | Market Cap Treemap | **41.1 ms** | 1138.6 ms | **27.7x** |
| **Hierarchical** | Global Sunburst Hierarchy | **44.2 ms** | 1116.2 ms | **25.3x** |
| **Hierarchical** | Icicle Partition Chart | **35.2 ms** | 1095.0 ms | **31.1x** |
| **Radial & Polar** | Radar Performance Comparison | **62.5 ms** | 1028.6 ms | **16.5x** |
| **Radial & Polar** | Polar Wind Rose | **42.8 ms** | 1150.5 ms | **26.9x** |
| **Specialized Diagrams** | Energy Flow Sankey Diagram | **32.5 ms** | 1535.5 ms | **47.3x** |
| **Specialized Diagrams** | Parallel Categories Diagram | **49.7 ms** | 1166.3 ms | **23.5x** |
| **Specialized Diagrams** | Formatted Data Table | **40.7 ms** | 1073.1 ms | **26.3x** |
| **Specialized Diagrams** | Carpet Coordinate Plot | **58.9 ms** | 1136.5 ms | **19.3x** |

> **Overall Summary**: Mirage delivers a **20x to 65x speedup** across all chart types while using **~25x less disk space** and requiring **zero browser processes**.

---

## Visual Fidelity & Side-by-Side Comparisons

Every plot exported by Mirage matches the exact visual output, layout geometry, font proportions, and colors generated by Plotly and Kaleido.

### Core Cartesian

#### Scatter & Line Chart (Mirage: 55.9ms | Kaleido: 1074.0ms)

![Scatter & Line Chart](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_scatter_line.png)

#### Grouped Bar Chart (Mirage: 51.2ms | Kaleido: 1023.1ms)

![Grouped Bar Chart](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_bar.png)

#### Donut / Pie Chart (Mirage: 51.4ms | Kaleido: 1147.8ms)

![Donut / Pie Chart](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_pie.png)

#### Box Plot (Mirage: 56.2ms | Kaleido: 1171.2ms)

![Box Plot](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_box.png)

#### Violin Plot (Mirage: 54.4ms | Kaleido: 1165.4ms)

![Violin Plot](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_violin.png)

#### Frequency Histogram (Mirage: 39.9ms | Kaleido: 1098.7ms)

![Frequency Histogram](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_histogram.png)

#### 2D Density Histogram (Mirage: 63.5ms | Kaleido: 1092.7ms)

![2D Density Histogram](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_histogram2d.png)

#### 2D Contour Plot (Mirage: 74.1ms | Kaleido: 1097.0ms)

![2D Contour Plot](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_contour.png)

#### Performance Heatmap (Mirage: 58.2ms | Kaleido: 1078.1ms)

![Performance Heatmap](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_heatmap.png)

#### Ternary Phase Diagram (Mirage: 58.8ms | Kaleido: 1071.9ms)

![Ternary Phase Diagram](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_scatterternary.png)

### Financial & Business

#### Candlestick Stock Chart (Mirage: 85.2ms | Kaleido: 1126.1ms)

![Candlestick Stock Chart](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_candlestick.png)

#### OHLC Financial Chart (Mirage: 77.9ms | Kaleido: 1096.7ms)

![OHLC Financial Chart](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_ohlc.png)

#### Waterfall Profit & Loss (Mirage: 42.4ms | Kaleido: 1075.7ms)

![Waterfall Profit & Loss](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_waterfall.png)

#### Sales Conversion Funnel (Mirage: 59.7ms | Kaleido: 1116.3ms)

![Sales Conversion Funnel](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_funnel.png)

#### Funnel Area Analysis (Mirage: 45.8ms | Kaleido: 1094.3ms)

![Funnel Area Analysis](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_funnelarea.png)

#### KPI Performance Indicator (Mirage: 37.8ms | Kaleido: 1033.5ms)

![KPI Performance Indicator](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_indicator.png)

### Hierarchical

#### Market Cap Treemap (Mirage: 41.1ms | Kaleido: 1138.6ms)

![Market Cap Treemap](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_treemap.png)

#### Global Sunburst Hierarchy (Mirage: 44.2ms | Kaleido: 1116.2ms)

![Global Sunburst Hierarchy](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_sunburst.png)

#### Icicle Partition Chart (Mirage: 35.2ms | Kaleido: 1095.0ms)

![Icicle Partition Chart](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_icicle.png)

### Radial & Polar

#### Radar Performance Comparison (Mirage: 62.5ms | Kaleido: 1028.6ms)

![Radar Performance Comparison](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_scatterpolar.png)

#### Polar Wind Rose (Mirage: 42.8ms | Kaleido: 1150.5ms)

![Polar Wind Rose](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_barpolar.png)

### Specialized Diagrams

#### Energy Flow Sankey Diagram (Mirage: 32.5ms | Kaleido: 1535.5ms)

![Energy Flow Sankey Diagram](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_sankey.png)

#### Parallel Categories Diagram (Mirage: 49.7ms | Kaleido: 1166.3ms)

![Parallel Categories Diagram](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_parcats.png)

#### Formatted Data Table (Mirage: 40.7ms | Kaleido: 1073.1ms)

![Formatted Data Table](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_table.png)

#### Carpet Coordinate Plot (Mirage: 58.9ms | Kaleido: 1136.5ms)

![Carpet Coordinate Plot](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_carpet.png)

---

## Supported Plotly Traces (28 Total)

Mirage includes full pure-vector support for all 28 non-WebGL Plotly trace types:

| Category | Supported Traces |
| :--- | :--- |
| **Core Cartesian** | `scatter` (lines, markers, area, text, ecdf), `bar` (vertical, horizontal, stacked, grouped, timeline), `pie` (donut), `box`, `violin`, `histogram`, `histogram2d`, `histogram2dcontour`, `contour`, `heatmap`, `scatterternary`, `image` |
| **Financial & Business** | `candlestick`, `ohlc`, `waterfall`, `funnel`, `funnelarea`, `indicator` (gauges, KPI big numbers) |
| **Hierarchical Partitions** | `treemap`, `sunburst`, `icicle` |
| **Radial / Polar** | `scatterpolar` (radar/spider), `barpolar` |
| **Specialized Diagrams & Tables** | `sankey`, `parcats` (parallel categories), `table`, `carpet`, `scattercarpet`, `contourcarpet` |

*(Note: WebGL traces like `scatter3d`, `surface`, `mesh3d`, and `parcoords` render via GPU shader canvases and are not pure vector SVG).*

---

## License

MIT License. Copyright (c) 2026 Benjamin Lear.
