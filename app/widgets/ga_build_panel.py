"""GA Build panel widget — displays GA search controls and results.

Only formats structured data from :class:`GASearchResult`.
All GA logic stays in the service layer — this widget has zero engine imports.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class GABuildPanel(QWidget):
    """Build page panel showing GA search controls and last-run results.

    The widget is intentionally passive — it does not call any engine or
    service directly.  The parent wires the *Run GA* button click to the
    service layer and feeds results back via :meth:`update_from_result`.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # ── Controls bar ────────────────────────────────────────────────────
        self.btn_run_ga = QPushButton("▶  Run GA Search")
        self.btn_run_ga.setObjectName("btn_run_ga")
        
        self.btn_run_gp = QPushButton("▶  Run GP Search")
        self.btn_run_gp.setObjectName("btn_run_gp")
        
        btn_style = """
            QPushButton {
                background-color: #26a69a;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover { background-color: #2bbbb0; }
            QPushButton:disabled { background-color: #555557; color: #8e8e93; }
        """
        self.btn_run_ga.setStyleSheet(btn_style)
        self.btn_run_gp.setStyleSheet(btn_style)

        self.status_label = QLabel("No search has been run yet.")
        self.status_label.setObjectName("ga_status_label")
        self.status_label.setStyleSheet(
            "color: #8e8e93; font-weight: bold; font-size: 12px;"
        )

        controls = QFrame()
        controls.setFrameShape(QFrame.Shape.StyledPanel)
        controls.setStyleSheet("""
            QFrame {
                background-color: #1e1e24;
                border: 1px solid #2a2a2e;
                border-radius: 4px;
            }
            QLabel { border: none; background: transparent; }
        """)
        ctrl_layout = QHBoxLayout(controls)
        ctrl_layout.setContentsMargins(8, 8, 8, 8)
        ctrl_layout.setSpacing(12)
        ctrl_layout.addWidget(self.status_label, 1)
        ctrl_layout.addWidget(self.btn_run_ga)
        ctrl_layout.addWidget(self.btn_run_gp)

        # ── MTF Controls row ────────────────────────────────────────────────
        self.chk_enable_mtf = QCheckBox("Enable MTF candidates")
        self.chk_enable_mtf.setObjectName("chk_enable_mtf")
        self.chk_enable_mtf.setToolTip(
            "Adds higher-timeframe conditions to generated strategies. Slower\n"
            "and requires enough data for higher-timeframe warmup."
        )
        self.chk_enable_mtf.setChecked(False)
        self.chk_enable_mtf.setStyleSheet("color: #e0e0e3;")

        mtf_tf_label = QLabel("Timeframes:")
        mtf_tf_label.setStyleSheet("color: #8e8e93; border: none;")
        self.le_allowed_timeframes = QLineEdit("5,15")
        self.le_allowed_timeframes.setObjectName("le_allowed_timeframes")
        self.le_allowed_timeframes.setEnabled(False)
        self.le_allowed_timeframes.setFixedWidth(80)
        self.le_allowed_timeframes.setStyleSheet(
            "background: #121212; color: #e0e0e3; border: 1px solid #3a3a3c; border-radius: 3px; padding: 2px 4px;"
        )

        mtf_prob_label = QLabel("Probability:")
        mtf_prob_label.setStyleSheet("color: #8e8e93; border: none;")
        self.spin_mtf_probability = QDoubleSpinBox()
        self.spin_mtf_probability.setObjectName("spin_mtf_probability")
        self.spin_mtf_probability.setRange(0.0, 1.0)
        self.spin_mtf_probability.setSingleStep(0.05)
        self.spin_mtf_probability.setValue(0.25)
        self.spin_mtf_probability.setEnabled(False)
        self.spin_mtf_probability.setFixedWidth(60)
        self.spin_mtf_probability.setStyleSheet(
            "background: #121212; color: #e0e0e3; border: 1px solid #3a3a3c; border-radius: 3px; padding: 2px;"
        )

        self.chk_enable_mtf.toggled.connect(self.le_allowed_timeframes.setEnabled)
        self.chk_enable_mtf.toggled.connect(self.spin_mtf_probability.setEnabled)

        mtf_layout = QHBoxLayout()
        mtf_layout.setContentsMargins(8, 0, 8, 8)
        mtf_layout.setSpacing(12)
        mtf_layout.addWidget(self.chk_enable_mtf)
        mtf_layout.addWidget(mtf_tf_label)
        mtf_layout.addWidget(self.le_allowed_timeframes)
        mtf_layout.addWidget(mtf_prob_label)
        mtf_layout.addWidget(self.spin_mtf_probability)
        mtf_layout.addStretch()

        mtf_container = QWidget()
        mtf_container.setLayout(mtf_layout)

        # ── Scrollable results area ─────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )

        self._container = QWidget()
        self._results_layout = QVBoxLayout(self._container)
        self._results_layout.setContentsMargins(0, 0, 0, 0)
        self._results_layout.setSpacing(12)
        self._scroll.setWidget(self._container)

        self._show_empty_state()

        # ── Outer layout ────────────────────────────────────────────────────
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)
        outer.addWidget(controls)
        outer.addWidget(mtf_container)
        outer.addWidget(self._scroll, 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_mtf_config_dict(self) -> dict:
        """Return shallow-validated MTF configuration.

        If disabled, or if validation fails, returns defaults that
        keep MTF disabled.
        """
        is_enabled = self.chk_enable_mtf.isChecked()
        if not is_enabled:
            return {
                "enabled": False,
                "allowed_timeframes": [],
                "mtf_probability": 0.0,
            }

        raw_tf = self.le_allowed_timeframes.text()
        tfs = []
        for part in raw_tf.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                val = int(part)
                if val <= 0:
                    tfs = []
                    break
                tfs.append(val)
            except ValueError:
                tfs = []
                break

        prob = float(self.spin_mtf_probability.value())

        # Shallow validation: disable if empty valid timeframes or <=0 probability
        if not tfs or prob <= 0.0:
            return {
                "enabled": False,
                "allowed_timeframes": [],
                "mtf_probability": 0.0,
            }

        return {
            "enabled": True,
            "allowed_timeframes": tfs,
            "mtf_probability": prob,
        }

    def set_running(self, is_gp: bool = False) -> None:
        """Indicate that a search is in progress."""
        self.btn_run_ga.setEnabled(False)
        self.btn_run_gp.setEnabled(False)
        
        if is_gp:
            self.btn_run_gp.setText("Running…")
            self.status_label.setText("GP search in progress…")
        else:
            self.btn_run_ga.setText("Running…")
            self.status_label.setText("GA search in progress…")
            
        self.status_label.setStyleSheet(
            "color: #ffb300; font-weight: bold; font-size: 12px;"
        )

    def set_idle(self) -> None:
        """Re-enable the buttons after a run completes."""
        self.btn_run_ga.setEnabled(True)
        self.btn_run_ga.setText("▶  Run GA Search")
        self.btn_run_gp.setEnabled(True)
        self.btn_run_gp.setText("▶  Run GP Search")

    def update_from_result(self, result, *, source_label: str = "") -> None:
        """Populate the results area from a GA search result.

        Parameters
        ----------
        result
            Structured output from the GA search service.
        source_label : str
            Human-readable dataset source (e.g. filename or ``"Mock fallback"``).
        """
        self._clear_results()

        # ── Status bar ──────────────────────────────────────────────────────
        is_gp = "gp_" in getattr(result, "best_strategy", None).name if getattr(result, "best_strategy", None) else False
        algo_name = "GP" if is_gp else "GA"
        self.status_label.setText(
            f"✓ {algo_name} completed — Best score: {result.best_score:.4f}"
        )
        self.status_label.setStyleSheet(
            "color: #26a69a; font-weight: bold; font-size: 12px;"
        )

        # ── Summary card ────────────────────────────────────────────────────
        src = source_label or "Unknown"
        self._add_card(f"{algo_name} Search Summary", (
            f"Data source: {src}\n"
            f"Generations: {result.generation_count}  |  "
            f"Population: {result.final_population_size}\n"
            f"Best score: {result.best_score:.6f}  |  "
            f"Best strategy: {result.best_strategy.name}"
        ))

        # ── Best strategy blocks ────────────────────────────────────────────
        strat = result.best_strategy
        blocks = []
        for label, block in [
            ("Long Entry", strat.long_entry),
            ("Long Exit", strat.long_exit),
            ("Short Entry", strat.short_entry),
            ("Short Exit", strat.short_exit),
        ]:
            if block.conditions:
                conds = []
                for c in block.conditions:
                    params = ", ".join(f"{k}={v}" for k, v in c.params.items())
                    conds.append(f"{c.left} {c.operator} {c.indicator}({params})")
                blocks.append(f"{label}: {f' {block.logic} '.join(conds)}")
            else:
                blocks.append(f"{label}: Inactive")
        self._add_card("Best Strategy Logic", "\n".join(blocks))

        # ── Per-generation tracking ─────────────────────────────────────────
        gen_lines = []
        for i, (best, avg) in enumerate(
            zip(result.generation_best_scores, result.generation_avg_scores)
        ):
            bar_len = max(0, int(best * 40))
            bar = "█" * min(bar_len, 40)
            gen_lines.append(
                f"Gen {i:>3d}  |  Best: {best:>8.4f}  |  Avg: {avg:>8.4f}  |  {bar}"
            )
        self._add_card(
            "Generation Tracking (Best / Avg Scores)",
            "\n".join(gen_lines) if gen_lines else "No generation data.",
            mono=True,
        )

        self._results_layout.addStretch()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _clear_results(self) -> None:
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_empty_state(self) -> None:
        label = QLabel(
            "No search has been run yet.\n\n"
            "Click the ▶ Run GA Search or ▶ Run GP Search button above to start a "
            "Genetic Algorithm or Genetic Programming search for robust strategies."
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #8e8e93; font-size: 14px; padding: 40px;")
        label.setWordWrap(True)
        self._results_layout.addWidget(label)

    def _add_card(
        self, title: str, body: str, *, mono: bool = False
    ) -> None:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(
            "QFrame { background: #1e1e24; border: 1px solid #2a2a2e; "
            "border-radius: 6px; }"
        )

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #26a69a; "
            "border: none; background: transparent;"
        )
        card_layout.addWidget(title_label)

        body_label = QLabel(body)
        font_family = "'Courier New', Courier, monospace" if mono else "inherit"
        body_label.setStyleSheet(
            f"font-size: 13px; color: #e0e0e3; border: none; "
            f"background: transparent; font-family: {font_family};"
        )
        body_label.setWordWrap(True)
        body_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        card_layout.addWidget(body_label)

        self._results_layout.addWidget(card)
