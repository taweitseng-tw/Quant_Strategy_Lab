"""Deterministic random strategy generator — fixed-template with random parameters.

Produces strategies from the MVP four-block template using SMA, RSI, MACD,
and ATR conditions.
"""

from __future__ import annotations

import random
from dataclasses import asdict

from core.models.strategy import Condition, Strategy, StrategyBlock

GENERATOR_VERSION = "0.2.0"

# Parameter ranges.
DEFAULT_SMA_PERIOD_RANGE = (5, 100)
DEFAULT_RSI_PERIOD_RANGE = (5, 30)
DEFAULT_RSI_THRESHOLD_RANGE = (20, 80)
DEFAULT_ATR_PERIOD_RANGE = (5, 30)
DEFAULT_ATR_THRESHOLD_RANGE = (0.5, 5.0)
DEFAULT_MACD_FAST_RANGE = (3, 20)
DEFAULT_MACD_SLOW_RANGE = (15, 50)
DEFAULT_MACD_SIGNAL_RANGE = (5, 15)
DEFAULT_VOLUME_THRESHOLD_RANGE = (1000, 100000)
DEFAULT_VOLUME_SMA_PERIOD_RANGE = (5, 50)
DEFAULT_VOLUME_SMA_MULTIPLIER_RANGE = (0.5, 5.0)

# Supported indicator types and their probabilities of selection.
_INDICATOR_TYPES = ("SMA", "RSI", "MACD", "ATR", "VOLUME", "VOLUME_SMA")
_DEFAULT_INDICATOR_WEIGHTS = (0.35, 0.30, 0.15, 0.20, 0.0, 0.0)


