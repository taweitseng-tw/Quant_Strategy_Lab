"""CSV importer for MultiCharts / TradeStation-style OHLCV data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.models.dataset import DatasetMeta
from data_engine.normalizer import INTERNAL_COLUMNS, NormalizerError, normalize


class CsvImporter:
    """Read a source CSV, normalize to internal OHLCV schema, and save the
    normalized output into the project's ``data/raw/`` directory.
    """

    def import_file(
        self,
        source_path: Path | str,
        project_root: Path | str,
        *,
        symbol: str = "",
        timeframe: str = "",
    ) -> tuple[pd.DataFrame, DatasetMeta]:
        """Import *source_path*, normalize, and save to *project_root*/data/raw/.

        Returns ``(normalized_df, dataset_meta)``.
        """
        source = Path(source_path).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Source CSV not found: {source}")

        project = Path(project_root).resolve()

        # --- 1. Read CSV -------------------------------------------------------------------
        try:
            raw_df = pd.read_csv(source)
        except Exception as exc:
            raise NormalizerError(f"Failed to read CSV: {exc}") from exc

        if raw_df.empty:
            raise NormalizerError("CSV file contains no data rows.")

        # --- 2. Normalize ------------------------------------------------------------------
        normalized = normalize(raw_df)

        # --- 3. Save normalized output to project data/raw/ --------------------------------
        raw_dir = project / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)

        safe_name = source.stem or "imported"
        out_path = raw_dir / f"{safe_name}_normalized.csv"
        normalized.to_csv(out_path, index=False)

        # --- 4. Build metadata -------------------------------------------------------------
        meta = DatasetMeta(
            name=safe_name,
            symbol=symbol,
            timeframe=timeframe,
            source_type="csv",
            source_path=str(source),
            normalized_path=str(out_path),
            row_count=len(normalized),
            start_datetime=str(normalized["datetime"].iloc[0]),
            end_datetime=str(normalized["datetime"].iloc[-1]),
        )

        return normalized, meta
