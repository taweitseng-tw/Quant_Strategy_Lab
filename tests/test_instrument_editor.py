"""Tests for InstrumentService and InstrumentEditor widget — Task 009B."""

from __future__ import annotations

import json
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from core.models.instrument import InstrumentProfile
from app.services.instrument_service import InstrumentService, DEFAULT_PROFILES
from app.widgets.instrument_editor import InstrumentEditor


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Fixture to initialize a QApplication instance for GUI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def tmp_project_dir() -> Path:
    """Fixture to create a temporary project structure and clean it up."""
    base = Path(tempfile.mkdtemp())
    proj = base / "test_project"
    proj.mkdir()
    (proj / "config").mkdir()
    yield proj
    shutil.rmtree(base, ignore_errors=True)


# ---------------------------------------------------------------------------
# InstrumentService Tests
# ---------------------------------------------------------------------------

def test_instrument_service_in_memory_defaults() -> None:
    """Verify that InstrumentService initializes with default profiles in-memory when no project exists."""
    service = InstrumentService()
    assert service.is_mock_data() is True
    assert service.project_path is None
    
    profiles = service.get_profiles()
    assert len(profiles) == len(DEFAULT_PROFILES)
    
    # Active symbol should be defaulted to the first profile's symbol
    active = service.get_active_profile()
    assert active is not None
    assert active.symbol == DEFAULT_PROFILES[0].symbol


def test_instrument_service_active_profile_switching() -> None:
    """Verify that we can set different active profiles."""
    service = InstrumentService()
    
    # Switch to NQ
    service.set_active_profile("NQ")
    active = service.get_active_profile()
    assert active is not None
    assert active.symbol == "NQ"
    
    # Switch to invalid does not change active
    service.set_active_profile("INVALID")
    active2 = service.get_active_profile()
    assert active2 is not None
    assert active2.symbol == "NQ"
    
    # Switch to None clears active
    service.set_active_profile(None)
    assert service.get_active_profile() is None


def test_instrument_service_save_and_delete_in_memory() -> None:
    """Verify save_profile and delete_profile behavior in-memory."""
    service = InstrumentService()
    
    new_profile = InstrumentProfile(
        symbol="BTCUSD",
        name="Bitcoin Spot USD",
        market="Crypto",
        tick_size=0.01,
        point_value=1.0,
        commission_value=0.5,
        slippage_ticks=2.0,
        currency="USD"
    )
    
    # Save
    service.save_profile(new_profile)
    profiles = service.get_profiles()
    assert any(p.symbol == "BTCUSD" for p in profiles)
    
    # Set Active and select it
    service.set_active_profile("BTCUSD")
    assert service.get_active_profile().name == "Bitcoin Spot USD"
    
    # Delete
    service.delete_profile("BTCUSD")
    profiles = service.get_profiles()
    assert not any(p.symbol == "BTCUSD" for p in profiles)
    
    # Deleted active should fallback to first profile or None
    assert service.get_active_profile().symbol == DEFAULT_PROFILES[0].symbol


def test_instrument_service_empty_symbol_raises() -> None:
    """Verify that saving a profile with an empty symbol raises ValueError."""
    service = InstrumentService()
    bad_profile = InstrumentProfile(symbol="")
    with pytest.raises(ValueError, match="symbol cannot be empty"):
        service.save_profile(bad_profile)


# ---------------------------------------------------------------------------
# Disk-based Persistence Tests
# ---------------------------------------------------------------------------

