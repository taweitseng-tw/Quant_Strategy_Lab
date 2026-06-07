Completed:
- Batch 060G-Impl + 060H-Design Fix — Initialize-on-disk migration test, adapter design hardening, typo fix.

Files changed:
- tests/test_dataset_snapshot_hash_migration.py
- docs/dataset_repo_adapter_post_migration_insert_only_design_060H.md
- repository/db.py

Behavior changed:
1. Added test_initialize_migrates_old_disk_project_db: creates old-style project.sqlite on disk, re-opens with DatabaseManager(tmp_path).initialize(), asserts column exists and old row has default ''.
2. 060H design now has dual INSERT SQL (post-migration with snapshot_hash, old-DB without). Old-DB fallback covers both dedup WHERE and INSERT columns.
3. 060H transaction methods hardened: insert_dataset() rolls back only on SQLite write/commit failure, uses __cause__ guard. Validation/Duplicate errors do NOT rollback. insert_dataset_no_commit() does no commit/rollback.
4. 060H tests expanded to 12 (added SQLite INSERT rollback, validation no rollback, duplicate no rollback, old-DB INSERT omits column).
5. Fixed "Exisitng" -> "Existing" typo in db.py docstring.

Tests run:
- test_dataset_snapshot_hash_migration.py: 6 passed.
- Full suite: 1192 passed, 0 warnings.

Known risks:
- None. All fixes are test-only or design-only except the one docstring typo.

Reviewer focus:
- test_initialize_migrates_old_disk_project_db: full roundtrip (raw sqlite3 → close → DatabaseManager → verify).
- 060H section 5 (dual SQL) and section 7 (transaction guard).
