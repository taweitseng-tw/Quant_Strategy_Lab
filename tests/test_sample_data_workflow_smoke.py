"""Sample data workflow smoke tests - Tasks 265-270.

These tests use real sample CSV files and existing service/engine APIs only.
They avoid UI automation and do not introduce new architecture.
"""

from __future__ import annotations

from pathlib import Path

from app.services.data_service import DataService
from backtest_engine.runner import run_backtest
from core.models.strategy import Condition, Strategy, StrategyBlock
from reports.generator import generate_markdown_report


SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"
SAMPLE_OHLCV = SAMPLE_DIR / "sample_ohlcv.csv"
SAMPLE_TXF = SAMPLE_DIR / "sample_txf.csv"


def _make_simple_strategy() -> Strategy:
    """Create a minimal long-only moving-average strategy."""
    return Strategy(
        name="sample_smoke",
        long_entry=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 5}, operator=">")],
            logic="AND",
        ),
        long_exit=StrategyBlock(
            conditions=[Condition(indicator="SMA", params={"period": 5}, operator="<")],
            logic="AND",
        ),
    )


def test_sample_ohlcv_file_exists() -> None:
    """The sample OHLCV file must exist and be non-empty."""
    assert SAMPLE_OHLCV.is_file(), f"Sample file not found: {SAMPLE_OHLCV}"
    assert SAMPLE_OHLCV.stat().st_size > 0


def test_sample_txf_file_exists() -> None:
    """The sample TXF file must exist and be non-empty."""
    assert SAMPLE_TXF.is_file(), f"Sample file not found: {SAMPLE_TXF}"
    assert SAMPLE_TXF.stat().st_size > 0


def test_sample_ohlcv_import_produces_normalized_data() -> None:
    """Import sample_ohlcv.csv through DataService and verify normalized output."""
    df, meta, quality = DataService().import_file(
        SAMPLE_OHLCV,
        symbol="TEST",
        timeframe="1min",
    )

    assert len(df) > 0
    assert list(df.columns) == ["datetime", "open", "high", "low", "close", "volume"]
    assert meta.symbol == "TEST"
    assert meta.row_count == len(df)
    assert quality.passed, f"Quality check failed: {quality.errors}"


def test_sample_txf_import_produces_normalized_data() -> None:
    """Import sample_txf.csv through DataService and verify normalized output."""
    df, meta, quality = DataService().import_file(
        SAMPLE_TXF,
        symbol="TXF",
        timeframe="1min",
    )

    assert len(df) > 0
    assert list(df.columns) == ["datetime", "open", "high", "low", "close", "volume"]
    assert meta.symbol == "TXF"
    assert meta.row_count == len(df)
    assert quality.passed, f"Quality check failed: {quality.errors}"


def test_sample_ohlcv_backtest_produces_structured_output() -> None:
    """Import sample OHLCV, run backtest, and verify structured output."""
    df, _, _ = DataService().import_file(SAMPLE_OHLCV, symbol="TEST")
    result = run_backtest(_make_simple_strategy(), df)

    assert result.metrics is not None
    assert "total_pnl" in result.metrics
    assert "profit_factor" in result.metrics
    assert "max_drawdown_pnl" in result.metrics
    assert "total_trades" in result.metrics
    assert result.metrics["total_trades"] > 0

    assert len(result.trades) == result.metrics["total_trades"]
    assert result.equity_curve is not None
    assert len(result.equity_curve) > 1

    assert result.assumptions is not None
    assert "initial_capital" in result.assumptions


def test_sample_txf_backtest_produces_structured_output() -> None:
    """Run the same backtest smoke using TXF sample data."""
    df, _, _ = DataService().import_file(SAMPLE_TXF, symbol="TXF", timeframe="1min")
    result = run_backtest(_make_simple_strategy(), df)

    assert result.metrics["total_trades"] > 0
    assert len(result.trades) == result.metrics["total_trades"]
    assert result.equity_curve is not None
    assert len(result.equity_curve) > 1


def test_sample_workflow_produces_markdown_report() -> None:
    """Generate a markdown report from sample-data backtest output."""
    df, _, _ = DataService().import_file(SAMPLE_OHLCV, symbol="TEST")
    strategy = _make_simple_strategy()
    result = run_backtest(strategy, df)

    report = generate_markdown_report(strategy, result)

    assert isinstance(report, str)
    assert len(report) > 100
    assert "Total Net Profit" in report
    assert "Profit Factor" in report
    assert "Total Trades" in report
    assert strategy.name in report
