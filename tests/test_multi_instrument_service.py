"""Tests for MultiInstrumentBacktestService — Task 032B.

These tests verify the service-layer orchestrator that runs one
:class:`Strategy` across multiple (DataFrame, instrument-profile) pairs
by reusing :func:`backtest_engine.runner.run_backtest` without modifying
the engine.

Coverage:

* end-to-end success across multiple instruments
* deterministic input ordering
* per-instrument metrics forwarding
* aggregate metrics computed from successful runs only
* empty-input safety
* one failure must not stop the rest
* input DataFrames must not be mutated
* NaN / infinite profit_factor values must be excluded from the mean
* the service module does not import PySide6 (engine passivity)
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.services.multi_instrument_service import (
    InstrumentBacktestInput,
    MultiInstrumentBacktestResult,
    PerInstrumentBacktestResult,
    run_multi_instrument_backtest,
)
from core.models.instrument import InstrumentProfile
from core.models.strategy import Condition, Strategy, StrategyBlock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_uptrend_df(n_bars: int = 50) -> pd.DataFrame:
    """Create normalized OHLCV data with a clean uptrend (close always rising)."""
    rng = np.random.default_rng(42)
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
    close = np.linspace(100.0, 150.0, n_bars)
    noise = rng.uniform(0.5, 2.0, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open":  close - noise * 0.3,
        "high":  close + noise,
        "low":   close - noise,
        "close": close,
        "volume": rng.integers(1000, 5000, n_bars),
    })


def _make_downtrend_df(n_bars: int = 50) -> pd.DataFrame:
    """Create normalized OHLCV data with a clean downtrend."""
    rng = np.random.default_rng(7)
    times = pd.date_range("2024-02-01 09:00", periods=n_bars, freq="1min")
    close = np.linspace(150.0, 100.0, n_bars)
    noise = rng.uniform(0.5, 2.0, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open":  close + noise * 0.3,
        "high":  close + noise,
        "low":   close - noise,
        "close": close,
        "volume": rng.integers(1000, 5000, n_bars),
    })


def _make_flat_then_jump_df(n_bars: int = 50) -> pd.DataFrame:
    """Flat then jump — produces reliable SMA cross signals."""
    times = pd.date_range("2024-03-01 09:00", periods=n_bars, freq="1min")
    close = [100.0] * 10 + [120.0] * (n_bars - 10)
    return pd.DataFrame({
        "datetime": times,
        "open":  [c - 1.0 for c in close],
        "high":  [c + 1.0 for c in close],
        "low":   [c - 2.0 for c in close],
        "close": close,
        "volume": [1000] * n_bars,
    })


def _make_simple_long_strategy(sma_period: int = 5) -> Strategy:
    """Close > SMA(N) → long entry; Close < SMA(N) → long exit."""
    return Strategy(
        name="test_sma_cross",
        long_entry=StrategyBlock(
            conditions=[
                Condition(indicator="SMA", params={"period": sma_period}, operator=">"),
            ],
            logic="AND",
        ),
        long_exit=StrategyBlock(
            conditions=[
                Condition(indicator="SMA", params={"period": sma_period}, operator="<"),
            ],
            logic="AND",
        ),
    )


def _corrupt_df_missing_columns() -> pd.DataFrame:
    """DataFrame missing required OHLCV columns — engine will raise."""
    return pd.DataFrame({
        "datetime": pd.date_range("2024-01-02 08:30", periods=5, freq="1min"),
        "price": [1.0, 2.0, 3.0, 4.0, 5.0],
    })


# ---------------------------------------------------------------------------
# End-to-end success
# ---------------------------------------------------------------------------


def test_multi_instrument_runs_all_inputs():
    """One strategy, two instruments → both succeed and result is complete."""
    strat = _make_simple_long_strategy(sma_period=5)
    inputs = [
        InstrumentBacktestInput(label="ES", df=_make_uptrend_df(60), instrument=None),
        InstrumentBacktestInput(label="NQ", df=_make_downtrend_df(60), instrument=None),
    ]
    result = run_multi_instrument_backtest(strat, inputs)

    assert isinstance(result, MultiInstrumentBacktestResult)
    assert result.instrument_count == 2
    assert result.success_count == 2
    assert result.failure_count == 0
    assert len(result.per_instrument) == 2
    for r in result.per_instrument:
        assert isinstance(r, PerInstrumentBacktestResult)
        assert r.success is True
        assert r.error_message is None
        # Standard metrics must be present.
        assert "total_pnl" in r.metrics
        assert "total_trades" in r.metrics
        assert "profit_factor" in r.metrics
        assert "max_drawdown_pnl" in r.metrics


# ---------------------------------------------------------------------------
# Deterministic ordering
# ---------------------------------------------------------------------------


def test_multi_instrument_preserves_input_order():
    """The per_instrument list must mirror input order exactly."""
    strat = _make_simple_long_strategy(sma_period=5)
    inputs = [
        InstrumentBacktestInput(label="alpha", df=_make_uptrend_df(60)),
        InstrumentBacktestInput(label="beta", df=_make_flat_then_jump_df(60)),
        InstrumentBacktestInput(label="gamma", df=_make_downtrend_df(60)),
    ]
    result = run_multi_instrument_backtest(strat, inputs)

    labels = [r.label for r in result.per_instrument]
    assert labels == ["alpha", "beta", "gamma"]


# ---------------------------------------------------------------------------
# Per-instrument metrics are passed through
# ---------------------------------------------------------------------------


def test_multi_instrument_returns_per_instrument_metrics():
    """Successful runs must carry the BacktestResult metrics dict."""
    strat = _make_simple_long_strategy(sma_period=5)
    inputs = [
        InstrumentBacktestInput(label="ES", df=_make_uptrend_df(60)),
    ]
    result = run_multi_instrument_backtest(strat, inputs)

    assert result.per_instrument[0].success
    m = result.per_instrument[0].metrics
    # All standard metric keys are exposed.
    for k in (
        "total_trades",
        "winning_trades",
        "losing_trades",
        "win_rate",
        "total_pnl",
        "avg_trade",
        "gross_profit",
        "gross_loss",
        "profit_factor",
        "max_drawdown_pnl",
    ):
        assert k in m, f"missing metric {k}"


# ---------------------------------------------------------------------------
# Aggregates ignore failed instruments
# ---------------------------------------------------------------------------


def test_multi_instrument_aggregate_metrics_success_only():
    """Aggregates must use only successful runs."""
    strat = _make_simple_long_strategy(sma_period=5)
    inputs = [
        InstrumentBacktestInput(label="good_A", df=_make_uptrend_df(60)),
        InstrumentBacktestInput(label="bad",   df=_corrupt_df_missing_columns()),
        InstrumentBacktestInput(label="good_B", df=_make_downtrend_df(60)),
    ]
    result = run_multi_instrument_backtest(strat, inputs)

    assert result.instrument_count == 3
    assert result.success_count == 2
    assert result.failure_count == 1

    # Failed instrument must be reported as a failure.
    failed = [r for r in result.per_instrument if not r.success]
    assert len(failed) == 1
    assert failed[0].label == "bad"
    assert failed[0].error_message is not None
    assert failed[0].metrics == {}
    assert failed[0].warnings == []

    # Aggregate metrics must exist and be numeric where required.
    agg = result.aggregate_metrics
    for k in (
        "total_trades_sum",
        "mean_total_pnl",
        "median_total_pnl",
        "min_total_pnl",
        "max_total_pnl",
        "worst_max_drawdown_pnl",
        "mean_profit_factor",
    ):
        assert k in agg, f"missing aggregate key {k}"

    # total_trades_sum is the sum of the two successful runs.
    expected_trades = sum(
        r.metrics["total_trades"]
        for r in result.per_instrument
        if r.success
    )
    assert agg["total_trades_sum"] == expected_trades

    # mean_total_pnl is the mean of the two successful runs.
    expected_mean = float(np.mean([
        r.metrics["total_pnl"]
        for r in result.per_instrument
        if r.success
    ]))
    assert agg["mean_total_pnl"] == pytest.approx(expected_mean)

    # median_total_pnl is the median of the two successful runs.
    expected_median = float(np.median([
        r.metrics["total_pnl"]
        for r in result.per_instrument
        if r.success
    ]))
    assert agg["median_total_pnl"] == pytest.approx(expected_median)

    # A failure warning is recorded.
    assert any("failed" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# Empty input list
# ---------------------------------------------------------------------------


def test_multi_instrument_empty_input_safe_result():
    """An empty input list must yield a structured safe result, not crash."""
    strat = _make_simple_long_strategy(sma_period=5)
    result = run_multi_instrument_backtest(strat, [])

    assert isinstance(result, MultiInstrumentBacktestResult)
    assert result.instrument_count == 0
    assert result.success_count == 0
    assert result.failure_count == 0
    assert result.per_instrument == []

    # Safe empty aggregate values.
    agg = result.aggregate_metrics
    assert agg["total_trades_sum"] == 0
    assert agg["mean_total_pnl"] == 0.0
    assert agg["median_total_pnl"] == 0.0
    assert agg["min_total_pnl"] == 0.0
    assert agg["max_total_pnl"] == 0.0
    assert agg["worst_max_drawdown_pnl"] == 0.0
    assert agg["mean_profit_factor"] is None

    # A warning is recorded.
    assert any("empty" in w.lower() for w in result.warnings)
    # Assumptions dict is still populated.
    assert "engine" in result.assumptions
    assert result.assumptions["engine"] == "backtest_engine.runner.run_backtest"


# ---------------------------------------------------------------------------
# One failure does not stop the others
# ---------------------------------------------------------------------------


def test_multi_instrument_one_failure_does_not_stop_others():
    """A bad input in the middle of the list must not stop later runs."""
    strat = _make_simple_long_strategy(sma_period=5)
    inputs = [
        InstrumentBacktestInput(label="A", df=_make_uptrend_df(60)),
        InstrumentBacktestInput(label="B_bad", df=_corrupt_df_missing_columns()),
        InstrumentBacktestInput(label="C", df=_make_flat_then_jump_df(60)),
    ]
    result = run_multi_instrument_backtest(strat, inputs)

    assert result.instrument_count == 3
    assert result.success_count == 2
    assert result.failure_count == 1
    assert [r.label for r in result.per_instrument] == ["A", "B_bad", "C"]
    assert result.per_instrument[0].success is True
    assert result.per_instrument[1].success is False
    assert result.per_instrument[2].success is True
    # The later successful run still has metrics.
    assert "total_pnl" in result.per_instrument[2].metrics


# ---------------------------------------------------------------------------
# Input DataFrames are not mutated
# ---------------------------------------------------------------------------


def test_multi_instrument_does_not_mutate_input_dataframes():
    """Running backtests across many DataFrames must leave them unchanged."""
    strat = _make_simple_long_strategy(sma_period=5)
    df_a = _make_uptrend_df(60)
    df_b = _make_downtrend_df(60)

    # Snapshot the DataFrames.
    snap_a = df_a.copy()
    snap_b = df_b.copy()

    inputs = [
        InstrumentBacktestInput(label="A", df=df_a),
        InstrumentBacktestInput(label="B", df=df_b),
    ]
    run_multi_instrument_backtest(strat, inputs)

    # Compare values, dtypes and column lists.
    pd.testing.assert_frame_equal(df_a, snap_a)
    pd.testing.assert_frame_equal(df_b, snap_b)
    assert list(df_a.columns) == list(snap_a.columns)
    assert list(df_b.columns) == list(snap_b.columns)


# ---------------------------------------------------------------------------
# NaN / inf profit_factor handling
# ---------------------------------------------------------------------------


def test_multi_instrument_mean_profit_factor_ignores_nan_inf(monkeypatch):
    """NaN and inf profit_factor values must be excluded from the mean."""

    # Build a list of (label, fake_metrics) and patch _run_single to return
    # pre-canned PerInstrumentBacktestResult objects.  This isolates the
    # aggregation logic from the engine.
    from app.services import multi_instrument_service as svc

    canned_results = [
        PerInstrumentBacktestResult(
            label="A", success=True,
            metrics={
                "total_pnl": 100.0,
                "total_trades": 5,
                "profit_factor": 2.0,
                "max_drawdown_pnl": 10.0,
            },
        ),
        PerInstrumentBacktestResult(
            label="B", success=True,
            metrics={
                "total_pnl": 200.0,
                "total_trades": 4,
                "profit_factor": float("nan"),
                "max_drawdown_pnl": 5.0,
            },
        ),
        PerInstrumentBacktestResult(
            label="C", success=True,
            metrics={
                "total_pnl": 50.0,
                "total_trades": 3,
                "profit_factor": float("inf"),
                "max_drawdown_pnl": 7.0,
            },
        ),
        PerInstrumentBacktestResult(
            label="D", success=True,
            metrics={
                "total_pnl": 75.0,
                "total_trades": 2,
                "profit_factor": 4.0,  # Only this one and A should count.
                "max_drawdown_pnl": 2.0,
            },
        ),
    ]

    def fake_run_single(*, strategy, spec, initial_capital, commission,
                        slippage_ticks, tick_size, point_value):
        return next(r for r in canned_results if r.label == spec.label)

    monkeypatch.setattr(svc, "_run_single", fake_run_single)

    strat = _make_simple_long_strategy(sma_period=5)
    inputs = [InstrumentBacktestInput(label=r.label, df=_make_uptrend_df(60))
              for r in canned_results]
    result = run_multi_instrument_backtest(strat, inputs)

    agg = result.aggregate_metrics
    # mean of {2.0, 4.0} = 3.0 (NaN and inf excluded).
    assert agg["mean_profit_factor"] == pytest.approx(3.0)

    # total_trades_sum is the sum of all four successful runs.
    assert agg["total_trades_sum"] == 5 + 4 + 3 + 2

    # mean_total_pnl uses only numeric values.
    expected_mean = (100.0 + 200.0 + 50.0 + 75.0) / 4
    assert agg["mean_total_pnl"] == pytest.approx(expected_mean)

    # median_total_pnl uses only numeric values (median of 50, 75, 100, 200 is 87.5).
    assert agg["median_total_pnl"] == pytest.approx(87.5)

    # worst_max_drawdown_pnl is the max of {10.0, 5.0, 7.0, 2.0} -> 10.0.
    assert agg["worst_max_drawdown_pnl"] == 10.0

    # A warning must mention the exclusion.
    assert any("profit_factor" in w.lower() for w in result.warnings)

    # Sanity: confirm the constants we used are actually non-finite.
    assert math.isnan(float("nan"))
    assert math.isinf(float("inf"))


# ---------------------------------------------------------------------------
# Engine passivity — service must not import PySide6
# ---------------------------------------------------------------------------


def test_multi_instrument_module_has_no_pyside_import():
    """The service must remain engine-pure (no GUI imports)."""
    module_path = Path(__file__).resolve().parent.parent / "app" / "services" / "multi_instrument_service.py"
    assert module_path.exists()

    # Only scan non-docstring lines for forbidden tokens to avoid matching
    # tokens that legitimately appear in comments / docstrings.
    raw_lines = module_path.read_text(encoding="utf-8").splitlines()
    in_docstring = False
    code_lines: list[str] = []
    for line in raw_lines:
        stripped = line.strip()
        # Toggle docstring tracking on triple-quote boundaries.
        if '"""' in stripped:
            # Count occurrences; odd count = entering/leaving docstring block.
            count = stripped.count('"""')
            if count % 2 == 1:
                in_docstring = not in_docstring
            # Even count of triple-quotes on a single line → self-contained
            # docstring; stay in whatever state we were in.
            continue
        if in_docstring:
            continue
        # Drop leading comments so we only inspect code.
        if stripped.startswith("#"):
            continue
        code_lines.append(line)

    code_blob = "\n".join(code_lines).lower()
    forbidden = ("pyside6", "pyqt5", "pyqt6", "qwidget", "qmainwindow", "qtcore")
    for token in forbidden:
        assert token not in code_blob, f"forbidden GUI import / symbol found: {token}"

    # And double-check the actual module object after import.
    mod = sys.modules.get("app.services.multi_instrument_service")
    assert mod is not None
    assert not hasattr(mod, "QWidget")
    assert not hasattr(mod, "QtCore")