def generate_strategies(
    count: int = 10,
    seed: int = 42,
    *,
    sma_period_range: tuple[int, int] = DEFAULT_SMA_PERIOD_RANGE,
    rsi_period_range: tuple[int, int] = DEFAULT_RSI_PERIOD_RANGE,
    rsi_threshold_range: tuple[int, int] = DEFAULT_RSI_THRESHOLD_RANGE,
    atr_period_range: tuple[int, int] = DEFAULT_ATR_PERIOD_RANGE,
    atr_threshold_range: tuple[float, float] = DEFAULT_ATR_THRESHOLD_RANGE,
    macd_fast_range: tuple[int, int] = DEFAULT_MACD_FAST_RANGE,
    macd_slow_range: tuple[int, int] = DEFAULT_MACD_SLOW_RANGE,
    macd_signal_range: tuple[int, int] = DEFAULT_MACD_SIGNAL_RANGE,
    volume_threshold_range: tuple[int, int] = DEFAULT_VOLUME_THRESHOLD_RANGE,
    volume_sma_period_range: tuple[int, int] = DEFAULT_VOLUME_SMA_PERIOD_RANGE,
    volume_sma_multiplier_range: tuple[float, float] = DEFAULT_VOLUME_SMA_MULTIPLIER_RANGE,
    indicator_weights: tuple[float, ...] = _DEFAULT_INDICATOR_WEIGHTS,
    short_enabled_probability: float = 0.5,
    allowed_timeframes: tuple[int, ...] = (),
    mtf_probability: float = 0.0,
    generated_at: str | None = None,
) -> list[dict]:
    """Generate *count* strategies deterministically from *seed*.

    Each strategy uses the four-block template.  Each block randomly
    selects one of SMA, RSI, MACD, or ATR with configurable weights.

    - **Long Entry**:  always present, e.g. ``close > SMA(N)`` or ``RSI < 30``
    - **Long Exit**:   always present
    - **Short Entry**: present with *short_enabled_probability*
    - **Short Exit**:  only when short entry is present

    Parameters
    ----------
    count : int
        Number of strategies to generate (default 10).
    seed : int
        Random seed for reproducibility.
    indicator_weights : tuple[float, ...]
        Selection probability for (SMA, RSI, MACD, ATR) — default (0.35, 0.30, 0.15, 0.20).
    short_enabled_probability : float
        Probability [0, 1] that a strategy includes short-side blocks.
    allowed_timeframes : tuple[int, ...]
        Tuple of allowed timeframe multipliers (e.g., (5, 15)). Duplicates are removed and values are sorted.
        Note: The generator validates these are positive ints, but the runner evaluates whether they
        are valid integer multiples of the actual data's base timeframe during backtesting.
    mtf_probability : float
        Probability [0, 1] that a generated condition will be assigned a timeframe.
    generated_at : str or None
        Inject a fixed timestamp for deterministic tests.

    Returns
    -------
    list[dict]
        Each dict contains ``strategy`` and ``provenance``.
    """
    rng = random.Random(seed)
    results: list[dict] = []

    if not isinstance(mtf_probability, (int, float)) or isinstance(mtf_probability, bool):
        raise ValueError(f"mtf_probability must be a float, got {type(mtf_probability).__name__}")
    if mtf_probability < 0.0 or mtf_probability > 1.0:
        raise ValueError(f"mtf_probability must be between 0.0 and 1.0, got {mtf_probability}")

    valid_tfs = set()
    for tf in allowed_timeframes:
        if not isinstance(tf, int) or isinstance(tf, bool):
            raise ValueError(f"allowed_timeframes elements must be int, got {type(tf).__name__} ({tf!r})")
        if tf <= 0:
            raise ValueError(f"allowed_timeframes elements must be positive, got {tf}")
        valid_tfs.add(tf)
    normalized_tfs = tuple(sorted(list(valid_tfs)))

    period_sma_min, period_sma_max = sma_period_range
    period_rsi_min, period_rsi_max = rsi_period_range
    thresh_rsi_min, thresh_rsi_max = rsi_threshold_range
    period_atr_min, period_atr_max = atr_period_range
    thresh_atr_min, thresh_atr_max = atr_threshold_range
    macd_f_min, macd_f_max = macd_fast_range
    macd_s_min, macd_s_max = macd_slow_range
    macd_sig_min, macd_sig_max = macd_signal_range
    thresh_vol_min, thresh_vol_max = volume_threshold_range
    period_vsma_min, period_vsma_max = volume_sma_period_range
    mult_vsma_min, mult_vsma_max = volume_sma_multiplier_range
    
    # Pad weights with 0.0 if caller provided old 4-element weights
    weights = list(indicator_weights)
    if len(weights) < len(_INDICATOR_TYPES):
        weights.extend([0.0] * (len(_INDICATOR_TYPES) - len(weights)))
    padded_weights = tuple(weights)

    for i in range(count):
        long_entry = _random_block(rng, "entry", padded_weights,
                                   period_sma_min, period_sma_max,
                                   period_rsi_min, period_rsi_max,
                                   thresh_rsi_min, thresh_rsi_max,
                                   period_atr_min, period_atr_max,
                                   thresh_atr_min, thresh_atr_max,
                                   macd_f_min, macd_f_max,
                                   macd_s_min, macd_s_max,
                                   macd_sig_min, macd_sig_max,
                                   thresh_vol_min, thresh_vol_max,
                                   period_vsma_min, period_vsma_max,
                                   mult_vsma_min, mult_vsma_max,
                                   normalized_tfs, mtf_probability)
        long_exit = _random_block(rng, "exit", padded_weights,
                                  period_sma_min, period_sma_max,
                                  period_rsi_min, period_rsi_max,
                                  thresh_rsi_min, thresh_rsi_max,
                                  period_atr_min, period_atr_max,
                                  thresh_atr_min, thresh_atr_max,
                                  macd_f_min, macd_f_max,
                                  macd_s_min, macd_s_max,
                                  macd_sig_min, macd_sig_max,
                                  thresh_vol_min, thresh_vol_max,
                                  period_vsma_min, period_vsma_max,
                                  mult_vsma_min, mult_vsma_max,
                                  normalized_tfs, mtf_probability)

        has_short = rng.random() < short_enabled_probability
        if has_short:
            short_entry = _random_block(rng, "entry", padded_weights,
                                        period_sma_min, period_sma_max,
                                        period_rsi_min, period_rsi_max,
                                        thresh_rsi_min, thresh_rsi_max,
                                        period_atr_min, period_atr_max,
                                        thresh_atr_min, thresh_atr_max,
                                        macd_f_min, macd_f_max,
                                        macd_s_min, macd_s_max,
                                        macd_sig_min, macd_sig_max,
                                        thresh_vol_min, thresh_vol_max,
                                        period_vsma_min, period_vsma_max,
                                        mult_vsma_min, mult_vsma_max,
                                        normalized_tfs, mtf_probability)
            short_exit = _random_block(rng, "exit", padded_weights,
                                       period_sma_min, period_sma_max,
                                       period_rsi_min, period_rsi_max,
                                       thresh_rsi_min, thresh_rsi_max,
                                       period_atr_min, period_atr_max,
                                       thresh_atr_min, thresh_atr_max,
                                       macd_f_min, macd_f_max,
                                       macd_s_min, macd_s_max,
                                       macd_sig_min, macd_sig_max,
                                       thresh_vol_min, thresh_vol_max,
                                       period_vsma_min, period_vsma_max,
                                       mult_vsma_min, mult_vsma_max,
                                       normalized_tfs, mtf_probability)
        else:
            short_entry = StrategyBlock()
            short_exit = StrategyBlock()

        strat = Strategy(
            name=f"strat_{i:04d}",
            long_entry=long_entry,
            long_exit=long_exit,
            short_entry=short_entry,
            short_exit=short_exit,
        )

        provenance = {
            "strategy_json": _strategy_to_dict(strat),
            "random_seed": seed,
            "generator_version": GENERATOR_VERSION,
            "rule_block_versions": {
                "SMA": "0.2.0", "RSI": "0.2.0", "MACD": "0.2.0", "ATR": "0.2.0",
                "VOLUME": "0.2.0", "VOLUME_SMA": "0.2.0",
            },
            "parameter_ranges": {
                "sma_period": list(sma_period_range),
                "rsi_period": list(rsi_period_range),
                "rsi_threshold": list(rsi_threshold_range),
                "atr_period": list(atr_period_range),
                "atr_threshold": [atr_threshold_range[0], atr_threshold_range[1]],
                "macd_fast": list(macd_fast_range),
                "macd_slow": list(macd_slow_range),
                "macd_signal": list(macd_signal_range),
                "volume_threshold": list(volume_threshold_range),
                "volume_sma_period": list(volume_sma_period_range),
                "volume_sma_multiplier": [volume_sma_multiplier_range[0], volume_sma_multiplier_range[1]],
                "short_enabled_probability": short_enabled_probability,
                "indicator_weights": list(padded_weights),
                "allowed_timeframes": list(normalized_tfs),
                "mtf_probability": float(mtf_probability),
            },
            "dataset_id": None,
            "instrument_profile_id": None,
            "build_task_id": None,
            "fitness_config": {
                "dimensions": ["total_pnl", "profit_factor", "max_drawdown_pnl",
                               "avg_trade", "total_trades"],
            },
            "elimination_config": {
                "min_trades": 0,
                "min_profit_factor": 0.0,
            },
            "generated_at": generated_at,
        }

        results.append({"strategy": strat, "provenance": provenance})

    return results


