"""Export/Persistence release acceptance smoke test — Task 035A."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.workers import ImportWorker
from core.models.strategy import Strategy, StrategyBlock, Condition
from repository.dataset_repo import DatasetRepository
from repository.strategy_repo import StrategyRepository

SAMPLE_CSV = Path(__file__).resolve().parent.parent / "sample_data" / "sample_ohlcv.csv"


def _sync_import_start(worker):
    """Patched ImportWorker.start that runs the worker synchronously."""
    worker.run()
    worker.finished.emit()


def test_export_persistence_smoke(tmp_path: Path):
    """
    Focused smoke test covering the user-facing path:
    1. Create/open project.
    2. Import OHLCV dataset.
    3. Verify DatasetMeta persisted.
    4. Simulate GA success with best strategy.
    5. Verify GA best strategy persisted and loaded.
    6. Export selected strategy to Python .py.
    7. Verify Python export properties.
    8. Export report to PDF.
    9. Verify PDF file properties.
    """
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()

    window = MainWindow()
    
    project_dir = tmp_path / "smoke_project"
    
    # 1. Create/open project (mock UI folder selection)
    with patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory", return_value=str(project_dir)), \
         patch("PySide6.QtWidgets.QInputDialog.getText", return_value=("SmokeProject", True)), \
         patch("PySide6.QtWidgets.QMessageBox.information"), \
         patch("PySide6.QtWidgets.QMessageBox.question", return_value=True):
        window._handle_new_project()
        
    assert window.project_service.repository is not None
    db = window.project_service.repository.db
    assert db is not None

    # 2. Import OHLCV dataset (mock UI file selection and dialog)
    with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=(str(SAMPLE_CSV), "CSV")), \
         patch("PySide6.QtWidgets.QMessageBox.information"), \
         patch("PySide6.QtWidgets.QMessageBox.critical"), \
         patch.object(ImportWorker, "start", _sync_import_start):
        window._handle_import_ohlcv_data()
        
    # 3. Verify DatasetMeta persisted to project SQLite
    ds_repo = DatasetRepository(db)
    all_ds = ds_repo.list_all()
    assert len(all_ds) >= 1
    assert all_ds[0].symbol == "TXF"

    # 4. Simulate GA success with best strategy
    # Normally this is triggered by ga_worker emitting ga_finished.
    # We will invoke the handler directly.
    from dataclasses import dataclass

    @dataclass
    class MockGAResult:
        best_strategy: Strategy
        best_score: float
        generation_count: int
        final_population_size: int
        generation_best_scores: list
        generation_avg_scores: list

    ga_best = Strategy(
        name="Smoke GA Best",
        long_entry=StrategyBlock(conditions=[Condition(indicator="SMA", params={"period": 14}, operator=">")]),
    )
    mock_result = MockGAResult(
        best_strategy=ga_best, 
        best_score=100.5, 
        generation_count=5, 
        final_population_size=20,
        generation_best_scores=[10, 50, 100.5],
        generation_avg_scores=[5, 25, 50.25]
    )
    window._on_ga_success(mock_result, source_label="GA 5 Gen")
    
    # 5. Verify GA best strategy persisted and can be loaded
    strat_repo = StrategyRepository(db)
    strat_loaded = strat_repo.get_by_name("ga_best_latest")
    assert strat_loaded is not None
    assert strat_loaded.name == "ga_best_latest"
    
    # 6. Navigate/use Results selected strategy path
    # GA best is automatically injected into the Results ranking.
    assert len(window.ranked_data) > 0
    ga_index = next((i for i, strat in enumerate(window.ranked_data) if "[GA Best]" in strat["strategy"].name), 0)
    assert "[GA Best]" in window.ranked_data[ga_index]["strategy"].name
    
    # Select it in the UI
    window.results_table.table.setRowCount(len(window.ranked_data))
    window.results_table.table.selectRow(ga_index)
    window._handle_strategy_selection_changed()
    
    # 7. Export selected strategy to Python .py
    python_export_path = tmp_path / "smoke_strategy_export.py"
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(str(python_export_path), "Python Files (*.py)")), \
         patch("PySide6.QtWidgets.QMessageBox.information"):
        window._handle_export_code()
        
    # 8. Verify Python export includes research-only disclaimer and no broker/live/order keywords
    assert python_export_path.exists()
    with open(python_export_path, "r", encoding="utf-8") as f:
        py_content = f.read()
    
    assert "Research/backtesting only" in py_content
    assert "Not financial advice" in py_content
    assert "Not live trading code" in py_content
    # Smoke check for live trading terms absent (excluding disclaimer)
    assert "broker" not in py_content.lower()
    assert "order" not in py_content.lower()
    
    # 9. Export report to PDF
    pdf_export_path = tmp_path / "smoke_report.pdf"
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(str(pdf_export_path), "PDF Files (*.pdf)")), \
         patch("PySide6.QtWidgets.QMessageBox.information"):
        window._handle_export_report()
        
    # 10. Verify PDF file begins with %PDF and is non-empty
    assert pdf_export_path.exists()
    assert pdf_export_path.stat().st_size > 0
    with open(pdf_export_path, "rb") as f:
        header = f.read(4)
        assert header == b"%PDF"
