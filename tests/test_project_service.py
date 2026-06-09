"""Tests for ProjectService and its integration with other services — Task 020A."""

from __future__ import annotations

import tempfile
import shutil
from pathlib import Path
import pytest

from core.models.project import ProjectMeta
from app.services.project_service import ProjectService
from app.services.data_service import DataService
from app.services.instrument_service import InstrumentService


@pytest.fixture
def temp_dir() -> Path:
    """Fixture to provide a clean temporary directory for project creation/opening."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


def test_project_service_initialization() -> None:
    """Verify ProjectService initializes with no active project."""
    service = ProjectService()
    assert service.get_active_project() is None
    assert service.is_project_active() is False


def test_project_service_create_and_open_lifecycle(temp_dir) -> None:
    """Verify that ProjectService can create, close, and reopen projects successfully."""
    service = ProjectService()
    proj_path = temp_dir / "TestProject"
    
    # 1. Create project
    meta = service.create_project("TestProject", proj_path)
    assert service.is_project_active() is True
    assert service.get_active_project() == meta
    assert meta.name == "TestProject"
    assert meta.root_path == proj_path.resolve()
    assert proj_path.exists()
    assert (proj_path / "project.json").is_file()
    assert (proj_path / "project.sqlite").is_file()
    
    # 2. Close project
    service.close_project()
    assert service.is_project_active() is False
    assert service.get_active_project() is None
    
    # 3. Open project
    meta_opened = service.open_project(proj_path)
    assert service.is_project_active() is True
    assert service.get_active_project().name == "TestProject"
    assert service.get_active_project().root_path == proj_path.resolve()


def test_project_path_propagation_to_services(temp_dir) -> None:
    """Verify that setting the project path correctly propagates to DataService and InstrumentService."""
    project_service = ProjectService()
    data_service = DataService()
    instrument_service = InstrumentService()
    
    # Initially none have project paths set
    assert project_service.get_active_project() is None
    assert data_service.project_path is None
    assert instrument_service.project_path is None
    
    # Create project and manually propagate path
    proj_path = temp_dir / "PropagationProject"
    meta = project_service.create_project("PropagationProject", proj_path)
    
    data_service.set_project_path(meta.root_path)
    instrument_service.set_project_path(meta.root_path)
    
    assert data_service.project_path == proj_path.resolve()
    assert instrument_service.project_path == proj_path.resolve()
    
    # Verify profiles are populated from active project
    assert len(instrument_service.get_profiles()) > 0
    assert instrument_service.is_mock_data() is False


# ---------------------------------------------------------------------------
# Config template integrity through ProjectService (Task 112A-112C)
# ---------------------------------------------------------------------------


def test_project_service_create_creates_config_files(temp_dir) -> None:
    """ProjectService.create_project must create all three config files."""
    service = ProjectService()
    proj_path = temp_dir / "ConfigTest"
    meta = service.create_project("ConfigTest", proj_path)

    assert (meta.root_path / "config" / "instruments.json").is_file()
    assert (meta.root_path / "config" / "sessions.json").is_file()
    assert (meta.root_path / "config" / "app_settings.json").is_file()

    service.close_project()


def test_project_service_config_files_are_valid_json(temp_dir) -> None:
    """Config files created through ProjectService must be valid JSON."""
    import json

    service = ProjectService()
    proj_path = temp_dir / "JsonTest"
    meta = service.create_project("JsonTest", proj_path)

    for name in ("instruments.json", "sessions.json", "app_settings.json"):
        content = (meta.root_path / "config" / name).read_text(encoding="utf-8")
        data = json.loads(content)
        assert data is not None, f"{name} must be parseable JSON"

    service.close_project()


def test_project_service_open_preserves_custom_config_key(temp_dir) -> None:
    """Open_project through ProjectService must preserve custom keys in config files."""
    import json

    service = ProjectService()
    proj_path = temp_dir / "PreserveTest"
    meta = service.create_project("PreserveTest", proj_path)
    service.close_project()

    # Add a custom key to app_settings.json.
    cfg = meta.root_path / "config" / "app_settings.json"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    data["custom_service_key"] = "preserved"
    cfg.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Reopen through service - must preserve the custom key.
    service2 = ProjectService()
    meta2 = service2.open_project(proj_path)
    reopened = json.loads(
        (meta2.root_path / "config" / "app_settings.json").read_text(encoding="utf-8")
    )
    assert reopened.get("custom_service_key") == "preserved", (
        "Custom key must survive service-level open_project"
    )
    service2.close_project()


def test_project_service_open_returns_valid_meta(temp_dir) -> None:
    """ProjectService.open_project must return correct ProjectMeta."""
    service = ProjectService()
    proj_path = temp_dir / "MetaTest"
    meta = service.create_project("MetaTest", proj_path)
    service.close_project()

    service2 = ProjectService()
    meta2 = service2.open_project(proj_path)
    assert meta2.name == "MetaTest"
    assert meta2.root_path == proj_path.resolve()
    assert meta2.version == "0.0.1"
    service2.close_project()
