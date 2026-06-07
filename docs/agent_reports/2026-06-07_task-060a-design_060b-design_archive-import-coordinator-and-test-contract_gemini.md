Completed:
- Batch 060A-Design + 060B-Design — Archive Import Coordinator Architecture and Acceptance Test Contract Design.

Files changed:
- docs/archive_import_coordinator_architecture_060A.md (created)
- docs/archive_import_coordinator_acceptance_test_contract_060B.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
- No production code changed (design-only batch).
- Architecture defines precise 10-step coordinator sequence with error handling for 9 failure modes.
- Test contract defines 7 scenarios using spies/fakes with expected call ordering and no-call assertions.
- Next batch proposed: 060C-Impl (coordinator first pass) + 060D-Design (DatasetRepoAdapter insert-only slice design).

Tests run:
- Full suite: 1179 passed, 0 warnings (unchanged).

Assumptions:
- Coordinator implementation will follow 060A sequence exactly.
- Test implementation will use spy/fake pattern from 060B.

Known risks:
- Final-move-failure after DB commit is an acknowledged design gap — strategy row exists but dataset file may be missing.
- Malformed legacy strategy_json during UID scan is handled by the adapter silently skipping unparseable rows.

Reviewer focus:
- 060A sequence steps 6-7 (DB commit before file move).
- 060B test contract 3.5 (move failure after commit) and 3.7 (no-UI/no-CLI/no-engine boundary).
