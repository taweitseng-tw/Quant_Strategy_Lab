"""Validation summary dashboard widget — displays PipelineResult in cards."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


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
        self._add_section("Stress Tests", "\n".join(stress_lines) if stress_lines else "No stress results.")

        # --- Monte Carlo ---
        mc = self._get(result, "monte_carlo_summary", {}) or {}
        ps = mc.get("percentile_summary", {}) or {}
        pnl_ps = ps.get("total_pnl", {}) or {}
        wc = mc.get("worst_case", {}) or {}
        self._add_section("Monte Carlo", (
            f"Iterations: {mc.get('iterations', '?')}  |  "
            f"p05: {pnl_ps.get('p5', '?'):,.0f}  |  "
            f"p50: {pnl_ps.get('p50', '?'):,.0f}  |  "
            f"p95: {pnl_ps.get('p95', '?'):,.0f}  |  "
            f"Worst-case PnL: {wc.get('total_pnl', '?'):,.0f}"
        ) if pnl_ps else "No MC data.")

        # --- Walk-forward ---
        wf = self._get(result, "walk_forward_summary", {}) or {}
        self._add_section("Walk-Forward", (
            f"Windows: {wf.get('window_count', '?')}  |  "
            f"Passed: {wf.get('pass_count', '?')}  |  "
            f"Pass Rate: {(wf.get('pass_rate', 0) or 0) * 100:.0f}%"
        ) if wf else "Walk-forward skipped (dataset too short).")

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
