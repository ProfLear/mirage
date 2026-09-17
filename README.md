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

## Performance Benchmarks across 26 Chart Types

Below is an empirical benchmark comparing **Mirage** against **Kaleido** across 26 standard Plotly chart types (tested on Apple Silicon, measuring average per-image export latency after engine warmup):

| Category | Chart Type | Mirage Latency | Kaleido Latency | Speedup |
| :--- | :--- | :---: | :---: | :---: |
| **Core Cartesian** | Scatter & Line Chart | **59.9 ms** | 1529.3 ms | **25.5x** |
| **Core Cartesian** | Grouped Bar Chart | **47.5 ms** | 1636.6 ms | **34.5x** |
| **Core Cartesian** | Donut / Pie Chart | **49.3 ms** | 1550.5 ms | **31.5x** |
| **Core Cartesian** | Box Plot | **55.6 ms** | 1549.4 ms | **27.9x** |
| **Core Cartesian** | Violin Plot | **54.6 ms** | 1558.5 ms | **28.5x** |
| **Core Cartesian** | Frequency Histogram | **38.0 ms** | 1586.0 ms | **41.8x** |
| **Core Cartesian** | 2D Density Histogram | **58.3 ms** | 1594.5 ms | **27.4x** |
| **Core Cartesian** | 2D Contour Plot | **74.3 ms** | 1571.6 ms | **21.1x** |
| **Core Cartesian** | Performance Heatmap | **52.3 ms** | 1618.8 ms | **30.9x** |
| **Core Cartesian** | Ternary Phase Diagram | **54.3 ms** | 1543.0 ms | **28.4x** |
| **Financial & Business** | Candlestick Stock Chart | **70.9 ms** | 1528.7 ms | **21.6x** |
| **Financial & Business** | OHLC Financial Chart | **69.3 ms** | 1574.0 ms | **22.7x** |
| **Financial & Business** | Waterfall Profit & Loss | **45.0 ms** | 1525.3 ms | **33.9x** |
| **Financial & Business** | Sales Conversion Funnel | **40.6 ms** | 1536.6 ms | **37.9x** |
| **Financial & Business** | Funnel Area Analysis | **41.1 ms** | 1551.5 ms | **37.8x** |
| **Financial & Business** | KPI Performance Indicator | **39.3 ms** | 1558.2 ms | **39.7x** |
| **Hierarchical** | Market Cap Treemap | **34.4 ms** | 1528.6 ms | **44.4x** |
| **Hierarchical** | Global Sunburst Hierarchy | **39.2 ms** | 1525.7 ms | **38.9x** |
| **Hierarchical** | Icicle Partition Chart | **31.1 ms** | 1536.1 ms | **49.4x** |
| **Radial & Polar** | Radar Performance Comparison | **58.9 ms** | 1538.4 ms | **26.1x** |
| **Radial & Polar** | Polar Wind Rose | **46.9 ms** | 1535.5 ms | **32.7x** |
| **Specialized Diagrams** | Energy Flow Sankey Diagram | **32.4 ms** | 1571.4 ms | **48.5x** |
| **Specialized Diagrams** | Parallel Categories Diagram | **42.9 ms** | 1576.3 ms | **36.7x** |
| **Specialized Diagrams** | Parallel Coordinates Diagram | **40.9 ms** | 2689.3 ms | **65.7x** |
| **Specialized Diagrams** | Formatted Data Table | **43.9 ms** | 1600.3 ms | **36.5x** |
| **Specialized Diagrams** | Carpet Coordinate Plot | **49.9 ms** | 1552.9 ms | **31.1x** |

> **Overall Summary**: Mirage delivers a **21x to 65x speedup** across all chart types while using **~25x less disk space** and requiring **zero browser processes**.

---

## Visual Fidelity & Side-by-Side Comparisons

Every plot exported by Mirage matches the exact visual output, layout geometry, font proportions, and colors generated by Plotly and Kaleido.

### Core Cartesian

#### Scatter & Line Chart (Mirage: 59.9ms | Kaleido: 1529.3ms)

![Scatter & Line Chart](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_scatter_line.png)

#### Grouped Bar Chart (Mirage: 47.5ms | Kaleido: 1636.6ms)

![Grouped Bar Chart](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_bar.png)

#### Donut / Pie Chart (Mirage: 49.3ms | Kaleido: 1550.5ms)

![Donut / Pie Chart](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_pie.png)

#### Box Plot (Mirage: 55.6ms | Kaleido: 1549.4ms)

![Box Plot](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_box.png)

#### Violin Plot (Mirage: 54.6ms | Kaleido: 1558.5ms)

![Violin Plot](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_violin.png)

