from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
)
from core.models.strategy import Strategy

THRESHOLD_INDICATORS = {"RSI", "ATR"}


class ParameterHeatmapWidget(QWidget):
    """A passive widget for visualizing strategy parameters vs metrics.
    
    Displays numeric parameters from Strategy blocks alongside key metrics.
    Uses simple color shading for metric columns.
    """

    def __init__(self) -> None:
        super().__init__()
        self.ranked_data: list[dict] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.lbl_empty = QLabel("No strategy data available")
        self.lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_empty.setStyleSheet("color: #b0b0b5; font-size: 14px; font-style: italic;")

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.lbl_empty)
        layout.addWidget(self.table)

    def set_data(self, ranked_data: list[dict] | None) -> None:
        self.ranked_data = ranked_data if ranked_data else []
        self._refresh_table()

    def _extract_parameters(self, strategy: Strategy) -> dict[str, float]:
        """Extract all numeric parameters from the strategy's conditions."""
        params = {}
        blocks = {
            "LE": strategy.long_entry,
            "LX": strategy.long_exit,
            "SE": strategy.short_entry,
            "SX": strategy.short_exit,
        }
        for b_name, block in blocks.items():
            if block:
                for i, cond in enumerate(block.conditions):
                    ind = cond.indicator
                    prefix = f"{b_name}.{ind}" if len(block.conditions) == 1 else f"{b_name}.{ind}_{i}"
                    
                    if isinstance(cond.params, dict):
                        for k, v in cond.params.items():
                            if isinstance(v, (int, float)):
                                params[f"{prefix}.{k}"] = float(v)
                                
                    if cond.indicator.upper() in THRESHOLD_INDICATORS and isinstance(cond.right, (int, float)):
                        params[f"{prefix}.threshold"] = float(cond.right)
        return params

    def _as_float(self, value: object, default: float = 0.0) -> float:
        """Return a finite numeric value for display metrics."""
        if isinstance(value, (int, float)):
            return float(value)
        return default

    def _refresh_table(self) -> None:
        if not self.ranked_data:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.table.hide()
            self.lbl_empty.show()
            return

        self.lbl_empty.hide()
        self.table.show()

        # Gather all unique parameter keys
        all_param_keys = set()
        extracted_params_list = []
        for entry in self.ranked_data:
            strat = entry.get("strategy")
            if strat:
                params = self._extract_parameters(strat)
                extracted_params_list.append(params)
                all_param_keys.update(params.keys())
            else:
                extracted_params_list.append({})

        param_cols = sorted(list(all_param_keys))
        
        # Base columns
        base_cols = ["Rank", "Strategy", "Fitness", "Net PnL", "PF"]
        all_cols = base_cols + param_cols
        
        self.table.setColumnCount(len(all_cols))
        self.table.setHorizontalHeaderLabels(all_cols)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        self.table.setRowCount(len(self.ranked_data))

        # Determine min/max for metrics to apply shading
        metrics_stats = {
            "Fitness": {"min": float("inf"), "max": float("-inf")},
            "Net PnL": {"min": float("inf"), "max": float("-inf")},
            "PF": {"min": float("inf"), "max": float("-inf")}
        }
                         
        for entry in self.ranked_data:
            fitness = self._as_float(entry.get("fitness", 0.0))
            metrics = entry.get("metrics", {})
            pnl = self._as_float(metrics.get("total_pnl", 0.0))
            pf = self._as_float(metrics.get("profit_factor", 0.0))
            
            metrics_stats["Fitness"]["min"] = min(metrics_stats["Fitness"]["min"], fitness)
            metrics_stats["Fitness"]["max"] = max(metrics_stats["Fitness"]["max"], fitness)
            
            metrics_stats["Net PnL"]["min"] = min(metrics_stats["Net PnL"]["min"], pnl)
            metrics_stats["Net PnL"]["max"] = max(metrics_stats["Net PnL"]["max"], pnl)
            
            metrics_stats["PF"]["min"] = min(metrics_stats["PF"]["min"], pf)
            metrics_stats["PF"]["max"] = max(metrics_stats["PF"]["max"], pf)

        for row, (entry, params) in enumerate(zip(self.ranked_data, extracted_params_list)):
            strat = entry.get("strategy")
            strat_name = strat.name if strat else "Unknown"
            rank = entry.get("rank", row + 1)
            fitness = self._as_float(entry.get("fitness", 0.0))
            metrics = entry.get("metrics", {})
            pnl = self._as_float(metrics.get("total_pnl", 0.0))
            pf = self._as_float(metrics.get("profit_factor", 0.0))

            # Rank
            self.table.setItem(row, 0, QTableWidgetItem(str(rank)))
            # Strategy
            self.table.setItem(row, 1, QTableWidgetItem(strat_name))
            
            # Metrics with coloring
            self.table.setItem(row, 2, self._create_colored_item(f"{fitness:.4f}", fitness, metrics_stats["Fitness"]))
            self.table.setItem(row, 3, self._create_colored_item(f"{pnl:.2f}", pnl, metrics_stats["Net PnL"]))
            self.table.setItem(row, 4, self._create_colored_item(f"{pf:.2f}", pf, metrics_stats["PF"]))

            # Parameters
            for col_idx, p_key in enumerate(param_cols, start=len(base_cols)):
                val = params.get(p_key)
                if val is not None:
                    # Format float nicely
                    val_str = f"{val:.2f}" if isinstance(val, float) and not val.is_integer() else str(int(val)) if isinstance(val, float) and val.is_integer() else str(val)
                    item = QTableWidgetItem(val_str)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, col_idx, item)
                else:
                    item = QTableWidgetItem("-")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, col_idx, item)

    def _create_colored_item(self, text: str, value: float, stats: dict) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        vmin, vmax = stats["min"], stats["max"]
        if vmax > vmin:
            # Normalize to 0-1
            norm = (value - vmin) / (vmax - vmin)
            # Red: 239, 83, 80 (#ef5350)
            # Green: 38, 166, 154 (#26a69a)
            r = int(239 + norm * (38 - 239))
            g = int(83 + norm * (166 - 83))
            b = int(80 + norm * (154 - 80))
            item.setForeground(QColor(r, g, b))
        return item
