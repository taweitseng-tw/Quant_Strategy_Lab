"""Tests for walk-forward matrix engine — Task 030A."""

from __future__ import annotations

import numpy as np
import pandas as pd

from core.models.strategy import Condition, Strategy, StrategyBlock
from validation_engine.walk_forward import walk_forward
from validation_engine.walk_forward_matrix import (
    WalkForwardMatrixConfigResult,
    WalkForwardMatrixSummary,
    walk_forward_matrix,
)


def _make_test_df(n_bars: int = 240) -> pd.DataFrame:
    rng = np.random.default_rng(123)
    times = pd.date_range("2026-01-01 09:00", periods=n_bars, freq="1min")
    close = 100.0 + np.cumsum(rng.normal(0.03, 0.4, n_bars))
    close = np.maximum(close, 10.0)
    spread = rng.uniform(0.2, 1.0, n_bars)
    return pd.DataFrame({
        "datetime": times,
        "open": close - spread * 0.2,
        "high": close + spread,
        "low": close - spread,
        "close": close,
        "volume": rng.integers(100, 1000, n_bars),
    })


def _make_sma_strategy(period: int = 8) -> Strategy:
    return Strategy(
        name="wf_matrix_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": period}, operator=">"),
        ]),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": period}, operator="<"),
        ]),
    )


def test_walk_forward_matrix_runs_multiple_configurations() -> None:
    df = _make_test_df()
    strat = _make_sma_strategy()

    result = walk_forward_matrix(
        strat,
        df,
        train_bars_list=[60, 80],
        test_bars_list=[20, 30],
        step_bars_list=[20],
    )

    assert isinstance(result, WalkForwardMatrixSummary)
    assert result.config_count == 4
    assert len(result.configs) == 4
    assert all(isinstance(cfg, WalkForwardMatrixConfigResult) for cfg in result.configs)
    assert result.tested_count == 4


def test_walk_forward_matrix_matches_single_walk_forward_behavior() -> None:
    df = _make_test_df()
    strat = _make_sma_strategy()

    matrix = walk_forward_matrix(
        strat,
        df,
        train_bars_list=[60],
        test_bars_list=[20],
        step_bars_list=[20],
    )
    single = walk_forward(strat, df, train_bars=60, test_bars=20, step_bars=20)

    cfg = matrix.configs[0]
    assert cfg.window_count == single.window_count
    assert cfg.pass_count == single.pass_count
    assert cfg.pass_rate == single.pass_rate
    assert cfg.aggregate_metrics == single.aggregate_metrics


def test_walk_forward_matrix_reports_insufficient_data_without_crashing() -> None:
    df = _make_test_df(50)
    strat = _make_sma_strategy()

    result = walk_forward_matrix(
        strat,
        df,
        train_bars_list=[40, 100],
        test_bars_list=[20],
    )

    assert result.config_count == 2
    assert result.tested_count == 0
    assert result.insufficient_data_count == 2
    assert len(result.insufficient_data_configs) == 2
    assert result.best_pass_rate_config is None
    assert result.worst_pass_rate_config is None
    assert result.warnings


def test_walk_forward_matrix_is_deterministic() -> None:
    df = _make_test_df()
    strat = _make_sma_strategy()
    kwargs = {
        "train_bars_list": [50, 70],
        "test_bars_list": [20],
        "step_bars_list": [10, 20],
    }

    first = walk_forward_matrix(strat, df, **kwargs)
    second = walk_forward_matrix(strat, df, **kwargs)

    assert first == second


def test_walk_forward_matrix_summary_structure() -> None:
    df = _make_test_df()
    strat = _make_sma_strategy()

    result = walk_forward_matrix(
        strat,
        df,
        train_bars_list=[50, 80],
        test_bars_list=[20],
        step_bars_list=[20],
    )

    assert result.best_pass_rate_config is not None
    assert result.worst_pass_rate_config is not None
    for key in ("config_id", "train_bars", "test_bars", "step_bars", "window_count", "pass_count", "pass_rate"):
        assert key in result.best_pass_rate_config
        assert key in result.worst_pass_rate_config
    assert result.assumptions["method"] == "walk_forward_matrix"
    assert result.assumptions["total_bars"] == len(df)


def test_walk_forward_matrix_does_not_mutate_input_df() -> None:
    df = _make_test_df()
    original = df.copy(deep=True)
    strat = _make_sma_strategy()

    walk_forward_matrix(
        strat,
        df,
        train_bars_list=[50, 80],
        test_bars_list=[20],
        step_bars_list=[20],
    )

    pd.testing.assert_frame_equal(df, original)


def test_walk_forward_matrix_rejects_invalid_bar_config_as_warning() -> None:
    df = _make_test_df()
    strat = _make_sma_strategy()

    result = walk_forward_matrix(
        strat,
        df,
        train_bars_list=[50],
        test_bars_list=[20],
        step_bars_list=[0],
    )

    assert result.config_count == 1
    assert result.tested_count == 0
    assert result.insufficient_data_count == 1
    assert result.configs[0].warnings
    assert "positive" in result.configs[0].warnings[0]


