"""Tests for validation pipeline service — Task 024."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.models.strategy import Condition, Strategy, StrategyBlock
from app.services.validation_pipeline_service import (
    PipelineConfig,
    PipelineResult,
    run_validation_pipeline,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
        name="vp_test",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 10}, operator="<"),
        ], logic="AND"),
    )


# ---------------------------------------------------------------------------
# Pipeline result structure
# ---------------------------------------------------------------------------


def test_result_has_all_expected_sections():
    """PipelineResult must contain all 8 required sections."""
    df = _make_df(200)
    strat = _make_strategy()

    result = run_validation_pipeline(df, strat, commission=2.0)

    assert isinstance(result, PipelineResult)
    assert isinstance(result.split_metadata, dict)
    assert isinstance(result.baseline_metrics, dict)
    assert isinstance(result.stress_results, list)
    assert result.monte_carlo_summary is not None
    assert result.walk_forward_summary is not None
    assert result.elimination_result is not None
    assert isinstance(result.warnings, list)
    assert isinstance(result.config_snapshot, dict)


def test_split_metadata_present():
    """Split metadata must include train/validation/oos row counts."""
    df = _make_df(200)
    strat = _make_strategy()
    result = run_validation_pipeline(df, strat, commission=2.0)

    sm = result.split_metadata
    assert sm["train_rows"] > 0
    assert sm["validation_rows"] > 0
    assert sm["oos_rows"] > 0


def test_stress_results_contain_both_tests():
    """Stress results must include commission and slippage multipliers."""
    df = _make_df(200)
    strat = _make_strategy()
    result = run_validation_pipeline(df, strat, commission=2.0)

    test_names = [s["test_name"] for s in result.stress_results]
    assert any("commission" in t for t in test_names)
    assert any("slippage" in t for t in test_names)


def test_elimination_result_included():
    """Elimination must have passed, failed_rules, warnings, config_snapshot."""
    df = _make_df(200)
    strat = _make_strategy()
    result = run_validation_pipeline(df, strat, commission=2.0)

    elim = result.elimination_result
    assert isinstance(elim["passed"], bool)
    assert isinstance(elim["failed_rules"], list)
    assert isinstance(elim["warnings"], list)
    assert isinstance(elim["config_snapshot"], dict)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_deterministic_output():
    """Same config + seed must produce identical results."""
    df = _make_df(200)
    strat = _make_strategy()
    cfg = PipelineConfig(mc_base_seed=42, mc_iterations=20)

    r1 = run_validation_pipeline(df, strat, config=cfg, commission=2.0)
    r2 = run_validation_pipeline(df, strat, config=cfg, commission=2.0)

    assert r1.baseline_metrics == r2.baseline_metrics
    assert r1.stress_results == r2.stress_results
    assert r1.monte_carlo_summary == r2.monte_carlo_summary
    assert r1.walk_forward_summary == r2.walk_forward_summary
    assert r1.elimination_result == r2.elimination_result


# ---------------------------------------------------------------------------
# No mutation
# ---------------------------------------------------------------------------


def test_input_df_not_mutated():
    """The input DataFrame must be unchanged after pipeline run."""
    df = _make_df(200)
    df_copy = df.copy()
    strat = _make_strategy()

    run_validation_pipeline(df, strat, commission=2.0)
    pd.testing.assert_frame_equal(df, df_copy)


# ---------------------------------------------------------------------------
# Config snapshot
# ---------------------------------------------------------------------------


def test_config_snapshot_present():
    """Config snapshot must record the pipeline settings."""
    cfg = PipelineConfig(train_ratio=0.5, validation_ratio=0.3, oos_ratio=0.2, mc_iterations=15)
    df = _make_df(200)
    strat = _make_strategy()

    result = run_validation_pipeline(df, strat, config=cfg, commission=2.0)

    assert result.config_snapshot["train_ratio"] == 0.5
    assert result.config_snapshot["mc_iterations"] == 15


# ---------------------------------------------------------------------------
# Edge: short dataset
# ---------------------------------------------------------------------------


def test_short_dataset_skips_walk_forward():
    """A dataset too short for walk-forward must produce a warning and
    a null walk_forward_summary."""
    df = _make_df(30)
    strat = _make_strategy()
    cfg = PipelineConfig(wf_train_bars=500, wf_test_bars=100)

    result = run_validation_pipeline(df, strat, config=cfg, commission=2.0)

    assert result.walk_forward_summary is None
    assert any("walk-forward" in w.lower() for w in result.warnings)


def test_validation_pipeline_walk_forward_summary_compatible_with_stability_score():
    """Ensure that validation pipeline ignores stability_score or handles it without crashing."""
    df = _make_df(400)
    strat = _make_strategy()
    cfg = PipelineConfig(wf_train_bars=200, wf_test_bars=100)

    # Should run successfully and serialize walk_forward_summary correctly
    result = run_validation_pipeline(df, strat, config=cfg, commission=2.0)
    
    assert result.walk_forward_summary is not None
    # Verify that the keys it does serialize are present
    assert "window_count" in result.walk_forward_summary
    assert "pass_count" in result.walk_forward_summary
    assert "pass_rate" in result.walk_forward_summary
    
    import json
    # Prove the dict can be JSON serialized
    s = json.dumps(result.walk_forward_summary)
    assert len(s) > 0


# ---------------------------------------------------------------------------
# Task 044C: WFE Serialization Tests
# ---------------------------------------------------------------------------


def test_wf_serialization_with_wfe():
    """WFE fields are serialized correctly when calc_wfe=True."""
    from validation_engine.walk_forward import WalkForwardResult, WalkForwardWindow
    from app.services.validation_pipeline_service import _wf_to_dict
    
    # Enhanced result with WFE fields
    wf = WalkForwardResult(
        windows=[],
        window_count=10,
        pass_count=8,
        pass_rate=0.8,
        aggregate_metrics={"total_pnl": 1000},
        stability_score=0.5,
        average_wfe=0.9,
        median_wfe=0.85,
        defined_wfe_count=9,
        undefined_wfe_count=1,
    )
    
    d = _wf_to_dict(wf)
    
    # Existing fields unchanged
    assert d["window_count"] == 10
    assert d["pass_count"] == 8
    assert d["pass_rate"] == 0.8
    assert d["aggregate_metrics"] == {"total_pnl": 1000}
    
    # New fields present
    assert d["average_wfe"] == 0.9
    assert d["median_wfe"] == 0.85
    assert d["defined_wfe_count"] == 9
    assert d["undefined_wfe_count"] == 1


def test_wf_serialization_without_wfe():
    """calc_wfe=False produces safe empty serialization."""
    from validation_engine.walk_forward import WalkForwardResult
    from app.services.validation_pipeline_service import _wf_to_dict
    
    wf = WalkForwardResult(
        windows=[],
        window_count=10,
        pass_count=8,
        pass_rate=0.8,
        aggregate_metrics={"total_pnl": 1000},
        stability_score=0.5,
        # Default initialization gives None/0
    )
    
    d = _wf_to_dict(wf)
    
    assert d["average_wfe"] is None
    assert d["median_wfe"] is None
    assert d["defined_wfe_count"] == 0
    assert d["undefined_wfe_count"] == 0


def test_wf_serialization_old_mock_result():
    """Mocked or old objects without WFE attributes do not crash."""
    from types import SimpleNamespace
    from app.services.validation_pipeline_service import _wf_to_dict
    
    wf = SimpleNamespace(
        window_count=10,
        pass_count=8,
        pass_rate=0.8,
        aggregate_metrics={"total_pnl": 1000},
        # Missing all WFE attributes
    )
    
    d = _wf_to_dict(wf)
    
    assert d["window_count"] == 10
    assert d["average_wfe"] is None
    assert d["median_wfe"] is None
    assert d["defined_wfe_count"] == 0
    assert d["undefined_wfe_count"] == 0
