"""Validation summary dashboard widget — displays PipelineResult in cards."""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class _WFEquityChart(QWidget):
    """Small WF per-window equity line chart using PySide6 only."""

    CHART_HEIGHT = 200
    MARGIN = 40
    PASS_COLOR = QColor("#4CAF50")
    FAIL_COLOR = QColor("#F44336")
    AXIS_COLOR = QColor("#8e8e93")

    def __init__(self, windows: list[dict], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._windows = windows
        self._setup_ui()

    def _setup_ui(self) -> None:
        from PySide6.QtWidgets import QGraphicsView, QGraphicsScene

        self._scene = QGraphicsScene(self)
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._view.setStyleSheet("border: none; background: #1e1e24;")
        self._view.setFixedHeight(self.CHART_HEIGHT)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)

        self._draw_chart()

    def _draw_chart(self) -> None:
        if not self._windows:
            return

        # Determine the longest equity curve for x-range.
        max_len = max(len(w["equity_curve"]) for w in self._windows)
        if max_len < 2:
            return

        # Determine y-range across all windows.
        all_values = [v for w in self._windows for v in w["equity_curve"]]
        y_min, y_max = min(all_values), max(all_values)
        y_range = y_max - y_min or 1.0

        w = max(300, max_len * 2)  # scene width
        h = self.CHART_HEIGHT
        m = self.MARGIN
        plot_w = w - 2 * m
        plot_h = h - 2 * m

        self._scene.addLine(m, m, m, m + plot_h, QPen(self.AXIS_COLOR, 1.0))
        self._scene.addLine(m, m + plot_h, m + plot_w, m + plot_h, QPen(self.AXIS_COLOR, 1.0))

        label_specs = [
            (f"{y_max:,.0f}", 4, m - 8),
            (f"{y_min:,.0f}", 4, m + plot_h - 8),
            ("bar 0", m, h - 28),
            (f"bar {max_len - 1}", m + plot_w - 46, h - 28),
        ]
        for text, x_pos, y_pos in label_specs:
            item = self._scene.addText(text)
            item.setDefaultTextColor(self.AXIS_COLOR)
            item.setPos(x_pos, y_pos)

        def _to_scene(bar_idx: int, equity: float) -> tuple[float, float]:
            sx = m + (bar_idx / (max_len - 1)) * plot_w if max_len > 1 else m
            sy = m + ((y_max - equity) / y_range) * plot_h
            return sx, sy

        for win in self._windows:
            curve = win.get("equity_curve", [])
            if not isinstance(curve, list) or len(curve) < 2:
                continue
            color = self.PASS_COLOR if win.get("passed") else self.FAIL_COLOR
            pen = QPen(color, 1.5)
            poly = QPolygonF()
            for i, val in enumerate(curve):
                sx, sy = _to_scene(i, val)
                poly.append(QRectF(sx, sy, 0, 0).topLeft())
            self._scene.addPolygon(poly, pen)

        self._scene.setSceneRect(0, 0, w, h)


class _MCEquityChart(QWidget):
    """Single-line equity chart for MC worst-case (trade-step) equity curve."""

    CHART_HEIGHT = 150
    MARGIN = 40

    def __init__(self, equity_curve: list[float], curve_type: str = "trade_step",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._curve = equity_curve
        self._curve_type = curve_type
        self._setup_ui()

    def _setup_ui(self) -> None:
        from PySide6.QtWidgets import QGraphicsView, QGraphicsScene

        self._scene = QGraphicsScene(self)
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._view.setStyleSheet("border: none; background: #1e1e24;")
        self._view.setFixedHeight(self.CHART_HEIGHT)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)
        self._draw_chart()

    def _draw_chart(self) -> None:
        curve = self._curve
        if not curve or len(curve) < 2:
            return

        y_min, y_max = min(curve), max(curve)
        y_range = y_max - y_min or 1.0
        w = max(300, len(curve) * 2)
        h = self.CHART_HEIGHT
        m = self.MARGIN
        plot_w = w - 2 * m
        plot_h = h - 2 * m

        pen = QPen(QColor("#FF9800"), 1.5)
        poly = QPolygonF()
        for i, val in enumerate(curve):
            sx = m + (i / (len(curve) - 1)) * plot_w if len(curve) > 1 else m
            sy = m + ((y_max - val) / y_range) * plot_h
            poly.append(QRectF(sx, sy, 0, 0).topLeft())
        self._scene.addPolygon(poly, pen)
        self._scene.setSceneRect(0, 0, w, h)


