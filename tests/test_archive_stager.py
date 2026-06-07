"""Tests for ArchiveStager - Task 060K-Impl."""

from __future__ import annotations

from pathlib import Path

import pytest

from archive.stager import (
    ArchiveStager,
    HashMismatchError,
    StagerValidationError,
)


def _make_archive(tmp: Path, snapshot_content: str) -> Path:
    """Create a minimal archive folder with manifest.json and ohlcv_snapshot.csv."""
    root = tmp / "archive"
    root.mkdir(parents=True)
    (root / "manifest.json").write_text('{"version":"1.0.0"}')
    # Use write_bytes to avoid Windows CRLF translation.
    (root / "ohlcv_snapshot.csv").write_bytes(snapshot_content.encode("utf-8"))
    return root


def _sha256_of_file(path: Path) -> str:
    """Compute SHA-256 of a file (matches _sha256_file in stager)."""
    import hashlib as _h

    h = _h.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


@pytest.fixture
def project_root(tmp_path) -> Path:
    return tmp_path / "project"


@pytest.fixture
def archive_root(tmp_path) -> Path:
    return _make_archive(tmp_path, "col1,col2\n1,2\n3,4\n")


def test_stage_and_move_success(archive_root, project_root, tmp_path):
    """Full staging + move success path."""
    stager = ArchiveStager(archive_root, project_root, "exp1", "r1")
    expected = _sha256_of_file(archive_root / "ohlcv_snapshot.csv")
    staged = stager.stage_dataset_snapshot(expected)

    assert staged.exists()
    assert ".staging" in staged.parts
    assert "exp1_r1" in staged.parts

    final = stager.move_to_final_destination()
    assert final.exists()
    assert final.parent == project_root / "data" / "imported" / "exp1"
    assert final.name == "ohlcv.csv"

    stager.cleanup_temp()


def test_missing_snapshot_raises(project_root, tmp_path):
    """Source with no ohlcv_snapshot.csv must raise StagerValidationError."""
    root = tmp_path / "bad_archive"
    root.mkdir(parents=True)
    (root / "manifest.json").write_text("{}")

    stager = ArchiveStager(root, project_root, "exp", "r1")
    with pytest.raises(StagerValidationError, match="ohlcv_snapshot.csv"):
        stager.stage_dataset_snapshot("anyhash")


def test_hash_mismatch_deletes_staged_file(archive_root, project_root):
    """Hash mismatch must raise and delete the staged file."""
    stager = ArchiveStager(archive_root, project_root, "exp-hm", "r1")
    wrong_hash = "0" * 64

    with pytest.raises(HashMismatchError, match="hash mismatch"):
        stager.stage_dataset_snapshot(wrong_hash)

    assert stager._staged_path is None
    staged_dir = project_root / ".staging" / "exp-hm_r1"
    if staged_dir.exists():
        assert not (staged_dir / "ohlcv_snapshot.csv").exists()


def test_cleanup_removes_staging_dir(archive_root, project_root):
    """cleanup_temp must remove the staging directory."""
    stager = ArchiveStager(archive_root, project_root, "exp-clean", "r1")
    expected = _sha256_of_file(archive_root / "ohlcv_snapshot.csv")
    stager.stage_dataset_snapshot(expected)
    stager.move_to_final_destination()

    stager.cleanup_temp()
    staging_dir = project_root / ".staging" / "exp-clean_r1"
    assert not staging_dir.exists()


def test_db_failure_cleanup_no_final_files(archive_root, project_root):
    """After staging only (no final move), cleanup must not create final files."""
    stager = ArchiveStager(archive_root, project_root, "exp-db", "r1")
    expected = _sha256_of_file(archive_root / "ohlcv_snapshot.csv")
    stager.stage_dataset_snapshot(expected)

    stager.cleanup_temp()

    staging_dir = project_root / ".staging" / "exp-db_r1"
    assert not staging_dir.exists()
    final_file = project_root / "data" / "imported" / "exp-db" / "ohlcv.csv"
    assert not final_file.exists()


def test_move_failure_preserves_staged_file(archive_root, project_root, monkeypatch):
    """If final move fails, staged file and tracked path are preserved."""
    stager = ArchiveStager(archive_root, project_root, "exp-movefail", "r1")
    expected = _sha256_of_file(archive_root / "ohlcv_snapshot.csv")
    stager.stage_dataset_snapshot(expected)

    import archive.stager as stager_mod

    def _fail_move(src, dst, *a, **kw):
        raise OSError("simulated move failure")

    monkeypatch.setattr(stager_mod.shutil, "move", _fail_move)
    with pytest.raises(OSError, match="simulated move failure"):
        stager.move_to_final_destination()

    assert stager._staged_path is not None
    assert stager._staged_path.exists()
    stager.cleanup_temp()


def test_path_traversal_rejected(project_root, tmp_path):
    """Archive root with .. components must be rejected at validation."""
    root = tmp_path / "bad_archive"
    root.mkdir(parents=True)
    (root / "manifest.json").write_text("{}")
    (root / "ohlcv_snapshot.csv").write_text("content")

    traversal_root = root / ".." / "bad_archive"
    stager = ArchiveStager(traversal_root, project_root, "exp-pt", "r1")
    with pytest.raises(StagerValidationError, match="path traversal"):
        stager.validate_source()


def test_symlink_outside_archive_rejected(project_root, tmp_path, monkeypatch):
    """Symlinks pointing outside the archive root must be rejected."""
    root = tmp_path / "archive_sym"
    root.mkdir(parents=True)
    (root / "manifest.json").write_text("{}")
    (root / "ohlcv_snapshot.csv").write_text("content")

    class _OutsideSymlink:
        def is_symlink(self):
            return True

        def resolve(self):
            return tmp_path / "outside"

        def __str__(self):
            return str(root / "escape")

    monkeypatch.setattr(Path, "rglob", lambda self, pattern: [_OutsideSymlink()])

    stager = ArchiveStager(root, project_root, "exp-sym", "r1")
    with pytest.raises(StagerValidationError, match="outside archive"):
        stager.validate_source()
