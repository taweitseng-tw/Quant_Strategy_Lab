"""Tests for TXF real data import and processing — Task 011."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from core.models.instrument import InstrumentProfile
from core.models.strategy import Condition, Strategy, StrategyBlock
from data_engine.importers.csv_importer import CsvImporter
from data_engine.normalizer import INTERNAL_COLUMNS
from data_engine.resampler import resample
from backtest_engine.runner import run_backtest


# ---------------------------------------------------------------------------
# Fixture paths
# ---------------------------------------------------------------------------

SAMPLE_TXF = Path(__file__).resolve().parent.parent / "sample_data" / "sample_txf.csv"


# ---------------------------------------------------------------------------
# TXF instrument profile
# ---------------------------------------------------------------------------

def make_txf_profile(**overrides) -> InstrumentProfile:
    """Create a TXF instrument profile with defaults matching TAIFEX specs.

    Defaults:
      symbol=TXF, market=TAIFEX, tick_size=1, point_value=200,
      commission_value=50 TWD per side, slippage_ticks=1, currency=TWD.
    """
    defaults = dict(
        symbol="TXF",
        name="Taiwan Index Futures",
        market="TAIFEX",
        tick_size=1.0,
        point_value=200.0,       # NT$200 per index point
        commission_value=50.0,   # approx per-side commission
        slippage_ticks=1.0,
        currency="TWD",
    )
    defaults.update(overrides)
    return InstrumentProfile(**defaults)


# ---------------------------------------------------------------------------
# TXF format parsing
# ---------------------------------------------------------------------------


def test_txf_csv_format_is_recognised():
    """The TXF Date/Time/Open/High/Low/Close/TotalVolume columns must parse."""
    df = pd.read_csv(SAMPLE_TXF)
    assert list(df.columns) == ["Date", "Time", "Open", "High", "Low", "Close", "TotalVolume"]
    assert len(df) == 15


def test_txf_normalizes_to_canonical_schema():
    """TXF data must normalize to datetime, open, high, low, close, volume."""
    df = pd.read_csv(SAMPLE_TXF)
    result = pd.read_csv(SAMPLE_TXF)
    from data_engine.normalizer import normalize
    normalized = normalize(result)

    assert list(normalized.columns) == list(INTERNAL_COLUMNS)
    assert len(normalized) == 15
    assert normalized["datetime"].dtype.kind == "M"
    assert normalized["volume"].iloc[0] == 78


def test_txf_date_time_combined_correctly():
    """Date (2002/7/22) + Time (09:01:00) must become a single datetime."""
    df = pd.read_csv(SAMPLE_TXF)
    from data_engine.normalizer import normalize
    normalized = normalize(df)

    assert normalized["datetime"].iloc[0] == pd.Timestamp("2002-07-22 09:01:00")
    assert normalized["datetime"].iloc[-1] == pd.Timestamp("2002-07-22 09:15:00")


def test_txf_importer_saves_normalized_output(tmp_path):
    """The CsvImporter must save normalized TXF CSV to data/raw/."""
    importer = CsvImporter()
    _, meta = importer.import_file(SAMPLE_TXF, tmp_path, symbol="TXF", timeframe="1min")

    out_path = Path(meta.normalized_path)
    assert out_path.is_file()
    df2 = pd.read_csv(out_path)
    assert list(df2.columns) == list(INTERNAL_COLUMNS)
    assert len(df2) == 15


# ---------------------------------------------------------------------------
# TXF resampling
# ---------------------------------------------------------------------------


def test_txf_1min_resamples_to_5min():
    """15 TXF 1-min bars → 4 clock-aligned 5-min buckets.

    pd.Grouper(freq="5min") aligns to clock boundaries, so:
      - 09:01–09:04 → bucket 09:00 (4 bars)
      - 09:05–09:09 → bucket 09:05 (5 bars)
      - 09:10–09:14 → bucket 09:10 (5 bars)
      - 09:15        → bucket 09:15 (1 bar)
    """
    df = pd.read_csv(SAMPLE_TXF)
    from data_engine.normalizer import normalize
    normalized = normalize(df)

    result = resample(normalized, source_minutes=1, target_minutes=5)
    assert len(result) == 4

    # First bucket: bars 09:01–09:04 (only 4 bars before the 09:05 boundary).
    row0 = result.iloc[0]
    assert row0["datetime"] == pd.Timestamp("2002-07-22 09:00:00")
    assert row0["open"] == 5036.0
    assert row0["high"] == 5049.0
    assert row0["low"] == 5035.0
    assert row0["close"] == 5042.0
    assert row0["volume"] == 78 + 72 + 61 + 79  # = 290
    assert row0["available_at"] == pd.Timestamp("2002-07-22 09:04:00")


# ---------------------------------------------------------------------------
# TXF backtest (smoke test)
# ---------------------------------------------------------------------------


def test_txf_backtest_with_instrument_profile():
    """Backtest on TXF data with the TXF instrument profile must produce
    dollar-denominated PnL in TWD."""
    df = pd.read_csv(SAMPLE_TXF)
    from data_engine.normalizer import normalize
    normalized = normalize(df)

    txf = make_txf_profile()
    strat = Strategy(
        name="txf_smoke",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 3}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 3}, operator="<"),
        ], logic="AND"),
    )

    result = run_backtest(strat, normalized, instrument=txf)

    # Structured output integrity.
    assert isinstance(result.trades, list)
    assert result.equity_curve is not None

    # TXF profile recorded.
    assert result.assumptions["instrument"] == "TXF"
    assert result.assumptions["point_value"] == 200.0
    assert result.assumptions["commission_model"] == "per_side"

    # Accounting identity holds.
    if result.trades:
        total_pnl = sum(t.pnl for t in result.trades)
        equity_change = result.equity_curve["equity"].iloc[-1] - 100_000.0
        assert total_pnl == pytest.approx(equity_change)


def test_txf_profile_point_value_affects_pnl():
    """Changing point_value from 200→400 must double the PnL magnitude."""
    df = pd.read_csv(SAMPLE_TXF)
    from data_engine.normalizer import normalize
    normalized = normalize(df)

    strat = Strategy(
        name="txf_pv",
        long_entry=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 3}, operator=">"),
        ], logic="AND"),
        long_exit=StrategyBlock(conditions=[
            Condition(indicator="SMA", params={"period": 3}, operator="<"),
        ], logic="AND"),
    )

    # Use zero commission to isolate the point_value scaling effect.
    r200 = run_backtest(strat, normalized, instrument=make_txf_profile(point_value=200.0, commission_value=0.0))
    r400 = run_backtest(strat, normalized, instrument=make_txf_profile(point_value=400.0, commission_value=0.0))

    if len(r200.trades) > 0:
        ratio = r400.metrics["total_pnl"] / r200.metrics["total_pnl"]
        assert ratio == pytest.approx(2.0)  # 400/200 = 2×
