"""Strategy elimination rules engine — rejects fragile strategies before ranking.

Configurable thresholds filter strategies on backtest metrics plus optional
validation results (OOS, stress tests, Monte Carlo, Walk-forward).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class EliminationConfig:
    """Thresholds for automatic strategy rejection.

    Every field defaults to ``None`` (disabled).  Set a numeric value to
    activate the corresponding rule.
    """

    # Core backtest thresholds.
    min_total_pnl: float | None = None
    min_profit_factor: float | None = None
    max_drawdown_pnl: float | None = None
    min_avg_trade: float | None = None
    min_trade_count: int | None = None
    min_win_rate: float | None = None

    # Optional OOS thresholds (requires OOS metrics).
    min_oos_total_pnl: float | None = None
    min_oos_profit_factor: float | None = None

    # Optional stress-test thresholds.
    min_stress_pass_rate: float | None = None

    # Optional Monte Carlo thresholds.
    min_monte_carlo_p05_pnl: float | None = None

    # Optional Walk-forward thresholds.
    min_walk_forward_pass_rate: float | None = None

    # When True, missing optional inputs (OOS/stress/MC/WF) cause the
    # strategy to FAIL if the corresponding threshold is set.
    require_optional: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class EliminationResult:
    """Structured output of elimination rule evaluation."""

    passed: bool
    failed_rules: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics_snapshot: dict = field(default_factory=dict)
    config_snapshot: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def evaluate_elimination(
    metrics: dict,
    config: EliminationConfig,
    *,
    oos_metrics: dict | None = None,
    stress_results: list[dict] | None = None,
    mc_result: dict | None = None,
    wf_result: dict | None = None,
) -> EliminationResult:
    """Evaluate *metrics* against *config* thresholds.

    Parameters
    ----------
    metrics : dict
        Backtest metrics from :func:`backtest_engine.metrics.compute_metrics`.
    config : EliminationConfig
    oos_metrics : dict or None
        OOS-segment metrics (same schema as *metrics*).
    stress_results : list[dict] or None
        List of ``StressTestResult`` dicts (or dataclasses with ``.passed`` attr).
    mc_result : dict or None
        ``MonteCarloResult`` data, must have ``worst_case.total_pnl``
        or ``percentile_summary.total_pnl.p5``.
    wf_result : dict or None
        ``WalkForwardResult`` data, must have ``pass_rate``.

    Returns
    -------
    EliminationResult
    """
    failed: list[str] = []
    warnings: list[str] = []

    def _fail(rule: str) -> None:
        failed.append(rule)

    # ── core thresholds ─────────────────────────────────────────────────────
    _check_gt("min_total_pnl", metrics.get("total_pnl"), config.min_total_pnl, _fail)
    _check_gt("min_profit_factor", metrics.get("profit_factor"), config.min_profit_factor, _fail)
    _check_lt("max_drawdown_pnl", metrics.get("max_drawdown_pnl"), config.max_drawdown_pnl, _fail)
    _check_gt("min_avg_trade", metrics.get("avg_trade"), config.min_avg_trade, _fail)
    _check_gt("min_trade_count", metrics.get("total_trades"), config.min_trade_count, _fail)
    _check_gt("min_win_rate", metrics.get("win_rate"), config.min_win_rate, _fail)

    # ── optional OOS ─────────────────────────────────────────────────────────
    if oos_metrics is not None:
        _check_gt("min_oos_total_pnl", oos_metrics.get("total_pnl"), config.min_oos_total_pnl, _fail)
        _check_gt("min_oos_profit_factor", oos_metrics.get("profit_factor"), config.min_oos_profit_factor, _fail)
    else:
        _optional_missing("OOS", config.min_oos_total_pnl, config.min_oos_profit_factor,
                          require=config.require_optional, fail=_fail, warnings=warnings)

    # ── optional stress ──────────────────────────────────────────────────────
    if stress_results is not None:
        if config.min_stress_pass_rate is not None:
            total = len(stress_results)
            passed = sum(1 for s in stress_results if _get_passed(s))
            rate = passed / total if total > 0 else 0.0
            if rate < config.min_stress_pass_rate:
                _fail(f"min_stress_pass_rate ({rate:.2f} < {config.min_stress_pass_rate})")
    else:
        _optional_missing("stress", config.min_stress_pass_rate,
                          require=config.require_optional, fail=_fail, warnings=warnings)

    # ── optional Monte Carlo ─────────────────────────────────────────────────
    if mc_result is not None:
        if config.min_monte_carlo_p05_pnl is not None:
            p05 = _extract_p05_pnl(mc_result)
            if p05 is not None and p05 < config.min_monte_carlo_p05_pnl:
                _fail(f"min_monte_carlo_p05_pnl ({p05:.2f} < {config.min_monte_carlo_p05_pnl})")
    else:
        _optional_missing("Monte Carlo", config.min_monte_carlo_p05_pnl,
                          require=config.require_optional, fail=_fail, warnings=warnings)

    # ── optional Walk-forward ────────────────────────────────────────────────
    if wf_result is not None:
        if config.min_walk_forward_pass_rate is not None:
            wf_rate = float(wf_result.get("pass_rate", 0.0))
            if wf_rate < config.min_walk_forward_pass_rate:
                _fail(f"min_walk_forward_pass_rate ({wf_rate:.2f} < {config.min_walk_forward_pass_rate})")
    else:
        _optional_missing("Walk-forward", config.min_walk_forward_pass_rate,
                          require=config.require_optional, fail=_fail, warnings=warnings)

    return EliminationResult(
        passed=len(failed) == 0,
        failed_rules=failed,
        warnings=warnings,
        metrics_snapshot=dict(metrics),
        config_snapshot=config.to_dict(),
    )


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _check_gt(
    name: str,
    actual: Any,
    threshold: float | int | None,
    fail: callable,
) -> None:
    if threshold is not None:
        try:
            val = float(actual)
        except (TypeError, ValueError):
            fail(f"{name}: value {actual!r} is not numeric")
            return
        if val < threshold:
            fail(f"{name} ({val:.4f} < {threshold})")


def _check_lt(
    name: str,
    actual: Any,
    threshold: float | int | None,
    fail: callable,
) -> None:
    """threshold is an upper bound — actual must be <= threshold."""
    if threshold is not None:
        try:
            val = float(actual)
        except (TypeError, ValueError):
            fail(f"{name}: value {actual!r} is not numeric")
            return
        if val > threshold:
            fail(f"{name} ({val:.4f} > {threshold})")


def _optional_missing(
    source: str,
    *thresholds: Any,
    require: bool,
    fail: callable,
    warnings: list[str],
) -> None:
    if any(t is not None for t in thresholds):
        msg = f"{source} data not provided but {source} threshold(s) are set."
        if require:
            fail(msg)
        else:
            warnings.append(msg + f"  Skipping {source} rules.")


def _get_passed(stress: Any) -> bool:
    if hasattr(stress, "passed"):
        return bool(stress.passed)
    if isinstance(stress, dict):
        return bool(stress.get("passed", False))
    return False


def _extract_p05_pnl(mc: Any) -> float | None:
    """Extract p5 total_pnl from a MonteCarloResult-like object."""
    if isinstance(mc, dict):
        wc = mc.get("worst_case", {})
        if isinstance(wc, dict) and "total_pnl" in wc:
            return float(wc["total_pnl"])
        ps = mc.get("percentile_summary", {})
        tp = ps.get("total_pnl", {})
        if isinstance(tp, dict) and "p5" in tp:
            return float(tp["p5"])
    if hasattr(mc, "worst_case"):
        wc = getattr(mc, "worst_case", {})
        if isinstance(wc, dict) and "total_pnl" in wc:
            return float(wc["total_pnl"])
    return None
