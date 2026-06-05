"""Multi-dimensional strategy ranking — not net profit only.

Produces a deterministic fitness score from backtest metrics so that
strategies are ranked on robustness, not just a single dimension.
"""

from __future__ import annotations


# Weight configuration for fitness dimensions.
DEFAULT_WEIGHTS = {
    "total_pnl": 0.25,
    "profit_factor": 0.25,
    "max_drawdown_pnl": 0.20,
    "avg_trade": 0.15,
    "total_trades": 0.15,
}

# Normalisation anchors (per $100k initial capital).
_ANCHORS = {
    "total_pnl": 50_000.0,       # $50k → score 1.0
    "profit_factor": 3.0,        # PF 3.0 → score 1.0
    "max_drawdown_pnl": 20_000.0,  # $20k DD → score 0.0 (inverted)
    "avg_trade": 500.0,          # $500 avg trade → score 1.0
    "total_trades": 30,          # 30 trades → score 1.0
}

# Minimum trades to avoid ranking tiny-sample strategies highly.
MIN_TRADES_FOR_FULL_SCORE = 5


def compute_fitness(metrics: dict, weights: dict | None = None) -> float:
    """Compute a multi-dimensional fitness score from backtest metrics.

    Each dimension is normalised to roughly [0, 1] and combined via weighted sum.
    ``max_drawdown_pnl`` is inverted (lower drawdown → higher score).
    ``total_trades`` is penalised when below *MIN_TRADES_FOR_FULL_SCORE*.

    Parameters
    ----------
    metrics : dict
        Output of :func:`backtest_engine.metrics.compute_metrics`.
    weights : dict or None
        Dimension weights (defaults to :data:`DEFAULT_WEIGHTS`).

    Returns
    -------
    float
        Fitness score (higher is better).  Bounded roughly [0, 1] but can
        exceed 1.0 for exceptional strategies.
    """
    w = weights or DEFAULT_WEIGHTS
    score = 0.0
    total_weight = 0.0

    for dim, weight in w.items():
        total_weight += weight
        raw = float(metrics.get(dim, 0.0))
        anchor = _ANCHORS.get(dim, 1.0)

        if dim == "max_drawdown_pnl":
            # Invert: lower drawdown → higher score.
            # score = max(0, 1 - raw / anchor)
            norm = max(0.0, 1.0 - raw / anchor)
        elif dim == "total_trades":
            norm = min(raw / anchor, 1.0)
            # Penalty for too few trades.
            if raw < MIN_TRADES_FOR_FULL_SCORE:
                norm *= raw / MIN_TRADES_FOR_FULL_SCORE
        elif dim == "profit_factor":
            norm = min(raw / anchor, 1.0)
        elif dim == "avg_trade":
            # Cap: an outlier avg_trade shouldn't dominate the score.
            norm = min(raw / anchor, 1.0)
        else:
            # total_pnl — can exceed 1.0 for strong strategies.
            norm = raw / anchor

        score += norm * weight

    # Normalise by total weight so score is roughly [0, 1].
    return score / total_weight if total_weight > 0 else 0.0


def rank_strategies(
    backtest_results: list[dict],
    weights: dict | None = None,
) -> list[dict]:
    """Rank a list of backtested strategies by multi-dimensional fitness.

    **Non-mutating** — the caller's original list and dicts are not modified.
    Returns a new list of shallow-copied dicts with ``fitness`` and ``rank``
    keys added.

    Parameters
    ----------
    backtest_results : list[dict]
        Each dict must have keys ``strategy``, ``provenance``, and ``metrics``.
    weights : dict or None

    Returns
    -------
    list[dict]
        A new list sorted by fitness descending, each entry augmented with
        ``fitness`` (float) and ``rank`` (int).
    """
    # Work on copies so the caller's originals are untouched.
    copied: list[dict] = []
    for entry in backtest_results:
        c = dict(entry)
        c["fitness"] = round(compute_fitness(c.get("metrics", {}), weights), 6)
        copied.append(c)

    copied.sort(key=lambda e: e["fitness"], reverse=True)

    for i, entry in enumerate(copied):
        entry["rank"] = i + 1

    return copied
