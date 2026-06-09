Completed:
- Batch 062N-Impl — Price-Noise Widget Display Implementation.

Files changed:
- app/widgets/validation_summary.py (price_noise detail sub-lines)
- tests/test_validation_summary.py (3 new tests)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. ValidationSummary now shows price_noise detail sub-lines when stress_results contains test_name="price_noise".
2. Detail lines show: Noise %, Iterations, Method, Research only flag.
3. Warnings are displayed after the detail line.
4. 3 widget tests: shown when opt-in, omitted by default, warnings displayed.

Tests run:
- Widget tests: 34 passed.

Assumptions:
- Price-noise stress result includes "assumptions" dict with noise_pct, iterations, method.
- research_only flag defaults to True in display code.

Known risks:
- None within widget-only scope.

Reviewer focus:
- price_noise detail block in validation_summary.py stress section.
- 3 widget tests covering in/out states and warnings.
