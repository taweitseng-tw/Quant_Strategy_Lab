"""Tests for parameter perturbation stress test."""

import pandas as pd
import numpy as np
from core.models.strategy import Strategy, StrategyBlock, Condition, RiskManagement
from core.models.backtest_result import BacktestResult
from validation_engine.stress_test import stress_parameter_perturbation


def _make_df(size=100) -> pd.DataFrame:
    """Make dummy data."""
    dates = pd.date_range("2024-01-01 09:00", periods=size, freq="1min")
    return pd.DataFrame({
        "datetime": dates,
        "open": np.linspace(100, 200, size),
        "high": np.linspace(101, 201, size),
        "low": np.linspace(99, 199, size),
        "close": np.linspace(100.5, 200.5, size),
        "volume": np.ones(size) * 1000
    })


def _make_strategy() -> Strategy:
    return Strategy(
        name="test_strat",
        long_entry=StrategyBlock(
            conditions=[
                Condition(indicator="SMA", params={"period": 10, "threshold": 0.5}, operator=">"),
                Condition(indicator="TEST", params={"flag": True}, operator="==")
            ]
        ),
        risk_management=RiskManagement(stop_loss_ticks=10, take_profit_pct=0.05)
    )


def test_no_mutation_guarantee():
    """Verify the original strategy is not mutated during perturbation."""
    df = _make_df()
    strat = _make_strategy()
    
    baseline_metrics = {"total_pnl": 100.0, "total_trades": 10}
    baseline = BacktestResult(trades=[True]*10, metrics=baseline_metrics)  # type: ignore

    res = stress_parameter_perturbation(
        strategy=strat,
        df=df,
        baseline=baseline,
        variants_count=5
    )

    # Verify original parameters are exactly the same
    assert strat.long_entry.conditions[0].params["period"] == 10
    assert strat.long_entry.conditions[0].params["threshold"] == 0.5
    assert strat.long_entry.conditions[1].params["flag"] is True
    assert strat.risk_management.stop_loss_ticks == 10
    assert strat.risk_management.take_profit_pct == 0.05


from unittest.mock import MagicMock

def test_generator_shift_check(monkeypatch):
    """Verify parameters are shifted correctly."""
    df = _make_df()
    strat = _make_strategy()
    
    baseline_metrics = {"total_pnl": 100.0, "total_trades": 10}
    baseline = BacktestResult(trades=[True]*10, metrics=baseline_metrics)  # type: ignore

    # Mock the backtest runner so we can inspect the variants it gets
    mock_run = MagicMock()
    mock_run.return_value = BacktestResult(trades=[], metrics={"total_pnl": 90.0})
    monkeypatch.setattr("validation_engine.stress_test.run_backtest", mock_run)

    # Mock random to produce predictable shifts
    monkeypatch.setattr("validation_engine.stress_test.random.randint", lambda a, b: 2)
    monkeypatch.setattr("validation_engine.stress_test.random.random", lambda: 0.99) # Sign positive

    res = stress_parameter_perturbation(
        strategy=strat,
        df=df,
        baseline=baseline,
        variants_count=1,
        int_shift_range=(2, 2),
        float_shift_pct=0.10
    )

    assert mock_run.call_count == 1
    variant_strat = mock_run.call_args[0][0]
    
    # int period: 10 + 2 = 12
    assert variant_strat.long_entry.conditions[0].params["period"] == 12
    # float threshold: 0.5 * 1.10 = 0.55
    assert abs(variant_strat.long_entry.conditions[0].params["threshold"] - 0.55) < 1e-6
    # boolean flag untouched
    assert variant_strat.long_entry.conditions[1].params["flag"] is True
    # int SL ticks: 10 + 2 = 12
    assert variant_strat.risk_management.stop_loss_ticks == 12
    # float TP pct: 0.05 * 1.10 = 0.055
    assert abs(variant_strat.risk_management.take_profit_pct - 0.055) < 1e-6


def test_robust_strategy_survival(monkeypatch):
    """If all variants return similar PnL, test passes."""
    df = _make_df()
    strat = _make_strategy()
    
    baseline_metrics = {"total_pnl": 100.0, "total_trades": 10}
    baseline = BacktestResult(trades=[True]*10, metrics=baseline_metrics)  # type: ignore

    mock_run = MagicMock()
    # Variants return 100, 95, 105, 100, 100 -> avg 100
    mock_run.side_effect = [
        BacktestResult(trades=[], metrics={"total_pnl": 100.0}),
        BacktestResult(trades=[], metrics={"total_pnl": 95.0}),
        BacktestResult(trades=[], metrics={"total_pnl": 105.0}),
        BacktestResult(trades=[], metrics={"total_pnl": 100.0}),
        BacktestResult(trades=[], metrics={"total_pnl": 100.0}),
    ]
    monkeypatch.setattr("validation_engine.stress_test.run_backtest", mock_run)

    res = stress_parameter_perturbation(
        strategy=strat,
        df=df,
        baseline=baseline,
        variants_count=5,
        degradation_threshold=0.50
    )

    assert res.passed is True
    assert res.degradation["total_pnl"] == 0.0


def test_overfit_strategy_collapse(monkeypatch):
    """If average variant drops below threshold, test fails."""
    df = _make_df()
    strat = _make_strategy()
    
    baseline_metrics = {"total_pnl": 100.0, "total_trades": 10}
    baseline = BacktestResult(trades=[True]*10, metrics=baseline_metrics)  # type: ignore

    mock_run = MagicMock()
    # Variants collapse completely: 10, -5, 20, 0, -25 -> avg 0
    mock_run.side_effect = [
        BacktestResult(trades=[], metrics={"total_pnl": 10.0}),
        BacktestResult(trades=[], metrics={"total_pnl": -5.0}),
        BacktestResult(trades=[], metrics={"total_pnl": 20.0}),
        BacktestResult(trades=[], metrics={"total_pnl": 0.0}),
        BacktestResult(trades=[], metrics={"total_pnl": -25.0}),
    ]
    monkeypatch.setattr("validation_engine.stress_test.run_backtest", mock_run)

    res = stress_parameter_perturbation(
        strategy=strat,
        df=df,
        baseline=baseline,
        variants_count=5,
        degradation_threshold=0.50
    )

    assert res.passed is False
    assert res.degradation["total_pnl"] == -1.0 # 100 to 0 is -100%
