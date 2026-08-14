# Interaction and Axes

## Contents

- Own axis state
- Preserve limits during data refresh
- Strict single-axis autoscale
- Continuous autoscale modes
- Double-click and benchmark behavior
- Custom right-click menu
- Manual ranges and persistence
- Interaction test matrix

## Own axis state

Maintain explicit state in the chart control:

```csharp
private bool _hasAxisLimits;
private bool _automaticX = true;
private bool _automaticY = true;
```

Distinguish these operations:

- One-shot X autoscale
- One-shot Y autoscale
- One-shot full-curve autoscale
- Continuous X autoscale on new data
- Continuous Y autoscale on new data
- Manual limits

Do not use one boolean for all six behaviors.

## Preserve limits during data refresh

An unconditional `Axes.AutoScale()` after every `Plot.Clear()` causes wheel zoom, pan, and manual limits to snap back on the next live update.

Snapshot limits before rebuilding, add the data, then apply each axis policy independently:

```csharp
AxisLimits? previous = _hasAxisLimits
    ? PlotControl.Plot.Axes.GetLimits()
    : null;

PlotControl.Plot.Clear();
PlotControl.Plot.Add.Signal(values, periodSeconds);
PlotControl.Plot.Axes.Margins(0.03, 0.10);

if (!_hasAxisLimits || _automaticX)
    PlotControl.Plot.Axes.AutoScaleX();
else if (previous.HasValue)
    PlotControl.Plot.Axes.SetLimitsX(previous.Value.Left, previous.Value.Right);

if (!_hasAxisLimits || _automaticY)
    PlotControl.Plot.Axes.AutoScaleY();
else if (previous.HasValue)
    PlotControl.Plot.Axes.SetLimitsY(previous.Value.Bottom, previous.Value.Top);

_hasAxisLimits = values.Length > 0 || previous.HasValue;
```

Configure `Margins`, `MarginsX`, or `MarginsY` before the matching autoscale call. Adding margins afterward configures future autoscaling but does not reliably change limits already calculated.

Add the crosshair after autoscale, or hide it while calculating limits, so an interaction plottable cannot influence the data range.

## Strict single-axis autoscale

Even if the library exposes `AutoScaleX()` and `AutoScaleY()`, explicitly restore the opposite axis. This protects behavior from continuous modes, plottable rules, and future library changes.

```csharp
private void AutoScaleXOnly()
{
    AxisLimits old = PlotControl.Plot.Axes.GetLimits();
    PlotControl.Plot.Axes.MarginsX(0.03);
    PlotControl.Plot.Axes.AutoScaleX();
    PlotControl.Plot.Axes.SetLimitsY(old.Bottom, old.Top);
    PlotControl.Refresh();
}

private void AutoScaleYOnly()
{
    AxisLimits old = PlotControl.Plot.Axes.GetLimits();
    PlotControl.Plot.Axes.MarginsY(0.10);
    PlotControl.Plot.Axes.AutoScaleY();
    PlotControl.Plot.Axes.SetLimitsX(old.Left, old.Right);
    PlotControl.Refresh();
}
```

When a user invokes a one-shot axis command, disable continuous X and Y modes first unless the product explicitly defines otherwise. This prevents the next live frame from visually turning a single-axis command into a full autoscale.

## Continuous autoscale modes

Represent continuous X and Y with independent checkable menu items. Synchronize `IsChecked` from internal state whenever the menu opens.

When enabling automatic X, perform an immediate X-only autoscale. Preserve Y. Do the inverse for automatic Y. During each data rebuild, autoscale only the axes whose modes remain enabled.

Disable continuous modes after:

- mouse wheel zoom;
- a detected drag pan, not merely a single click;
- one-shot autoscale;
- accepted manual XY limits.

Detect drag using `SystemParameters.MinimumHorizontalDragDistance` and `MinimumVerticalDragDistance` so clicking to inspect a point does not unexpectedly disable autoscale.

## Double-click and benchmark behavior

ScottPlot 5 uses double-left-click to toggle benchmark/performance text by default. Disable it before handling the gesture:

```csharp
PlotControl.UserInputProcessor.DoubleLeftClickBenchmark(false);
PlotControl.PreviewMouseDoubleClick += (_, e) =>
{
    if (e.ChangedButton != MouseButton.Left)
        return;

    DisableContinuousAutoScale();
    PlotControl.Plot.Axes.Margins(0.03, 0.10);
    PlotControl.Plot.Axes.AutoScale();
    PlotControl.Refresh();
    e.Handled = true;
};
```

Use a preview handler so application behavior wins before child controls process the routed event. Verify the lower-left benchmark/FPS text never appears.

## Custom right-click menu

Create a WPF `ContextMenu` owned by the wrapper control with these common actions:

1. Autoscale X once
2. Autoscale Y once
3. Autoscale the full curve once
4. Toggle continuous X autoscale
5. Toggle continuous Y autoscale
6. Enter manual XY limits

Intercept `PreviewMouseRightButtonDown` and `PreviewMouseRightButtonUp`, mark both handled, and open the custom menu at `PlacementMode.MousePoint`. This suppresses ScottPlot's built-in menu without disabling wheel or left-drag interactivity.

If the pinned ScottPlot version still displays both menus, inspect its public `UserInputProcessor` response collection and remove only the context-menu response supported by that version. Do not clear all responses because that also removes pan and wheel zoom.

## Manual ranges and persistence

Accept four finite numbers and require:

```text
X minimum < X maximum
Y minimum < Y maximum
```

Default the dialog to the most recently saved range for that chart. Fall back to the current rendered limits if no saved range exists.

Key storage by semantic chart identity, for example:

```text
Left.Live
Left.Captured
Right.Live
Right.Captured
```

Write settings atomically using a partial file, flush, then replace/move. After the user accepts the dialog, disable continuous autoscale, call `SetLimitsX()` and `SetLimitsY()`, refresh, and persist the range.

Treat a missing, unknown-schema, or malformed settings file as “no saved range” rather than crashing the chart.

## Interaction test matrix

Run these checks with live data still updating:

| Action | Expected X | Expected Y | Continuous modes |
|---|---|---|---|
| Wheel zoom | Changes | Changes or axis-under-mouse | Off |
| Drag pan | Changes | Changes | Off |
| Autoscale X once | Fits data | Exactly unchanged | Off |
| Autoscale Y once | Exactly unchanged | Fits data | Off |
| Autoscale curve once | Fits data | Fits data | Off |
| Enable auto X | Follows new data | Preserved/manual | X on, Y unchanged |
| Enable auto Y | Preserved/manual | Follows new data | Y on, X unchanged |
| Enter manual XY | Entered limits | Entered limits | Off |
| Double-click | Fits data | Fits data | Off |

Record numeric limits before and after X-only and Y-only operations; do not rely only on visual inspection.