# ---------------------------------------------------------------------------
# Assumptions are recorded
# ---------------------------------------------------------------------------


def test_multi_instrument_assumptions_recorded():
    """The MultiInstrumentBacktestResult.assumptions dict is populated."""
    strat = _make_simple_long_strategy(sma_period=5)
    inputs = [
        InstrumentBacktestInput(label="ES", df=_make_uptrend_df(60)),
    ]
    result = run_multi_instrument_backtest(
        strat, inputs, initial_capital=50_000.0, commission=2.0
    )

    a = result.assumptions
    assert a["execution_model"] == "next_bar_open"
    assert a["same_bar_ambiguity"] == "stop_loss_first"
    assert a["position_model"] == "single_position"
    assert a["initial_capital"] == 50_000.0
    assert a["commission_per_side"] == 2.0
    assert a["input_count"] == 1
    assert a["engine"] == "backtest_engine.runner.run_backtest"


# ---------------------------------------------------------------------------
# InstrumentProfile is honored by the underlying engine
# ---------------------------------------------------------------------------


def test_multi_instrument_instrument_profile_scales_pnl():
    """Two instruments with different point_value must produce scaled PnL."""
    strat = _make_simple_long_strategy(sma_period=5)
    pv1 = _make_uptrend_df(60)
    pv50 = _make_uptrend_df(60)

    inputs = [
        InstrumentBacktestInput(
            label="pv1",
            df=pv1,
            instrument=InstrumentProfile(symbol="X", point_value=1.0),
        ),
        InstrumentBacktestInput(
            label="pv50",
            df=pv50,
            instrument=InstrumentProfile(symbol="X", point_value=50.0),
        ),
    ]
    result = run_multi_instrument_backtest(strat, inputs, commission=0.0)

    assert result.success_count == 2
    by_label = {r.label: r for r in result.per_instrument}
    pnl_1 = by_label["pv1"].metrics["total_pnl"]
    pnl_50 = by_label["pv50"].metrics["total_pnl"]

    if pnl_1 != 0.0:
        assert pnl_50 / pnl_1 == pytest.approx(50.0)