def _strategy_to_dict(strategy: Strategy) -> dict:
    """Serialize a Strategy to a JSON-compatible dict."""
    return asdict(strategy)


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _maybe_add_timeframe(
    params: dict,
    rng: random.Random,
    allowed_timeframes: tuple[int, ...],
    mtf_probability: float
) -> None:
    """Optionally inject a 'timeframe' into condition params."""
    if not allowed_timeframes or mtf_probability <= 0.0:
        return
    if rng.random() < mtf_probability:
        params["timeframe"] = rng.choice(allowed_timeframes)


def _random_block(
    rng: random.Random,
    direction: str,
    weights: tuple[float, ...],
    sma_min: int, sma_max: int,
    rsi_p_min: int, rsi_p_max: int,
    rsi_t_min: int, rsi_t_max: int,
    atr_p_min: int, atr_p_max: int,
    atr_t_min: float, atr_t_max: float,
    macd_f_min: int, macd_f_max: int,
    macd_s_min: int, macd_s_max: int,
    macd_sig_min: int, macd_sig_max: int,
    vol_t_min: int, vol_t_max: int,
    vsma_p_min: int, vsma_p_max: int,
    vsma_m_min: float, vsma_m_max: float,
    allowed_timeframes: tuple[int, ...] = (),
    mtf_probability: float = 0.0,
) -> StrategyBlock:
    """Generate one block (entry or exit) with a randomly chosen indicator."""
    ind = rng.choices(_INDICATOR_TYPES, weights=weights, k=1)[0]

    if ind == "SMA":
        period = rng.randint(sma_min, sma_max)
        op = ">" if direction == "entry" else "<"
        cond = Condition(indicator="SMA", params={"period": period}, operator=op)

    elif ind == "RSI":
        period = rng.randint(rsi_p_min, rsi_p_max)
        threshold = float(rng.randint(rsi_t_min, rsi_t_max))
        op = ">" if direction == "entry" else "<"
        cond = Condition(indicator="RSI", params={"period": period},
                         operator=op, right=threshold)

    elif ind == "MACD":
        fast = rng.randint(macd_f_min, macd_f_max)
        slow = rng.randint(macd_s_min, macd_s_max)
        if fast >= slow:
            fast, slow = slow - 1, fast + 1  # ensure fast < slow
            fast = max(fast, macd_f_min)
        sig = rng.randint(macd_sig_min, macd_sig_max)
        op = ">" if direction == "entry" else "<"
        cond = Condition(indicator="MACD", params={
            "fast": fast, "slow": slow, "signal": sig,
        }, operator=op)

    elif ind == "ATR":
        period = rng.randint(atr_p_min, atr_p_max)
        threshold = round(rng.uniform(atr_t_min, atr_t_max), 2)
        op = ">" if direction == "entry" else "<"
        cond = Condition(indicator="ATR", params={"period": period},
                         operator=op, right=threshold)
                         
    elif ind == "VOLUME":
        threshold = rng.randint(vol_t_min, vol_t_max)
        op = ">" if direction == "entry" else "<"
        cond = Condition(indicator="VOLUME", params={},
                         operator=op, right=float(threshold))
                         
    elif ind == "VOLUME_SMA":
        period = rng.randint(vsma_p_min, vsma_p_max)
        multiplier = round(rng.uniform(vsma_m_min, vsma_m_max), 2)
        op = ">" if direction == "entry" else "<"
        cond = Condition(indicator="VOLUME_SMA", params={"period": period},
                         operator=op, right=multiplier)
    else:
        return StrategyBlock()

    _maybe_add_timeframe(cond.params, rng, allowed_timeframes, mtf_probability)

    return StrategyBlock(conditions=[cond], logic="AND")
