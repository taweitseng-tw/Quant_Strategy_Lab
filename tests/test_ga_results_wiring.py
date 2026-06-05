"""Tests for GA Results page integration — Task 031F.

Verifies that:
- StrategyService accepts injected_strategies and appends them.
- MainWindow _on_ga_success stores the latest GA strategy with a [GA Best] prefix.
- MainWindow _refresh_results_ranking injects the GA strategy into the Results ranking table.
"""

from __future__ import annotations

import os
import sys
import pandas as pd
import pytest

from core.models.strategy import Strategy, StrategyBlock, Condition

# Skip entire module if display is unavailable (headless CI).
pytestmark = pytest.mark.skipif(
    sys.platform != "win32" and not os.environ.get("DISPLAY"),
    reason="Requires display or Windows",
)

# ---------------------------------------------------------------------------
# Service level tests
# ---------------------------------------------------------------------------

def test_strategy_service_injects_ga_strategy():
    """StrategyService must append injected strategies to the random ranking pool."""
    from app.services.strategy_service import StrategyService
    
    svc = StrategyService()
    df = svc.generate_deterministic_mock_ohlcv(count=100)
    
    ga_strat = Strategy(
        name="[GA Best] injected_strat",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">")
        ])
    )
    
    ranked, is_mock = svc.get_ranked_strategies(dataset_df=df, injected_strategies=[ga_strat])
    
    # Normally 10 strategies are generated. With 1 injected, there should be 11.
    assert len(ranked) == 11
    
    # Verify the injected strategy is in the list
    found = any(item["strategy"].name == "[GA Best] injected_strat" for item in ranked)
    assert found is True
    
    # Verify provenance was set
    for item in ranked:
        if item["strategy"].name == "[GA Best] injected_strat":
            assert item["provenance"].get("generator") == "ga_search"
            assert item["provenance"].get("source_type") == "ga_evolved"
            assert item["provenance"].get("injected_strategy") is True
            assert item["provenance"].get("strategy_name") == "[GA Best] injected_strat"

# ---------------------------------------------------------------------------
# UI integration tests
# ---------------------------------------------------------------------------

def test_main_window_on_ga_success_injects_result(monkeypatch):
    """MainWindow must store GA result and display it on the Results page."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow
    from app.services.ga_service import GASearchResult

    window = MainWindow()
    
    ga_strat = Strategy(
        name="test_ga_strat",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 15}, operator=">"),
        ])
    )
    
    # Create a mock result
    result = GASearchResult(
        best_strategy=ga_strat,
        best_score=0.9999,
        generation_count=5,
        final_population_size=10,
    )
    
    # Simulate a successful GA run
    window._on_ga_success(result, source_label="Test Source")
    
    # 1. State should be stored with [GA Best] prefix
    assert hasattr(window, "_latest_ga_strategy")
    assert window._latest_ga_strategy.name == "[GA Best] test_ga_strat"
    
    # 2. Results page summary label should be populated
    text = window.ga_results_summary_label.text()
    assert "[GA Best] test_ga_strat" in text
    assert "0.9999" in text
    assert "Test Source" in text
    
    # 3. Strategy should be in the ranking table
    found = False
    for i in range(window.results_table.table.rowCount()):
        item = window.results_table.table.item(i, 1)  # Name column
        if "[GA Best] test_ga_strat" in item.text():
            found = True
            break
            
    assert found is True


def test_main_window_ga_summary_escapes_rich_text(monkeypatch):
    """GA summary label must escape dynamic text inside rich-text markup."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow
    from app.services.ga_service import GASearchResult

    window = MainWindow()
    ga_strat = Strategy(
        name="<img src=x onerror=alert(1)>",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 15}, operator=">"),
        ])
    )
    result = GASearchResult(
        best_strategy=ga_strat,
        best_score=0.5,
        generation_count=1,
        final_population_size=2,
    )

    window._on_ga_success(result, source_label="<script>alert(1)</script>")
    text = window.ga_results_summary_label.text()

    assert "<img src=x onerror=alert(1)>" not in text
    assert "<script>alert(1)</script>" not in text
    assert "&lt;img src=x onerror=alert(1)&gt;" in text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in text