#### Frequency Histogram (Mirage: 38.0ms | Kaleido: 1586.0ms)

![Frequency Histogram](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_histogram.png)

#### 2D Density Histogram (Mirage: 58.3ms | Kaleido: 1594.5ms)

![2D Density Histogram](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_histogram2d.png)

#### 2D Contour Plot (Mirage: 74.3ms | Kaleido: 1571.6ms)

![2D Contour Plot](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_contour.png)

#### Performance Heatmap (Mirage: 52.3ms | Kaleido: 1618.8ms)

![Performance Heatmap](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_heatmap.png)

#### Ternary Phase Diagram (Mirage: 54.3ms | Kaleido: 1543.0ms)

![Ternary Phase Diagram](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_scatterternary.png)

### Financial & Business

#### Candlestick Stock Chart (Mirage: 70.9ms | Kaleido: 1528.7ms)

![Candlestick Stock Chart](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_candlestick.png)

#### OHLC Financial Chart (Mirage: 69.3ms | Kaleido: 1574.0ms)

![OHLC Financial Chart](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_ohlc.png)

#### Waterfall Profit & Loss (Mirage: 45.0ms | Kaleido: 1525.3ms)

![Waterfall Profit & Loss](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_waterfall.png)

#### Sales Conversion Funnel (Mirage: 40.6ms | Kaleido: 1536.6ms)

![Sales Conversion Funnel](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_funnel.png)

#### Funnel Area Analysis (Mirage: 41.1ms | Kaleido: 1551.5ms)

![Funnel Area Analysis](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_funnelarea.png)

#### KPI Performance Indicator (Mirage: 39.3ms | Kaleido: 1558.2ms)

![KPI Performance Indicator](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_indicator.png)

### Hierarchical

#### Market Cap Treemap (Mirage: 34.4ms | Kaleido: 1528.6ms)

![Market Cap Treemap](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_treemap.png)

#### Global Sunburst Hierarchy (Mirage: 39.2ms | Kaleido: 1525.7ms)

![Global Sunburst Hierarchy](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_sunburst.png)

#### Icicle Partition Chart (Mirage: 31.1ms | Kaleido: 1536.1ms)

![Icicle Partition Chart](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_icicle.png)

### Radial & Polar

#### Radar Performance Comparison (Mirage: 58.9ms | Kaleido: 1538.4ms)

![Radar Performance Comparison](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_scatterpolar.png)

#### Polar Wind Rose (Mirage: 46.9ms | Kaleido: 1535.5ms)

![Polar Wind Rose](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_barpolar.png)

### Specialized Diagrams

#### Energy Flow Sankey Diagram (Mirage: 32.4ms | Kaleido: 1571.4ms)

![Energy Flow Sankey Diagram](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_sankey.png)

#### Parallel Categories Diagram (Mirage: 42.9ms | Kaleido: 1576.3ms)

![Parallel Categories Diagram](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_parcats.png)

#### Parallel Coordinates Diagram (Mirage: 40.9ms | Kaleido: 2689.3ms)

![Parallel Coordinates Diagram](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_parcoords.png)

#### Formatted Data Table (Mirage: 43.9ms | Kaleido: 1600.3ms)

![Formatted Data Table](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_table.png)

#### Carpet Coordinate Plot (Mirage: 49.9ms | Kaleido: 1552.9ms)

![Carpet Coordinate Plot](https://raw.githubusercontent.com/ProfLear/mirage/main/assets/benchmarks/compare_carpet.png)

---

## Supported Plotly Traces (29 Total)

Mirage includes full pure-vector support for all 29 non-3D Plotly trace types:

| Category | Supported Traces |
| :--- | :--- |
| **Core Cartesian** | `scatter` (lines, markers, area, text, ecdf), `bar` (vertical, horizontal, stacked, grouped, timeline), `pie` (donut), `box`, `violin`, `histogram`, `histogram2d`, `histogram2dcontour`, `contour`, `heatmap`, `scatterternary`, `image` |
| **Financial & Business** | `candlestick`, `ohlc`, `waterfall`, `funnel`, `funnelarea`, `indicator` (gauges, KPI big numbers) |
| **Hierarchical Partitions** | `treemap`, `sunburst`, `icicle` |
| **Radial / Polar** | `scatterpolar` (radar/spider), `barpolar` |
| **Specialized Diagrams & Tables** | `sankey`, `parcats`, `parcoords`, `table`, `carpet`, `scattercarpet`, `contourcarpet` |

*(Note: 3D WebGL plots like `scatter3d`, `surface`, and `mesh3d` are excluded because their GL math shaders exceed the stack capacity of embedded QuickJS without a GPU).*

---

## License

MIT License. Copyright (c) 2026 Benjamin Lear.
