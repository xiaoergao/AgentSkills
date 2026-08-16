---
name: build-wpf-dpi-ui
description: Build, audit, and troubleshoot readable high-DPI WPF interfaces with a consistent font hierarchy, CJK-safe typography, device-independent layout, and correct WPF-to-physical-pixel boundaries for ScottPlot or other Skia/canvas controls. Use for XAML font sizes and styles, dense engineering dashboards, numeric readouts, dialogs, per-monitor DPI behavior, blurry or shrinking text, double-scaled controls, clipped layouts, and pointer-to-canvas coordinate mismatches.
---

# Build WPF DPI UI

## Overview

Use this skill to keep a WPF application's typography and layout readable across monitor scales without double-scaling the standard WPF UI. Treat embedded physical-pixel canvases as explicit DPI boundaries and compensate only at those boundaries.

## Workflow

1. Inventory the current UI before changing it.
   - Search XAML, styles, themes, and code-created controls for `FontSize`, `FontFamily`, `FontWeight`, fixed dimensions, `UseLayoutRounding`, and `SnapsToDevicePixels`.
   - Search canvas or plotting code for `DisplayScale`, `DpiScale`, pixel conversion, title styles, tick styles, and pointer coordinate conversion.
   - Record implicit defaults separately from explicit values. Do not claim an application-wide font token exists when controls merely inherit the WPF default.
2. Classify each visual element.
   - Standard WPF control or WPF overlay: keep sizes in device-independent pixels (DIPs).
   - Physical-pixel canvas text: scale the canvas font at the rendering boundary.
   - WPF pointer position passed to a physical-pixel API: convert logical coordinates to physical pixels exactly once.
3. Preserve or introduce a small role-based type scale.
   - Start with the audited baseline in [references/typography-and-layout.md](references/typography-and-layout.md).
   - Prefer shared styles or resource tokens when several controls use the same role.
   - Keep body text on the platform font unless the product has an explicit typeface policy.
4. Make the layout tolerate text growth.
   - Prefer `Auto` and `*` rows/columns, wrapping, minimum sizes, and scrolling over fixed text-bearing heights.
   - Use minimum window sizes to protect essential controls, but verify that smaller screens remain usable.
5. Implement canvas DPI compensation.
   - Read [references/dpi-boundaries.md](references/dpi-boundaries.md) before changing ScottPlot, SkiaSharp, Direct2D, bitmap, or custom drawing code.
   - Keep the compensation local to the canvas control. Do not multiply every WPF `FontSize`, margin, or dimension by monitor scale.
6. Validate at realistic scale factors and monitor transitions.
   - Test at 100%, 125%, 150%, and 200%, plus the highest supported scale.
   - Move a live window between monitors when per-monitor behavior matters.
   - Check text hierarchy, clipping, CJK glyphs, canvas labels, pointer alignment, and minimum-window usability.

## Non-negotiable boundaries

- WPF `FontSize`, `Margin`, `Padding`, `Width`, and `Height` are DIPs. Do not manually multiply them by DPI scale.
- `UseLayoutRounding` and `SnapsToDevicePixels` improve edge alignment; they are not font-scaling mechanisms.
- Scale only a renderer that consumes physical pixels. Cache the applied scale when repeated updates would churn layout or rendering.
- Convert WPF pointer coordinates to physical pixels before calling a physical-pixel canvas API. Do not scale resulting data coordinates again.
- Keep WPF overlays in DIPs even when they sit above a scaled canvas.
- Use an explicit installed CJK-capable font for canvas-rendered Chinese text because canvas font fallback can differ from WPF fallback.
- Do not change an application manifest or global DPI-awareness policy merely to fix one embedded canvas. Treat that as a separate application-level decision and regression-test all windows.

## Deliverables

When applying this skill, leave behind:

- a short inventory of the existing font roles and DPI boundaries;
- centralized styles or clearly named constants for repeated font roles;
- local canvas scaling and coordinate conversion where required;
- a verification note listing tested scale factors and monitor transitions;
- no unrelated visual redesign unless the user requested one.
