"""Archive manifest model and integrity error type."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class ArchiveIntegrityError(Exception):
    """Raised when an archive fails integrity verification."""


@dataclass
class ArchiveManifest:
    """Metadata and file listing for a reproducible experiment archive.

    Fields
    ------
    archive_version : str
        Schema version, e.g. ``"1.0.0"``.
    experiment_name : str
        Human-readable name for the archived experiment.
    generated_at : str
        ISO-8601 timestamp of archive creation.
    generator_version : str
        QSL software version at archive time.
    files : list[str]
        Relative paths to all files in the archive.
    content_hashes : dict[str, str]
        ``{filename: sha256_hex}`` for every file in ``files``.
    disclaimer_path : str
        Path to ``disclaimer.txt`` inside the archive.
    """

    archive_version: str
    experiment_name: str
    generated_at: str
    generator_version: str
    files: list[str] = field(default_factory=list)
    content_hashes: dict[str, str] = field(default_factory=dict)
    disclaimer_path: str = "disclaimer.txt"

    # -- JSON serialization ---------------------------------------------------

    MANIFEST_FILENAME = "manifest.json"

    def to_dict(self) -> dict:
        """Dict representation with deterministic key ordering."""
        return {
            "archive_version": self.archive_version,
            "experiment_name": self.experiment_name,
            "generated_at": self.generated_at,
            "generator_version": self.generator_version,
            "files": sorted(self.files),
            "content_hashes": dict(sorted(self.content_hashes.items())),
            "disclaimer_path": self.disclaimer_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ArchiveManifest":
        """Construct from a deserialized dict (keys are optional-compatible)."""
        return cls(
            archive_version=data["archive_version"],
            experiment_name=data["experiment_name"],
            generated_at=data["generated_at"],
            generator_version=data["generator_version"],
            files=data.get("files", []),
            content_hashes=data.get("content_hashes", {}),
            disclaimer_path=data.get("disclaimer_path", "disclaimer.txt"),
        )

    def to_json(self, indent: int = 2) -> str:
        """Deterministic JSON string with deterministic field order."""
        import json
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False)

    @classmethod
    def from_json(cls, text: str) -> "ArchiveManifest":
        """Parse from a JSON string."""
        import json
        return cls.from_dict(json.loads(text))

    # -- folder read / write helpers ------------------------------------------

    def write_to_folder(self, root: str | Path) -> Path:
        """Write ``manifest.json`` into *root* and return the file path."""
        import json
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        path = root / self.MANIFEST_FILENAME
        path.write_text(self.to_json(), encoding="utf-8")
        return path

    @classmethod
    def read_from_folder(cls, root: str | Path) -> "ArchiveManifest":
        """Read ``manifest.json`` from *root* and return an ArchiveManifest."""
        root = Path(root)
        path = root / cls.MANIFEST_FILENAME
        text = path.read_text(encoding="utf-8")
        return cls.from_json(text)
