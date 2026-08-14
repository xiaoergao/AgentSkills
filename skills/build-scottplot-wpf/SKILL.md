---
name: build-scottplot-wpf
description: Build and troubleshoot configurable interactive ScottPlot 5 charts in WPF with correct high-DPI rendering, large signal data, per-chart axis and title settings, modifier-specific wheel zoom, mouse coordinate readout, pan, custom double-click and right-click behavior, detached snapshot windows, box zoom/statistics, independent X/Y autoscaling, manual limits, and live-update range preservation. Use when implementing or fixing ScottPlot.WPF controls, chart configuration pages, Chinese chart titles, detached waveform inspection, or interaction bugs such as shrinking DPI fonts, benchmark text, flickering hover values, snapping axes, or single-axis autoscale changing both axes.
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
7. Model every chart's range, autoscale, wheel gestures, title, and detached-view permission independently; key persistence by semantic chart identity.
8. Remove ScottPlot's default wheel response when product-configurable modifier mappings are required, then own the preview wheel event completely.
9. Replace default double-click and context-menu behavior before adding application gestures.
10. Use a stable snapshot for detached analysis windows unless the product explicitly requires a synchronized live clone.
11. Validate at multiple DPI settings, with live updates and representative maximum-size data.

## Load the Right Reference

- Read [references/dpi-and-rendering.md](references/dpi-and-rendering.md) when setting up packages, rendering large signals, compensating ScottPlot canvas fonts, converting mouse coordinates, or troubleshooting WPF builds.
- Read [references/interaction-and-axes.md](references/interaction-and-axes.md) when implementing autoscale, wheel/pan persistence, double-click, crosshairs, context menus, or manual XY ranges.
- Read [references/configuration-and-detached-view.md](references/configuration-and-detached-view.md) when building per-chart configuration UI, modifier-specific wheel behavior, configurable/Chinese titles, detached windows, box zoom, or selection statistics.

## Required Design Rules

- Treat WPF text as device-independent units and ScottPlot canvas text as physical-pixel rendering that may require `DisplayScale` compensation.
- Multiply WPF mouse positions by `WpfPlot.DisplayScale` before calling `Plot.GetCoordinates()`.
- Call `UserInputProcessor.DoubleLeftClickBenchmark(false)` before assigning double-click to autoscale.
- Apply margins before autoscaling because margins configure the next autoscale operation.
- Add or hide crosshairs so they cannot distort automatic data limits.
- For an X-only operation, snapshot Y limits, autoscale X, then restore Y. Reverse this for Y-only.
- Disable continuous auto modes after wheel zoom, drag pan, one-shot adjustment, or manual limit entry unless the product explicitly requests otherwise.
- Key persisted manual ranges by chart identity, such as side plus live/captured role.
- Persist the full configuration for each chart, not one global chart profile. Validate finite ordered limits and defined interaction enums before saving.
- When implementing configurable wheel gestures, remove only `MouseWheelZoom`, mark `PreviewMouseWheel` handled, and apply the selected axis policy around the pointer.
- Explicitly choose a title font that covers the configured character set. For Chinese ScottPlot titles on Windows, set `Plot.Axes.Title.Label.FontName` to an installed CJK font after setting title text.
- Keep detached analysis deterministic: copy the values and sample period at open time, disable pan while box selection is active, and ignore non-finite samples in statistics.
- Keep idle overlays hidden. Show coordinate readout only when the pointer resolves to a valid sample if a clean chart is desired.
- During live rebuilds, retain the last pointer position and recompute the readout before the single refresh instead of hiding and re-showing it every frame.

## Verification Gate

Verify all of the following before handing off:

- Build succeeds with locked packages and zero new warnings.
- Axis labels remain readable at 100%, 125%, 150%, 200%, and the highest supported DPI.
- Double-click does not show benchmark, FPS, or refresh-rate text.
- X-only autoscale leaves Y minimum and maximum bit-for-bit unchanged; Y-only does the inverse.
- Wheel zoom and pan do not snap back on the next live-data update.
- Continuous X and Y modes can be toggled independently and their check marks match internal state.
- Manual limits reject non-finite values and `minimum >= maximum`, persist successfully, and reload for the correct chart.
- Each chart reloads its own axis, autoscale, wheel, title, and detached-view settings without leaking settings to another chart.
- Direct, Ctrl, Shift, and Alt wheel actions match their configured Disabled/XY/X/Y modes; ambiguous multi-modifier input has a documented deterministic rule.
- Non-Latin titles render as glyphs rather than tofu boxes in both embedded and detached charts.
- Detached box zoom maps WPF pixels through `DisplayScale`; box statistics report the intended X interval and exclude invalid samples.
- The largest expected signal renders and remains interactive without expanding into per-point WPF elements.
