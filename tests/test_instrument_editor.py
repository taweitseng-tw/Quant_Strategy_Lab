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


def test_instrument_service_save_preserves_unrelated_config_files(tmp_project_dir) -> None:
    """Saving instrument profiles must not mutate sessions or app settings."""
    sessions_path = tmp_project_dir / "config" / "sessions.json"
    settings_path = tmp_project_dir / "config" / "app_settings.json"
    sessions_data = [{"name": "custom_session", "start": "09:00", "end": "13:30"}]
    settings_data = {
        "execution_model": "next_bar_open",
        "same_bar_ambiguity": "stop_loss_first",
        "custom_key": "preserve-me",
    }
    sessions_path.write_text(json.dumps(sessions_data, indent=2), encoding="utf-8")
    settings_path.write_text(json.dumps(settings_data, indent=2), encoding="utf-8")

    service = InstrumentService(tmp_project_dir)
    profile = InstrumentProfile(
        symbol="QSL",
        name="QSL Test",
        market="Test",
        tick_size=0.5,
        point_value=10.0,
        commission_value=1.0,
        slippage_ticks=1.0,
        currency="USD",
        session_template="custom_session",
    )
    service.save_profile(profile)

    instruments_path = tmp_project_dir / "config" / "instruments.json"
    instruments = json.loads(instruments_path.read_text(encoding="utf-8"))
    assert any(item["symbol"] == "QSL" for item in instruments)
    assert json.loads(sessions_path.read_text(encoding="utf-8")) == sessions_data
    assert json.loads(settings_path.read_text(encoding="utf-8")) == settings_data

    reloaded = InstrumentService(tmp_project_dir)
    assert any(p.symbol == "QSL" for p in reloaded.get_profiles())


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


# ---------------------------------------------------------------------------
# Malformed/empty instruments.json recovery - Task 114A-114C
# ---------------------------------------------------------------------------


def test_recovers_from_malformed_instruments_json(tmp_project_dir) -> None:
    """Malformed instruments.json must recover to DEFAULT_PROFILES and
    rewrite the file as valid JSON."""
    cfg = tmp_project_dir / "config" / "instruments.json"
    cfg.write_text("not valid json", encoding="utf-8")

    service = InstrumentService(tmp_project_dir)
    profiles = service.get_profiles()
    assert len(profiles) == len(DEFAULT_PROFILES), "Must recover to default profiles"
    assert profiles[0].symbol == DEFAULT_PROFILES[0].symbol

    # File must now be valid JSON.
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == len(DEFAULT_PROFILES)
    assert data[0]["symbol"] == "ES"


def test_recovers_from_empty_list_instruments_json(tmp_project_dir) -> None:
    """Empty list in instruments.json must initialize DEFAULT_PROFILES and
    write valid JSON."""
    cfg = tmp_project_dir / "config" / "instruments.json"
    cfg.write_text("[]", encoding="utf-8")
    sessions_path = tmp_project_dir / "config" / "sessions.json"
    settings_path = tmp_project_dir / "config" / "app_settings.json"
    sessions_data = [{"name": "empty_list_session"}]
    settings_data = {"execution_model": "next_bar_open", "custom_key": "keep"}
    sessions_path.write_text(json.dumps(sessions_data, indent=2), encoding="utf-8")
    settings_path.write_text(json.dumps(settings_data, indent=2), encoding="utf-8")

    service = InstrumentService(tmp_project_dir)
    profiles = service.get_profiles()
    assert len(profiles) == len(DEFAULT_PROFILES), "Must recover to default profiles"
    assert profiles[0].symbol == "ES"

    # File must now contain the full default list.
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert len(data) == len(DEFAULT_PROFILES)
    assert json.loads(sessions_path.read_text(encoding="utf-8")) == sessions_data
    assert json.loads(settings_path.read_text(encoding="utf-8")) == settings_data


