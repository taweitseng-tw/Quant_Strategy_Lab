"""Service layer for strategy operations — Task 006B."""

from __future__ import annotations

from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from core.models.instrument import InstrumentProfile
from strategy_engine.generator import generate_strategies
from backtest_engine.runner import run_backtest
from strategy_engine.ranking import rank_strategies, DEFAULT_WEIGHTS
from validation_engine.elimination import EliminationConfig, evaluate_elimination


class StrategyService:
    """Handles strategy generation, backtesting, and ranking outside UI widgets."""

    # Conservative default elimination config for prototype/v0.1.
    # Strategies that fail any threshold are marked "eliminated" but
    # remain in the result list so users can inspect why.
    DEFAULT_ELIMINATION_CONFIG = EliminationConfig(
        min_trade_count=5,
        min_profit_factor=0.5,
        max_drawdown_pnl=50_000.0,
        min_avg_trade=-500.0,
    )

    def __init__(self, elimination_config: EliminationConfig | None = None) -> None:
        self.elimination_config = elimination_config or self.DEFAULT_ELIMINATION_CONFIG
        self.fitness_weights = dict(DEFAULT_WEIGHTS)

    def update_elimination_config(self, config_dict: dict) -> None:
        """Update the elimination configuration from a primitive dictionary.
        
        Unknown keys are safely ignored. Keys mapping to None disable that threshold.
        Passing an empty dict preserves the existing configuration.
        """
        current_dict = self.elimination_config.to_dict()
        valid_keys = set(current_dict.keys())
        
        updated = False
        for k, v in config_dict.items():
            if k in valid_keys:
                current_dict[k] = v
                updated = True
                
        if updated:
            self.elimination_config = EliminationConfig(**current_dict)

    def get_elimination_config_dict(self) -> dict:
        """Get the current elimination configuration as a primitive dictionary."""
        return self.elimination_config.to_dict()

    def get_fitness_weights(self) -> dict:
        """Return a defensive copy of the current fitness weights."""
        return dict(self.fitness_weights)

    def update_fitness_weights(self, weights: dict) -> None:
        """Update fitness weights with partial or full replacement.

        - Keys from ``DEFAULT_WEIGHTS`` that are present in *weights* are
          updated (values clamped to [0.0, 1.0]).
        - Keys not in *weights* are preserved.
        - Unknown keys and non-numeric values are silently ignored.
        """
        for k, v in weights.items():
            if k in DEFAULT_WEIGHTS and isinstance(v, (int, float)) and not isinstance(v, bool):
                self.fitness_weights[k] = max(0.0, min(1.0, float(v)))

    def get_ranked_strategies(
        self,
        dataset_df: pd.DataFrame | None = None,
        instrument: InstrumentProfile | None = None,
        injected_strategies: list | None = None,
    ) -> tuple[list[dict], bool]:
        """Generate, backtest, and rank 10 strategies (plus any injected).
        
        If dataset_df is None, generates and uses a deterministic mock dataset.
        
        Returns:
            tuple: (ranked_strategies_list, is_mock_data_boolean)
        """
        is_mock = False
        if dataset_df is None:
            dataset_df = self.generate_deterministic_mock_ohlcv()
            is_mock = True
            
        # 1. Generate 10 deterministic strategies
        generated = generate_strategies(count=10, seed=42)
        
        # Inject extra strategies if provided (GA, GP, Imported)
        if injected_strategies:
            for strat in injected_strategies:
                gen_name = "ga_search"
                src_type = "ga_evolved"
                
                if strat.name.startswith("[GP Best]"):
                    gen_name = "gp_search"
                    src_type = "gp_evolved"
                elif strat.name.startswith("[Imported]"):
                    gen_name = "json_import"
                    src_type = "imported"
                    
                generated.append({
                    "strategy": strat,
                    "provenance": {
                        "generator": gen_name,
                        "generator_version": f"{gen_name}_1.0",
                        "source_type": src_type,
                        "injected_strategy": True,
                        "strategy_name": strat.name,
                    },
                })

        # 2. Run backtest for each strategy
        backtest_results = []
        for item in generated:
            strategy = item["strategy"]
            provenance = item["provenance"]
            
            # Run event-driven backtest
            if instrument is not None:
                backtest_res = run_backtest(
                    strategy=strategy,
                    df=dataset_df,
                    initial_capital=100_000.0,
                    instrument=instrument,
                    commission=None,
                    slippage_ticks=None,
                    tick_size=None,
                )
            else:
                backtest_res = run_backtest(
                    strategy=strategy,
                    df=dataset_df,
                    initial_capital=100_000.0,
                    commission=2.0,
                    slippage_ticks=1.0,
                    tick_size=0.1
                )
            
            backtest_results.append({
                "strategy": strategy,
                "provenance": provenance,
                "metrics": backtest_res.metrics,
                "equity_curve": backtest_res.equity_curve,
                "drawdown_curve": backtest_res.drawdown_curve,
                "trades": backtest_res.trades,
                "warnings": backtest_res.warnings,
            })
            
        # 3. Rank strategies based on fitness score
        ranked = rank_strategies(backtest_results, weights=self.fitness_weights)

        # 4. Apply elimination rules — mark strategies without removing them.
        for entry in ranked:
            elimination = evaluate_elimination(
                entry["metrics"],
                self.elimination_config,
            )
            entry["elimination_passed"] = elimination.passed
            entry["elimination_failed_rules"] = elimination.failed_rules
            entry["elimination_status"] = "passed" if elimination.passed else "eliminated"

        return ranked, is_mock

    @staticmethod
    def generate_deterministic_mock_ohlcv(seed: int = 42, count: int = 200) -> pd.DataFrame:
        """Generate a fully deterministic daily OHLCV dataset for backtesting."""
        rng = np.random.default_rng(seed)
        start_time = datetime(2026, 1, 1)
        dates = [start_time + timedelta(days=i) for i in range(count)]
        
        open_prices = []
        high_prices = []
        low_prices = []
        close_prices = []
        volumes = []
        
        current_price = 100.0
        for _ in range(count):
            o = current_price + rng.normal(0, 1.0)
            c = o + rng.normal(0.1, 1.5)
            h = max(o, c) + abs(rng.normal(0.3, 0.5))
            l = min(o, c) - abs(rng.normal(0.3, 0.5))
            v = int(rng.uniform(1000, 5000))
            
            open_prices.append(o)
            high_prices.append(h)
            low_prices.append(l)
            close_prices.append(c)
            volumes.append(v)
            current_price = c
            
        df = pd.DataFrame({
            "datetime": dates,
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "volume": volumes
        })
        return df
