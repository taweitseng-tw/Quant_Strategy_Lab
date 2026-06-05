"""project.json read / write helpers for the local project folder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_JSON_FILENAME = "project.json"

# Required project subdirectory structure per AGENTS.md §9.2.
PROJECT_SUBDIRS: list[str] = [
    "data/raw",
    "data/normalized",
    "data/resampled",
    "strategies/generated",
    "strategies/passed",
    "strategies/archived",
    "reports/html",
    "reports/markdown",
    "reports/excel",
    "logs",
    "exports/json",
    "exports/pseudocode",
    "config",
]


def read_project_json(project_dir: Path) -> dict[str, Any]:
    """Read and parse the project.json file in *project_dir*."""
    path = project_dir / PROJECT_JSON_FILENAME
    if not path.is_file():
        raise FileNotFoundError(f"project.json not found in {project_dir}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_project_json(project_dir: Path, data: dict[str, Any]) -> None:
    """Write *data* into project.json inside *project_dir*."""
    path = project_dir / PROJECT_JSON_FILENAME
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
