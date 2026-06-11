"""Tests for Run button validation pipeline wiring — Task 025."""

from __future__ import annotations

import sys
import pytest
from PySide6.QtWidgets import QApplication

from app.services.validation_pipeline_service import PipelineResult, run_validation_pipeline


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


# ---------------------------------------------------------------------------
# Service path tests (no UI needed)
# ---------------------------------------------------------------------------


def test_run_action_calls_service_path():
    """The validation pipeline service must be callable with mock data."""
    import numpy as np
    import pandas as pd
    from core.models.strategy import Condition, Strategy, StrategyBlock
    from app.services.validation_pipeline_service import PipelineConfig

    # Simulate what _handle_run does — call the service with mock data.
    rng = np.random.default_rng(42)
    times = pd.date_range("2024-01-02", periods=200, freq="1min")
    df = pd.DataFrame({
        "datetime": times,
        "open":  100.0 + rng.normal(0, 1, 200).cumsum(),
        "high":  102.0 + rng.normal(0, 1, 200).cumsum(),
        "low":   98.0 + rng.normal(0, 1, 200).cumsum(),
        "close": 101.0 + rng.normal(0, 1, 200).cumsum(),
        "volume": rng.integers(500, 5000, 200),
    })

    strategy = Strategy(
        name="test_run",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator="<"),
        ], logic="AND"),
    )

    result = run_validation_pipeline(
        df, strategy,
        config=PipelineConfig(mc_iterations=10),
        commission=2.0,
    )

    assert isinstance(result, PipelineResult)
    assert result.baseline_metrics is not None
    assert result.stress_results is not None
    assert result.monte_carlo_summary is not None


def test_run_result_stores_expected_sections():
    """Result must contain all sections that _handle_run logs."""
    import numpy as np
    import pandas as pd
    from core.models.strategy import Condition, Strategy, StrategyBlock
    from app.services.validation_pipeline_service import PipelineConfig

    rng = np.random.default_rng(99)
    times = pd.date_range("2024-01-02", periods=200, freq="1min")
    df = pd.DataFrame({
        "datetime": times,
        "open":  rng.normal(100, 1, 200).cumsum() + 100,
        "high":  rng.normal(102, 1, 200).cumsum() + 102,
        "low":   rng.normal(98, 1, 200).cumsum() + 98,
        "close": rng.normal(101, 1, 200).cumsum() + 101,
        "volume": rng.integers(500, 5000, 200),
    })

    strategy = Strategy(
        name="store_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator="<"),
        ], logic="AND"),
    )

    result = run_validation_pipeline(df, strategy, commission=2.0)

    # Verify all sections that _handle_run references.
    assert isinstance(result.split_metadata, dict)
    assert isinstance(result.baseline_metrics, dict)
    assert "total_pnl" in result.baseline_metrics
    assert "profit_factor" in result.baseline_metrics
    assert "total_trades" in result.baseline_metrics
    assert isinstance(result.stress_results, list)
    assert len(result.stress_results) >= 1
    assert result.monte_carlo_summary is not None
    assert "worst_case" in result.monte_carlo_summary
    assert result.walk_forward_summary is not None
    assert "pass_rate" in result.walk_forward_summary
    assert result.elimination_result is not None
    assert "passed" in result.elimination_result


def test_mock_fallback_is_labeled():
    """Mock data via generate_deterministic_mock_ohlcv must be distinguishable."""
    import pandas as pd
    from app.services.strategy_service import StrategyService

    svc = StrategyService()
    mock_df = svc.generate_deterministic_mock_ohlcv(seed=42, count=100)

    assert len(mock_df) == 100
    assert list(mock_df.columns) == ["datetime", "open", "high", "low", "close", "volume"]
    # Mock data uses daily dates starting 2026-01-01 — distinct from 1-min data.
    assert mock_df["datetime"].iloc[0] == pd.Timestamp("2026-01-01")


def test_validation_pipeline_error_is_surfaced():
    """An invalid call (empty DataFrame) must raise from the service."""
    import pandas as pd
    from core.models.strategy import Condition, Strategy, StrategyBlock

    df = pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])
    strategy = Strategy(
        name="error_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator="<"),
        ], logic="AND"),
    )

    with pytest.raises(Exception):
        run_validation_pipeline(df, strategy, commission=2.0)


def test_pipeline_config_receives_elimination_config():
    """PipelineConfig must accept an EliminationConfig and serialize it."""
    from app.services.validation_pipeline_service import PipelineConfig
    from validation_engine.elimination import EliminationConfig

    elim = EliminationConfig(min_profit_factor=1.5, max_drawdown_pnl=10000.0)
    cfg = PipelineConfig(
        mc_iterations=5,
        elimination_config=elim,
    )
    d = cfg.to_dict()
    assert d["elimination_config"] is not None
    assert d["elimination_config"]["min_profit_factor"] == 1.5
    assert d["elimination_config"]["max_drawdown_pnl"] == 10000.0
    assert d["elimination_config"]["min_trade_count"] is None


def test_pipeline_config_elimination_config_defaults_to_none():
    """PipelineConfig without elimination_config must serialize to None."""
    from app.services.validation_pipeline_service import PipelineConfig

    cfg = PipelineConfig(mc_iterations=5)
    d = cfg.to_dict()
    assert d["elimination_config"] is None
