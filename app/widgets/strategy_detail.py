"""StrategyDetailWidget for displaying human-readable strategy information."""

from __future__ import annotations

import html

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QGridLayout, QTextBrowser, QPushButton
)
from PySide6.QtCore import Qt, Signal
from core.models.strategy import Strategy

THRESHOLD_INDICATORS = {"RSI", "ATR"}


class StrategyDetailWidget(QWidget):
    """A passive inspector widget to display strategy details, logic, and metrics."""
    
    add_custom_condition_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.set_strategy_data(None)
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        self.content_layout.setSpacing(12)
        
        # Header (Name & Status)
        self.lbl_name = QLabel()
        self.lbl_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #26a69a;")
        
        self.lbl_status = QLabel()
        self.lbl_status.setWordWrap(True)
        
        # Metrics Grid
        self.metrics_frame = QFrame()
        self.metrics_frame.setStyleSheet("background-color: #1e1e24; border-radius: 4px; padding: 8px;")
        metrics_layout = QGridLayout(self.metrics_frame)
        
        self.lbl_fitness = QLabel("Fitness: -")
        self.lbl_pnl = QLabel("Total PnL: -")
        self.lbl_pf = QLabel("Profit Factor: -")
        self.lbl_trades = QLabel("Trades: -")
        
        metrics_layout.addWidget(self.lbl_fitness, 0, 0)
        metrics_layout.addWidget(self.lbl_pnl, 0, 1)
        metrics_layout.addWidget(self.lbl_pf, 1, 0)
        metrics_layout.addWidget(self.lbl_trades, 1, 1)
        
        # Provenance
        self.lbl_provenance = QLabel()
        self.lbl_provenance.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        
        # Blocks (TextBrowser for easy markdown-like reading)
        self.txt_blocks = QTextBrowser()
        self.txt_blocks.setStyleSheet(
            "background-color: #1e1e24; border: 1px solid #2a2a2e; "
            "padding: 8px; font-family: monospace; font-size: 13px;"
        )
        
        self.content_layout.addWidget(self.lbl_name)
        self.content_layout.addWidget(self.lbl_status)
        self.content_layout.addWidget(self.metrics_frame)
        self.content_layout.addWidget(self.lbl_provenance)
        
        lbl_logic = QLabel("Strategy Logic")
        lbl_logic.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        
        self.btn_add_condition = QPushButton("+ Add Custom Condition")
        self.btn_add_condition.setStyleSheet("""
            QPushButton {
                background-color: #5c6bc0;
                color: white;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover { background-color: #7986cb; }
            QPushButton:disabled { background-color: #424242; color: #757575; }
        """)
        self.btn_add_condition.clicked.connect(self.add_custom_condition_requested.emit)
        self.btn_add_condition.setEnabled(False)
        
        logic_header_layout = QHBoxLayout()
        logic_header_layout.addWidget(lbl_logic)
        logic_header_layout.addStretch()
        logic_header_layout.addWidget(self.btn_add_condition)
        
        self.content_layout.addLayout(logic_header_layout)
        self.content_layout.addWidget(self.txt_blocks, stretch=1)
        
        self.content_layout.addStretch()
        self.scroll.setWidget(self.content_widget)
        layout.addWidget(self.scroll)
        
    def set_strategy_data(self, ranked_entry: dict | None) -> None:
        """Update the widget with data from the strategy ranking list."""
        if not ranked_entry:
            self._show_empty()
            return
            
        strategy: Strategy | None = ranked_entry.get("strategy")
        if not strategy:
            self._show_empty()
            return
            
        self.btn_add_condition.setEnabled(True)
        self.lbl_name.setText(html.escape(strategy.name or "Unnamed Strategy"))
        
        # Status / Elimination
        elimination_passed = ranked_entry.get("elimination_passed", True)
        failed_rules = ranked_entry.get("elimination_failed_rules", []) or []
        if not elimination_passed:
            rules_str = html.escape(", ".join(str(r) for r in failed_rules) if failed_rules else "Unknown")
            self.lbl_status.setText(f"Status: ELIMINATED\nFailed rules: {rules_str}")
            self.lbl_status.setStyleSheet("color: #ef5350; font-weight: bold;")
        else:
            self.lbl_status.setText("Status: PASSED / VALID")
            self.lbl_status.setStyleSheet("color: #26a69a; font-weight: bold;")
            
        # Metrics
        metrics = ranked_entry.get("metrics", {}) or {}
        fitness = self._as_float(ranked_entry.get("fitness", 0.0))
        pnl = self._as_float(metrics.get("total_pnl", ranked_entry.get("total_pnl", 0.0)))
        pf = self._as_float(metrics.get("profit_factor", ranked_entry.get("profit_factor", 0.0)))
        trades_count = int(self._as_float(metrics.get("total_trades", ranked_entry.get("total_trades", 0))))
        
        self.lbl_fitness.setText(f"Fitness: {fitness:.4f}")
        self.lbl_pnl.setText(f"Total PnL: {pnl:.2f}")
        self.lbl_pf.setText(f"Profit Factor: {pf:.4f}")
        self.lbl_trades.setText(f"Trades: {trades_count}")
        
        # Provenance
        provenance = ranked_entry.get("provenance", {}) or {}
        if provenance:
            source = provenance.get("generator_version") or provenance.get("generator") or provenance.get("source_type") or "N/A"
            lines = [f"Source: {html.escape(str(source))}"]
            if provenance.get("random_seed") is not None:
                lines.append(f"Seed: {html.escape(str(provenance['random_seed']))}")
            if provenance.get("dataset_id") is not None:
                lines.append(f"Dataset: {html.escape(str(provenance['dataset_id']))}")
            if provenance.get("source_type") is not None:
                lines.append(f"Type: {html.escape(str(provenance['source_type']))}")
            self.lbl_provenance.setText(" | ".join(lines))
        else:
            self.lbl_provenance.setText("Provenance: None")
            
        # Logic Blocks
        blocks_html = self._format_blocks(strategy)
        self.txt_blocks.setHtml(blocks_html)
        
    def _show_empty(self) -> None:
        self.lbl_name.setText("No Strategy Selected")
        self.lbl_status.setText("Select a strategy from the ranking table to view its details.")
        self.lbl_status.setStyleSheet("color: #8e8e93;")
        self.lbl_fitness.setText("Fitness: -")
        self.lbl_pnl.setText("Total PnL: -")
        self.btn_add_condition.setEnabled(False)
        self.lbl_pf.setText("Profit Factor: -")
        self.lbl_trades.setText("Trades: -")
        self.lbl_provenance.setText("")
        self.txt_blocks.setText("")

    def _as_float(self, value: object, default: float = 0.0) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        return default
        
    def _format_blocks(self, strat: Strategy) -> str:
        blocks = []
        for title, block in [
            ("Long Entry", strat.long_entry),
            ("Long Exit", strat.long_exit),
            ("Short Entry", strat.short_entry),
            ("Short Exit", strat.short_exit),
        ]:
            blocks.append(f"<h3 style='color: #82aaff; margin-bottom: 2px; margin-top: 10px;'>{html.escape(title)}</h3>")
            if not block or not block.conditions:
                blocks.append("<span style='color: #616161;'>&lt;No conditions&gt;</span><br>")
                continue
                
            logic = block.logic or "AND"
            cond_strs = []
            for c in block.conditions:
                cond_strs.append(self._format_condition(c))
            
            blocks.append(f" <b style='color: #c792ea;'>{html.escape(logic)}</b> ".join(cond_strs))
            blocks.append("<br>")
            
        return "".join(blocks)

    def _format_condition(self, condition) -> str:
        indicator = html.escape(str(condition.indicator))
        operator = html.escape(str(getattr(condition, "operator", "")))
        params = getattr(condition, "params", {}) or {}
        
        timeframe = params.get("timeframe")
        display_params = {k: v for k, v in params.items() if k != "timeframe"}
        
        params_str = ", ".join(
            f"{html.escape(str(k))}={html.escape(str(v))}" for k, v in display_params.items()
        )
        indicator_expr = f"<b>{indicator}</b>({params_str})"
        indicator_key = str(condition.indicator).upper()
        right = getattr(condition, "right", None)

        if indicator_key in THRESHOLD_INDICATORS and isinstance(right, (int, float)):
            base_expr = f"{indicator_expr} <i>{operator}</i> {html.escape(str(right))}"
        elif indicator_key == "MACD":
            base_expr = f"{indicator_expr} <i>{operator}</i> signal"
        else:
            left_val = html.escape(str(getattr(condition, "left", "close")))
            base_expr = f"{left_val} <i>{operator}</i> {indicator_expr}"

        if timeframe is not None:
            return f"{base_expr} <span style='color: #ff9800; font-weight: bold;'>[TF: {html.escape(str(timeframe))}m]</span>"
        return base_expr