def test_instrument_service_disk_persistence(tmp_project_dir) -> None:
    """Verify that InstrumentService writes to and reads from config/instruments.json when active."""
    service = InstrumentService(tmp_project_dir)
    assert service.is_mock_data() is False
    assert service.project_path == tmp_project_dir
    
    # File config/instruments.json should be initialized with defaults
    instruments_file = tmp_project_dir / "config" / "instruments.json"
    assert instruments_file.is_file()
    
    # Load raw JSON to check structure
    with open(instruments_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) == len(DEFAULT_PROFILES)
    assert data[0]["symbol"] == "ES"
    
    # Save a custom profile
    my_profile = InstrumentProfile(
        symbol="MY_SYM",
        name="My Custom Sym",
        tick_size=0.05,
        point_value=10.0,
        commission_value=1.5,
        slippage_ticks=1.0,
        currency="USD"
    )
    service.save_profile(my_profile)
    
    # Verify disk has updated
    with open(instruments_file, "r", encoding="utf-8") as f:
        updated_data = json.load(f)
    assert len(updated_data) == len(DEFAULT_PROFILES) + 1
    assert any(item["symbol"] == "MY_SYM" for item in updated_data)
    
    # Verify a new service instance reading from same folder loads it
    service2 = InstrumentService(tmp_project_dir)
    assert any(p.symbol == "MY_SYM" for p in service2.get_profiles())
    
    # Delete from service2
    service2.delete_profile("MY_SYM")
    assert not any(p.symbol == "MY_SYM" for p in service2.get_profiles())
    
    # Verify disk reflects deletion
    with open(instruments_file, "r", encoding="utf-8") as f:
        after_delete_data = json.load(f)
    assert not any(item["symbol"] == "MY_SYM" for item in after_delete_data)


# ---------------------------------------------------------------------------
# InstrumentEditor UI Widget Tests
# ---------------------------------------------------------------------------

def test_instrument_editor_widget_initialization(qapp) -> None:
    """Verify that InstrumentEditor widget builds and loads the profiles correctly."""
    service = InstrumentService()
    editor = InstrumentEditor(service)
    
    # Check that profiles are populated in list widget
    assert editor.list_widget.count() == len(DEFAULT_PROFILES)
    
    # Check that first item is bolded/Active
    first_item = editor.list_widget.item(0)
    assert "[Active]" in first_item.text()
    
    # Check default form values match the first profile
    assert editor.input_symbol.text() == "ES"
    assert editor.input_name.text() == "E-mini S&P 500"
    assert editor.spin_tick_size.value() == 0.25
    assert editor.spin_point_value.value() == 50.0
    assert editor.spin_commission.value() == 2.0
    assert editor.spin_slippage.value() == 1.0


def test_instrument_editor_widget_new_profile_clears_form(qapp) -> None:
    """Verify that clicking 'New Profile' clears the form inputs."""
    service = InstrumentService()
    editor = InstrumentEditor(service)
    
    # Trigger 'New Profile'
    editor._handle_new()
    
    assert editor.input_symbol.text() == ""
    assert editor.input_symbol.isReadOnly() is False
    assert editor.input_name.text() == ""
    assert editor.input_market.text() == ""
    assert editor.spin_tick_size.value() == 0.25
    assert editor.spin_point_value.value() == 50.0
    assert editor.spin_commission.value() == 2.0
    assert editor.spin_slippage.value() == 1.0
    assert editor.btn_delete.isEnabled() is False
    assert editor.btn_set_active.isEnabled() is False


def test_instrument_editor_selection_and_active_switching(qapp, monkeypatch) -> None:
    """Verify that selecting a different item in the list switches the details form and active state."""
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )

    service = InstrumentService()
    editor = InstrumentEditor(service)
    
    # Track signal emission
    emitted_symbol = []
    editor.active_profile_changed.connect(lambda s: emitted_symbol.append(s))
    
    # Find NQ item and select it
    nq_item = None
    for i in range(editor.list_widget.count()):
        item = editor.list_widget.item(i)
        if item.data(Qt.ItemDataRole.UserRole) == "NQ":
            nq_item = item
            break
            
    assert nq_item is not None
    editor.list_widget.setCurrentItem(nq_item)
    
    # Forms should be populated with NQ values
    assert editor.input_symbol.text() == "NQ"
    assert editor.input_name.text() == "E-mini Nasdaq 100"
    assert editor.spin_point_value.value() == 20.0
    
    # Set as active
    editor._handle_set_active()
    
    assert service.get_active_profile().symbol == "NQ"
    assert len(emitted_symbol) == 1
    assert emitted_symbol[0] == "NQ"
    
    # Verify NQ list item has [Active] tag now
    new_nq_item = None
    for i in range(editor.list_widget.count()):
        item = editor.list_widget.item(i)
        if item.data(Qt.ItemDataRole.UserRole) == "NQ":
            new_nq_item = item
            break
    assert new_nq_item is not None
    assert "[Active]" in new_nq_item.text()
