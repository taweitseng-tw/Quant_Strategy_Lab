"""Project metadata model."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ProjectMeta:
    """Minimal project metadata stored in project.json and project.sqlite."""

    name: str
    root_path: Path
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    description: str = ""
    version: str = "0.0.1"

    def to_json(self) -> str:
        data = asdict(self)
        data["root_path"] = str(data["root_path"])
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
        return json.dumps(data, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> ProjectMeta:
        data = json.loads(raw)
        data["root_path"] = Path(data["root_path"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)

    @classmethod
    def from_dict(cls, data: dict) -> ProjectMeta:
        if isinstance(data.get("root_path"), str):
            data["root_path"] = Path(data["root_path"])
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