def test_recovery_preserves_sessions_json(tmp_project_dir) -> None:
    """Recovery from malformed instruments.json must not mutate sessions.json."""
    cfg = tmp_project_dir / "config" / "instruments.json"
    cfg.write_text("not json", encoding="utf-8")

    sessions_path = tmp_project_dir / "config" / "sessions.json"
    sessions_path.write_text(
        json.dumps([{"name": "preserved_session"}], indent=2), encoding="utf-8"
    )

    _ = InstrumentService(tmp_project_dir)

    saved = json.loads(sessions_path.read_text(encoding="utf-8"))
    assert saved == [{"name": "preserved_session"}], "sessions.json must be preserved"


def test_recovery_preserves_app_settings_custom_keys(tmp_project_dir) -> None:
    """Recovery from malformed instruments.json must preserve custom keys in
    app_settings.json."""
    cfg = tmp_project_dir / "config" / "instruments.json"
    cfg.write_text("not json", encoding="utf-8")

    settings_path = tmp_project_dir / "config" / "app_settings.json"
    settings_path.write_text(
        json.dumps({"execution_model": "next_bar_open", "my_custom_key": "survive"}, indent=2),
        encoding="utf-8",
    )

    _ = InstrumentService(tmp_project_dir)

    saved = json.loads(settings_path.read_text(encoding="utf-8"))
    assert saved.get("execution_model") == "next_bar_open"
    assert saved.get("my_custom_key") == "survive", "Custom keys must be preserved"


# ---------------------------------------------------------------------------
# InstrumentEditor UI save isolation - Task 115
# ---------------------------------------------------------------------------


def test_editor_save_updates_instruments_json_only(qapp, tmp_project_dir, monkeypatch) -> None:
    """Saving through the editor must update instruments.json but not
    sessions.json or app_settings.json."""
    from app.widgets.instrument_editor import InstrumentEditor

    # Pre-write sessions and app_settings with known content.
    sessions_path = tmp_project_dir / "config" / "sessions.json"
    sessions_path.write_text(
        json.dumps([{"name": "session_snapshot"}], indent=2), encoding="utf-8"
    )
    settings_path = tmp_project_dir / "config" / "app_settings.json"
    settings_path.write_text(
        json.dumps({"execution_model": "next_bar_open", "my_key": "preserve"}, indent=2),
        encoding="utf-8",
    )

    service = InstrumentService(tmp_project_dir)
    editor = InstrumentEditor(service)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)

    # Edit the first profile via the UI form.
    try:
        editor.input_name.setText("Changed Name Via Editor")
        editor._handle_save()
    finally:
        editor.close()

    # instruments.json must reflect the change.
    instruments_path = tmp_project_dir / "config" / "instruments.json"
    instruments_data = json.loads(instruments_path.read_text(encoding="utf-8"))
    assert any(p["name"] == "Changed Name Via Editor" for p in instruments_data)

    # sessions.json and app_settings.json must be untouched.
    assert json.loads(sessions_path.read_text(encoding="utf-8")) == [{"name": "session_snapshot"}]
    assert json.loads(settings_path.read_text(encoding="utf-8")) == {
        "execution_model": "next_bar_open",
        "my_key": "preserve",
    }


# ---------------------------------------------------------------------------
# Missing instruments.json recovery isolation - Task 116
# ---------------------------------------------------------------------------


def test_missing_instruments_json_recovers_and_writes(tmp_project_dir) -> None:
    """When instruments.json does not exist, InstrumentService must recover
    to DEFAULT_PROFILES, write valid JSON, and preserve unrelated config."""
    # Pre-write sessions and app_settings.
    sessions_path = tmp_project_dir / "config" / "sessions.json"
    sessions_path.write_text(
        json.dumps([{"name": "preserved_session"}], indent=2), encoding="utf-8"
    )
    settings_path = tmp_project_dir / "config" / "app_settings.json"
    settings_path.write_text(
        json.dumps({"my_custom": "value"}, indent=2), encoding="utf-8"
    )

    # Intentionally do NOT create instruments.json.
    instruments_path = tmp_project_dir / "config" / "instruments.json"
    assert not instruments_path.is_file()

    service = InstrumentService(tmp_project_dir)

    # File must now exist with DEFAULT_PROFILES.
    assert instruments_path.is_file()
    data = json.loads(instruments_path.read_text(encoding="utf-8"))
    assert len(data) == len(DEFAULT_PROFILES)
    assert data[0]["symbol"] == "ES"

    # Profiles loaded correctly.
    profiles = service.get_profiles()
    assert len(profiles) == len(DEFAULT_PROFILES)
    assert profiles[0].symbol == "ES"

    # Unrelated config preserved.
    assert json.loads(sessions_path.read_text(encoding="utf-8")) == [{"name": "preserved_session"}]
    assert json.loads(settings_path.read_text(encoding="utf-8")) == {"my_custom": "value"}


