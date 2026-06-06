"""Validation pipeline service — orchestrates v0.1 validation modules.

Provides a single callable API that runs the full research validation
pipeline: split → backtest → stress → Monte Carlo → walk-forward → elimination.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

import pandas as pd

from core.models.strategy import Strategy
from core.models.instrument import InstrumentProfile
from backtest_engine.runner import run_backtest
from validation_engine.splitter import split_by_ratio
from validation_engine.stress_test import stress_commission_multiplier, stress_slippage_multiplier, stress_one_bar_delay, stress_parameter_perturbation, stress_remove_best_n_trades
from validation_engine.monte_carlo import run_missed_trade_monte_carlo
from validation_engine.walk_forward import walk_forward
from validation_engine.walk_forward_matrix import walk_forward_matrix
from validation_engine.elimination import EliminationConfig, evaluate_elimination


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class PipelineConfig:
    """Configuration for a validation pipeline run.

    All fields have defaults tuned for fast prototype use.
    Set *mc_iterations* higher for production-quality confidence intervals.
    """

    # Split ratios.
    train_ratio: float = 0.6
    validation_ratio: float = 0.2
    oos_ratio: float = 0.2

    # Stress-test multiplier.
    stress_commission_multiplier: float = 2.0
    stress_slippage_multiplier: float = 2.0
    run_one_bar_delay_stress: bool = True
    run_parameter_perturbation: bool = True
    run_remove_best_n_trades_stress: bool = False
    remove_best_n_trades_n: int = 3
    remove_best_n_trades_degradation_threshold: float = 0.30

    # Monte Carlo.
    mc_iterations: int = 25
    mc_miss_probability: float = 0.1
    mc_base_seed: int = 42

    # Walk-forward (auto-sized when None).
    wf_train_bars: int | None = None
    wf_test_bars: int | None = None
    calc_wfe: bool = False

    # Walk-forward Matrix (disabled by default)
    run_matrix: bool = False
    matrix_train_bars_list: list[int] | None = None
    matrix_test_bars_list: list[int] | None = None
    matrix_step_bars_list: list[int] | None = None

    # Quality precheck (opt-in only).
    run_is_baseline_quality_precheck: bool = False
    fail_is_baseline_on_nonpositive_pnl: bool = False

    # Elimination.
    elimination_config: EliminationConfig | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["elimination_config"] = (
            self.elimination_config.to_dict() if self.elimination_config else None
        )
        return d


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class PipelineResult:
    """Structured output of a full validation pipeline run."""

    split_metadata: dict = field(default_factory=dict)
    baseline_metrics: dict = field(default_factory=dict)
    stress_results: list[dict] = field(default_factory=list)
    monte_carlo_summary: dict | None = None
    walk_forward_summary: dict | None = None
    walk_forward_matrix_summary: dict | None = None
    elimination_result: dict | None = None
    oos_metrics: dict | None = None
    precheck_failed: bool = False
    warnings: list[str] = field(default_factory=list)
    config_snapshot: dict = field(default_factory=dict)
    data_source: str = ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_validation_pipeline(
    df: pd.DataFrame,
    strategy: Strategy,
    config: PipelineConfig | None = None,
    *,
    instrument: InstrumentProfile | None = None,
    data_source: str = "",
    **backtest_kwargs,
) -> PipelineResult:
    """Run the full v0.1 validation pipeline on *df* with *strategy*.

    Parameters
    ----------
    df : DataFrame
        Normalized OHLCV data.
    strategy : Strategy
    config : PipelineConfig or None
        Defaults to :class:`PipelineConfig()` with fast prototype settings.
    instrument : InstrumentProfile or None
    **backtest_kwargs
        Passed to :func:`run_backtest` (commission, slippage_ticks, …).

    Returns
    -------
    PipelineResult
    """
    cfg = config or PipelineConfig()
    warnings: list[str] = []

    # ── 1. Split ────────────────────────────────────────────────────────────
    split = split_by_ratio(df, cfg.train_ratio, cfg.validation_ratio, cfg.oos_ratio)

    # ── 2. Baseline backtest (on IS/train segment) ──────────────────────────
    baseline = run_backtest(strategy, split.train, instrument=instrument, **backtest_kwargs)

    # ── 2.5 OOS backtest (on OOS segment, if available) ─────────────────────
    oos_baseline = None
    if split.oos is not None and len(split.oos) > 0:
        oos_baseline = run_backtest(strategy, split.oos, instrument=instrument, **backtest_kwargs)
    else:
        warnings.append("OOS segment is empty or None — OOS metrics not available for elimination.")

    # ── 2.7 IS baseline quality precheck (opt-in) ──────────────────────────
    if cfg.run_is_baseline_quality_precheck:
        precheck_fail_reason: str | None = None

        if baseline.metrics.get("total_trades", 0) == 0:
            precheck_fail_reason = "Validation precheck failed: strategy has zero baseline trades."
        elif cfg.fail_is_baseline_on_nonpositive_pnl and baseline.metrics.get("total_pnl", 0) <= 0:
            precheck_fail_reason = "Validation precheck failed: strategy has non-positive baseline PnL."

        if precheck_fail_reason:
            warnings.append(f"{precheck_fail_reason} Stress/MC/WF skipped.")
            return PipelineResult(
                split_metadata={
                    "train_rows": split.train_meta.get("row_count", 0),
                    "validation_rows": split.validation_meta.get("row_count", 0),
                    "oos_rows": split.oos_meta.get("row_count", 0),
                },
                baseline_metrics=baseline.metrics,
                oos_metrics=oos_baseline.metrics if oos_baseline is not None else None,
                precheck_failed=True,
                elimination_result={
                    "passed": False,
                    "failed_rules": [precheck_fail_reason],
                    "warnings": [],
                    "config_snapshot": {},
                },
                warnings=warnings,
                config_snapshot=cfg.to_dict(),
                data_source=data_source,
            )

    # ── 3. Stress tests ─────────────────────────────────────────────────────
    stress_results: list[dict] = []

    comm = stress_commission_multiplier(
        strategy, split.train, baseline,
        multiplier=cfg.stress_commission_multiplier,
        instrument=instrument,
    )
    stress_results.append(_stress_to_dict(comm))

    slip = stress_slippage_multiplier(
        strategy, split.train, baseline,
        multiplier=cfg.stress_slippage_multiplier,
        instrument=instrument,
    )
    stress_results.append(_stress_to_dict(slip))

    if cfg.run_one_bar_delay_stress:
        delay_res = stress_one_bar_delay(
            strategy, split.train, baseline, instrument=instrument
        )
        stress_results.append(_stress_to_dict(delay_res))

    if cfg.run_parameter_perturbation:
        import random
        state = random.getstate()
        random.seed(cfg.mc_base_seed)
        param_res = stress_parameter_perturbation(
            strategy, split.train, baseline, instrument=instrument
        )
        random.setstate(state)
        stress_results.append(_stress_to_dict(param_res))

    if cfg.run_remove_best_n_trades_stress:
        n_trades_res = stress_remove_best_n_trades(
            baseline,
            n=cfg.remove_best_n_trades_n,
            degradation_threshold=cfg.remove_best_n_trades_degradation_threshold,
        )
        stress_results.append(_stress_to_dict(n_trades_res))

    # ── 4. Monte Carlo ──────────────────────────────────────────────────────
    mc = run_missed_trade_monte_carlo(
        baseline,
        iterations=cfg.mc_iterations,
        miss_probability=cfg.mc_miss_probability,
        base_seed=cfg.mc_base_seed,
    )
    mc_summary = _mc_to_dict(mc)

    # ── 5. Walk-forward ─────────────────────────────────────────────────────
    n = len(df)
    wf_train = cfg.wf_train_bars or max(20, n // 3)
    wf_test = cfg.wf_test_bars or max(10, n // 6)

    if n < wf_train + wf_test:
        warnings.append(
            f"Walk-forward skipped: dataset too short ({n} bars) for "
            f"train={wf_train} + test={wf_test}."
        )
        wf_summary = None
    else:
        wf = walk_forward(strategy, df, train_bars=wf_train, test_bars=wf_test, calc_wfe=cfg.calc_wfe)
        wf_summary = _wf_to_dict(wf)

    # ── 5.5 Walk-forward Matrix ─────────────────────────────────────────────
    wf_matrix_summary = None
    if cfg.run_matrix:
        m_train = cfg.matrix_train_bars_list or [wf_train]
        m_test = cfg.matrix_test_bars_list or [wf_test]
        matrix_res = walk_forward_matrix(
            strategy,
            df,
            train_bars_list=m_train,
            test_bars_list=m_test,
            step_bars_list=cfg.matrix_step_bars_list,
            instrument=instrument,
            **backtest_kwargs,
        )
        wf_matrix_summary = _matrix_to_dict(matrix_res)

    # ── 6. Elimination ──────────────────────────────────────────────────────
    elim_cfg = cfg.elimination_config or EliminationConfig(
        min_trade_count=0, min_profit_factor=0.0,
        max_drawdown_pnl=1_000_000.0, min_avg_trade=-10_000.0,
    )
    oos_metrics = oos_baseline.metrics if oos_baseline is not None else None
    elim = evaluate_elimination(
        baseline.metrics, elim_cfg,
        oos_metrics=oos_metrics,
    )
    elim_dict: dict = {
        "passed": elim.passed,
        "failed_rules": elim.failed_rules,
        "warnings": elim.warnings,
        "config_snapshot": elim.config_snapshot,
    }

    return PipelineResult(
        split_metadata={
            "train_rows": split.train_meta.get("row_count", 0),
            "validation_rows": split.validation_meta.get("row_count", 0),
            "oos_rows": split.oos_meta.get("row_count", 0),
        },
        baseline_metrics=baseline.metrics,
        stress_results=stress_results,
        monte_carlo_summary=mc_summary,
        walk_forward_summary=wf_summary,
        walk_forward_matrix_summary=wf_matrix_summary,
        elimination_result=elim_dict,
        oos_metrics=oos_metrics,
        precheck_failed=False,
        warnings=warnings,
        config_snapshot=cfg.to_dict(),
        data_source=data_source,
    )


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _stress_to_dict(sr) -> dict:
    result: dict = {
        "test_name": sr.test_name,
        "passed": sr.passed,
        "degradation": sr.degradation,
        "stressed_metrics": sr.stressed_metrics,
    }
    # Include assumptions, warnings, and threshold when present.
    if hasattr(sr, "assumptions"):
        result["assumptions"] = sr.assumptions
    if hasattr(sr, "warnings"):
        result["warnings"] = sr.warnings
    if hasattr(sr, "threshold"):
        result["threshold"] = sr.threshold
    return result


def _mc_to_dict(mc) -> dict:
    return {
        "iterations": mc.iterations,
        "percentile_summary": mc.percentile_summary,
        "worst_case": mc.worst_case,
    }


def _wf_to_dict(wf) -> dict:
    return {
        "window_count": wf.window_count,
        "pass_count": wf.pass_count,
        "pass_rate": wf.pass_rate,
        "aggregate_metrics": wf.aggregate_metrics,
        "average_wfe": getattr(wf, "average_wfe", None),
        "median_wfe": getattr(wf, "median_wfe", None),
        "defined_wfe_count": getattr(wf, "defined_wfe_count", 0),
        "undefined_wfe_count": getattr(wf, "undefined_wfe_count", 0),
    }


def _matrix_to_dict(matrix) -> dict:
    return {
        "config_count": matrix.config_count,
        "tested_count": matrix.tested_count,
        "insufficient_data_count": matrix.insufficient_data_count,
        "insufficient_data_configs": matrix.insufficient_data_configs,
        "best_pass_rate_config": matrix.best_pass_rate_config,
        "worst_pass_rate_config": matrix.worst_pass_rate_config,
        "assumptions": matrix.assumptions,
        "warnings": matrix.warnings,
    }
