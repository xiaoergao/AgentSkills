# DPI and Rendering

## Contents

- Package and target framework
- WPF build considerations
- Large signal rendering
- ScottPlot-only DPI compensation
- DPI-correct mouse coordinates
- Clean coordinate readout

## Package and target framework

Pin `ScottPlot.WPF` centrally and commit the lock file. Inspect the current NuGet dependency graph instead of assuming the latest package supports the project's existing Windows target.

The tested baseline was ScottPlot.WPF 5.1.59. Its SkiaSharp dependency required a Windows 10.0.19041-compatible application target in that environment:

```xml
<TargetFramework>net10.0-windows10.0.19041.0</TargetFramework>
<PackageReference Include="ScottPlot.WPF" />
```

Re-evaluate the minimum target whenever ScottPlot or SkiaSharp changes. Do not copy this target version blindly into older applications.

For a dependency property that receives arrays from a view model, prefer an interface type. This also avoids WPF markup-compiler edge cases around array-typed dependency properties:

```csharp
public static readonly DependencyProperty ValuesProperty = DependencyProperty.Register(
    nameof(Values),
    typeof(IReadOnlyList<double>),
    typeof(InteractiveWaveformPlot),
    new PropertyMetadata(Array.Empty<double>(), OnPlotDataChanged));
```

## WPF build considerations

WPF markup compilation creates a temporary project whose name is derived from the real project. If repository-wide build props place intermediate output under `$(MSBuildProjectName)`, make the acquisition project's WPF temporary project resolve to the same stable intermediate directory. Otherwise restore assets may appear to be missing only during XAML compilation.

Keep this workaround scoped to the affected WPF project prefix. Do not redirect all repository projects into one shared `obj` directory.

## Large signal rendering

Use a signal plot for evenly spaced measurements:

```csharp
double periodSeconds = sampleIntervalSeconds;
double[] values = source.Select(x => x.IsValid ? x.Value : double.NaN).ToArray();
var signal = wpfPlot.Plot.Add.Signal(values, periodSeconds);
signal.LineWidth = 1.5f;
```

Do not create a `Point`, WPF `Polyline`, marker, or visual element for every sample. A controller-sized capture can contain over one million points.

For a short live history, replacing a small array and rebuilding the signal is acceptable. For high-rate or long live streams, retain the plottable/data source where the pinned ScottPlot API permits it, throttle UI refreshes, and keep acquisition off the UI thread.

## ScottPlot-only DPI compensation

WPF font sizes are device-independent units. ScottPlot renders axis text into a Skia-backed physical-pixel canvas, so an unscaled tick font can look smaller as display scaling increases.

Compensate inside the ScottPlot control only:

```csharp
private const float BasePlotFontSize = 12f;
private double _lastDisplayScale = double.NaN;

private void ApplyPlotTypographyForDpi()
{
    double scale = Math.Clamp(PlotControl.DisplayScale, 1.0, 3.0);
    if (Math.Abs(scale - _lastDisplayScale) < 0.01)
        return;

    float size = BasePlotFontSize * (float)scale;
    PlotControl.Plot.Axes.Bottom.TickLabelStyle.FontSize = size;
    PlotControl.Plot.Axes.Left.TickLabelStyle.FontSize = size;
    PlotControl.Plot.Axes.Top.TickLabelStyle.FontSize = size;
    PlotControl.Plot.Axes.Right.TickLabelStyle.FontSize = size;
    _lastDisplayScale = scale;
}
```

Call this after the control loads and while rebuilding data so a move between monitors is eventually observed. Use a reasonable scale clamp to prevent pathological sizes.

Do not add an application manifest or change main-window font sizes merely to fix ScottPlot when other controls already scale correctly. WPF overlay labels placed above the chart should remain in logical units and should not receive this multiplication.

## DPI-correct mouse coordinates

`GetPosition()` returns WPF logical coordinates, while ScottPlot expects physical plot pixels. Convert before resolving data coordinates:

```csharp
Point p = e.GetPosition(PlotControl);
var pixel = new ScottPlot.Pixel(
    p.X * PlotControl.DisplayScale,
    p.Y * PlotControl.DisplayScale);
Coordinates coordinates = PlotControl.Plot.GetCoordinates(pixel);
```

For a signal with a fixed period, resolve the nearest sample rather than reporting an arbitrary mouse Y value:

```csharp
int index = (int)Math.Round(coordinates.X / periodSeconds,
    MidpointRounding.AwayFromZero);

if (index >= 0 && index < values.Length && double.IsFinite(values[index]))
{
    double x = index * periodSeconds;
    double y = values[index];
    crosshair.Position = new Coordinates(x, y);
}
```

## Clean coordinate readout

Keep the chart free of permanent instructional overlays when requested. Start the readout container collapsed, show it only for a valid nearest sample, and collapse it on mouse leave or an invalid sample. This preserves mouse inspection without permanently covering data.

Do not show placeholder strings such as “move mouse to inspect” or “no data” inside the plot unless the product explicitly asks for them.