# ---------------------------------------------------------------------------
# Invalid list items recovery - Task 117
# ---------------------------------------------------------------------------


def test_invalid_items_without_symbol_recovers(tmp_project_dir) -> None:
    """instruments.json containing dicts without 'symbol' must recover to
    DEFAULT_PROFILES and write valid JSON."""
    instruments_path = tmp_project_dir / "config" / "instruments.json"
    invalid_data = [
        {"name": "No Symbol", "value": 100},
        {"not_symbol": "Also Missing", "tick_size": 0.5},
    ]
    instruments_path.write_text(json.dumps(invalid_data, indent=2), encoding="utf-8")

    service = InstrumentService(tmp_project_dir)

    # File rewritten with DEFAULT_PROFILES.
    data = json.loads(instruments_path.read_text(encoding="utf-8"))
    assert len(data) == len(DEFAULT_PROFILES)
    assert data[0]["symbol"] == "ES"

    # Profiles recovered.
    profiles = service.get_profiles()
    assert len(profiles) == len(DEFAULT_PROFILES)
    assert profiles[0].symbol == "ES"


def test_invalid_items_preserves_unrelated_config(tmp_project_dir) -> None:
    """Recovery from invalid list items must preserve sessions and app_settings."""
    instruments_path = tmp_project_dir / "config" / "instruments.json"
    instruments_path.write_text(
        json.dumps([{"bad": "item"}], indent=2), encoding="utf-8"
    )
    sessions_path = tmp_project_dir / "config" / "sessions.json"
    sessions_path.write_text(
        json.dumps([{"name": "keep_session"}], indent=2), encoding="utf-8"
    )
    settings_path = tmp_project_dir / "config" / "app_settings.json"
    settings_path.write_text(
        json.dumps({"keep": "me"}, indent=2), encoding="utf-8"
    )

    _ = InstrumentService(tmp_project_dir)

    assert json.loads(sessions_path.read_text(encoding="utf-8")) == [{"name": "keep_session"}]
    assert json.loads(settings_path.read_text(encoding="utf-8")) == {"keep": "me"}


# ---------------------------------------------------------------------------
# Partial valid/invalid mix - 117 edge case
# ---------------------------------------------------------------------------


def test_partial_valid_items_loaded_invalid_skipped(tmp_project_dir) -> None:
    """When instruments.json has some valid and some invalid items, valid
    items must be loaded and invalid items silently skipped without recovery
    or file rewrite."""
    instruments_path = tmp_project_dir / "config" / "instruments.json"
    mixed_data = [
        {"symbol": "ES", "name": "E-mini S&P 500", "tick_size": 0.25, "point_value": 50.0,
         "commission_value": 2.0, "slippage_ticks": 1.0, "currency": "USD"},
        {"bad": "item"},
        {"symbol": "NQ", "name": "E-mini Nasdaq 100", "tick_size": 0.25, "point_value": 20.0,
         "commission_value": 2.0, "slippage_ticks": 1.0, "currency": "USD"},
    ]
    instruments_path.write_text(json.dumps(mixed_data, indent=2), encoding="utf-8")

    service = InstrumentService(tmp_project_dir)
    profiles = service.get_profiles()
    symbols = [p.symbol for p in profiles]
    assert "ES" in symbols, "Valid item must be loaded"
    assert "NQ" in symbols, "Valid item must be loaded"
    assert len(symbols) == 2, "Only valid items should be loaded; invalid skipped"

    # File should NOT be rewritten - valid items existed so no recovery triggered.
    data = json.loads(instruments_path.read_text(encoding="utf-8"))
    assert len(data) == 3, "File should retain all items (no rewrite on partial load)"
