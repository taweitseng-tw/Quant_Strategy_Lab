"""Tests for ProjectRepository lifecycle hardening — Task 002A."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from repository.project_repo import ProjectRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_project_dir() -> Path:
    """Return a path inside a fresh temp directory (cleanup after test)."""
    base = Path(tempfile.mkdtemp())
    yield base / "test_project"
    # Best-effort cleanup — close() should have released all handles.
    shutil.rmtree(base, ignore_errors=True)


@pytest.fixture
def repo() -> ProjectRepository:
    """Return a fresh ProjectRepository (no open project)."""
    return ProjectRepository()


# ---------------------------------------------------------------------------
# create_project – happy path
# ---------------------------------------------------------------------------


def test_create_project_creates_folder_structure(repo, tmp_project_dir):
    """All required subdirectories, project.json, project.sqlite, and config
    files must exist after a successful create_project() call."""
    meta = repo.create_project("test-proj", tmp_project_dir)

    root = meta.root_path
    assert root.is_dir()
    assert (root / "project.json").is_file()
    assert (root / "project.sqlite").is_file()

    # Spot-check a few key subdirectories from PROJECT_SUBDIRS.
    assert (root / "data" / "raw").is_dir()
    assert (root / "data" / "normalized").is_dir()
    assert (root / "strategies" / "generated").is_dir()
    assert (root / "reports" / "html").is_dir()
    assert (root / "logs").is_dir()
    assert (root / "exports" / "json").is_dir()
    assert (root / "config").is_dir()

    # Config template files.
    assert (root / "config" / "instruments.json").is_file()
    assert (root / "config" / "sessions.json").is_file()
    assert (root / "config" / "app_settings.json").is_file()

    # Metadata.
    assert meta.name == "test-proj"
    assert meta.version == "0.0.1"
    assert meta.root_path == root

    repo.close()


def test_create_project_db_has_single_row(repo, tmp_project_dir):
    """The projects table must contain exactly one row after creation."""
    meta = repo.create_project("db-row-test", tmp_project_dir)

    rows = repo.db.connection.execute("SELECT * FROM projects").fetchall()
    assert len(rows) == 1
    row = rows[0]
    assert row["name"] == meta.name
    assert row["root_path"] == str(meta.root_path)
    assert row["version"] == meta.version

    repo.close()


# ---------------------------------------------------------------------------
# Config template content integrity tests (Task 110A-110C)
# ---------------------------------------------------------------------------


def test_config_instruments_json_is_valid_empty_list(repo, tmp_project_dir):
    """config/instruments.json must be valid JSON and default to an empty list."""
    meta = repo.create_project("cfg-test", tmp_project_dir)
    path = meta.root_path / "config" / "instruments.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list), "instruments.json should be a list"
    assert len(data) == 0, "instruments.json should be empty by default"
    repo.close()


def test_config_sessions_json_is_valid_empty_list(repo, tmp_project_dir):
    """config/sessions.json must be valid JSON and default to an empty list."""
    meta = repo.create_project("cfg-test", tmp_project_dir)
    path = meta.root_path / "config" / "sessions.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list), "sessions.json should be a list"
    assert len(data) == 0, "sessions.json should be empty by default"
    repo.close()


def test_config_app_settings_json_has_conservative_defaults(repo, tmp_project_dir):
    """config/app_settings.json must include expected conservative backtest defaults."""
    meta = repo.create_project("cfg-test", tmp_project_dir)
    path = meta.root_path / "config" / "app_settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "app_settings.json should be a dict"
    assert data.get("execution_model") == "next_bar_open", (
        f"Expected next_bar_open, got {data.get('execution_model')!r}"
    )
    assert data.get("same_bar_ambiguity") == "stop_loss_first", (
        f"Expected stop_loss_first, got {data.get('same_bar_ambiguity')!r}"
    )
    assert "default_timeframe" in data, "default_timeframe key must exist"
    assert data.get("version") == "0.0.1"
    repo.close()


def test_overwrite_rewrites_valid_config_templates(repo, tmp_project_dir):
    """Overwrite recreation must produce fresh, valid config templates."""
    meta1 = repo.create_project("first", tmp_project_dir)
    repo.close()
    # Mutate the config to prove it gets rewritten.
    bad_path = meta1.root_path / "config" / "instruments.json"
    bad_path.write_text("not json", encoding="utf-8")

    repo2 = ProjectRepository()
    meta2 = repo2.create_project("second", tmp_project_dir, overwrite=True)

    # All three config files must be valid JSON again.
    for name in ("instruments.json", "sessions.json", "app_settings.json"):
        content = (meta2.root_path / "config" / name).read_text(encoding="utf-8")
        data = json.loads(content)
        assert data is not None, f"{name} must be valid JSON after overwrite"
    repo2.close()


# ---------------------------------------------------------------------------
# create_project – duplicate rejection
# ---------------------------------------------------------------------------


def test_create_project_refuses_existing_by_default(repo, tmp_project_dir):
    """Calling create_project() twice on the same path must raise
    FileExistsError when overwrite is False (default)."""
    repo.create_project("first", tmp_project_dir)
    repo.close()

    repo2 = ProjectRepository()
    with pytest.raises(FileExistsError, match="already exists"):
        repo2.create_project("second", tmp_project_dir)
    repo2.close()


def test_create_project_overwrite_replaces(repo, tmp_project_dir):
    """With overwrite=True, create_project() on an existing folder must
    succeed and produce a fresh project."""
    repo.create_project("first", tmp_project_dir)
    repo.close()

    repo2 = ProjectRepository()
    meta = repo2.create_project("second", tmp_project_dir, overwrite=True)

    assert meta.name == "second"
    assert (meta.root_path / "project.json").is_file()
    assert (meta.root_path / "project.sqlite").is_file()

    # Only one row (replaced, not duplicated).
    rows = repo2.db.connection.execute("SELECT * FROM projects").fetchall()
    assert len(rows) == 1
    assert rows[0]["name"] == "second"

    repo2.close()


# ---------------------------------------------------------------------------
# open_project
# ---------------------------------------------------------------------------


def test_open_project_after_create(repo, tmp_project_dir):
    """open_project() must succeed after create_project() and return the
    same metadata."""
    meta1 = repo.create_project("open-test", tmp_project_dir)
    repo.close()

    repo2 = ProjectRepository()
    meta2 = repo2.open_project(tmp_project_dir)

    assert meta2.name == meta1.name
    assert meta2.root_path == meta1.root_path
    assert meta2.version == meta1.version
    repo2.close()


def test_open_project_nonexistent_dir_raises(repo):
    """open_project() on a non-existent directory must raise FileNotFoundError."""
    fake = Path(tempfile.gettempdir()) / "qsl_nonexistent_002a_test"
    with pytest.raises(FileNotFoundError):
        repo.open_project(fake)


def test_open_project_missing_project_json_raises(repo, tmp_project_dir):
    """If a directory exists but has no project.json, open_project() must raise."""
    tmp_project_dir.mkdir(parents=True, exist_ok=True)
    with pytest.raises(FileNotFoundError, match="project.json"):
        repo.open_project(tmp_project_dir)


# ---------------------------------------------------------------------------
# close + temp-folder deletion (Windows file-lock guard)
# ---------------------------------------------------------------------------


def test_close_releases_file_handles_for_cleanup(repo, tmp_project_dir):
    """After repo.close(), the entire project directory must be deletable
    without PermissionError — this catches WAL/SHM file-lock bugs on Windows."""
    repo.create_project("cleanup-test", tmp_project_dir)
    repo.close()

    # Must succeed — if WAL handles linger, rmtree fails on Windows.
    shutil.rmtree(tmp_project_dir.parent, ignore_errors=False)


# ---------------------------------------------------------------------------
# projects table — duplicate root_path prevention
# ---------------------------------------------------------------------------


def test_projects_table_rejects_duplicate_root_path(repo, tmp_project_dir):
    """The UNIQUE constraint on root_path must prevent a second row with the
    same root_path, even if someone bypasses create_project()."""
    repo.create_project("unique-test", tmp_project_dir)

    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):
        repo.db.connection.execute(
            "INSERT INTO projects (name, root_path, description, version, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("dup", str(tmp_project_dir), "", "0.0.1", "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
        )
        repo.db.connection.commit()

    repo.close()
