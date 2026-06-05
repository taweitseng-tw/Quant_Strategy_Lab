"""Passive widget for configuring strategy elimination rules — Task 041B."""

from __future__ import annotations

from typing import Any
from PySide6 import QtCore
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QFormLayout,
)


class EliminationConfigWidget(QWidget):
    """Passive widget that allows users to configure elimination thresholds.
    
    Emits a dict containing the current configuration whenever it changes.
    Does NOT import or couple to the validation_engine.
    """

    config_changed = QtCore.Signal(dict)

    # Hardcoded defaults matching StrategyService.DEFAULT_ELIMINATION_CONFIG
    _DEFAULT_CONFIG = {
        "min_trade_count": 5,
        "min_profit_factor": 0.5,
        "max_drawdown_pnl": 50000.0,
        "min_avg_trade": -500.0,
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._block_emit = False
        
        # Store references to inputs for programmatic access
        self._inputs: dict[str, tuple[QCheckBox, QWidget]] = {}
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ── Buttons ──
        btn_layout = QHBoxLayout()
        self.btn_defaults = QPushButton("Apply Defaults")
        self.btn_clear = QPushButton("Clear All")
        btn_layout.addWidget(self.btn_defaults)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # ── Core Rules Group ──
        core_group = QGroupBox("Core Backtest Rules")
        core_layout = QFormLayout(core_group)
        
        self._add_rule(core_layout, "min_total_pnl", "Min Total PnL", -1000000.0, 1000000.0, 100.0, True)
        self._add_rule(core_layout, "min_profit_factor", "Min Profit Factor", 0.0, 100.0, 0.1, True)
        self._add_rule(core_layout, "max_drawdown_pnl", "Max Drawdown PnL", 0.0, 1000000.0, 100.0, True)
        self._add_rule(core_layout, "min_avg_trade", "Min Avg Trade", -1000000.0, 1000000.0, 10.0, True)
        self._add_rule(core_layout, "min_trade_count", "Min Trade Count", 0, 10000, 1, False)
        self._add_rule(core_layout, "min_win_rate", "Min Win Rate", 0.0, 1.0, 0.05, True)
        
        main_layout.addWidget(core_group)

        # ── Advanced Rules Group ──
        adv_group = QGroupBox("Advanced / Validation Rules")
        adv_layout = QFormLayout(adv_group)
        
        self._add_rule(adv_layout, "min_oos_total_pnl", "Min OOS Total PnL", -1000000.0, 1000000.0, 100.0, True)
        self._add_rule(adv_layout, "min_oos_profit_factor", "Min OOS Profit Factor", 0.0, 100.0, 0.1, True)
        self._add_rule(adv_layout, "min_stress_pass_rate", "Min Stress Pass Rate", 0.0, 1.0, 0.05, True)
        self._add_rule(adv_layout, "min_monte_carlo_p05_pnl", "Min MC 5% PnL", -1000000.0, 1000000.0, 100.0, True)
        self._add_rule(adv_layout, "min_walk_forward_pass_rate", "Min WF Pass Rate", 0.0, 1.0, 0.05, True)
        
        self.cb_require_optional = QCheckBox("Require optional validation data")
        self.cb_require_optional.toggled.connect(self._on_input_changed)
        adv_layout.addRow("", self.cb_require_optional)

        main_layout.addWidget(adv_group)
        main_layout.addStretch()

        # Connect buttons
        self.btn_defaults.clicked.connect(self.apply_defaults)
        self.btn_clear.clicked.connect(self.clear_all)

    def _add_rule(self, layout: QFormLayout, key: str, label: str, min_val: float, max_val: float, step: float, is_double: bool) -> None:
        """Helper to create a checkbox + spinbox row."""
        cb = QCheckBox(label)
        
        if is_double:
            spin = QDoubleSpinBox()
            spin.setRange(min_val, max_val)
            spin.setSingleStep(step)
            spin.valueChanged.connect(self._on_input_changed)
        else:
            spin = QSpinBox()
            spin.setRange(int(min_val), int(max_val))
            spin.setSingleStep(int(step))
            spin.valueChanged.connect(self._on_input_changed)
            
        spin.setEnabled(False)
        cb.toggled.connect(lambda checked, s=spin: s.setEnabled(checked))
        cb.toggled.connect(self._on_input_changed)
        
        layout.addRow(cb, spin)
        self._inputs[key] = (cb, spin)

    def _on_input_changed(self, *args: Any) -> None:
        """Triggered whenever any checkbox or spinbox changes."""
        if not self._block_emit:
            self.config_changed.emit(self.get_config_dict())

    def apply_defaults(self) -> None:
        """Apply the default conservative thresholds."""
        self.set_config_dict(self._DEFAULT_CONFIG)

    def clear_all(self) -> None:
        """Disable all rules by unchecking their checkboxes."""
        clear_cfg = {key: None for key in self._inputs}
        clear_cfg["require_optional"] = False
        self.set_config_dict(clear_cfg)

    def get_config_dict(self) -> dict[str, Any]:
        """Read the current UI state into a standard dict."""
        cfg: dict[str, Any] = {}
        for key, (cb, spin) in self._inputs.items():
            if cb.isChecked():
                cfg[key] = spin.value()
            else:
                cfg[key] = None
                
        cfg["require_optional"] = self.cb_require_optional.isChecked()
        return cfg

    def set_config_dict(self, cfg: dict[str, Any]) -> None:
        """Update the UI state to match the given dict without triggering intermediate signals.
        Missing keys are ignored, preserving their current state.
        """
        self._block_emit = True
        try:
            for key, (cb, spin) in self._inputs.items():
                if key in cfg:
                    val = cfg[key]
                    if val is not None:
                        cb.setChecked(True)
                        spin.setValue(val)
                    else:
                        cb.setChecked(False)
                        
            if "require_optional" in cfg:
                self.cb_require_optional.setChecked(bool(cfg["require_optional"]))
        finally:
            self._block_emit = False
            
        # Emit exactly once after all changes are applied
        self.config_changed.emit(self.get_config_dict())
