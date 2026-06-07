# Import Write Coordinator Design — Task 059X

> Design-only. No production code changed.

## 1. Current State

| Component | Status |
|---|---|
| `ImportAuditLog` schema + `ensure_import_audit_log_schema()` | ✅ Done (059U) |
| `AuditLogRepositoryAdapter.insert_failure_log()` | ✅ Done (059W) |
| `ArchiveImporter.build_preview()` (read-only) | ✅ Done (059Q) |
| Strategy/dataset/validation repository adapters | ❌ Not implemented |
| Filesystem staging (copy snapshot) | ❌ Not implemented |
| Import write coordinator | ❌ Not implemented (this document) |

## 2. Coordinator Responsibilities (Future)

```python
class ImportWriteCoordinator:
    """Sequence a verified archive import: validate, stage, write, audit.
    """
```

The coordinator will:

1. **Preview**: Call `ArchiveImporter.build_preview()` to read and verify the archive.
2. **Audit schema**: Ensure `ImportAuditLog` table exists.
3. **Conflict check**: Look up existing strategy/dataset by UID/hash.
4. **Stage filesystem**: Copy dataset snapshot from archive to project `data/`.
5. **Write repository**: Insert/update strategy + dataset + validation rows.
6. **Write audit log**: Log success or failure.
7. **Rollback on failure**: Coordinator-level transaction.

## 3. Boundary: What exists now vs what is future

| Step | Status |
|---|---|
| Read + verify archive manifest | ✅ 059Q (build_preview) |
| Ensure audit schema | ✅ 059U (ensure_import_audit_log_schema) |
| Write failed audit row | ✅ 059W (insert_failure_log) |
| Write strategy/dataset/validation rows | ❌ StrategyRepoAdapter, DatasetRepoAdapter — future |
| Copy dataset file to project | ❌ Filesystem staging — future |
| Coordinator orchestration | ❌ Future |

## 4. Next Two-Task Batch

**Batch 059Y-Impl + 059Z-Design — StrategyRepoAdapter Duplicate-Reject Insert-Only Slice + Filesystem Staging Design**

- 059Y: `StrategyRepoAdapter.insert_strategy(strategy_dto)` — insert-only, rejects on duplicate UID with a domain exception. No overwrite/update. No dataset/validation writes. No file copy.
- 059Z: Filesystem staging (copy snapshot) design only — no implementation.
- **No coordinator implementation. No overwrite/update of existing strategies. No dataset/validation writes. No file copy implementation.**

## 5. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-07
- **Dependencies**: 059W (audit log adapter) — Done