class ValidationSummary(QWidget):
    """Compact dashboard displaying a PipelineResult from run_validation_pipeline().

    Shows: data source, split metadata, baseline metrics, stress, MC, WF,
    and elimination status.  Only formats structured data — no quant logic.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(12)

        self._scroll.setWidget(self._container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

        self._show_empty_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_empty(self) -> None:
        """Display the empty-state placeholder."""
        self._clear()
        self._show_empty_state()

    def update_from_result(self, result, source_label: str = "") -> None:
        """Populate the dashboard from a PipelineResult (or dict)."""
        self._clear()

        # --- Source label ---
        src = source_label or ("Mock data" if self._get(result, "_is_mock", False) else "Loaded data")
        self._add_section("Data Source", f"{src}  —  {self._get(result, 'split_metadata', {}).get('train_rows', '?')} train bars")

        # --- Precheck ---
        if self._get(result, "precheck_failed", False):
            elim = self._get(result, "elimination_result", {}) or {}
            rules = elim.get("failed_rules", [])
            reason = rules[0] if rules else "Precheck failed for an unknown reason."
            self._add_section("Precheck", f"FAILED — {reason}", passed=False)

        # --- Split ---
        sm = self._get(result, "split_metadata", {})
        self._add_section("Split", (
            f"Train: {sm.get('train_rows', '?')} rows  |  "
            f"Validation: {sm.get('validation_rows', '?')} rows  |  "
            f"OOS: {sm.get('oos_rows', '?')} rows"
        ))

        # --- Baseline ---
        bm = self._get(result, "baseline_metrics", {})
        self._add_section("Baseline Metrics", (
            f"PnL: {bm.get('total_pnl', 0):,.0f}  |  "
            f"PF: {bm.get('profit_factor', 0):.2f}  |  "
            f"Trades: {bm.get('total_trades', 0)}  |  "
            f"Max DD: {bm.get('max_drawdown_pnl', 0):,.0f}  |  "
            f"Win Rate: {(bm.get('win_rate', 0) or 0) * 100:.0f}%"
        ))

        # --- Stress ---
        stress = self._get(result, "stress_results", [])
        stress_lines = []
        for s in stress:
            name = s.get("test_name", "?")
            passed = "✓" if s.get("passed", False) else "✗"
            deg = s.get("degradation", {})
            pnl_deg = deg.get("total_pnl", 0)
            stress_lines.append(f"{name}: {passed}  PnL Δ={pnl_deg:.1%}")

            # Detail sub-lines for remove_best_n_trades.
            if name == "remove_best_n_trades":
                assumptions = s.get("assumptions", {}) or {}
                if assumptions:
                    n_val = assumptions.get("n", "?")
                    removed = assumptions.get("removed_count", "?")
                    surviving = assumptions.get("surviving_count", "?")
                    pnl_loss = assumptions.get("pnl_loss_ratio", "?")
                    if isinstance(pnl_loss, float):
                        pnl_loss = f"{pnl_loss:.3f}"
                    threshold = (s.get("threshold", {}) or {}).get("max_pnl_loss", "?")
                    if isinstance(threshold, float):
                        threshold = f"{threshold:.2f}"
                    stress_lines.append(
                        f"  → Removed: {removed} of {removed + surviving if isinstance(removed, int) and isinstance(surviving, int) else '?'} trades "
                        f"(n={n_val}, pnl_loss={pnl_loss}, threshold={threshold})"
                    )
                warnings = s.get("warnings", []) or []
                for w in warnings:
                    stress_lines.append(f"  → ⚠ {w}")

            # Detail sub-lines for price_noise (Task 062N-Impl).
            if name == "price_noise":
                assumptions = s.get("assumptions", {}) or {}
                noise_pct = assumptions.get("noise_pct", "?")
                noise_str = (
                    f"{noise_pct:.1%}"
                    if isinstance(noise_pct, (int, float)) and not isinstance(noise_pct, bool)
                    else str(noise_pct)
                )
                iterations = assumptions.get("iterations", "?")
                method = assumptions.get("method", "?")
                research_only = assumptions.get("research_only", "?")
                stress_lines.append(
                    f"  → Noise: {noise_str}, Iterations: {iterations}, "
                    f"Method: {method}, Research only: {research_only}"
                )
                warnings = s.get("warnings", []) or []
                for w in warnings:
                    stress_lines.append(f"  → ⚠ {w}")
        self._add_section("Stress Tests", "\n".join(stress_lines) if stress_lines else "No stress results.")

        # --- Monte Carlo ---
        mc = self._get(result, "monte_carlo_summary", {}) or {}
        ps = mc.get("percentile_summary", {}) or {}
        pnl_ps = ps.get("total_pnl", {}) or {}
        wc = mc.get("worst_case", {}) or {}
        wc_pnl = wc.get("total_pnl", "N/A")
        if isinstance(wc_pnl, (int, float)):
            wc_pnl = f"{wc_pnl:,.0f}"
        self._add_section("Monte Carlo", (
            f"Iterations: {mc.get('iterations', '?')}  |  "
            f"p05: {pnl_ps.get('p5', '?'):,.0f}  |  "
            f"p50: {pnl_ps.get('p50', '?'):,.0f}  |  "
            f"p95: {pnl_ps.get('p95', '?'):,.0f}  |  "
            f"Worst-case PnL: {wc_pnl}"
        ) if pnl_ps else "No MC data.")

        # --- Bootstrap MC ---
        bootstrap = self._get(result, "bootstrap_monte_carlo_result", {}) or {}
        if bootstrap:
            ci = bootstrap.get("confidence_intervals", {}) or {}
            if ci:  # only show when CI data is non-empty
                lines = [
                    f"Iterations: {bootstrap.get('iterations', '?')}  |  "
                    f"Stability: {bootstrap.get('stability_score', '?')}"
                ]
                for key, label, fmt in [("total_pnl", "PnL", ",.0f"), ("profit_factor", "PF", ".2f"), ("max_drawdown_pnl", "Max DD", ",.0f")]:
                    d = ci.get(key, {})
                    if d:
                        lines.append(
                            f"{label} 95% CI [{d.get('ci_lower', 0):{fmt}} — {d.get('ci_upper', 0):{fmt}}] "
                            f"mean={d.get('ci_mean', 0):{fmt}}"
                        )
                self._add_section("Bootstrap MC", "\n".join(lines))

        # --- MC Worst-Case Equity Chart ---
        wc_curve = mc.get("worst_case_equity_curve")
        if isinstance(wc_curve, list) and len(wc_curve) >= 2:
            raw_curve_type = str(mc.get("worst_case_equity_curve_type", "trade_step"))
            display_curve_type = raw_curve_type.replace("_", "-")
            if raw_curve_type == "trade_step":
                curve_note = "surviving trades only; not bar-by-bar equity"
            else:
                curve_note = "curve type not verified as bar-by-bar equity"
            label = f"MC Worst-Case Equity ({display_curve_type})"
            self._add_section(label, f"Curve type: {display_curve_type} ({curve_note}). Points: {len(wc_curve)}")
            chart = _MCEquityChart(wc_curve, curve_type=raw_curve_type)
            chart_frame = QFrame()
            chart_frame.setStyleSheet("QFrame { border: none; background: transparent; }")
            chart_layout = QVBoxLayout(chart_frame)
            chart_layout.setContentsMargins(14, 0, 14, 10)
            chart_layout.addWidget(chart)
            self._layout.addWidget(chart_frame)

        # --- Walk-forward ---
        wf = self._get(result, "walk_forward_summary", {}) or {}
        wf_text = (
            f"Windows: {wf.get('window_count', '?')}  |  "
            f"Passed: {wf.get('pass_count', '?')}  |  "
            f"Pass Rate: {(wf.get('pass_rate', 0) or 0) * 100:.0f}%"
        )
        # WF Efficiency (optional).
        has_wfe = "average_wfe" in wf or "median_wfe" in wf
        if has_wfe:
            avg_wfe = wf.get("average_wfe")
            med_wfe = wf.get("median_wfe")
            avg_str = f"{avg_wfe:.2f}" if avg_wfe is not None else "N/A"
            med_str = f"{med_wfe:.2f}" if med_wfe is not None else "N/A"
            defined_count = wf.get("defined_wfe_count", 0)
            undefined_count = wf.get("undefined_wfe_count", 0)
            wf_text += (
                f"  |  WFE: Avg={avg_str}, Median={med_str}, "
                f"Defined={defined_count}, Undefined={undefined_count}"
            )
        self._add_section("Walk-Forward", wf_text if wf else "Walk-forward skipped (dataset too short).")

        # --- WF Equity Summary ---
        windows = wf.get("windows") or []
        equity_windows = [w for w in windows
                          if isinstance(w.get("equity_curve"), list) and len(w.get("equity_curve", [])) >= 2]
        if equity_windows:
            MAX_SHOW = 5
            lines = []
            for i, w in enumerate(equity_windows[:MAX_SHOW]):
                curve = w["equity_curve"]
                start_eq = curve[0]
                end_eq = curve[-1]
                pct = (end_eq - start_eq) / abs(start_eq) * 100 if abs(start_eq) > 1e-9 else 0.0
                status = "PASSED" if w.get("passed") else "FAILED"
                lines.append(
                    f"W{w.get('index', i)}: {start_eq:,.0f} → {end_eq:,.0f} "
                    f"({pct:+.1f}%)  {status}"
                )
            if len(equity_windows) > MAX_SHOW:
                lines.append(f"... {len(equity_windows) - MAX_SHOW} more windows")
            self._add_section("WF Equity Summary", "\n".join(lines))

            # WF Equity line chart.
            chart = _WFEquityChart(equity_windows)
            # Wrap the chart in a QFrame for consistency with cards.
            chart_frame = QFrame()
            chart_frame.setStyleSheet("QFrame { border: none; background: transparent; }")
            chart_layout = QVBoxLayout(chart_frame)
            chart_layout.setContentsMargins(14, 0, 14, 10)
            chart_layout.addWidget(chart)
            self._layout.addWidget(chart_frame)

        # --- Walk-forward Matrix ---
        wfm = self._get(result, "walk_forward_matrix_summary", {}) or {}
        if wfm:
            best = wfm.get("best_pass_rate_config") or {}
            worst = wfm.get("worst_pass_rate_config") or {}
            lines = [
                f"Configs: {wfm.get('config_count', '?')} total  |  "
                f"Tested: {wfm.get('tested_count', '?')}  |  "
                f"Insufficient data: {wfm.get('insufficient_data_count', '?')}",
            ]
            if best:
                lines.append(
                    f"Best: {best.get('config_id', '?')}  "
                    f"({best.get('train_bars', '?')}/{best.get('test_bars', '?')}/{best.get('step_bars', '?')})  "
                    f"Pass Rate: {(best.get('pass_rate', 0) or 0) * 100:.0f}%"
                )
            if worst:
                lines.append(
                    f"Worst: {worst.get('config_id', '?')}  "
                    f"({worst.get('train_bars', '?')}/{worst.get('test_bars', '?')}/{worst.get('step_bars', '?')})  "
                    f"Pass Rate: {(worst.get('pass_rate', 0) or 0) * 100:.0f}%"
                )
            self._add_section("Walk-Forward Matrix", "\n".join(lines))

        # --- OOS Metrics ---
        oos = self._get(result, "oos_metrics", {}) or {}
        if oos and oos.get("total_trades", 0) is not None:
            self._add_section("OOS Metrics", (
                f"PnL: {oos.get('total_pnl', 0):,.0f}  |  "
                f"PF: {oos.get('profit_factor', 0):.2f}  |  "
                f"Trades: {oos.get('total_trades', 0)}  |  "
                f"Max DD: {oos.get('max_drawdown_pnl', 0):,.0f}  |  "
                f"Win Rate: {(oos.get('win_rate', 0) or 0) * 100:.0f}%"
            ))
        else:
            self._add_section("OOS Metrics", "No OOS data.")

        # --- Elimination ---
        elim = self._get(result, "elimination_result", {}) or {}
        passed = elim.get("passed", False)
        rules = elim.get("failed_rules", [])
        status = "✓ PASSED" if passed else f"✗ ELIMINATED — {'; '.join(rules)}"
        self._add_section("Elimination", status, passed=passed)

        self._layout.addStretch()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _clear(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_empty_state(self) -> None:
        label = QLabel("No validation run yet.\n\nClick the ▶ Run button in the toolbar to execute the full validation pipeline.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #8e8e93; font-size: 14px; padding: 40px;")
        label.setWordWrap(True)
        self._layout.addWidget(label)

    def _add_section(self, title: str, body: str, passed: bool | None = None) -> None:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        if passed is True:
            card.setStyleSheet("QFrame { background: #1a2a1e; border: 1px solid #2a4a2e; border-radius: 6px; }")
        elif passed is False:
            card.setStyleSheet("QFrame { background: #2a1a1e; border: 1px solid #4a2a2e; border-radius: 6px; }")
        else:
            card.setStyleSheet("QFrame { background: #1e1e24; border: 1px solid #2a2a2e; border-radius: 6px; }")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #26a69a; border: none; background: transparent;")
        card_layout.addWidget(title_label)

        body_label = QLabel(body)
        body_label.setStyleSheet("font-size: 13px; color: #e0e0e3; border: none; background: transparent;")
        body_label.setWordWrap(True)
        card_layout.addWidget(body_label)

        self._layout.addWidget(card)

    @staticmethod
    def _get(obj, key, default=None):
        """Get key from dict or dataclass."""
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
