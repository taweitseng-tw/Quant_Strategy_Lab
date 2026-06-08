"""ProjectArchiveDataSource — provides archive data from the project repository layer.

Satisfies the ``ArchiveDataSource`` protocol used by ``ArchiveBuilder``.
No PySide6 / UI imports.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any


class ProjectArchiveDataSource:
    """Provides strategy, dataset, and validation data from project repositories.

    Constructor parameters
    ----------------------
    strategy_rows_provider : callable
        A zero-argument callable returning a list of dicts with keys
        (at minimum) ``id``, ``name``, ``strategy_json``.
        Expected to wrap ``StrategyRepository.list_all_raw()``.
        The adapter consumes raw strategy rows filtered by strategy_uid
        inside ``strategy_json``.
    dataset_rows_provider : callable
        A single-argument callable ``(dataset_id: int) -> dict | None``.
        Expected to wrap ``DatasetRepository.get_raw_by_id()``.
    validation_result_provider : callable
        A single-argument callable ``(strategy_uid: str) -> dict | None``.
        Expected to look up validation results (e.g. from a stored dict
        or service method).
    """

    def __init__(
        self,
        strategy_rows_provider,
        dataset_rows_provider,
        validation_result_provider,
    ) -> None:
        self._get_strategies = strategy_rows_provider
        self._get_dataset = dataset_rows_provider
        self._get_validation = validation_result_provider

    # ------------------------------------------------------------------
    # ArchiveDataSource protocol
    # ------------------------------------------------------------------

    def get_strategy(self, strategy_uid: str) -> dict[str, Any] | None:
        """Return a strategy dict matching *strategy_uid* or None.

        Scans all stored strategy rows, parses ``strategy_json``, and
        looks for the matching ``strategy_uid`` field inside the JSON.
        Returns None if the UID is not found, the JSON is malformed, or
        the JSON is not a dict.
        """
        rows = self._get_strategies()
        for row in rows:
            raw = row.get("strategy_json")
            if not raw:
                continue
            try:
                payload = json.loads(raw) if isinstance(raw, str) else raw
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(payload, dict) and payload.get("strategy_uid") == strategy_uid:
                # Return the full row dict enriched with parsed payload fields.
                result = dict(row)
                result["strategy_json"] = json.dumps(payload, ensure_ascii=False)
                result["name"] = payload.get("name", row.get("name", ""))
                result["generator_version"] = payload.get("generator_version", "0.2.0")
                return result
        return None

    def get_dataset(self, dataset_id: int) -> dict[str, Any] | None:
        """Return a dataset dict or None."""
        return self._get_dataset(dataset_id)

    def get_validation_result(self, strategy_uid: str) -> dict[str, Any] | None:
        """Return a validation result dict or None."""
        result = self._get_validation(strategy_uid)
        if result is None:
            return None
        if isinstance(result, dict):
            return result
        if is_dataclass(result):
            return asdict(result)
        return None
