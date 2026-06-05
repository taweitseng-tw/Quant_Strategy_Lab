"""Reusable ranking table widget for displaying ranked strategies in Quant Strategy Lab."""

from __future__ import annotations

import logging
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Set up logging
logger = logging.getLogger(__name__)


class RankingTable(QWidget):
    """Reusable widget focusing purely on displaying ranked strategies.
    
    Accepts already-ranked strategy dicts and renders them inside a beautifully formatted QTableWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)

        # Status / Header Label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 13px; font-weight: bold; padding: 4px;")
        self.layout.addWidget(self.status_label)

        # QTableWidget Initialization
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Rank",
            "Strategy Name",
            "Fitness",
            "Total PnL",
            "Profit Factor",
            "Max Drawdown",
            "Win Rate",
            "Trade Count",
            "Elimination",
        ])

        # Style horizontal headers
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Rank
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents) # Trade Count
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents) # Elimination

        # Setup modern selection & grid behavior
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        # Premium Dark Mode Table Styling
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #121214;
                alternate-background-color: #1a1a1e;
                gridline-color: #2a2a2e;
                color: #e0e0e3;
                border: 1px solid #2a2a2e;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #1e1e24;
                color: #a0a0a5;
                font-weight: bold;
                border: 1px solid #2a2a2e;
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #26a69a;
                color: #ffffff;
            }
        """)

        self.layout.addWidget(self.table)

    def set_ranking_data(self, ranked_rows: list[dict], is_mock: bool = False) -> None:
        """Populate the table with ranked strategy data.
        
        Args:
            ranked_rows: List of dicts, sorted by fitness descending. Each dict contains:
                         rank, strategy (Strategy model object), fitness, metrics (dict).
            is_mock: Boolean indicating if this is internal sample/mock data.
        """
        # Set status label based on mock flag
        if is_mock:
            self.status_label.setText("⚠ Sample / Mock Strategy Ranking (No Project Loaded)")
            self.status_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #ffb300; padding: 4px;")
        else:
            self.status_label.setText("✓ Active Strategy Ranking Results")
            self.status_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #26a69a; padding: 4px;")

        self.table.clearSelection()
        self.table.setRowCount(0)
        self.table.setRowCount(len(ranked_rows))

        for row_idx, item in enumerate(ranked_rows):
            rank = item.get("rank", row_idx + 1)
            strategy = item.get("strategy")
            strategy_name = strategy.name if strategy else item.get("name", f"strat_{row_idx:04d}")
            fitness = item.get("fitness", 0.0)
            
            metrics = item.get("metrics", {})
            total_pnl = metrics.get("total_pnl", 0.0)
            profit_factor = metrics.get("profit_factor", 0.0)
            max_drawdown = metrics.get("max_drawdown_pnl", 0.0)
            win_rate = metrics.get("win_rate", 0.0)
            trade_count = metrics.get("total_trades", 0)

            # 1. Rank Column
            rank_item = QTableWidgetItem(str(rank))
            rank_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, rank_item)

            # 2. Strategy Name Column
            name_item = QTableWidgetItem(strategy_name)
            name_item.setFont(QtGui.QFont("Courier New", 10, QtGui.QFont.Weight.Bold))
            self.table.setItem(row_idx, 1, name_item)

            # 3. Fitness Column (Color-coded)
            fitness_item = QTableWidgetItem(f"{fitness:.4f}")
            fitness_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            
            # Choose color code for fitness
            if fitness >= 0.6:
                color = QtGui.QColor("#26a69a") # Premium Teal
            elif fitness >= 0.3:
                color = QtGui.QColor("#ffb300") # Premium Amber
            else:
                color = QtGui.QColor("#ef5350") # Premium Coral/Red
                
            fitness_item.setForeground(QtGui.QBrush(color))
            fitness_item.setFont(QtGui.QFont("MS Shell Dlg 2", 9, QtGui.QFont.Weight.Bold))
            self.table.setItem(row_idx, 2, fitness_item)

            # 4. Total PnL Column
            pnl_item = QTableWidgetItem(f"${total_pnl:,.2f}")
            pnl_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            if total_pnl > 0:
                pnl_item.setForeground(QtGui.QBrush(QtGui.QColor("#26a69a")))
            elif total_pnl < 0:
                pnl_item.setForeground(QtGui.QBrush(QtGui.QColor("#ef5350")))
            self.table.setItem(row_idx, 3, pnl_item)

            # 5. Profit Factor Column
            pf_str = "N/A" if profit_factor == 999.0 else f"{profit_factor:.2f}"
            pf_item = QTableWidgetItem(pf_str)
            pf_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            if profit_factor >= 1.5:
                pf_item.setForeground(QtGui.QBrush(QtGui.QColor("#26a69a")))
            self.table.setItem(row_idx, 4, pf_item)

            # 6. Max Drawdown Column
            dd_item = QTableWidgetItem(f"${max_drawdown:,.2f}")
            dd_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            if max_drawdown > 0:
                dd_item.setForeground(QtGui.QBrush(QtGui.QColor("#ef5350")))
            self.table.setItem(row_idx, 5, dd_item)

            # 7. Win Rate Column
            wr_item = QTableWidgetItem(f"{win_rate * 100:.1f}%")
            wr_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            if win_rate >= 0.5:
                wr_item.setForeground(QtGui.QBrush(QtGui.QColor("#26a69a")))
            self.table.setItem(row_idx, 6, wr_item)

            # 8. Trade Count Column
            tc_item = QTableWidgetItem(str(trade_count))
            tc_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 7, tc_item)

            # 9. Elimination Status Column
            passed = item.get("elimination_passed", True)
            failed_rules = item.get("elimination_failed_rules", [])
            
            status_text = "Passed" if passed else "Eliminated"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            
            if passed:
                status_color = QtGui.QColor("#26a69a")  # Premium Teal
            else:
                status_color = QtGui.QColor("#ef5350")  # Premium Coral/Red
                
            status_item.setForeground(QtGui.QBrush(status_color))
            status_item.setFont(QtGui.QFont("MS Shell Dlg 2", 9, QtGui.QFont.Weight.Bold))
            
            # Show details of failed rules as tooltip
            if not passed and failed_rules:
                rules_str = ", ".join(failed_rules)
                status_item.setToolTip(f"Failed rules: {rules_str}")
            else:
                status_item.setToolTip("Passed all elimination rules")
                
            self.table.setItem(row_idx, 8, status_item)
            
        # Select first row by default if rows exist
        if len(ranked_rows) > 0:
            self.table.selectRow(0)
