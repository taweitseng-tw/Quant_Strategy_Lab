# Next Engineering Task Candidate Brief ??Task 064J

> Decision brief only. No production code changed.
> Generated: 2026-06-09

## Context

The 064-series documentation hygiene (064C??64I) is substantially complete:
- Context brief refreshed
- Task board deduplicated
- Untracked file hygiene inventoried
- `.codegraph/` ignored
- `docs/archive/` policy decided
- Artifact staging plan documented
- Post-063D/063E/063F acceptance smoke recorded

The next step should produce **real engineering progress**, not another documentation-only loop.

---

## Candidate 1: Data Workflow Polish / Import UX Hardening

### Scope
Improve the first-time user experience for importing OHLCV data. Current pain points documented in PRD and user feedback: no import wizard, limited format feedback, session filter UX is basic.

### Context level
Level 2 ??service layer + UI wiring changes.

### Why now
- Data import is the user's first interaction with the platform ??polish here has outsized UX impact.
- The stale "13 DataService failures" claim has been retired; focused data workflow tests (17/17) pass.
- The existing data pipeline (import ??normalize ??resample) is complete at the engine level but the UX around it is bare.
- No dependency on remaining 064-series hygiene decisions ??can proceed immediately.

### Files likely involved
- `app/ui/main_window.py` ??Data page imports, import wizard wiring
- `app/services/data_service.py` ??import flow hardening
- `data_engine/` ??read-only contract reference only; no engine changes in the first batch
- `tests/test_data_page_wiring.py`, `tests/test_dataset_persistence_wiring.py` ??new test coverage
- `docs/task_board.md`, `docs/changelog.md` ??task tracking

### Risks
- Scope creep into a full "import wizard" could balloon. Must constrain to small UX wins (format feedback, error messages, session filter defaults).
- Data format detection is heuristic ??may need careful edge case handling.

### Verification commands
```
.venv/Scripts/python.exe -m pytest tests/test_data_page_wiring.py tests/test_dataset_persistence_wiring.py tests/test_project_service.py -q
git diff --check
```

### Acceptance criteria
1. Data import UX shows clear format expectations before import.
2. Import error messages include actionable guidance (not raw exceptions).
3. Session filter defaults are more usable (pre-fill common session templates).
4. No regression in existing data workflow tests (17/17 pass).
5. No backend engine changes ??UI/service layer only.

---

## Candidate 2: Strategy Quality / Robustness Expansion

### Scope
Add remaining PRD §12 validation features and robustness improvements: improved elimination rule configuration, fitness multi-metric weighting, and strategy explainability output.

### Context level
Level 3 ??engine + validation logic changes.

### Why now
- The 064B decision noted "little scope remains ??this milestone is functionally complete" for the original v0.2 validation expansion.
- True engineering progress would require defining a new milestone (v0.3) with concrete PRD items.
- Risk of repeating the "documentation-first" pattern if the scope is not clearly bounded.

### Files likely involved
- `validation_engine/elimination_rules.py` ??rule configuration expansion
- `strategy_engine/fitness.py` ??multi-weight scoring
- `reports/generator.py` ??explainability output
- `app/ui/main_window.py` ??fitness config controls
- Related test files

### Risks
- No clearly bounded scope ??easily expands into a full milestone definition exercise.
- Requires Codex/user to define what "strategy quality" means in concrete terms before any implementation.
- Highest risk of turning into another planning/documentation loop.

### Verification commands
```
.venv/Scripts/python.exe -m pytest tests/test_elimination_rules.py tests/test_fitness.py -q
git diff --check
```

### Acceptance criteria
1. Elimination rule configuration is extended (at minimum: expose existing config to UI).
2. Fitness scoring supports at least one additional weighting strategy.
3. Strategy report includes a basic explainability section (which rules triggered, which didn't).
4. All existing validation tests continue to pass.
5. No new dependencies beyond the current stack.

---

## Candidate 3: System Hardening / Technical Debt Cleanup

### Scope
Resolve remaining technical debt items from Proposed Task 054: fix test warnings, bump test counts in README, commit the 062??64 production code changes that are currently unstaged, and resolve any remaining CI/lint issues.

### Context level
Level 1?? ??primarily infrastructure and documentation.

### Why now
- 15 production files (062??64 implementation) are still unstaged ??a clear future commit/staging plan would close the loop on that work.
- Test warnings and README staleness are low-effort fixes.
- However, the 064-series already covered extensive documentation hygiene ??this would be a second documentation/infrastructure pass.

### Files likely involved
- `README.md` ??test count bump
- `docs/task_board.md`, `docs/changelog.md` ??tracking
- Potentially `pyproject.toml` ??lint config fixes
- `scripts/agent_status.ps1` ??status script hardening

### Risks
- Low risk ??mostly documentation and infrastructure.
- Risk of scope creep into "fix all warnings" without a clear stopping criterion.
- Per the recommendation rule, this is another documentation-heavy pass, not "real engineering progress."

### Verification commands
```
.venv/Scripts/python.exe -m pytest -q
git diff --check
```

### Acceptance criteria
1. README test count reflects current suite (??291 or current verified count).
2. All 062??64 unstaged production changes have a clear commit/staging plan; this candidate brief does not stage or commit them.
3. No new warnings introduced.
4. `git diff --check` passes.

---

## Recommendation

### Candidate 1 ??Data Workflow Polish / Import UX Hardening

Rationale:
1. **Smallest scope with highest user impact.** Data import is every user's first interaction. Even small UX wins (format feedback, better error messages, pre-filled session defaults) create visible progress.
2. **Avoids another documentation loop.** This produces real UI and service-layer changes ??buttons, dialogs, improved error flows ??not more planning documents.
3. **No dependency bottleneck.** The stale DataService failure claim is retired. Focused data workflow tests pass. The path is clear.
4. **Constrained scope risk is manageable.** The candidate can be delivered in 1?? focused batches without expanding into a full milestone definition.
5. **Leaves Strategy Quality and Technical Debt for a separate decision.** Both are valid but larger conversations. Data workflow polish is a concrete, bounded slice that can start immediately.

### Suggested first batch
**Batch 065A-Impl:** Data import UX hardening ??format validation feedback and actionable error messages in the import flow. No wizard, no session filter redesign ??just make the existing import tell the user what went wrong and how to fix it.

---

## Metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-09
- **Task**: 064J