def test_wf_matrix_robustness_score_present():
    df = _make_test_df()
    strat = _make_sma_strategy()
    result = walk_forward_matrix(
        strat, df,
        train_bars_list=[60, 80], test_bars_list=[20, 30], step_bars_list=[20]
    )
    assert result.matrix_robustness_score is not None
    assert 0.0 <= result.matrix_robustness_score <= 1.0


def test_wf_matrix_robustness_score_uses_default_threshold():
    df = _make_test_df()
    strat = _make_sma_strategy()
    result = walk_forward_matrix(
        strat, df,
        train_bars_list=[60, 80], test_bars_list=[20, 30]
    )
    assert result.assumptions["min_pass_rate_for_robustness"] == 0.5


def test_wf_matrix_robustness_score_custom_threshold():
    df = _make_test_df()
    strat = _make_sma_strategy()
    result = walk_forward_matrix(
        strat, df,
        train_bars_list=[60, 80], test_bars_list=[20, 30],
        min_pass_rate_for_robustness=0.8
    )
    assert result.assumptions["min_pass_rate_for_robustness"] == 0.8
    # Calculate expected
    tested = [cfg for cfg in result.configs if cfg.window_count > 0]
    expected = sum(1 for cfg in tested if cfg.pass_rate >= 0.8) / len(tested)
    assert result.matrix_robustness_score == expected


def test_wf_matrix_robustness_score_none_when_no_tested_configs():
    df = _make_test_df(50)  # insufficient data
    strat = _make_sma_strategy()
    result = walk_forward_matrix(
        strat, df,
        train_bars_list=[40, 100], test_bars_list=[20]
    )
    assert result.tested_count == 0
    assert result.matrix_robustness_score is None


def test_wf_matrix_assumptions_include_robustness_threshold():
    df = _make_test_df()
    strat = _make_sma_strategy()
    result = walk_forward_matrix(
        strat, df,
        train_bars_list=[60], test_bars_list=[20]
    )
    assert "min_pass_rate_for_robustness" in result.assumptions


def test_existing_wf_matrix_output_fields_unchanged():
    df = _make_test_df()
    strat = _make_sma_strategy()
    result = walk_forward_matrix(
        strat, df,
        train_bars_list=[60], test_bars_list=[20]
    )
    assert hasattr(result, "config_count")
    assert hasattr(result, "tested_count")
    assert hasattr(result, "best_pass_rate_config")
    assert hasattr(result, "worst_pass_rate_config")


def test_wf_matrix_robustness_excludes_insufficient_data():
    df = _make_test_df(100)
    strat = _make_sma_strategy()
    # 60+20 = 80 (tested), 120+20 = 140 (insufficient)
    result = walk_forward_matrix(
        strat, df,
        train_bars_list=[60, 120], test_bars_list=[20]
    )
    assert result.config_count == 2
    assert result.tested_count == 1
    assert result.insufficient_data_count == 1
    
    cfg = result.configs[0] if result.configs[0].window_count > 0 else result.configs[1]
    expected_score = 1.0 if cfg.pass_rate >= 0.5 else 0.0
    assert result.matrix_robustness_score == expected_score


def test_wf_matrix_robustness_threshold_out_of_range_safe_behavior():
    df = _make_test_df()
    strat = _make_sma_strategy()
    
    # threshold 2.0 -> no config can have pass_rate >= 2.0
    result_high = walk_forward_matrix(
        strat, df,
        train_bars_list=[60], test_bars_list=[20],
        min_pass_rate_for_robustness=2.0
    )
    assert result_high.matrix_robustness_score == 0.0
    
    # threshold -1.0 -> all configs pass
    result_low = walk_forward_matrix(
        strat, df,
        train_bars_list=[60], test_bars_list=[20],
        min_pass_rate_for_robustness=-1.0
    )
    assert result_low.matrix_robustness_score == 1.0


def test_wf_matrix_best_worst_unchanged_with_robustness():
    df = _make_test_df()
    strat = _make_sma_strategy()
    result = walk_forward_matrix(
        strat, df,
        train_bars_list=[60, 80], test_bars_list=[20, 30]
    )
    assert result.best_pass_rate_config is not None
    assert result.worst_pass_rate_config is not None
    
    # Should still correctly find min and max pass rate configs
    all_rates = [cfg.pass_rate for cfg in result.configs if cfg.window_count > 0]
    assert result.best_pass_rate_config["pass_rate"] == max(all_rates)
    assert result.worst_pass_rate_config["pass_rate"] == min(all_rates)


def test_wf_matrix_summary_serializable_with_robustness_score():
    df = _make_test_df()
    strat = _make_sma_strategy()
    result = walk_forward_matrix(
        strat, df,
        train_bars_list=[60], test_bars_list=[20]
    )
    from dataclasses import asdict
    import json
    d = asdict(result)
    s = json.dumps(d)
    assert "matrix_robustness_score" in s
