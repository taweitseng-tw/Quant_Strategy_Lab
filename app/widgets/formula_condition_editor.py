"""Passive widget for entering and previewing formula conditions — Task 045C1."""

from __future__ import annotations

from PySide6 import QtCore
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QGroupBox,
    QDialog,
    QComboBox,
)

from strategy_engine.formula_parser import parse_formula_to_block, FormulaParseError
from core.models.strategy import StrategyBlock


class FormulaConditionEditor(QWidget):
    """Passive widget that lets a user type a safe formula string and previews it.
    
    Emits a formula_accepted signal containing a parsed StrategyBlock only when 
    the formula is valid and the user clicks 'Apply'.
    """

    formula_accepted = QtCore.Signal(StrategyBlock)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        self._current_block: StrategyBlock | None = None
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # ── Input Area ──
        input_group = QGroupBox("Formula Input")
        input_layout = QVBoxLayout(input_group)
        
        self.le_formula = QLineEdit()
        self.le_formula.setPlaceholderText("e.g. close > SMA(20) AND RSI(14) > 70")
        self.le_formula.textChanged.connect(self._on_text_changed)
        input_layout.addWidget(self.le_formula)
        
        # ── Status and Preview ──
        self.lbl_status = QLabel("Enter a formula.")
        self.lbl_status.setStyleSheet("color: gray;")
        self.lbl_status.setWordWrap(True)
        input_layout.addWidget(self.lbl_status)
        
        self.lbl_preview = QLabel("")
        self.lbl_preview.setWordWrap(True)
        input_layout.addWidget(self.lbl_preview)
        
        main_layout.addWidget(input_group)
        
        # ── Buttons ──
        btn_layout = QHBoxLayout()
        self.btn_clear = QPushButton("Clear")
        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setEnabled(False)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addWidget(self.btn_apply)
        
        main_layout.addLayout(btn_layout)
        
        # Connect buttons
        self.btn_clear.clicked.connect(self.clear)
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        
        self._validate_current_text()

    def _on_text_changed(self, text: str) -> None:
        """Triggered whenever the user types in the formula line edit."""
        self._validate_current_text()

    def _validate_current_text(self) -> None:
        """Parse the text and update the UI status."""
        text = self.le_formula.text().strip()
        if not text:
            self._set_invalid_state("Enter a formula.")
            return

        try:
            block = parse_formula_to_block(text)
            self._set_valid_state(block)
        except FormulaParseError as e:
            self._set_invalid_state(f"Error: {str(e)}")
        except Exception as e:
            # Fallback for unexpected errors during parsing to prevent UI crashes
            self._set_invalid_state(f"Unexpected error: {str(e)}")

    def _set_invalid_state(self, message: str) -> None:
        """Set the widget to an invalid state with a given error message."""
        self._current_block = None
        self.btn_apply.setEnabled(False)
        self.lbl_status.setText(message)
        self.lbl_status.setStyleSheet("color: red;")
        self.lbl_preview.setText("")

    def _set_valid_state(self, block: StrategyBlock) -> None:
        """Set the widget to a valid state with a parsed StrategyBlock."""
        self._current_block = block
        self.btn_apply.setEnabled(True)
        self.lbl_status.setText("Valid formula.")
        self.lbl_status.setStyleSheet("color: green;")
        
        cond_count = len(block.conditions)
        logic_str = block.logic
        self.lbl_preview.setText(f"Preview: {cond_count} condition(s) joined by {logic_str}.")

    def _on_apply_clicked(self) -> None:
        """Emit the strategy block if valid."""
        if self._current_block is not None:
            self.formula_accepted.emit(self._current_block)

    def get_formula(self) -> str:
        """Return the current raw text in the formula input."""
        return self.le_formula.text()

    def set_formula(self, text: str) -> None:
        """Set the formula text programmatically and re-validate."""
        self.le_formula.setText(text)

    def clear(self) -> None:
        """Clear the formula text and reset to invalid empty state."""
        self.le_formula.clear()


class FormulaConditionDialog(QDialog):
    """Dialog wrapper around FormulaConditionEditor to select target block."""
    
    # Emits (target_block_name, strategy_block)
    condition_added = QtCore.Signal(str, StrategyBlock)
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Custom Condition")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Target Block Selection
        block_layout = QHBoxLayout()
        block_layout.addWidget(QLabel("Target Block:"))
        self.combo_target_block = QComboBox()
        self.combo_target_block.addItems([
            "Long Entry",
            "Long Exit",
            "Short Entry",
            "Short Exit"
        ])
        block_layout.addWidget(self.combo_target_block, stretch=1)
        layout.addLayout(block_layout)
        
        # Editor Widget
        self.editor = FormulaConditionEditor()
        self.editor.formula_accepted.connect(self._on_formula_accepted)
        layout.addWidget(self.editor)
        
    def _on_formula_accepted(self, block: StrategyBlock) -> None:
        """Bubble up the signal with the selected target block and close dialog."""
        target_block_name = self.combo_target_block.currentText()
        self.condition_added.emit(target_block_name, block)
        self.accept()
