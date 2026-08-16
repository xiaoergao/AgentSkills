# WPF UI font and DPI rules

Copy or merge this section into the target repository's `AGENTS.md`. It is a behavioral implementation rule, not a Codex command-permission `.rules` file.

## WPF UI font and DPI rules

- Treat WPF `FontSize`, `Margin`, `Padding`, `Width`, and `Height` as device-independent pixels. Never multiply ordinary WPF layout values by monitor DPI scale.
- Preserve a small semantic font hierarchy. Use shared styles or named resources for repeated roles; keep one-off values local.
- Default ordinary UI text to the platform WPF font. Use a verified CJK-capable family such as `Microsoft YaHei UI` when a renderer cannot provide reliable Chinese fallback.
- Reserve `Consolas` or another monospace font for measurements, coordinates, and code-like values, not body copy.
- Prefer `Auto`/`*` layout, wrapping, minimum sizes, and scrolling. Do not give localized text a fixed-height container that can clip at high DPI.
- Treat `UseLayoutRounding` and `SnapsToDevicePixels` as pixel-alignment tools, not font-scaling tools.
- Identify third-party canvas boundaries explicitly. Scale physical-pixel canvas fonts from an immutable base size using the control's current display scale; do not scale the surrounding WPF UI.
- Convert WPF logical pointer positions to physical pixels exactly once before passing them to a physical-pixel canvas API. Keep WPF overlays in logical coordinates and never rescale returned data coordinates.
- Reapply canvas typography after plot rebuilds and monitor-DPI transitions. Cache the last applied scale to avoid needless churn, and never multiply an already-scaled size.
- Do not change the application manifest or global DPI-awareness policy solely to repair an embedded canvas. Make that a separate reviewed change with full-window regression testing.
- Verify at 100%, 125%, 150%, and 200% scaling; move a live window across mixed-DPI monitors; check CJK glyphs, clipping, plot-label size, pointer alignment, and minimum-window usability.
- For the full workflow and ScottPlot 5 examples, use the `build-wpf-dpi-ui` Skill.
