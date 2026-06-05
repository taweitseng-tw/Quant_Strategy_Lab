"""Instrument Profile Editor Widget — Task 009B.

Provides a PySide6 GUI to create, edit, delete, and select active InstrumentProfiles.
All operations are delegated to the InstrumentService.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.models.instrument import InstrumentProfile
from app.services.instrument_service import InstrumentService


class InstrumentEditor(QWidget):
    """GUI widget for editing and selecting Instrument Profiles."""

    active_profile_changed = Signal(str)  # Emitted when active profile changes (passes symbol)

    def __init__(self, instrument_service: InstrumentService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = instrument_service
        self._current_selected_symbol: str | None = None
        self._init_ui()
        self.refresh_list()

    def _init_ui(self) -> None:
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # 1. Project Status Banner
        self.banner = QLabel()
        self.banner.setFrameShape(QFrame.Shape.StyledPanel)
        self.banner.setWordWrap(True)
        self.banner.setMinimumHeight(45)
        self.banner.setContentsMargins(10, 10, 10, 10)
        self._update_banner_style()
        main_layout.addWidget(self.banner)

        # 2. Main content split layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # Left panel: Profiles List
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)
        
        list_label = QLabel("Available Profiles")
        list_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #26a69a;")
        left_layout.addWidget(list_label)

        self.list_widget = QListWidget()
        self.list_widget.setFixedWidth(240)
        self.list_widget.currentItemChanged.connect(self._handle_list_selection)
        left_layout.addWidget(self.list_widget)

        # Button to set selected as active
        self.btn_set_active = QPushButton("Set Selected as Active")
        self.btn_set_active.setStyleSheet(
            "background-color: #26a69a; color: white; font-weight: bold; height: 28px;"
        )
        self.btn_set_active.clicked.connect(self._handle_set_active)
        left_layout.addWidget(self.btn_set_active)

        content_layout.addLayout(left_layout)

        # Right panel: Edit Form
        self.form_group = QGroupBox("Profile Editor")
        self.form_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; color: #26a69a; }")
        form_layout = QVBoxLayout(self.form_group)
        form_layout.setContentsMargins(12, 16, 12, 12)
        form_layout.setSpacing(12)

        # The actual form fields
        grid_form = QFormLayout()
        grid_form.setSpacing(10)
        grid_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.input_symbol = QLineEdit()
        self.input_symbol.setPlaceholderText("e.g. ES")
        self.input_symbol.setMaxLength(10)
        grid_form.addRow("Symbol/Code *:", self.input_symbol)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. E-mini S&P 500")
        grid_form.addRow("Name:", self.input_name)

        self.input_market = QLineEdit()
        self.input_market.setPlaceholderText("e.g. Futures, FX, Equities")
        grid_form.addRow("Market Type:", self.input_market)

        self.input_currency = QLineEdit()
        self.input_currency.setText("USD")
        grid_form.addRow("Currency:", self.input_currency)

        # Tick Size
        self.spin_tick_size = QDoubleSpinBox()
        self.spin_tick_size.setRange(0.0001, 1000.0)
        self.spin_tick_size.setDecimals(4)
        self.spin_tick_size.setSingleStep(0.01)
        self.spin_tick_size.setValue(0.25)
        grid_form.addRow("Tick Size:", self.spin_tick_size)

        # Point Value
        self.spin_point_value = QDoubleSpinBox()
        self.spin_point_value.setRange(0.01, 100000.0)
        self.spin_point_value.setDecimals(2)
        self.spin_point_value.setSingleStep(1.0)
        self.spin_point_value.setValue(50.0)
        grid_form.addRow("Point Value (multiplier):", self.spin_point_value)

        # Commission
        self.spin_commission = QDoubleSpinBox()
        self.spin_commission.setRange(0.0, 1000.0)
        self.spin_commission.setDecimals(2)
        self.spin_commission.setSingleStep(0.5)
        self.spin_commission.setValue(2.0)
        grid_form.addRow("Commission (per-side $):", self.spin_commission)

        # Slippage Ticks
        self.spin_slippage = QDoubleSpinBox()
        self.spin_slippage.setRange(0.0, 100.0)
        self.spin_slippage.setDecimals(1)
        self.spin_slippage.setSingleStep(0.5)
        self.spin_slippage.setValue(1.0)
        grid_form.addRow("Default Slippage (ticks):", self.spin_slippage)

        self.input_session = QLineEdit()
        self.input_session.setPlaceholderText("e.g. US_Index_Futures")
        grid_form.addRow("Session Template:", self.input_session)

        form_layout.addLayout(grid_form)

        # Form Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_new = QPushButton("New Profile")
        self.btn_new.setStyleSheet("height: 28px;")
        self.btn_new.clicked.connect(self._handle_new)
        btn_layout.addWidget(self.btn_new)

        self.btn_save = QPushButton("Save / Update")
        self.btn_save.setStyleSheet("background-color: #2b5797; color: white; font-weight: bold; height: 28px;")
        self.btn_save.clicked.connect(self._handle_save)
        btn_layout.addWidget(self.btn_save)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setStyleSheet("background-color: #b91d47; color: white; font-weight: bold; height: 28px;")
        self.btn_delete.clicked.connect(self._handle_delete)
        btn_layout.addWidget(self.btn_delete)

        form_layout.addLayout(btn_layout)
        content_layout.addWidget(self.form_group, 1)

        main_layout.addLayout(content_layout)

    def _update_banner_style(self) -> None:
        """Style the status banner based on the service's project state."""
        if self.service.is_mock_data():
            self.banner.setStyleSheet(
                "background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; "
                "border-radius: 4px; font-weight: 500;"
            )
            self.banner.setText(
                "⚠️ <b>Working in In-Memory Mock Mode.</b> All instrument profile changes are stored in memory only. "
                "To persist these changes, create or open a project folder."
            )
        else:
            self.banner.setStyleSheet(
                "background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; "
                "border-radius: 4px; font-weight: 500;"
            )
            self.banner.setText(
                f"✅ <b>Active Project Mode.</b> Instrument profiles are persisted to:<br>"
                f"<code>{self.service.project_path / 'config' / 'instruments.json'}</code>"
            )

    def refresh_project_status(self) -> None:
        """Call this when project state changes to update the editor banner."""
        self._update_banner_style()
        self.refresh_list()

    def refresh_list(self) -> None:
        """Reload the list widget from service layer data."""
        self.list_widget.clear()
        active_profile = self.service.get_active_profile()
        active_symbol = active_profile.symbol if active_profile else None

        for p in self.service.get_profiles():
            item = QListWidgetItem()
            display_text = f"{p.symbol} — {p.name}" if p.name else p.symbol
            if p.symbol == active_symbol:
                display_text += " [Active]"
                font = QFont()
                font.setBold(True)
                item.setFont(font)
                
            item.setText(display_text)
            item.setData(Qt.ItemDataRole.UserRole, p.symbol)
            self.list_widget.addItem(item)

        # Select the item matching self._current_selected_symbol if possible, else default to active
        target_symbol = self._current_selected_symbol or active_symbol
        self._select_in_list(target_symbol)

    def _select_in_list(self, symbol: str | None) -> None:
        if not symbol:
            self._handle_new()
            return
            
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == symbol:
                self.list_widget.setCurrentItem(item)
                return
                
        # If symbol not found, default to new
        self._handle_new()

    def _handle_list_selection(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if not current:
            return
            
        symbol = current.data(Qt.ItemDataRole.UserRole)
        self._current_selected_symbol = symbol
        
        # Load from service and populate form
        profile = None
        for p in self.service.get_profiles():
            if p.symbol == symbol:
                profile = p
                break
                
        if profile:
            self.input_symbol.setText(profile.symbol)
            self.input_symbol.setReadOnly(True)  # Cannot edit primary key symbol directly once saved
            self.input_name.setText(profile.name)
            self.input_market.setText(profile.market)
            self.input_currency.setText(profile.currency)
            self.spin_tick_size.setValue(profile.tick_size)
            self.spin_point_value.setValue(profile.point_value)
            self.spin_commission.setValue(profile.commission_value)
            self.spin_slippage.setValue(profile.slippage_ticks)
            self.input_session.setText(profile.session_template)
            self.btn_delete.setEnabled(True)
            self.btn_set_active.setEnabled(True)

    def _handle_new(self) -> None:
        self._current_selected_symbol = None
        self.list_widget.setCurrentItem(None)
        
        self.input_symbol.clear()
        self.input_symbol.setReadOnly(False)
        self.input_symbol.setFocus()
        self.input_name.clear()
        self.input_market.clear()
        self.input_currency.setText("USD")
        self.spin_tick_size.setValue(0.25)
        self.spin_point_value.setValue(50.0)
        self.spin_commission.setValue(2.0)
        self.spin_slippage.setValue(1.0)
        self.input_session.clear()
        
        self.btn_delete.setEnabled(False)
        self.btn_set_active.setEnabled(False)

    def _handle_save(self) -> None:
        symbol = self.input_symbol.text().strip().upper()
        if not symbol:
            QMessageBox.warning(self, "Validation Error", "Profile Symbol is required.")
            return

        name = self.input_name.text().strip()
        market = self.input_market.text().strip()
        currency = self.input_currency.text().strip()
        tick_size = self.spin_tick_size.value()
        point_value = self.spin_point_value.value()
        commission = self.spin_commission.value()
        slippage = self.spin_slippage.value()
        session = self.input_session.text().strip()

        profile = InstrumentProfile(
            symbol=symbol,
            name=name,
            market=market,
            tick_size=tick_size,
            point_value=point_value,
            commission_value=commission,
            slippage_ticks=slippage,
            currency=currency,
            session_template=session,
        )

        try:
            # Delegate CRUD saving to service layer
            self.service.save_profile(profile)
            self._current_selected_symbol = symbol
            self.refresh_list()
            QMessageBox.information(
                self, "Success", f"Instrument profile '{symbol}' saved successfully."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profile: {e}")

    def _handle_delete(self) -> None:
        symbol = self.input_symbol.text().strip().upper()
        if not symbol:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete instrument profile '{symbol}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Delegate CRUD delete to service layer
                self.service.delete_profile(symbol)
                self._current_selected_symbol = None
                self.refresh_list()
                QMessageBox.information(
                    self, "Deleted", f"Instrument profile '{symbol}' deleted successfully."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete profile: {e}")

    def _handle_set_active(self) -> None:
        if not self._current_selected_symbol:
            return
            
        try:
            self.service.set_active_profile(self._current_selected_symbol)
            self.refresh_list()
            self.active_profile_changed.emit(self._current_selected_symbol)
            QMessageBox.information(
                self, "Active Selected", f"Profile '{self._current_selected_symbol}' is now set as Active."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set active profile: {e}")
