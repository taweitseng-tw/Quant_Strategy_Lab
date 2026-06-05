"""Service layer for Project operations — Task 020A."""

from __future__ import annotations

import logging
from pathlib import Path

from core.models.project import ProjectMeta
from repository.project_repo import ProjectRepository

logger = logging.getLogger(__name__)


class ProjectService:
    """Service to manage active project state and orchestrate folder lifecycles.
    
    Coordinates ProjectRepository to create/open/close projects, and tracks
    the currently loaded active project metadata.
    """

    def __init__(self, repository: ProjectRepository | None = None) -> None:
        self.repository = repository or ProjectRepository()
        self._active_project: ProjectMeta | None = None

    def create_project(
        self,
        name: str,
        root_path: Path | str,
        description: str = "",
        overwrite: bool = False,
    ) -> ProjectMeta:
        """Create a new project using the repository and set it as active."""
        if self._active_project:
            self.close_project()

        meta = self.repository.create_project(
            name=name,
            root_path=root_path,
            description=description,
            overwrite=overwrite,
        )
        self._active_project = meta
        logger.info(f"Created new project: {meta.name} at {meta.root_path}")
        return meta

    def open_project(self, root_path: Path | str) -> ProjectMeta:
        """Open an existing project using the repository and set it as active."""
        if self._active_project:
            self.close_project()

        meta = self.repository.open_project(root_path)
        self._active_project = meta
        logger.info(f"Opened project: {meta.name} at {meta.root_path}")
        return meta

    def close_project(self) -> None:
        """Close the active project and release repository resources."""
        if self._active_project:
            logger.info(f"Closing project: {self._active_project.name}")
            self.repository.close()
            self._active_project = None

    def get_active_project(self) -> ProjectMeta | None:
        """Return the current active project metadata."""
        return self._active_project

    def is_project_active(self) -> bool:
        """Return True if a project is currently open."""
        return self._active_project is not None
