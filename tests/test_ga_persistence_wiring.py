"""Tests for GA Persistence integration — Task 032C.

Verifies that:
- MainWindow _on_ga_success saves the latest GA strategy to SQLite.
- MainWindow _handle_open_project loads the latest GA strategy from SQLite.
"""

from __future__ import annotations

import os
import sys

import pytest
from PySide6.QtWidgets import QApplication

from core.models.project import ProjectMeta
from core.models.strategy import Strategy, StrategyBlock, Condition
from repository.db import DatabaseManager
from app.services.ga_service import GASearchResult

# Skip entire module if display is unavailable (headless CI).
pytestmark = pytest.mark.skipif(
    sys.platform != "win32" and not os.environ.get("DISPLAY"),
    reason="Requires display or Windows",
)

@pytest.fixture
def memory_db():
    """Provides an initialized in-memory database."""
    db = DatabaseManager(":memory:")
    db.initialize()
    yield db
    db.close()


def test_main_window_saves_ga_best_on_success(memory_db, monkeypatch):
    """Verify that a successful GA run persists the strategy when a project is open."""
    app = QApplication.instance() or QApplication([])
    from app.ui.main_window import MainWindow

    window = MainWindow()
    
    # Mock an open project with an in-memory DB
    window.project_service._active_project = ProjectMeta(
        name="TestProject",
        root_path="virtual/path",
        created_at=None,
        updated_at=None,
    )
    window.project_service.repository._db = memory_db

    # Create a mock result
    ga_strat = Strategy(
        name="test_ga_strat",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 15}, operator=">"),
        ])
    )
    result = GASearchResult(
        best_strategy=ga_strat,
        best_score=0.9999,
        generation_count=5,
        final_population_size=10,
    )
    
    # Trigger success flow
    window._on_ga_success(result, source_label="Test Source")
    
    # Verify the strategy was stored in the in-memory DB
    from app.services.strategy_persistence_service import StrategyPersistenceService
    pers_svc = StrategyPersistenceService(memory_db)
    
    saved = pers_svc.load_best_strategy("latest")
    assert saved is not None
    assert saved.name == "ga_best_latest"
    
    # And UI correctly added the prefix
    assert window._latest_ga_strategy.name == "[GA Best] test_ga_strat"


def test_main_window_loads_ga_best_on_project_open(memory_db, monkeypatch):
    """Verify that opening a project loads the previously saved GA best strategy."""
    app = QApplication.instance() or QApplication([])
    from app.ui.main_window import MainWindow
    
    # 1. Pre-populate the in-memory database with a GA strategy
    from app.services.strategy_persistence_service import StrategyPersistenceService
    pers_svc = StrategyPersistenceService(memory_db)
    
    saved_strat = Strategy(
        name="ga_best_latest",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="RSI", params={"period": 14}, operator="<"),
        ])
    )
    pers_svc.save_best_strategy(saved_strat, label="latest")
    
    # 2. Mock project opening process
    window = MainWindow()
    
    # Mock open_project to set our in-memory db instead of a real file
    original_open = window.project_service.open_project
    def mock_open_project(path):
        meta = ProjectMeta(
            name="TestProject",
            root_path="virtual/path",
            created_at=None,
            updated_at=None,
        )
        window.project_service._active_project = meta
        window.project_service.repository._db = memory_db
        return meta

    monkeypatch.setattr(window.project_service, "open_project", mock_open_project)
    
    # We must mock QFileDialog and QMessageBox so it doesn't wait for user input
    from PySide6.QtWidgets import QFileDialog, QMessageBox
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args, **kwargs: "virtual/path")
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.StandardButton.Ok)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: QMessageBox.StandardButton.Ok)
    
    # Trigger project open
    window._handle_open_project()
    
    # 3. Verify it was loaded and properly injected into the UI state
    assert hasattr(window, "_latest_ga_strategy")
    assert window._latest_ga_strategy is not None
    assert window._latest_ga_strategy.name == "[GA Best] ga_best_latest"
    assert window._latest_ga_strategy.long_entry.conditions[0].indicator == "RSI"
