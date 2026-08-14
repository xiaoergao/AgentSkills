---
name: build-scottplot-wpf
description: Build and troubleshoot interactive ScottPlot 5 charts in WPF with correct high-DPI rendering, large signal data, mouse coordinate readout, wheel zoom, pan, custom double-click behavior, custom right-click menus, independent X/Y autoscaling, manual axis limits, and live-update range preservation. Use when implementing or fixing ScottPlot.WPF controls, especially when fonts shrink on high-DPI displays, benchmark text appears after double-click, axes snap back during live refresh, or single-axis autoscale changes both axes.
---

# Build ScottPlot WPF

Implement ScottPlot as an isolated WPF control. Preserve normal WPF styling, explicitly own axis state, and verify interactions against the pinned ScottPlot version.

## Workflow

1. Inspect the target framework, ScottPlot.WPF version, SkiaSharp dependency, update rate, maximum point count, and existing DPI behavior.
2. Pin package versions and use a Windows target framework compatible with their transitive dependencies.
3. Choose `Signal` for evenly spaced high-volume data. Convert invalid samples to `NaN` so the line breaks instead of inventing values.
4. Keep ScottPlot-specific DPI compensation inside the chart control. Do not change application-wide DPI or other WPF font sizes when they already render correctly.
5. Separate one-shot axis commands from continuous autoscale modes. Preserve the opposite axis explicitly for X-only and Y-only commands.
6. Preserve manual wheel, pan, and entered limits across data refreshes. Never call full `AutoScale()` unconditionally in every data update.
7. Replace default double-click and context-menu behavior before adding application gestures.
8. Validate at multiple DPI settings, with live updates and representative maximum-size data.

## Load the Right Reference

- Read [references/dpi-and-rendering.md](references/dpi-and-rendering.md) when setting up packages, rendering large signals, compensating ScottPlot canvas fonts, converting mouse coordinates, or troubleshooting WPF builds.
- Read [references/interaction-and-axes.md](references/interaction-and-axes.md) when implementing autoscale, wheel/pan persistence, double-click, crosshairs, context menus, or manual XY ranges.

## Required Design Rules

- Treat WPF text as device-independent units and ScottPlot canvas text as physical-pixel rendering that may require `DisplayScale` compensation.
- Multiply WPF mouse positions by `WpfPlot.DisplayScale` before calling `Plot.GetCoordinates()`.
- Call `UserInputProcessor.DoubleLeftClickBenchmark(false)` before assigning double-click to autoscale.
- Apply margins before autoscaling because margins configure the next autoscale operation.
- Add or hide crosshairs so they cannot distort automatic data limits.
- For an X-only operation, snapshot Y limits, autoscale X, then restore Y. Reverse this for Y-only.
- Disable continuous auto modes after wheel zoom, drag pan, one-shot adjustment, or manual limit entry unless the product explicitly requests otherwise.
- Key persisted manual ranges by chart identity, such as side plus live/captured role.
- Keep idle overlays hidden. Show coordinate readout only when the pointer resolves to a valid sample if a clean chart is desired.

## Verification Gate

Verify all of the following before handing off:

- Build succeeds with locked packages and zero new warnings.
- Axis labels remain readable at 100%, 125%, 150%, 200%, and the highest supported DPI.
- Double-click does not show benchmark, FPS, or refresh-rate text.
- X-only autoscale leaves Y minimum and maximum bit-for-bit unchanged; Y-only does the inverse.
- Wheel zoom and pan do not snap back on the next live-data update.
- Continuous X and Y modes can be toggled independently and their check marks match internal state.
- Manual limits reject non-finite values and `minimum >= maximum`, persist successfully, and reload for the correct chart.
- The largest expected signal renders and remains interactive without expanding into per-point WPF elements.
