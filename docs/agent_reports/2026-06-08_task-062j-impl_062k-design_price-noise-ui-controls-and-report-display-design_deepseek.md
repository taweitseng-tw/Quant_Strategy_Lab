Completed:
- Batch 062J-Impl + 062K-Design — Price-Noise UI Controls Implementation and Report Price-Noise Display Design.

Files changed:
- app/ui/main_window.py (Validate page controls + PipelineConfig wiring)
- tests/test_wfe_ui_wiring.py (4 new tests)
- docs/price_noise_report_display_design_062K.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. Validate page now has Price-Noise Stress controls (checkbox + 3 spinboxes), default-off.
2. _handle_run() wires price-noise config fields into PipelineConfig.
3. UI tests prove controls exist, toggle state, false/custom values.

Tests run:
- Pipeline tests: 40 passed.

Assumptions:
- UI controls are wired after bootstrap controls and before the validation summary widget.
- Spinboxes start disabled and enable when checkbox is checked.

Known risks:
- Price-noise with large iterations may be slow — default is 50.

Reviewer focus:
- Price-noise controls in Validate page (line ~410 in main_window.py).
- PipelineConfig wiring in _handle_run() — 4 new fields.
- 4 UI tests covering defaults, toggle, false, custom.
