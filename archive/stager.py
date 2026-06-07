"""ArchiveStager — copy, verify, and move dataset snapshot files for archive import.

Stages ``ohlcv_snapshot.csv`` into a project-local ``.staging/`` directory,
verifies SHA-256 against the archive manifest, and moves to final destination
only after DB commit.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class HashMismatchError(Exception):
    """Raised when a staged file's SHA-256 does not match the expected hash."""


class StagerValidationError(Exception):
    """Raised when source validation fails (missing files, path traversal, symlinks)."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SNAPSHOT_FILENAME = "ohlcv_snapshot.csv"
_FINAL_FILENAME = "ohlcv.csv"
_CHUNK_SIZE = 8192


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(_CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


def _copy_file(src: Path, dest: Path) -> None:
    shutil.copy2(src, dest)


# ---------------------------------------------------------------------------
# ArchiveStager
# ---------------------------------------------------------------------------


class ArchiveStager:
    """Copy, verify, and move dataset snapshot files for archive import.

    Parameters
    ----------
    archive_root : str or Path
        Root of the unpacked archive folder.
    project_root : str or Path
        Project directory (contains ``.staging/`` and ``data/imported/``).
    experiment_name : str
        Archive experiment name — used in staging and final path names.
    run_id : str
        Short unique run identifier (timestamp or UUID).
    """

    def __init__(
        self,
        archive_root: str | Path,
        project_root: str | Path,
        experiment_name: str,
        run_id: str,
    ) -> None:
        self._src = Path(archive_root)
        self._project_root = Path(project_root)
        self._staging = (
            self._project_root / ".staging" / f"{experiment_name}_{run_id}"
        )
        self._final_dir = self._project_root / "data" / "imported" / experiment_name
        self._staged_path: Path | None = None

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def validate_source(self) -> None:
        """Check that the archive root contains required files and no path
        traversal or symlinks to locations outside the archive."""
        if ".." in self._src.parts:
            raise StagerValidationError(
                f"Archive root contains path traversal component: {self._src}"
            )
        if not self._src.is_dir():
            raise StagerValidationError(
                f"Archive root is not a directory: {self._src}"
            )
        if not (self._src / "manifest.json").is_file():
            raise StagerValidationError(
                f"manifest.json not found in archive: {self._src}"
            )
        snapshot = self._src / _SNAPSHOT_FILENAME
        if not snapshot.is_file():
            raise StagerValidationError(
                f"{_SNAPSHOT_FILENAME} not found in archive: {self._src}"
            )

        # Reject path traversal and symlinks outside archive.
        real_root = self._src.resolve()
        for p in self._src.rglob("*"):
            actual = p.resolve()
            # If it's a symlink, check it resolves inside the archive.
            if p.is_symlink():
                try:
                    actual.relative_to(real_root)
                except ValueError:
                    raise StagerValidationError(
                        f"Symlink '{p}' points outside archive root."
                    )
            # Reject `..` components in relative names.
            try:
                p.relative_to(self._src)
            except (ValueError, OSError):
                raise StagerValidationError(
                    f"Path '{p}' escapes archive root."
                )

    def stage_dataset_snapshot(self, expected_hash: str) -> Path:
        """Copy ``ohlcv_snapshot.csv`` to staging directory and verify hash.

        Parameters
        ----------
        expected_hash : str
            SHA-256 hex from the archive manifest.

        Returns
        -------
        Path
            Path to the staged file.

        Raises
        ------
        HashMismatchError
            If the staged file's hash does not match *expected_hash*.
            The staged file is deleted before raising.
        """
        self.validate_source()
        src = self._src / _SNAPSHOT_FILENAME
        self._staging.mkdir(parents=True, exist_ok=True)
        self._staged_path = self._staging / _SNAPSHOT_FILENAME
        _copy_file(src, self._staged_path)

        actual = _sha256_file(self._staged_path)
        if actual != expected_hash:
            self._staged_path.unlink(missing_ok=True)
            self._staged_path = None
            raise HashMismatchError(
                f"Staged file hash mismatch: "
                f"expected {expected_hash[:16]}..., got {actual[:16]}..."
            )
        return self._staged_path

    def move_to_final_destination(self) -> Path:
        """Move staged file to ``data/imported/<exp>/ohlcv.csv``.

        Call AFTER DB commit.  On failure, the staged file is preserved
        and ``self._staged_path`` remains set so callers can retry or
        inspect the file.

        Returns
        -------
        Path
            Final destination path.

        Raises
        ------
        RuntimeError
            If no file is staged.
        """
        if self._staged_path is None:
            raise RuntimeError("No staged file to move.")
        self._final_dir.mkdir(parents=True, exist_ok=True)
        src = self._staged_path
        dest = self._final_dir / _FINAL_FILENAME
        moved = Path(shutil.move(str(src), str(dest)))
        self._staged_path = None   # only AFTER successful move
        return moved

    def cleanup_temp(self) -> None:
        """Remove the staging directory and its contents."""
        if self._staging.exists():
            shutil.rmtree(self._staging, ignore_errors=True)
