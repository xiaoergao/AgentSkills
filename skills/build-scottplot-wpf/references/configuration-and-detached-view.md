# Configuration and Detached View

## Contents

- Per-chart configuration model
- Atomic persistence and live binding
- Modifier-specific wheel zoom
- Configurable titles and CJK fonts
- Detached snapshot window
- Box zoom and selection statistics
- Configuration verification matrix

## Per-chart configuration model

Give every chart a stable semantic key such as `Left.Live`, `Left.Captured`, `Right.Live`, or `Right.Captured`. Do not share a mutable global configuration object across charts.

Persist at least:

```text
XMinimum, XMaximum, YMinimum, YMaximum
AutomaticX, AutomaticY
Wheel, CtrlWheel, ShiftWheel, AltWheel
ShowTitle, Title
EnableDetachedView
```

Represent wheel behavior with a closed enum: `Disabled`, `ZoomXY`, `ZoomX`, `ZoomY`. Reject undefined enum values, non-finite limits, `XMinimum >= XMaximum`, `YMinimum >= YMaximum`, null titles, and unreasonable title lengths.

Use safe defaults that preserve existing behavior. A practical default is direct wheel = XY, Ctrl = X, Shift = Y, Alt = disabled, automatic X/Y enabled, title hidden, and detached view enabled.

## Atomic persistence and live binding

Keep chart settings separate from device/acquisition settings when saving a chart must not rewrite hardware parameters. Store a versioned dictionary keyed by chart identity.

Write atomically:

1. validate every configuration;
2. serialize to `*.partial` in the target directory;
3. flush asynchronously and call `Flush(flushToDisk: true)`;
4. replace/move the partial file over the target;
5. delete the partial file on failure.

Treat missing, malformed, unknown-schema, and invalid individual entries as defaults rather than crashing chart construction.

Bind each chart control to an observable settings object. Suppress configuration callbacks while synchronizing limits from interactions to prevent a wheel event from recursively rebuilding the plot. If a user temporarily enters `minimum >= maximum`, retain the last valid rendered limits and reject the configuration on save.

## Modifier-specific wheel zoom

ScottPlot's default wheel response will conflict with product-defined mappings. Remove only that response:

```csharp
using ScottPlot.Interactivity.UserActionResponses;

PlotControl.UserInputProcessor.RemoveAll<MouseWheelZoom>();
PlotControl.PreviewMouseWheel += Plot_PreviewMouseWheel;
```

Always mark the preview event handled, including the disabled case. Resolve the exact modifier state to the configured action. Define a deterministic policy for multiple modifiers; disabling ambiguous combinations is a safe default.

Zoom around the pointer:

```csharp
Point p = e.GetPosition(PlotControl);
var pixel = new Pixel(p.X * PlotControl.DisplayScale,
                      p.Y * PlotControl.DisplayScale);
Coordinates center = PlotControl.Plot.GetCoordinates(pixel);
AxisLimits limits = PlotControl.Plot.Axes.GetLimits();
double factor = e.Delta > 0 ? 0.80 : 1.25;

double xMin = center.X + (limits.Left - center.X) * factor;
double xMax = center.X + (limits.Right - center.X) * factor;
```

Apply X only, Y only, or both according to the mapping. Turn off continuous autoscale only for axes changed by the wheel, synchronize the resulting valid limits to the settings object, then refresh once.

## Configurable titles and CJK fonts

Set or hide the title explicitly on every rebuild:

```csharp
if (settings.ShowTitle && !string.IsNullOrWhiteSpace(settings.Title))
{
    PlotControl.Plot.Title(settings.Title.Trim(), dpiAwareTitleSize);
    PlotControl.Plot.Axes.Title.Label.FontName = "Microsoft YaHei UI";
}
else
{
    PlotControl.Plot.Title(false);
}
```

ScottPlot renders text through its canvas font resolver, not WPF font fallback. Square/tofu glyphs usually indicate an unsupported ScottPlot font, not corrupt UTF-8. Choose an installed font that covers the configured script, or call `Label.SetBestFont()` where the pinned version supports and reliably resolves it. Apply DPI compensation to the title size inside the plot only.

Use the same title policy in embedded and detached charts.

## Detached snapshot window

Expose an `Open in detached window` menu item only when enabled for that chart and data exists. Pass a copied value array, sample period, and immutable configuration snapshot. A snapshot prevents live-window scrolling from changing a selected analysis interval.

Useful detached operations:

- normal left-drag pan;
- configured wheel zoom;
- double-click and button full autoscale;
- restore saved configured limits;
- box zoom;
- X-interval selection statistics;
- copy statistics.

Keep selection as an explicit mode. Disable ScottPlot left-drag pan while box selection is active, draw a WPF `Canvas`/`Border` overlay, capture the mouse on selection start, and restore pan when the selection completes or is cancelled.

Convert both rectangle endpoints with `DisplayScale` before applying coordinate limits. Require non-trivial X/Y extent for box zoom. For interval statistics, X extent is authoritative; Y height may remain visual only if the UI says so.

## Box zoom and selection statistics

For an evenly sampled signal, map the selected X interval to inclusive indexes with `Ceiling(start / period)` and `Floor(end / period)`, then clamp to the array.

Exclude `NaN` and infinities. Report enough context to audit the result:

```text
start/end index
valid sample count
start/end time and duration
minimum, maximum, peak-to-peak
mean, RMS, standard deviation
```

State whether standard deviation is population or sample. Do not silently treat invalid points as zero.

## Configuration verification matrix

Verify every semantic chart key independently:

| Check | Expected |
|---|---|
| Save/restart | The same chart reloads all settings |
| Switch chart in config UI | Values change to that chart's profile |
| Direct/Ctrl/Shift/Alt wheel | Each follows its own configured mode |
| X-only wheel | Y limits and auto-Y remain unchanged |
| Y-only wheel | X limits and auto-X remain unchanged |
| Disabled wheel | Neither axis changes and default ScottPlot zoom does not run |
| Restore explicit range | Last manually saved range wins and survives refresh |
| Restore fallback range | Fixed profile limits apply when no explicit range exists |
| Live refresh under stationary pointer | Coordinate overlay remains visible without flashing |
| Chinese title | Embedded and detached title glyphs render correctly |
| Detached snapshot | Main live refresh does not move the selected data |
| Box zoom | Limits match the rectangle in DPI-correct coordinates |
| Box statistics | Invalid points are excluded and indexes/times are correct |
