"""Walk-forward matrix orchestration.

This module evaluates multiple fixed-window walk-forward configurations by
delegating each run to :func:`validation_engine.walk_forward.walk_forward`.
It does not optimize parameters or mutate the input data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Any

import pandas as pd

from core.models.strategy import Strategy
from validation_engine.walk_forward import walk_forward


@dataclass
class WalkForwardMatrixConfigResult:
    """Result for one walk-forward matrix configuration."""

    config_id: str
    train_bars: int
    test_bars: int
    step_bars: int
    window_count: int = 0
    pass_count: int = 0
    pass_rate: float = 0.0
    aggregate_metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    insufficient_data: bool = False

    def to_summary_dict(self) -> dict[str, Any]:
        """Return a compact serializable summary of this configuration."""
        return {
            "config_id": self.config_id,
            "train_bars": self.train_bars,
            "test_bars": self.test_bars,
            "step_bars": self.step_bars,
            "window_count": self.window_count,
            "pass_count": self.pass_count,
            "pass_rate": self.pass_rate,
            "insufficient_data": self.insufficient_data,
        }


@dataclass
class WalkForwardMatrixSummary:
    """Aggregate result for a walk-forward matrix run."""

    config_count: int = 0
    tested_count: int = 0
    insufficient_data_count: int = 0
    configs: list[WalkForwardMatrixConfigResult] = field(default_factory=list)
    best_pass_rate_config: dict[str, Any] | None = None
    worst_pass_rate_config: dict[str, Any] | None = None
    insufficient_data_configs: list[str] = field(default_factory=list)
    matrix_robustness_score: float | None = None
    assumptions: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def walk_forward_matrix(
    strategy: Strategy,
    df: pd.DataFrame,
    *,
    train_bars_list: list[int],
    test_bars_list: list[int],
    step_bars_list: list[int] | None = None,
    min_pass_rate_for_robustness: float = 0.5,
    instrument=None,
    **backtest_kwargs,
) -> WalkForwardMatrixSummary:
    """Run fixed-window walk-forward across a grid of configurations.

    The Cartesian product of ``train_bars_list``, ``test_bars_list``, and
    ``step_bars_list`` is evaluated.  If ``step_bars_list`` is omitted, each
    configuration uses ``step_bars = test_bars`` to match the default
    non-overlapping behavior of :func:`walk_forward`.
    """
    warnings: list[str] = []

    if not train_bars_list or not test_bars_list:
        warnings.append("train_bars_list and test_bars_list must both be non-empty.")
        return WalkForwardMatrixSummary(
            config_count=0,
            assumptions={
                "method": "walk_forward_matrix",
                "train_bars_list": list(train_bars_list),
                "test_bars_list": list(test_bars_list),
                "step_bars_list": list(step_bars_list) if step_bars_list is not None else None,
            },
            warnings=warnings,
        )

    raw_configs = _build_config_grid(train_bars_list, test_bars_list, step_bars_list)
    config_results: list[WalkForwardMatrixConfigResult] = []

    for index, (train_bars, test_bars, step_bars) in enumerate(raw_configs, start=1):
        config_id = f"wf_matrix_{index:03d}"
        result = _run_single_config(
            config_id=config_id,
            strategy=strategy,
            df=df,
            train_bars=train_bars,
            test_bars=test_bars,
            step_bars=step_bars,
            instrument=instrument,
            backtest_kwargs=backtest_kwargs,
        )
        config_results.append(result)

    tested = [cfg for cfg in config_results if cfg.window_count > 0]
    insufficient = [cfg for cfg in config_results if cfg.insufficient_data]

    summary_warnings = warnings[:]
    if insufficient:
        summary_warnings.append(f"{len(insufficient)} configuration(s) had insufficient data or no windows.")
        
    robustness_score = None
    if tested:
        passed_configs = sum(1 for cfg in tested if cfg.pass_rate >= min_pass_rate_for_robustness)
        robustness_score = passed_configs / len(tested)

    return WalkForwardMatrixSummary(
        config_count=len(config_results),
        tested_count=len(tested),
        insufficient_data_count=len(insufficient),
        configs=config_results,
        best_pass_rate_config=_select_pass_rate_config(tested, best=True),
        worst_pass_rate_config=_select_pass_rate_config(tested, best=False),
        insufficient_data_configs=[cfg.config_id for cfg in insufficient],
        matrix_robustness_score=robustness_score,
        assumptions={
            "method": "walk_forward_matrix",
            "train_bars_list": list(train_bars_list),
            "test_bars_list": list(test_bars_list),
            "step_bars_list": list(step_bars_list) if step_bars_list is not None else None,
            "min_pass_rate_for_robustness": min_pass_rate_for_robustness,
            "total_bars": len(df),
        },
        warnings=summary_warnings,
    )


def _build_config_grid(
    train_bars_list: list[int],
    test_bars_list: list[int],
    step_bars_list: list[int] | None,
) -> list[tuple[int, int, int]]:
    if step_bars_list is not None:
        return [(train, test, step) for train, test, step in product(train_bars_list, test_bars_list, step_bars_list)]

    return [(train, test, test) for train, test in product(train_bars_list, test_bars_list)]


def _run_single_config(
    *,
    config_id: str,
    strategy: Strategy,
    df: pd.DataFrame,
    train_bars: int,
    test_bars: int,
    step_bars: int,
    instrument,
    backtest_kwargs: dict[str, Any],
) -> WalkForwardMatrixConfigResult:
    if train_bars <= 0 or test_bars <= 0 or step_bars <= 0:
        return WalkForwardMatrixConfigResult(
            config_id=config_id,
            train_bars=train_bars,
            test_bars=test_bars,
            step_bars=step_bars,
            warnings=["train_bars, test_bars, and step_bars must all be positive."],
            insufficient_data=True,
        )

    wf = walk_forward(
        strategy,
        df,
        train_bars=train_bars,
        test_bars=test_bars,
        step_bars=step_bars,
        instrument=instrument,
        **backtest_kwargs,
    )

    insufficient = wf.window_count == 0
    return WalkForwardMatrixConfigResult(
        config_id=config_id,
        train_bars=train_bars,
        test_bars=test_bars,
        step_bars=step_bars,
        window_count=wf.window_count,
        pass_count=wf.pass_count,
        pass_rate=wf.pass_rate,
        aggregate_metrics=dict(wf.aggregate_metrics),
        warnings=list(wf.warnings),
        insufficient_data=insufficient,
    )


def _select_pass_rate_config(
    configs: list[WalkForwardMatrixConfigResult],
    *,
    best: bool,
) -> dict[str, Any] | None:
    if not configs:
        return None

    ordered = sorted(
        configs,
        key=lambda cfg: (
            cfg.pass_rate,
            cfg.pass_count,
            cfg.window_count,
            -cfg.train_bars,
            -cfg.test_bars,
            -cfg.step_bars,
        ),
        reverse=best,
    )
    return ordered[0].to_summary_dict()
