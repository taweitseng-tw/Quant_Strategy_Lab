"""Tests for archive manifest verifier — Task 059C-Impl."""

from __future__ import annotations

import hashlib

import pytest

from archive.manifest import ArchiveManifest, ArchiveIntegrityError
from archive.verifier import ArchiveVerifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


def test_verify_all_passes_for_valid_archive(tmp_path):
    """Verifier must return True when all files, hashes, and disclaimer are correct."""
    # Create files
    (tmp_path / "strategy.json").write_text('{"name":"test"}', encoding="utf-8")
    (tmp_path / "disclaimer.txt").write_text("Research only. Not financial advice.", encoding="utf-8")

    manifest = ArchiveManifest(
        archive_version="1.0.0",
        experiment_name="test_experiment",
        generated_at="2024-01-01T00:00:00Z",
        generator_version="0.2.0",
        files=["strategy.json", "disclaimer.txt"],
        content_hashes={
            "strategy.json": _sha256('{"name":"test"}'),
            "disclaimer.txt": _sha256("Research only. Not financial advice."),
        },
        disclaimer_path="disclaimer.txt",
    )

    verifier = ArchiveVerifier(manifest, tmp_path)
    assert verifier.verify_all() is True


# ---------------------------------------------------------------------------
# Missing file
# ---------------------------------------------------------------------------


def test_verify_raises_on_missing_file(tmp_path):
    """Verifier must raise ArchiveIntegrityError when a listed file is missing."""
    (tmp_path / "disclaimer.txt").write_text("ok", encoding="utf-8")

    manifest = ArchiveManifest(
        archive_version="1.0.0",
        experiment_name="test",
        generated_at="2024-01-01T00:00:00Z",
        generator_version="0.2.0",
        files=["strategy.json", "disclaimer.txt"],
        content_hashes={},
        disclaimer_path="disclaimer.txt",
    )

    verifier = ArchiveVerifier(manifest, tmp_path)
    with pytest.raises(ArchiveIntegrityError, match="Missing files"):
        verifier.verify_all()


# ---------------------------------------------------------------------------
# Hash mismatch
# ---------------------------------------------------------------------------


def test_verify_raises_on_hash_mismatch(tmp_path):
    """Verifier must raise ArchiveIntegrityError when content hash mismatches."""
    (tmp_path / "strategy.json").write_text('{"name":"real"}', encoding="utf-8")
    (tmp_path / "disclaimer.txt").write_text("ok", encoding="utf-8")

    manifest = ArchiveManifest(
        archive_version="1.0.0",
        experiment_name="test",
        generated_at="2024-01-01T00:00:00Z",
        generator_version="0.2.0",
        files=["strategy.json", "disclaimer.txt"],
        content_hashes={
            "strategy.json": _sha256('{"name":"tampered"}'),  # wrong hash
            "disclaimer.txt": _sha256("ok"),
        },
        disclaimer_path="disclaimer.txt",
    )

    verifier = ArchiveVerifier(manifest, tmp_path)
    with pytest.raises(ArchiveIntegrityError, match="Hash mismatch"):
        verifier.verify_all()


def test_verify_raises_when_listed_file_has_no_hash(tmp_path):
    """Every listed file must have an explicit SHA-256 hash."""
    (tmp_path / "strategy.json").write_text("{}", encoding="utf-8")
    (tmp_path / "disclaimer.txt").write_text("ok", encoding="utf-8")

    manifest = ArchiveManifest(
        archive_version="1.0.0",
        experiment_name="test",
        generated_at="2024-01-01T00:00:00Z",
        generator_version="0.2.0",
        files=["strategy.json", "disclaimer.txt"],
        content_hashes={
            "disclaimer.txt": _sha256("ok"),
        },
        disclaimer_path="disclaimer.txt",
    )

    verifier = ArchiveVerifier(manifest, tmp_path)
    with pytest.raises(ArchiveIntegrityError, match="Missing content hashes"):
        verifier.verify_all()


def test_verify_rejects_paths_that_escape_archive_root(tmp_path):
    """Archive-relative paths must not escape the archive root."""
    (tmp_path / "disclaimer.txt").write_text("ok", encoding="utf-8")

    manifest = ArchiveManifest(
        archive_version="1.0.0",
        experiment_name="test",
        generated_at="2024-01-01T00:00:00Z",
        generator_version="0.2.0",
        files=["../outside.txt", "disclaimer.txt"],
        content_hashes={
            "../outside.txt": _sha256("outside"),
            "disclaimer.txt": _sha256("ok"),
        },
        disclaimer_path="disclaimer.txt",
    )

    verifier = ArchiveVerifier(manifest, tmp_path)
    with pytest.raises(ArchiveIntegrityError, match="escapes root"):
        verifier.verify_all()


# ---------------------------------------------------------------------------
# Disclaimer checks
# ---------------------------------------------------------------------------


def test_verify_raises_on_missing_disclaimer(tmp_path):
    """Verifier must raise when disclaimer.txt is missing."""
    (tmp_path / "strategy.json").write_text("{}", encoding="utf-8")

    manifest = ArchiveManifest(
        archive_version="1.0.0",
        experiment_name="test",
        generated_at="2024-01-01T00:00:00Z",
        generator_version="0.2.0",
        files=["strategy.json"],
        content_hashes={
            "strategy.json": _sha256("{}"),
        },
        disclaimer_path="disclaimer.txt",
    )

    verifier = ArchiveVerifier(manifest, tmp_path)
    with pytest.raises(ArchiveIntegrityError, match="Disclaimer.*missing"):
        verifier.verify_all()


def test_verify_raises_on_empty_disclaimer(tmp_path):
    """Verifier must raise when disclaimer.txt is empty."""
    (tmp_path / "strategy.json").write_text("{}", encoding="utf-8")
    (tmp_path / "disclaimer.txt").write_text("", encoding="utf-8")

    manifest = ArchiveManifest(
        archive_version="1.0.0",
        experiment_name="test",
        generated_at="2024-01-01T00:00:00Z",
        generator_version="0.2.0",
        files=["strategy.json", "disclaimer.txt"],
        content_hashes={
            "strategy.json": _sha256("{}"),
            "disclaimer.txt": _sha256(""),
        },
        disclaimer_path="disclaimer.txt",
    )

    verifier = ArchiveVerifier(manifest, tmp_path)
    with pytest.raises(ArchiveIntegrityError, match="Disclaimer.*empty"):
        verifier.verify_all()
