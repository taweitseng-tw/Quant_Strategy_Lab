"""End-to-End smoke test for the GA user flow — Task 031G.

Verifies:
1. Launching main window.
2. Opening Build page and running GA search via UI.
3. Checking async completion.
4. Switching to Results page.
5. Verifying GA Best is in the ranking table and selectable.
"""

from __future__ import annotations

import os
import sys

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

# Skip entire module if display is unavailable (headless CI).
pytestmark = pytest.mark.skipif(
    sys.platform != "win32" and not os.environ.get("DISPLAY"),
    reason="Requires display or Windows",
)

def test_ga_e2e_flow(monkeypatch):
    """Smoke test for the end-to-end GA generation and results viewing flow."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from app.ui.main_window import MainWindow
    from app.services.ga_service import GASearchResult
    from core.models.strategy import Condition, Strategy, StrategyBlock

    class _FakeSignal:
        def __init__(self):
            self._callbacks = []

        def connect(self, callback):
            self._callbacks.append(callback)

        def emit(self, *args):
            for callback in list(self._callbacks):
                callback(*args)

    class _FakeGAWorker:
        def __init__(self, *args, **kwargs):
            self.success = _FakeSignal()
            self.failure = _FakeSignal()
            self.finished = _FakeSignal()
            self._running = False

        def isRunning(self):
            return self._running

        def start(self):
            self._running = True

            def complete():
                result = GASearchResult(
                    best_strategy=Strategy(
                        name="fake_ga_best",
                        long_entry=StrategyBlock(
                            conditions=[Condition(indicator="SMA", params={"period": 10}, operator=">")]
                        ),
                        long_exit=StrategyBlock(
                            conditions=[Condition(indicator="SMA", params={"period": 10}, operator="<")]
                        ),
                    ),
                    best_score=1.23,
                    generation_count=1,
                    final_population_size=1,
                    generation_best_scores=[1.23],
                    generation_avg_scores=[1.0],
                    config_snapshot={"population_size": 1, "max_generations": 1},
                )
                self.success.emit(result, "Fake GA")
                self._running = False
                self.finished.emit()

            QTimer.singleShot(250, complete)

    monkeypatch.setattr("app.workers.GAWorker", _FakeGAWorker)

    # 1. Launch app
    window = MainWindow()
    window.show()
    QTest.qWait(100)  # Let UI settle

    # 2. Open Build page (index 2)
    window.navigation.setCurrentRow(2)
    QTest.qWait(100)
    assert window.ga_build_panel.isVisible()

    # 3. Click Run GA
    assert window.ga_build_panel.btn_run_ga.isEnabled()
    QTest.mouseClick(window.ga_build_panel.btn_run_ga, Qt.MouseButton.LeftButton)
    QTest.qWait(100)

    # 4. Confirm it disables while running
    assert not window.ga_build_panel.btn_run_ga.isEnabled()

    # Wait for fake GA worker to finish (max 10 seconds)
    import time
    start_time = time.time()
    while not window.ga_build_panel.btn_run_ga.isEnabled():
        QApplication.processEvents()
        QTest.qWait(50)
        if time.time() - start_time > 10.0:
            raise TimeoutError("GA Worker did not finish within 10 seconds")

    assert window.ga_build_panel.btn_run_ga.isEnabled()
    assert "✓" in window.ga_build_panel.status_label.text()

    # 5. Confirm GA best strategy is displayed on Build page
    assert hasattr(window, "_latest_ga_strategy")
    assert "[GA Best]" in window._latest_ga_strategy.name

    # 6. Open Results page by name.
    results_row = next(
        i
        for i in range(window.navigation.count())
        if window.navigation.item(i).text() == "Results"
    )
    window.navigation.setCurrentRow(results_row)
    QTest.qWait(100)
    # Qt visibility checks can be flaky in headless environments, so verify
    # the actual stacked page index instead of only inspecting shared objects.
    assert window.workspace.currentIndex() == results_row

    # 7. Confirm [GA Best] strategy appears in ranking table
    found_row = -1
    for row in range(window.results_table.table.rowCount()):
        item = window.results_table.table.item(row, 1)  # Name column
        if "[GA Best]" in item.text():
            found_row = row
            break
            
    assert found_row != -1, "GA strategy not found in Results ranking table."

    chart_updates = []
    original_set_data = window.results_chart.set_data

    def spy_set_data(*args, **kwargs):
        chart_updates.append((args, kwargs))
        return original_set_data(*args, **kwargs)

    monkeypatch.setattr(window.results_chart, "set_data", spy_set_data)

    # 8. Select [GA Best] strategy
    window.results_table.table.clearSelection()
    QTest.qWait(50)
    window.results_table.table.selectRow(found_row)
    QTest.qWait(100)

    # 9. Confirm equity/drawdown chart updates
    assert chart_updates, "Selecting the GA strategy did not update the equity chart."
