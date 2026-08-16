# DPI boundaries for WPF and physical-pixel canvases

## Coordinate-space decision table

| Value or operation | Coordinate space | Apply display scale? |
| --- | --- | --- |
| WPF `FontSize`, margin, padding, width, height | Device-independent pixels | No |
| WPF overlay text or selection rectangle | Device-independent pixels | No |
| ScottPlot/Skia canvas font size | Physical render pixels | Yes, at the canvas boundary |
| `MouseEventArgs.GetPosition(...)` | WPF logical coordinates | Not while used in WPF |
| WPF pointer position passed to ScottPlot `Pixel` | Physical render pixels | Yes, once |
| Axis/data coordinates returned by the plot | Data space | No |

The key is not “scale everything on a high-DPI monitor.” The key is to identify the exact boundary where a device-independent WPF value enters an API that consumes physical pixels.

## ScottPlot 5 typography pattern

The audited application uses a 12-pixel canvas baseline, clamps `DisplayScale` to 1.0–3.0, and makes the title 1.2 times the tick size:

```csharp
private const float BasePlotFontSize = 12f;
private double _lastAppliedDisplayScale = double.NaN;

private void ApplyDpiAwarePlotTypography()
{
    double scale = Math.Clamp(PlotControl.DisplayScale, 1.0, 3.0);
    if (Math.Abs(scale - _lastAppliedDisplayScale) < 0.01)
        return;

    float tickSize = BasePlotFontSize * (float)scale;
    PlotControl.Plot.Axes.Bottom.TickLabelStyle.FontSize = tickSize;
    PlotControl.Plot.Axes.Left.TickLabelStyle.FontSize = tickSize;
    PlotControl.Plot.Axes.Top.TickLabelStyle.FontSize = tickSize;
    PlotControl.Plot.Axes.Right.TickLabelStyle.FontSize = tickSize;
    _lastAppliedDisplayScale = scale;
}

private void ApplyTitle(string title)
{
    float titleSize = BasePlotFontSize * 1.2f
        * (float)Math.Clamp(PlotControl.DisplayScale, 1.0, 3.0);
    PlotControl.Plot.Title(title, titleSize);
    PlotControl.Plot.Axes.Title.Label.FontName = "Microsoft YaHei UI";
}
```

Apply or reapply typography after the control has a valid display scale, after rebuilding the plot, and when the window crosses to a monitor with a different scale. Refresh once after the style changes. Cache the last scale when the code can be called repeatedly.

Do not multiply an already-scaled font on every update. Always derive the physical size from the immutable base size.

## Pointer conversion pattern

WPF reports logical pointer positions. ScottPlot's `Pixel` input addresses its physical render surface, so convert at the call site:

```csharp
Point position = e.GetPosition(PlotControl);
var pixel = new ScottPlot.Pixel(
    position.X * PlotControl.DisplayScale,
    position.Y * PlotControl.DisplayScale);
Coordinates coordinates = PlotControl.Plot.GetCoordinates(pixel);
```

Use the same conversion for hover readouts, wheel-zoom centers, crosshairs, box-selection endpoints, and any other WPF input sent to the plot. Centralize it in a helper when there is more than one call site.

Keep WPF selection rectangles and coordinate labels in their original logical coordinates. They are rendered by WPF and will be scaled by WPF itself.

## Failure signatures

| Symptom | Likely cause |
| --- | --- |
| Standard WPF controls are oversized | WPF DIPs were multiplied by scale manually |
| Plot labels shrink relative to buttons at 150–200% | Physical-pixel canvas fonts were not scaled |
| Plot labels grow after every update | The current size was multiplied repeatedly instead of using a base constant |
| Hover or zoom center is offset on high DPI | Logical pointer coordinates were passed to a physical-pixel API |
| WPF overlay is offset or too large | The overlay was converted to physical pixels even though WPF renders it |
| Chinese plot title shows boxes | Canvas font fallback did not find a CJK typeface |
| Appearance changes only after reopening a window | Canvas typography was not reapplied after monitor/DPI transition |

## Verification matrix

At minimum, verify:

1. 100%, 125%, 150%, and 200% display scaling.
2. A live window moved between two monitors with different scale factors.
3. English and Chinese titles, axis labels, settings, and long wrapped text.
4. Hover coordinates, wheel-zoom center, crosshair, and box-selection alignment.
5. Main, settings, modal, detached-detail, and context-menu surfaces.
6. Minimum supported window size and a smaller display where scrolling is required.
7. Repeated plot rebuilds and live updates, ensuring font size does not accumulate scale.
