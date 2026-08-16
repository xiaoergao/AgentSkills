# Typography and layout baseline

This baseline was audited from the current `Lk.Acquisition.App` WPF UI in `PS5_Vibration` on 2026-08-16. It captures the working hierarchy; adapt names and values to the target product instead of forcing every interface to look identical.

## Audited font roles

| Role | Current value | Typical use |
| --- | --- | --- |
| Body and form text | Inherited WPF system font and default size | Labels, settings, descriptive text |
| Explicit CJK dialog text | `Microsoft YaHei UI`, 13 DIP | Compact dialogs and code-created context menus requiring stable Chinese glyphs |
| Action text | 14 DIP | Primary window buttons |
| Section heading | 17 DIP, `SemiBold` | Settings groups |
| Window heading | 24 DIP, `SemiBold` | Application or page heading |
| Card heading | 25 DIP, `SemiBold` | Controller or measurement-card title |
| Primary numeric readout | `Consolas`, 31 DIP, `SemiBold` | Live measurement values |
| Measurement unit | 14 DIP, `SemiBold` | Unit adjacent to a primary value |
| Compact coordinate overlay | `Consolas`, 11 DIP | Cursor coordinates on a plot |
| Canvas tick label | Base 12 physical pixels multiplied by canvas display scale | ScottPlot axes |
| Canvas title | 1.2 times the scaled canvas tick size | ScottPlot title |

The app does not currently define a global `FontFamily` or `FontSize` in `App.xaml`. Most ordinary controls therefore inherit WPF defaults. Preserve that distinction when documenting or refactoring the UI.

## Font-family policy

- Use the platform UI font for ordinary WPF text and controls unless product design requires a different family.
- Use `Microsoft YaHei UI` when an explicit Windows CJK UI font is needed. Confirm the target deployment includes it before making it mandatory.
- Use `Consolas` for short measurements, coordinates, and code-like values where column alignment matters.
- Do not use a monospace font for paragraphs, general labels, or long Chinese text.
- Set a canvas title's font explicitly when Chinese glyph fallback is unreliable. WPF fallback behavior does not guarantee equivalent fallback in Skia-backed renderers.

## Layout policy

- Treat every XAML dimension as a DIP.
- Prefer `Auto` for content-sized rows and columns and `*` for remaining space.
- Give interactive or graphical regions useful `MinWidth` and `MinHeight` values instead of fixing their final size.
- Put long settings pages in a vertical `ScrollViewer`.
- Allow explanatory text to wrap and avoid fixed-height containers around localized strings.
- Use padding and minimum height to size buttons; do not rely on a fixed height that can clip text.
- Use `UseLayoutRounding="True"` and `SnapsToDevicePixels="True"` selectively for crisp dialog and border alignment.
- Recheck the layout with long Chinese and English labels, not only placeholder text.

## Refactoring guidance

Centralize a value only when it represents a repeated semantic role. An implicit `Button` style may own shared action padding and size, while measurement values and coordinate overlays should have separate named styles. Avoid replacing a clear local one-off value with a large token system that the application does not otherwise need.

A lightweight resource dictionary may use role names such as:

```xml
<sys:Double x:Key="FontSize.Action">14</sys:Double>
<sys:Double x:Key="FontSize.SectionHeading">17</sys:Double>
<sys:Double x:Key="FontSize.WindowHeading">24</sys:Double>
<sys:Double x:Key="FontSize.CardHeading">25</sys:Double>
<sys:Double x:Key="FontSize.PrimaryMeasurement">31</sys:Double>
<sys:Double x:Key="FontSize.CoordinateOverlay">11</sys:Double>
```

Keep physical-pixel canvas sizes out of the WPF resource scale. Store them as renderer-specific constants in the owning control.
