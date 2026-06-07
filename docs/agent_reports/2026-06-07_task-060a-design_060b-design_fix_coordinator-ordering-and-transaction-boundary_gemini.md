Completed:
- Batch 060A-Design + 060B-Design Fix — Coordinator Ordering and Transaction Boundary Correction.

Files changed:
- docs/archive_import_coordinator_architecture_060A.md
- docs/archive_import_coordinator_acceptance_test_contract_060B.md
- docs/changelog.md

Behavior changed:
- 060A: Sequence reordered to verify → preflight → stage → write → finalise → audit. StrategyRepoAdapter auto-commit constraint explicitly documented. Preflight steps before staging and durable insert. Malformed legacy JSON handling at coordinator level. Audit write failure is non-crashing secondary failure.
- 060B: Call ordering corrected. Preflight-specific spy methods added. Malformed legacy JSON acceptance scenario (5.7) added. Auto-commit limitation section (7) added. Staging failure asserts strategy insert NOT called. No-call assertions updated for safe ordering.

Tests run:
- Full suite: 1179 passed, 0 warnings (unchanged).

Assumptions:
- StrategyRepoAdapter auto-commit is a first-pass limitation; refactoring it for external transaction control is a prerequisite for unified coordinator transactions.
- Preflight duplicate UID scan is read-only; staging happens before durable insert.
- Malformed legacy strategy_json creates a latent duplicate risk; coordinator logs a warning and proceeds.

Known risks:
- No automated detection for latent duplicates hidden in unparseable strategy_json rows.
- StrategyRepoAdapter auto-commit means the coordinator cannot provide a unified rollback across strategy + dataset + validation writes in the first pass.

Reviewer focus:
- 060A section 4 (auto-commit constraint) and section 5 phase ordering (preflight before staging before write).
- 060B section 2 (architecture note) and section 4 (safe call ordering).
- 060B section 5.7 (malformed legacy JSON scenario) and section 7 (auto-commit limitation).
