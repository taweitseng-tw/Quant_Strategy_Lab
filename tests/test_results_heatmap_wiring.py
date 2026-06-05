"""Tests for Results page ↔ ParameterHeatmapWidget integration (Task 036A)."""

import pytest
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture(scope="module")
def main_window(qapp):
    return MainWindow()

def test_heatmap_exists_on_results_page(main_window):
    win = main_window
    assert hasattr(win, "heatmap_widget")
    
    # Check that it's in the tabs
    tab_texts = [win.results_tabs.tabText(i) for i in range(win.results_tabs.count())]
    assert "Parameter Heatmap" in tab_texts

def test_strategy_ranking_updates_heatmap(main_window):
    win = main_window
    
    # Ensure it handles the initial state / updates properly
    # win.ranked_data should already be pushed to the heatmap during _refresh_results_ranking
    if len(win.ranked_data) > 0:
        assert win.heatmap_widget.table.rowCount() == len(win.ranked_data)
        assert not win.heatmap_widget.table.isHidden()
    else:
        assert win.heatmap_widget.table.isHidden()
