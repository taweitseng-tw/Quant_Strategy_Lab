"""Project repository — creates and opens local project folders.

Owns the file-system and SQLite persistence for projects.
No PySide6 / UI imports — stays clean for engine and service layers.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.models.project import ProjectMeta
from core.schemas.project_json import (
    PROJECT_SUBDIRS,
    read_project_json,
    write_project_json,
)
from repository.db import DatabaseManager


# Default config file templates created inside a new project folder.
_DEFAULT_INSTRUMENTS_JSON: str = json.dumps([], indent=2)
_DEFAULT_SESSIONS_JSON: str = json.dumps([], indent=2)
_DEFAULT_APP_SETTINGS_JSON: str = json.dumps(
    {
        "version": "0.0.1",
        "default_timeframe": "1min",
        "language": "zh_TW",
        "execution_model": "next_bar_open",
        "same_bar_ambiguity": "stop_loss_first",
    },
    indent=2,
)


class ProjectRepository:
    """Repository for project lifecycle — create, open, update."""

    def __init__(self) -> None:
        self._db: DatabaseManager | None = None

    # ------------------------------------------------------------------
    # create
    # ------------------------------------------------------------------

    def create_project(
        self,
        name: str,
        root_path: Path | str,
        description: str = "",
        overwrite: bool = False,
    ) -> ProjectMeta:
        """Create a new project folder with the full directory structure,
        project.json, project.sqlite, and default config files.

        By default raises ``FileExistsError`` if *root_path* already contains
        a ``project.json`` or ``project.sqlite``.  Pass ``overwrite=True`` to
        replace them instead.

        Returns the new ProjectMeta on success.
        """
        root = Path(root_path).resolve()

        # --- Guard: refuse to silently overwrite an existing project. ---
        json_path = root / "project.json"
        db_path = root / "project.sqlite"
        if json_path.is_file() or db_path.is_file():
            if not overwrite:
                raise FileExistsError(
                    f"A project already exists at {root}. "
                    "Pass overwrite=True to replace it."
                )
            # Clean up previous project artefacts so we start fresh.
            _remove_if_exists(json_path)
            _remove_if_exists(db_path)
            _remove_if_exists(root / "project.sqlite-wal")
            _remove_if_exists(root / "project.sqlite-shm")

        root.mkdir(parents=True, exist_ok=True)

        # 1. Create subdirectory tree.
        for sub in PROJECT_SUBDIRS:
            (root / sub).mkdir(parents=True, exist_ok=True)

        # 2. Write default config files.
        config_dir = root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "instruments.json").write_text(_DEFAULT_INSTRUMENTS_JSON, encoding="utf-8")
        (config_dir / "sessions.json").write_text(_DEFAULT_SESSIONS_JSON, encoding="utf-8")
        (config_dir / "app_settings.json").write_text(_DEFAULT_APP_SETTINGS_JSON, encoding="utf-8")

        # 3. Build metadata and write project.json.
        now = datetime.now(timezone.utc)
        meta = ProjectMeta(
            name=name,
            root_path=root,
            created_at=now,
            updated_at=now,
            description=description,
            version="0.0.1",
        )
        write_project_json(root, _meta_to_dict(meta))

        # 4. Initialize SQLite database.
        self._db = DatabaseManager(root)
        self._db.initialize()
        self._db.connection.execute(
            "INSERT INTO projects (name, root_path, description, version, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (meta.name, str(meta.root_path), meta.description, meta.version,
             meta.created_at.isoformat(), meta.updated_at.isoformat()),
        )
        self._db.connection.commit()

        return meta

    # ------------------------------------------------------------------
    # open
    # ------------------------------------------------------------------

    def open_project(self, root_path: Path | str) -> ProjectMeta:
        """Open an existing project folder.

        Validates that the folder contains project.json and project.sqlite,
        then reads metadata from the json file.
        """
        root = Path(root_path).resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"Project directory not found: {root}")

        # Validate required files exist.
        json_path = root / "project.json"
        if not json_path.is_file():
            raise FileNotFoundError(f"project.json not found in {root}")
        db_path = root / "project.sqlite"
        if not db_path.is_file():
            raise FileNotFoundError(f"project.sqlite not found in {root}")

        # Read metadata from project.json.
        raw = read_project_json(root)
        meta = ProjectMeta.from_dict(raw)

        # Initialize database manager for further operations.
        self._db = DatabaseManager(root)
        self._db.initialize()

        # Update updated_at.
        meta.updated_at = datetime.now(timezone.utc)
        write_project_json(root, _meta_to_dict(meta))
        self._db.connection.execute(
            "UPDATE projects SET updated_at = ? WHERE name = ? AND root_path = ?",
            (meta.updated_at.isoformat(), meta.name, str(meta.root_path)),
        )
        self._db.connection.commit()

        return meta

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @property
    def db(self) -> DatabaseManager:
        if self._db is None:
            raise RuntimeError("No project is open — call create_project() or open_project() first.")
        return self._db

    def close(self) -> None:
        if self._db is not None:
            self._db.close()
            self._db = None


# ------------------------------------------------------------------
# internal helpers
# ------------------------------------------------------------------

def _meta_to_dict(meta: ProjectMeta) -> dict:
    return {
        "name": meta.name,
        "root_path": str(meta.root_path),
        "description": meta.description,
        "version": meta.version,
        "created_at": meta.created_at.isoformat(),
        "updated_at": meta.updated_at.isoformat(),
    }


def _remove_if_exists(path: Path) -> None:
    """Delete *path* if it exists; silently skip missing files."""
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass
