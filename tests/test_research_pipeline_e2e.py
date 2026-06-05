"""End-to-end research pipeline smoke test — Task 023A.

Covers: import → quality → split → backtest → stress → MC → WF → elimination.

Uses a small deterministic synthetic fixture.  No external files or large data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.models.strategy import Condition, Strategy, StrategyBlock
from data_engine.quality_checker import check_quality
from validation_engine.splitter import split_by_ratio
from backtest_engine.runner import run_backtest
from validation_engine.stress_test import stress_commission_multiplier
from validation_engine.monte_carlo import run_missed_trade_monte_carlo
from validation_engine.walk_forward import walk_forward
from validation_engine.elimination import EliminationConfig, evaluate_elimination


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


def _make_fixture(n_bars: int = 100) -> pd.DataFrame:
    """Deterministic synthetic OHLCV data with a mild uptrend."""
    rng = np.random.default_rng(123)
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
    close = 100.0 + np.cumsum(rng.normal(0.02, 0.5, n_bars))
    close = np.maximum(close, 10.0)
    noise = rng.uniform(0.3, 1.5, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open":  close - noise * 0.3,
        "high":  close + noise,
        "low":   close - noise,
        "close": close,
        "volume": rng.integers(500, 5000, n_bars),
    })


def _make_strategy() -> Strategy:
    return Strategy(
        name="e2e_smoke",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator="<"),
        ], logic="AND"),
    )


# ---------------------------------------------------------------------------
# End-to-end smoke test
# ---------------------------------------------------------------------------


def test_full_research_pipeline_e2e():
    """Walk the complete research pipeline and verify every step produces
    structured, valid output."""
    # ── 1. Import / normalize ───────────────────────────────────────────────
    df = _make_fixture(100)
    assert len(df) == 100
    assert list(df.columns) == ["datetime", "open", "high", "low", "close", "volume"]

    # ── 2. Quality check ────────────────────────────────────────────────────
    qr = check_quality(df, expected_freq_minutes=1)
    assert qr.passed
    assert qr.errors == []

    # ── 3. IS / Validation / OOS split ──────────────────────────────────────
    split = split_by_ratio(df, train_ratio=0.4, validation_ratio=0.3, oos_ratio=0.3)
    assert split.train is not None
    assert len(split.train) > 0
    assert split.validation is not None
    assert split.oos is not None
    # Verify no overlap.
    train_idx = set(split.train.index)
    val_idx = set(split.validation.index)
    oos_idx = set(split.oos.index)
    assert train_idx.isdisjoint(val_idx)
    assert train_idx.isdisjoint(oos_idx)

    # ── 4. Strategy ─────────────────────────────────────────────────────────
    strat = _make_strategy()

    # ── 5. Backtest (on train segment) ──────────────────────────────────────
    bt = run_backtest(strat, split.train, commission=2.0)
    assert isinstance(bt.metrics, dict)
    assert "total_trades" in bt.metrics
    assert "total_pnl" in bt.metrics
    assert bt.equity_curve is not None
    assert bt.drawdown_curve is not None

    # ── 6. Stress test (commission 2×) ──────────────────────────────────────
    stress = stress_commission_multiplier(strat, split.train, bt, multiplier=2.0)
    assert stress.test_name == "commission_2.0x"
    assert isinstance(stress.passed, bool)
    assert "total_pnl" in stress.stressed_metrics
    assert "total_pnl" in stress.degradation

    # ── 7. Monte Carlo (10 iterations, missed trades) ───────────────────────
    mc = run_missed_trade_monte_carlo(bt, iterations=10, base_seed=1)
    assert mc.iterations == 10
    assert len(mc.all_metrics) == 10 if bt.metrics["total_trades"] > 0 else True
    assert "total_pnl" in mc.percentile_summary or bt.metrics["total_trades"] == 0

    # ── 8. Walk-forward (small windows) ─────────────────────────────────────
    wf = walk_forward(strat, df, train_bars=30, test_bars=10)
    assert wf.window_count >= 1
    assert 0.0 <= wf.pass_rate <= 1.0
    for w in wf.windows:
        assert w.train_bars == 30
        assert w.test_bars == 10

    # ── 9. Elimination ──────────────────────────────────────────────────────
    config = EliminationConfig(
        min_trade_count=0,
        min_profit_factor=0.0,
        max_drawdown_pnl=1_000_000.0,
    )
    elim = evaluate_elimination(bt.metrics, config)
    assert elim.passed
    assert elim.failed_rules == []

    # ── 10. Determinism check ───────────────────────────────────────────────
    # Re-run and confirm identical results.
    bt2 = run_backtest(strat, split.train, commission=2.0)
    assert bt2.metrics["total_pnl"] == pytest.approx(bt.metrics["total_pnl"])
