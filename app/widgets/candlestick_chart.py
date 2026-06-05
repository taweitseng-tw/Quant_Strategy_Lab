"""Reusable candlestick chart widget using pyqtgraph for Quant Strategy Lab."""

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
    logger.warning("pyqtgraph is not available. Falling back to matplotlib or simple placeholder.")


class CandlestickItem(pg.GraphicsObject):
    """Custom pyqtgraph GraphicsObject to draw candlestick bars efficiently.
    
    Uses QPicture to cache drawing operations for high-performance rendering.
    """

    def __init__(self) -> None:
        super().__init__()
        self.picture = QtGui.QPicture()
        self._df: pd.DataFrame | None = None

    def set_data(self, df: pd.DataFrame) -> None:
        """Update the candlestick data and redraw."""
        self._df = df
        self.generate_picture()
        self.update()

    def generate_picture(self) -> None:
        """Pre-generate the QPicture representation of the candlesticks for rendering."""
        self.picture = QtGui.QPicture()
        if self._df is None or len(self._df) == 0:
            return

        painter = QtGui.QPainter(self.picture)
        
        # Convert datetimes to float timestamps (seconds since epoch)
        timestamps = self._df["datetime"].apply(lambda x: x.timestamp()).values
        opens = self._df["open"].values
        highs = self._df["high"].values
        lows = self._df["low"].values
        closes = self._df["close"].values

        # Calculate candlestick width based on time spacing
        if len(timestamps) > 1:
            # Detect minimum spacing to prevent candle overlapping
            diffs = np.diff(timestamps)
            min_spacing = np.min(diffs[diffs > 0]) if np.any(diffs > 0) else 60.0
            width = min_spacing * 0.6
        else:
            width = 60.0  # Default to 1-minute width in seconds

        # Premium aesthetics: custom TradingView-like HSL tailored colors
        # Green / Bullish: #26a69a (Teal)
        bullish_pen = pg.mkPen("#26a69a", width=1.5)
        bullish_brush = pg.mkBrush("#26a69a")
        
        # Red / Bearish: #ef5350 (Coral/Red)
        bearish_pen = pg.mkPen("#ef5350", width=1.5)
        bearish_brush = pg.mkBrush("#ef5350")

        for i in range(len(self._df)):
            t = timestamps[i]
            o = opens[i]
            h = highs[i]
            l = lows[i]
            c = closes[i]

            # Choose color based on candle direction
            if c >= o:
                painter.setPen(bullish_pen)
                painter.setBrush(bullish_brush)
            else:
                painter.setPen(bearish_pen)
                painter.setBrush(bearish_brush)

            # Draw wick
            painter.drawLine(QtCore.QPointF(t, l), QtCore.QPointF(t, h))

            # Draw body
            body_top = max(o, c)
            body_bottom = min(o, c)
            body_height = body_top - body_bottom

            # Handle flat body (open == close) to ensure it renders a thin line
            if body_height == 0:
                body_height = 0.0001

            painter.drawRect(QtCore.QRectF(t - width / 2.0, body_bottom, width, body_height))

        painter.end()

    def paint(self, painter: QtGui.QPainter, option: QtGui.QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        """Render the pre-drawn QPicture."""
        painter.drawPicture(0, 0, self.picture)

    def boundingRect(self) -> QtCore.QRectF:
        """Return the bounding rect of the pre-drawn QPicture."""
        return QtCore.QRectF(self.picture.boundingRect())


class CandlestickChart(QWidget):
    """Reusable Candlestick Chart Widget that renders from a normalized OHLCV DataFrame."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.is_mock_data = True
        
        if PYQTGRAPH_AVAILABLE:
            self._setup_pyqtgraph_chart()
        else:
            self._setup_fallback_label()

        # Load initial mock/sample data
        self.load_mock_data()

    def _setup_pyqtgraph_chart(self) -> None:
        # Create a DateAxisItem for X axis formatting
        self.date_axis = pg.DateAxisItem(orientation="bottom")
        
        # Style the axis
        self.date_axis.setPen(pg.mkPen("#8e8e93"))
        self.date_axis.setTextPen(pg.mkPen("#8e8e93"))

        # Create PlotWidget with our custom DateAxisItem
        self.plot_widget = pg.PlotWidget(
            axisItems={"bottom": self.date_axis},
            background="#121214"  # Premium sleek dark mode background
        )
        self.plot_widget.setMenuEnabled(True)
        self.plot_widget.setMouseEnabled(x=True, y=True)
        
        # Style grid lines
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)
        
        # Add labels
        self.plot_widget.setLabel("left", "Price", units="", **{"color": "#8e8e93"})
        self.plot_widget.setLabel("bottom", "Time", units="", **{"color": "#8e8e93"})

        # Initialize and add the CandlestickItem
        self.candlestick_item = CandlestickItem()
        self.plot_widget.addItem(self.candlestick_item)

        self.layout.addWidget(self.plot_widget)

    def _setup_fallback_label(self) -> None:
        self.fallback_label = QLabel(
            "pyqtgraph is not available.\nPlease install pyqtgraph or check system dependencies."
        )
        self.fallback_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.fallback_label)

    def set_data(self, df: pd.DataFrame, is_mock: bool = False) -> None:
        """Set a normalized OHLCV DataFrame for rendering on the chart.
        
        Args:
            df: A pandas DataFrame containing canonical columns: datetime, open, high, low, close, volume.
            is_mock: Boolean indicating if the data is placeholder/sample data.
        """
        self.is_mock_data = is_mock

        if not PYQTGRAPH_AVAILABLE:
            if hasattr(self, "fallback_label"):
                self.fallback_label.setText(
                    f"Fallback Mode - Received DataFrame with {len(df)} rows.\n"
                    "Please install pyqtgraph for interactive rendering."
                )
            return

        # Canonical column validation
        required_cols = ["datetime", "open", "high", "low", "close", "volume"]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            logger.error(f"Cannot set chart data: missing columns {missing}")
            return

        # Slicing guardrail for large datasets to keep UI extremely responsive
        original_len = len(df)
        if original_len > 2000:
            render_df = df.tail(2000).copy()
            logger.info(f"Slicing chart rendering from {original_len} to most recent 2000 rows for UI responsiveness.")
        else:
            render_df = df

        # Render data
        self.candlestick_item.set_data(render_df)
        
        # Set window title/header styling based on data status
        if is_mock:
            self.plot_widget.setTitle(
                "Sample / Mock Data (No Project Loaded)",
                color="#ffb300",  # Amber highlight
                size="12pt"
            )
        else:
            title_text = "Active Dataset OHLCV Chart"
            if original_len > 2000:
                title_text += f" (Displaying most recent 2,000 of {original_len:,} rows for performance)"
            self.plot_widget.setTitle(
                title_text,
                color="#26a69a",  # Teal highlight
                size="12pt"
            )

        # Auto-range the view to fit the data perfectly
        self.plot_widget.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)

    def load_mock_data(self) -> None:
        """Generate and load a clearly labeled mock dataset for visual feedback."""
        np.random.seed(42)
        start_time = datetime.now() - timedelta(days=50)
        
        # Generate 50 daily bars
        dates = [start_time + timedelta(days=i) for i in range(50)]
        
        open_prices = []
        high_prices = []
        low_prices = []
        close_prices = []
        volumes = []
        
        current_price = 100.0
        for _ in range(50):
            o = current_price + np.random.normal(0, 1.5)
            c = o + np.random.normal(0.2, 2.0)
            h = max(o, c) + abs(np.random.normal(0.5, 0.8))
            l = min(o, c) - abs(np.random.normal(0.5, 0.8))
            v = int(np.random.uniform(1000, 5000))
            
            open_prices.append(o)
            high_prices.append(h)
            low_prices.append(l)
            close_prices.append(c)
            volumes.append(v)
            current_price = c
            
        mock_df = pd.DataFrame({
            "datetime": dates,
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "volume": volumes
        })
        
        self.set_data(mock_df, is_mock=True)
