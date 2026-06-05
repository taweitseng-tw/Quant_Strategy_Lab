"""Large-load GA profiling harness for measuring backtest optimizations.

This script executes a large GA search (100 pop * 5 gen = 500 backtests)
over a 5,000 bar dataset. It uses cProfile and measures wall-clock time.
"""

import cProfile
import pstats
import time
from pathlib import Path

import numpy as np
import pandas as pd

from app.services.ga_service import GASearchConfig, run_ga_search


def _make_large_df(n_bars: int = 5000) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    times = pd.date_range("2024-01-01 00:00", periods=n_bars, freq="5min")
    close = 100.0 + np.cumsum(rng.normal(0.01, 0.4, n_bars))
    close = np.maximum(close, 10.0)
    noise = rng.uniform(0.2, 1.0, n_bars)
    
    # Simulate basic OHLCV
    return pd.DataFrame({
        "datetime": times,
        "open":  close - noise * 0.3,
        "high":  close + noise,
        "low":   close - noise,
        "close": close,
        "volume": rng.integers(500, 5000, n_bars),
    })


def main():
    print("Generating large dataset (5000 bars)...")
    df = _make_large_df(5000)
    
    # 500 total evaluations: 100 population * 5 generations
    cfg = GASearchConfig(
        population_size=100,
        max_generations=5,
        base_seed=123,
        elite_count=5,
        crossover_prob=0.8,
        mutation_prob=0.2
    )
    
    prof_path = Path("docs/perf_baselines/post_phase3_acceptance.prof")
    prof_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Running large load GA search (Pop={cfg.population_size}, Gen={cfg.max_generations})...")
    
    pr = cProfile.Profile()
    
    start_time = time.perf_counter()
    pr.enable()
    
    # Run the workload
    result = run_ga_search(df, config=cfg)
    
    pr.disable()
    end_time = time.perf_counter()
    
    wall_clock = end_time - start_time
    print(f"Wall-clock execution time: {wall_clock:.4f} seconds.")
    print(f"Best score achieved: {result.best_score:.4f}")
    
    pr.dump_stats(prof_path)
    print(f"cProfile stats saved to: {prof_path}")
    
    # Print top 15 cumulative time functions
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.CUMULATIVE).print_stats(15)

if __name__ == "__main__":
    main()
