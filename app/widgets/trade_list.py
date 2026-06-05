from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QPushButton,
    QComboBox,
    QFrame,
)
from core.models.backtest_result import Trade

class TradeListWidget(QWidget):
    """A polished, paginated widget for displaying a list of trades."""

    def __init__(self) -> None:
        super().__init__()
        self.trades: list[Trade | dict] = []
        self.current_page = 0
        self.page_size = 50

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ── Summary bar ──────────────────────────────────────────────────
        summary_frame = QFrame()
        summary_frame.setFrameShape(QFrame.Shape.StyledPanel)
        summary_frame.setStyleSheet(
            "QFrame { background-color: #1e1e24; border: 1px solid #2a2a2e; "
            "border-radius: 4px; }"
            "QLabel { border: none; background: transparent; }"
        )
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(8, 4, 8, 4)
        summary_layout.setSpacing(16)

        self.lbl_summary = QLabel("No trades")
        self.lbl_summary.setStyleSheet(
            "color: #b0b0b5; font-size: 12px;"
        )
        self.lbl_summary.setTextFormat(Qt.TextFormat.RichText)
        summary_layout.addWidget(self.lbl_summary)
        summary_layout.addStretch()

        # ── Controls Layout ──────────────────────────────────────────────
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        self.btn_prev = QPushButton("◀ Previous")
        self.btn_prev.setToolTip("Go to the previous page of trades")
        self.btn_prev.setEnabled(False)
        self.btn_prev.clicked.connect(self.prev_page)
        
        self.btn_next = QPushButton("Next ▶")
        self.btn_next.setToolTip("Go to the next page of trades")
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self.next_page)
        
        self.lbl_page_info = QLabel("No trades")
        
        self.combo_page_size = QComboBox()
        self.combo_page_size.addItems(["25", "50", "100"])
        self.combo_page_size.setCurrentText("50")
        self.combo_page_size.setToolTip("Number of trades displayed per page")
        self.combo_page_size.currentTextChanged.connect(self._handle_page_size_changed)
        
        controls_layout.addWidget(self.btn_prev)
        controls_layout.addWidget(self.lbl_page_info)
        controls_layout.addWidget(self.btn_next)
        controls_layout.addStretch()
        controls_layout.addWidget(QLabel("Page Size:"))
        controls_layout.addWidget(self.combo_page_size)

        # ── Table Layout ─────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Entry Time", "Exit Time", "Direction", "Entry Price", 
            "Exit Price", "Net PnL", "Duration", "Exit Reason"
        ])
        header = self.table.horizontalHeader()
        # Use Interactive for most columns so user can adjust; set defaults
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # Stretch time columns and let others auto-size
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Entry Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Exit Time
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # Duration
        # Fixed-width for compact columns
        self.table.setColumnWidth(2, 80)   # Direction
        self.table.setColumnWidth(3, 100)  # Entry Price
        self.table.setColumnWidth(4, 100)  # Exit Price
        self.table.setColumnWidth(5, 100)  # Net PnL
        self.table.setColumnWidth(7, 100)  # Exit Reason

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(summary_frame)
        layout.addWidget(self.table)
        layout.addLayout(controls_layout)

    def set_trades(self, trades: list[Trade] | list[dict] | None) -> None:
        self.trades = trades if trades else []
        self.current_page = 0
        self._refresh_table()

    def _handle_page_size_changed(self, text: str) -> None:
        self.page_size = int(text)
        self.current_page = 0
        self._refresh_table()

    def prev_page(self) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_table()

    def next_page(self) -> None:
        if (self.current_page + 1) * self.page_size < len(self.trades):
            self.current_page += 1
            self._refresh_table()

    def _get_pnl(self, t: Trade | dict) -> float:
        """Extract PnL from a Trade or dict."""
        if isinstance(t, dict):
            return t.get("pnl", 0.0)
        return t.pnl

    def _compute_summary(self) -> dict:
        """Compute summary statistics for the current trade list.

        Returns a dict with keys: total, net_pnl, wins, losses, avg_trade.
        """
        total = len(self.trades)
        if total == 0:
            return {"total": 0, "net_pnl": 0.0, "wins": 0, "losses": 0, "avg_trade": 0.0}

        pnls = [self._get_pnl(t) for t in self.trades]
        net_pnl = sum(pnls)
        wins = sum(1 for p in pnls if p > 0)
        losses = sum(1 for p in pnls if p < 0)
        avg_trade = net_pnl / total

        return {
            "total": total,
            "net_pnl": net_pnl,
            "wins": wins,
            "losses": losses,
            "avg_trade": avg_trade,
        }

    def _refresh_table(self) -> None:
        # ── Update summary ───────────────────────────────────────────────
        summary = self._compute_summary()
        if summary["total"] == 0:
            self.lbl_summary.setText("No trades")
            self.table.setRowCount(0)
            self.lbl_page_info.setText("No trades")
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
            return

        net_pnl = summary["net_pnl"]
        pnl_color = "#26a69a" if net_pnl >= 0 else "#ef5350"
        self.lbl_summary.setText(
            f"<b>Total Trades:</b> {summary['total']}  │  "
            f"<b>Net PnL:</b> <span style='color:{pnl_color}'>{net_pnl:,.2f}</span>  │  "
            f"<b>Win/Loss:</b> {summary['wins']}/{summary['losses']}  │  "
            f"<b>Avg Trade:</b> {summary['avg_trade']:,.2f}"
        )

        # ── Pagination ───────────────────────────────────────────────────
        total_pages = (len(self.trades) + self.page_size - 1) // self.page_size
        self.lbl_page_info.setText(f"Page {self.current_page + 1} of {total_pages} (Total: {len(self.trades)})")

        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled((self.current_page + 1) < total_pages)

        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.trades))
        page_trades = self.trades[start_idx:end_idx]

        self.table.setRowCount(len(page_trades))

        for row, t in enumerate(page_trades):
            if isinstance(t, dict):
                entry_time = t.get("entry_time", "")
                exit_time = t.get("exit_time", "")
                direction = t.get("direction", "")
                entry_price = t.get("entry_price", 0.0)
                exit_price = t.get("exit_price", 0.0)
                pnl = t.get("pnl", 0.0)
                exit_reason = t.get("exit_reason", "")
            else:
                entry_time = t.entry_time
                exit_time = t.exit_time
                direction = t.direction
                entry_price = t.entry_price
                exit_price = t.exit_price
                pnl = t.pnl
                exit_reason = t.exit_reason
                
            duration = ""
            if isinstance(entry_time, pd.Timestamp) and isinstance(exit_time, pd.Timestamp):
                diff = exit_time - entry_time
                duration = str(diff)
            
            def format_time(t_val):
                if isinstance(t_val, pd.Timestamp):
                    return t_val.strftime("%Y-%m-%d %H:%M")
                return str(t_val)

            self.table.setItem(row, 0, QTableWidgetItem(format_time(entry_time)))
            self.table.setItem(row, 1, QTableWidgetItem(format_time(exit_time)))
            
            dir_item = QTableWidgetItem(direction.upper())
            if direction.lower() == "long":
                dir_item.setForeground(QColor("#26a69a"))
            elif direction.lower() == "short":
                dir_item.setForeground(QColor("#ef5350"))
            self.table.setItem(row, 2, dir_item)

            self.table.setItem(row, 3, QTableWidgetItem(f"{entry_price:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{exit_price:.2f}"))
            
            pnl_item = QTableWidgetItem(f"{pnl:.2f}")
            if pnl > 0:
                pnl_item.setForeground(QColor("#26a69a"))
            elif pnl < 0:
                pnl_item.setForeground(QColor("#ef5350"))
            self.table.setItem(row, 5, pnl_item)
            
            self.table.setItem(row, 6, QTableWidgetItem(duration))
            self.table.setItem(row, 7, QTableWidgetItem(exit_reason))
