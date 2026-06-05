"""Tests for Walk-forward Matrix integration in validation pipeline and reports."""

from __future__ import annotations

import pytest
import pandas as pd
import numpy as np

from core.models.strategy import Condition, Strategy, StrategyBlock
from core.models.backtest_result import BacktestResult
from app.services.validation_pipeline_service import (
    PipelineConfig,
    run_validation_pipeline,
)
from reports.generator import generate_markdown_report, generate_html_report


def _make_df(n_bars: int = 300) -> pd.DataFrame:
    rng = np.random.default_rng(123)
    times = pd.date_range("2024-01-02 08:30", periods=n_bars, freq="1min")
    close = 100.0 + np.cumsum(rng.normal(0.01, 0.4, n_bars))
    close = np.maximum(close, 10.0)
    noise = rng.uniform(0.2, 1.0, n_bars)
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
        name="wf_matrix_test_strat",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">"),
        ], logic="AND"),
    )


def test_matrix_disabled_by_default():
    df = _make_df(200)
    strat = _make_strategy()
    cfg = PipelineConfig()
    assert not cfg.run_matrix
    
    result = run_validation_pipeline(df, strat, config=cfg)
    assert result.walk_forward_matrix_summary is None


def test_matrix_enabled_produces_summary():
    df = _make_df(300)
    strat = _make_strategy()
    cfg = PipelineConfig(
        run_matrix=True,
        matrix_train_bars_list=[50, 60],
        matrix_test_bars_list=[20],
        matrix_step_bars_list=[20]
    )
    
    result = run_validation_pipeline(df, strat, config=cfg)
    
    m_summary = result.walk_forward_matrix_summary
    assert m_summary is not None
    assert isinstance(m_summary, dict)
    assert m_summary["config_count"] == 2
    assert m_summary["tested_count"] > 0
    assert "insufficient_data_count" in m_summary
    assert "insufficient_data_configs" in m_summary
    assert "best_pass_rate_config" in m_summary
    assert m_summary["assumptions"]["method"] == "walk_forward_matrix"


def test_matrix_report_integration():
    df = _make_df(300)
    strat = _make_strategy()
    
    cfg = PipelineConfig(
        run_matrix=True,
        matrix_train_bars_list=[50],
        matrix_test_bars_list=[20],
    )
    vr = run_validation_pipeline(df, strat, config=cfg)
    
    mock_result = BacktestResult(
        metrics={"total_pnl": 100.0, "profit_factor": 1.5, "win_rate": 0.5, "total_trades": 10},
        assumptions={},
        trades=[]
    )
    
    # Generate reports
    md = generate_markdown_report(strat, mock_result, validation_result=vr.__dict__)
    html_out = generate_html_report(strat, mock_result, validation_result=vr.__dict__)
    
    assert "- **WF Matrix**:" in md
    assert "configs tested" in md
    assert "insufficient=" in md
    assert "Best=wf_matrix_" in md
    
    assert "<b>WF Matrix:</b>" in html_out
    assert "configs tested" in html_out
    assert "insufficient=" in html_out
    assert "Best=wf_matrix_" in html_out


def test_matrix_report_integration_disabled_does_not_crash():
    df = _make_df(100)
    strat = _make_strategy()
    
    cfg = PipelineConfig(run_matrix=False)
    vr = run_validation_pipeline(df, strat, config=cfg)
    
    mock_result = BacktestResult(
        metrics={"total_pnl": 100.0, "profit_factor": 1.5, "win_rate": 0.5, "total_trades": 10},
        assumptions={},
        trades=[]
    )
    
    md = generate_markdown_report(strat, mock_result, validation_result=vr.__dict__)
    html_out = generate_html_report(strat, mock_result, validation_result=vr.__dict__)
    
    assert "WF Matrix" not in md
    assert "WF Matrix" not in html_out


def test_matrix_pipeline_output_is_deterministic():
    df = _make_df(300)
    strat = _make_strategy()
    cfg = PipelineConfig(
        run_matrix=True,
        matrix_train_bars_list=[50, 60],
        matrix_test_bars_list=[20],
        matrix_step_bars_list=[20],
    )

    first = run_validation_pipeline(df, strat, config=cfg)
    second = run_validation_pipeline(df, strat, config=cfg)

    assert first.walk_forward_matrix_summary == second.walk_forward_matrix_summary


def test_walk_forward_matrix_still_works_with_enhanced_walk_forward_result():
    """Ensure that walk_forward_matrix works perfectly with the new stability_score and pass_criteria parameters."""
    df = _make_df(300)
    strat = _make_strategy()
    
    # We pass matrix backtest kwargs that walk_forward natively supports
    from validation_engine.walk_forward_matrix import walk_forward_matrix
    
    matrix_res = walk_forward_matrix(
        strat, df,
        train_bars_list=[50],
        test_bars_list=[20],
        step_bars_list=[20],
        pass_criteria={"min_total_pnl": 0.0}
    )
    
    assert matrix_res.config_count == 1
    # Check that it handled the walk_forward result without crashing
    cfg_res = matrix_res.configs[0]
    assert cfg_res.window_count > 0
    # Stability score itself doesn't strictly need to be bubbled up to matrix yet,
    # just confirming that having it in walk_forward doesn't break matrix.
    assert hasattr(cfg_res, "pass_rate")
