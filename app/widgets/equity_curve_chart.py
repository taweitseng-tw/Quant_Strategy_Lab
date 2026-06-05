"""Reusable Equity Curve and Drawdown Chart widget using pyqtgraph for Quant Strategy Lab.

Provides dynamic dual-plot rendering of equity and drawdown curves in sleek premium styling.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

# Set up logging
logger = logging.getLogger(__name__)

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    logger.warning("pyqtgraph is not available. Falling back to simple label placeholder.")


class EquityCurveChart(QWidget):
    """Reusable Equity and Drawdown Curve Chart Widget.
    
    Displays the equity curve and drawdown curve in synchronized dual plots.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(6)
        
        self.is_mock_data = True
        
        if PYQTGRAPH_AVAILABLE:
            self._setup_pyqtgraph_charts()
        else:
            self._setup_fallback_label()

        # Load initial mock/sample data
        self.load_mock_data()

    def _setup_pyqtgraph_charts(self) -> None:
        # 1. Equity Plot (Upper Plot)
        self.equity_date_axis = pg.DateAxisItem(orientation="bottom")
        self.equity_date_axis.setPen(pg.mkPen("#8e8e93"))
        self.equity_date_axis.setTextPen(pg.mkPen("#8e8e93"))

        self.equity_plot = pg.PlotWidget(
            axisItems={"bottom": self.equity_date_axis},
            background="#121214"
        )
        self.equity_plot.setMenuEnabled(True)
        self.equity_plot.setMouseEnabled(x=True, y=True)
        self.equity_plot.showGrid(x=True, y=True, alpha=0.15)
        self.equity_plot.setLabel("left", "Equity", units="$", **{"color": "#8e8e93"})
        self.equity_plot.setLabel("bottom", "Time", units="", **{"color": "#8e8e93"})
        
        # 2. Drawdown Plot (Lower Plot)
        self.drawdown_date_axis = pg.DateAxisItem(orientation="bottom")
        self.drawdown_date_axis.setPen(pg.mkPen("#8e8e93"))
        self.drawdown_date_axis.setTextPen(pg.mkPen("#8e8e93"))

        self.drawdown_plot = pg.PlotWidget(
            axisItems={"bottom": self.drawdown_date_axis},
            background="#121214"
        )
        self.drawdown_plot.setMenuEnabled(True)
        self.drawdown_plot.setMouseEnabled(x=True, y=True)
        self.drawdown_plot.showGrid(x=True, y=True, alpha=0.15)
        self.drawdown_plot.setLabel("left", "Drawdown", units="$", **{"color": "#ef5350"})
        self.drawdown_plot.setLabel("bottom", "Time", units="", **{"color": "#8e8e93"})

        # Synchronize X-axis zooming and panning (extremely premium UX)
        self.drawdown_plot.setXLink(self.equity_plot)

        # Add PlotWidgets to Layout with stretch factors (Equity 70%, Drawdown 30%)
        self.layout.addWidget(self.equity_plot, stretch=7)
        self.layout.addWidget(self.drawdown_plot, stretch=3)

    def _setup_fallback_label(self) -> None:
        self.fallback_label = QLabel(
            "pyqtgraph is not available.\nPlease install pyqtgraph or check system dependencies."
        )
        self.fallback_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.fallback_label)

    def set_data(
        self,
        equity_df: pd.DataFrame,
        drawdown_df: pd.DataFrame | None = None,
        is_mock: bool = False
    ) -> None:
        """Set backtest equity and drawdown curves for rendering.
        
        Args:
            equity_df: DataFrame with ['datetime', 'equity'] columns.
            drawdown_df: Optional DataFrame with ['datetime', 'drawdown'] columns.
            is_mock: Boolean indicating if these are sample/mock curves.
        """
        self.is_mock_data = is_mock

        if not PYQTGRAPH_AVAILABLE:
            if hasattr(self, "fallback_label"):
                self.fallback_label.setText(
                    f"Fallback Mode - Received Equity Curve ({len(equity_df)} rows).\n"
                    "Please install pyqtgraph for interactive rendering."
                )
            return

        # 1. Plot Equity Curve
        if "datetime" not in equity_df.columns or "equity" not in equity_df.columns:
            logger.error("Equity DataFrame must contain 'datetime' and 'equity' columns.")
            return

        # Convert timestamps for DateAxis compatibility
        eq_times = equity_df["datetime"].apply(lambda x: x.timestamp()).values
        eq_vals = equity_df["equity"].values

        self.equity_plot.plot(eq_times, eq_vals, pen=pg.mkPen("#2196f3", width=2.5), clear=True)

        # 2. Plot Drawdown Curve (if available)
        has_drawdown = False
        if drawdown_df is not None and len(drawdown_df) > 0:
            if "datetime" in drawdown_df.columns and "drawdown" in drawdown_df.columns:
                dd_times = drawdown_df["datetime"].apply(lambda x: x.timestamp()).values
                dd_vals = drawdown_df["drawdown"].values
                
                # Render as a filled area going down from 0.0 for maximum visual impact
                self.drawdown_plot.plot(
                    dd_times,
                    dd_vals,
                    pen=pg.mkPen("#ef5350", width=1.5),
                    fillLevel=0.0,
                    brush=(239, 83, 80, 50),  # Red with alpha opacity
                    clear=True
                )
                has_drawdown = True
            else:
                logger.error("Drawdown DataFrame must contain 'datetime' and 'drawdown' columns.")

        # Show or hide drawdown panel based on availability
        self.drawdown_plot.setVisible(has_drawdown)

        # Title formatting with premium accent colors
        title_prefix = "Sample / Mock Data" if is_mock else "Backtest Performance"
        title_color = "#ffb300" if is_mock else "#26a69a"
        self.equity_plot.setTitle(f"{title_prefix} — Equity Curve", color=title_color, size="12pt")
        
        if has_drawdown:
            self.drawdown_plot.setTitle("Drawdown Curve", color="#ef5350", size="10pt")

        # Auto-range the views
        self.equity_plot.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)
        if has_drawdown:
            self.drawdown_plot.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)

    def load_mock_data(self) -> None:
        """Generate a premium-quality mock performance curve for initial display."""
        rng = np.random.default_rng(42)
        start_time = datetime.now() - timedelta(days=100)
        
        dates = [start_time + timedelta(days=i) for i in range(100)]
        
        equity = 100_000.0
        equity_values = []
        drawdown_values = []
        
        high_water_mark = 100_000.0
        
        for _ in range(100):
            # Normal walk with strong positive drift
            change = rng.normal(180.0, 1500.0)
            equity += change
            
            # Keep capital floor
            equity = max(equity, 10_000.0)
            
            high_water_mark = max(high_water_mark, equity)
            drawdown = equity - high_water_mark
            
            equity_values.append(equity)
            drawdown_values.append(drawdown)
            
        mock_eq_df = pd.DataFrame({
            "datetime": dates,
            "equity": equity_values
        })
        
        mock_dd_df = pd.DataFrame({
            "datetime": dates,
            "drawdown": drawdown_values
        })
        
        self.set_data(mock_eq_df, mock_dd_df, is_mock=True)

    def clear(self) -> None:
        """Clear the chart data and show an empty state."""
        if not PYQTGRAPH_AVAILABLE:
            return
            
        self.equity_plot.clear()
        self.drawdown_plot.clear()
        self.drawdown_plot.setVisible(False)
        self.equity_plot.setTitle("No Strategy Selected", color="#8e8e93", size="12pt")
