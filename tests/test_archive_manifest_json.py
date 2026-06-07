"""Tests for ArchiveManifest JSON serialization — Task 059G-Impl."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from archive.manifest import ArchiveManifest


def _sample_manifest() -> ArchiveManifest:
    return ArchiveManifest(
        archive_version="1.0.0",
        experiment_name="test_experiment",
        generated_at="2024-01-01T00:00:00Z",
        generator_version="0.2.0",
        files=["strategy.json", "disclaimer.txt"],
        content_hashes={
            "strategy.json": "abc123",
            "disclaimer.txt": "def456",
        },
        disclaimer_path="disclaimer.txt",
    )


# ---------------------------------------------------------------------------
# to_dict / from_dict round trip
# ---------------------------------------------------------------------------


def test_dict_round_trip():
    """to_dict then from_dict must produce an identical manifest."""
    m1 = _sample_manifest()
    d = m1.to_dict()
    m2 = ArchiveManifest.from_dict(d)
    assert m2.archive_version == m1.archive_version
    assert m2.experiment_name == m1.experiment_name
    # to_dict sorts files, so round-trip preserves content but reorders
    assert sorted(m2.files) == sorted(m1.files)
    assert m2.content_hashes == m1.content_hashes


# ---------------------------------------------------------------------------
# JSON round trip
# ---------------------------------------------------------------------------


def test_json_round_trip():
    """to_json then from_json must produce an identical manifest."""
    m1 = _sample_manifest()
    text = m1.to_json()
    m2 = ArchiveManifest.from_json(text)
    # to_dict sorts files, so compare sorted fields
    assert sorted(m2.files) == sorted(m1.files)
    assert m2.content_hashes == m1.content_hashes
    assert m2.archive_version == m1.archive_version


def test_json_deterministic_bytes():
    """Same manifest must always produce identical JSON bytes."""
    m1 = _sample_manifest()
    m2 = _sample_manifest()
    assert m1.to_json() == m2.to_json()


def test_json_default_field_order():
    """JSON output must have deterministic top-level field order."""
    m = _sample_manifest()
    text = m.to_json()
    # Keys should follow to_dict() field order
    expected_keys = [
        "archive_version",
        "experiment_name",
        "generated_at",
        "generator_version",
        "files",
        "content_hashes",
        "disclaimer_path",
    ]
    parsed = json.loads(text)
    keys = list(parsed.keys())
    assert keys == expected_keys, f"Expected {expected_keys}, got {keys}"


# ---------------------------------------------------------------------------
# Folder read/write helpers
# ---------------------------------------------------------------------------


def test_write_read_folder(tmp_path: Path):
    """write_to_folder then read_from_folder must round-trip."""
    m1 = _sample_manifest()
    written = m1.write_to_folder(tmp_path)
    assert written.name == "manifest.json"
    assert written.exists()

    m2 = ArchiveManifest.read_from_folder(tmp_path)
    # to_dict sorts files, so compare sorted
    assert sorted(m2.files) == sorted(m1.files)
    assert m2.content_hashes == m1.content_hashes
    assert m2.archive_version == m1.archive_version


def test_write_read_folder_subdirectory(tmp_path: Path):
    """write_to_folder must create intermediate directories."""
    sub = tmp_path / "a" / "b"
    m1 = _sample_manifest()
    m1.write_to_folder(sub)
    m2 = ArchiveManifest.read_from_folder(sub)
    assert sorted(m2.files) == sorted(m1.files)
    assert m2.content_hashes == m1.content_hashes
    assert m2.archive_version == m1.archive_version
