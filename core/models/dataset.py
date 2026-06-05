"""Dataset metadata model — matches datasets table per PRD §15.2."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class DatasetMeta:
    """Metadata for one imported OHLCV dataset — matches PRD §15.2."""

    name: str
    project_id: int | None = None
    symbol: str = ""
    timeframe: str = ""
    source_type: str = "csv"
    source_path: str = ""
    normalized_path: str = ""
    row_count: int = 0
    start_datetime: str = ""
    end_datetime: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
