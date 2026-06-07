# Archive Import Conflict Policy Design — Task 059N

## 1. Purpose

When importing reproducible strategy archives, the system must handle cases where the strategy or dataset being imported already exists in the local database or storage. This document defines the conflict scenarios, available resolution policies, default MVP behavior, user-facing warnings, and required audit logs/provenance tracking.

---

## 2. Conflict Scenarios

A conflict occurs when an entity in the import archive matches an entity already present in the user's workspace. There are two primary types of entities:

### 2.1 Strategy Collision
A collision occurs if a strategy in the archive has a `strategy_uid` that matches an existing record in the SQLite database (`Strategy` table).

### 2.2 Dataset Collision
A collision occurs if a dataset referenced in the archive has a key combination (e.g., same `symbol` and `timeframe` but different metadata, or same `id`) that matches an existing dataset record in the workspace database.

---

## 3. Conflict Resolution Policies

To handle collisions, the system will support four distinct resolution policies:

| Policy | Strategy Behavior | Dataset Behavior |
| :--- | :--- | :--- |
| **Reject Duplicate** (MVP Default) | Abort the entire import process. Raise a clean `DuplicateStrategyImportError`. Do not modify database or filesystem state. | Abort the import. Do not overwrite existing datasets or CSV snapshots. |
| **Overwrite with Explicit Opt-In** | Replace the existing strategy metadata, rule blocks, and validation results with the archive's version. | Overwrite dataset metadata and replace the CSV snapshot file under `data/normalized/` with the archive's snapshot. |
| **Keep Existing and Skip** | Skip importing this strategy. Keep the existing workspace strategy intact. Succeed without importing the conflicting strategy. | Keep the existing dataset metadata and snapshot file, and skip writing the archive's dataset snapshot. |
| **Duplicate with Suffix / New UID** | Generate a new `strategy_uid` (UUID4) for the imported strategy, append a suffix (e.g., `_Imported_20260607`) to its name, and import it as a new strategy. | If metadata matches, reuse the existing dataset. If it differs, create a new dataset with a new ID and write the snapshot with a unique filename. |

---

## 4. MVP Default Policy Selection

> [!IMPORTANT]  
> **MVP Default Policy: Reject Duplicate**
> 
> To guarantee complete safety against accidental data loss or overwriting of active, manually tuned strategies, the initial MVP implementation must default to the **Reject Duplicate** policy.
>
> If a duplicate is detected, the import fails immediately with a descriptive error message identifying the conflicting `strategy_uid` and name.

---

## 5. User-Facing Warnings and Prompts

When the import UI is implemented, the import wizard must follow this flow:
1. **Pre-Import Analysis**: Analyze the archive folder, verify its integrity, and check for collisions.
2. **Warning Presentation**: If a conflict is detected, present a warning modal to the user.
   > [!WARNING]  
   > **Conflict Warning Dialog Content:**
   > - **Title**: Strategy / Dataset Collision Detected
   > - **Message**: "The strategy '[Strategy Name]' (UID: `[strategy_uid]`) already exists in your local workspace. Overwriting it will replace all history, parameter settings, and validation results."
   > - **Options**:
   >   1. Cancel Import (Safe / Default)
   >   2. Import as Copy (Creates a new strategy with name '[Strategy Name]_Copy')
   >   3. Overwrite (Explicit opt-in required)

---

## 6. Audit Trail and Provenance Records

All imports must write audit logs into the workspace database to preserve the lineage of the strategy.

### 6.1 `ImportAuditLog` Database Schema
We will introduce a table to track every import action:
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `imported_at`: TEXT (ISO-8601 timestamp)
- `experiment_name`: TEXT
- `archive_version`: TEXT
- `strategy_uid`: TEXT (Reference to Strategy table)
- `conflict_policy_applied`: TEXT (e.g., `"REJECT"`, `"OVERWRITE"`, `"KEEP_EXISTING"`, `"RENAME"`)
- `status`: TEXT (`"SUCCESS"` or `"FAILED"`)
- `failure_reason`: TEXT (nullable)

### 6.2 Strategy Provenance Meta
The strategy JSON definition should be appended with import metadata:
```json
{
  "provenance": {
    "imported_from_archive": true,
    "imported_at": "2026-06-07T13:20:00Z",
    "original_strategy_uid": "original-uid-before-rename"
  }
}
```

---

## 7. Recommended Next Two-Task Batch

**Batch 059O-Design + 059P-Design - ArchiveImporter Repository Contract and Import Audit Schema Design**
- **059O-Design**: Design the repository adapter contracts, interface definitions, and boundary requirements for importing strategies, datasets, and validation results into the workspace storage, ensuring collision detection is handled cleanly.
- **059P-Design**: Design the database schema and provenance tracking requirements for import audit logs, and detail the collision detection logic boundaries without performing any database writes.
