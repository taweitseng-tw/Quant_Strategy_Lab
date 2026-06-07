"""Archive integrity verifier.

Verifies file existence, SHA-256 content hashes, and disclaimer
requirements for an ``ArchiveManifest`` against a filesystem root.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO

from archive.manifest import ArchiveManifest, ArchiveIntegrityError


def _sha256_hex(fp: BinaryIO, chunk_size: int = 8192) -> str:
    h = hashlib.sha256()
    while True:
        chunk = fp.read(chunk_size)
        if not chunk:
            break
        h.update(chunk)
    return h.hexdigest()


class ArchiveVerifier:
    """Verify archive integrity from a manifest and filesystem root.

    Parameters
    ----------
    manifest : ArchiveManifest
        The expected manifest.
    root : Path
        Filesystem path to the archive root directory.
    """

    def __init__(self, manifest: ArchiveManifest, root: Path) -> None:
        self._manifest = manifest
        self._root = Path(root)

    def verify_all(self) -> bool:
        """Run all integrity checks.

        Returns
        -------
        bool
            ``True`` if every check passes; otherwise an exception is raised.

        Raises
        ------
        ArchiveIntegrityError
            If any check fails.
        """
        self._check_files_exist()
        self._check_content_hashes()
        self._check_disclaimer()
        return True

    # -- internal checks --------------------------------------------------

    def _check_files_exist(self) -> None:
        missing = [f for f in self._manifest.files
                   if not self._archive_path(f).is_file()]
        if missing:
            raise ArchiveIntegrityError(
                f"Missing files in archive: {', '.join(missing)}"
            )

    def _check_content_hashes(self) -> None:
        missing_hashes = [
            filename for filename in self._manifest.files
            if filename not in self._manifest.content_hashes
        ]
        if missing_hashes:
            raise ArchiveIntegrityError(
                f"Missing content hashes for files: {', '.join(missing_hashes)}"
            )

        for filename, expected in self._manifest.content_hashes.items():
            path = self._archive_path(filename)
            try:
                with path.open("rb") as fp:
                    actual = _sha256_hex(fp)
            except FileNotFoundError:
                raise ArchiveIntegrityError(
                    f"File '{filename}' not found during hash verification."
                )
            if actual != expected:
                raise ArchiveIntegrityError(
                    f"Hash mismatch for '{filename}': "
                    f"expected {expected[:16]}..., got {actual[:16]}..."
                )

    def _check_disclaimer(self) -> None:
        path = self._archive_path(self._manifest.disclaimer_path)
        if not path.is_file():
            raise ArchiveIntegrityError(
                f"Disclaimer file '{self._manifest.disclaimer_path}' is missing."
            )
        if path.stat().st_size == 0:
            raise ArchiveIntegrityError(
                f"Disclaimer file '{self._manifest.disclaimer_path}' is empty."
            )

    def _archive_path(self, relative_path: str) -> Path:
        root = self._root.resolve()
        path = (root / relative_path).resolve()
        if path != root and root not in path.parents:
            raise ArchiveIntegrityError(
                f"Archive path escapes root: {relative_path}"
            )
        return path
