"""Desktop startup smoke test — Tasks 247-252.

Tests that the main application entrypoint and MainWindow import and
construct correctly without starting a long-running GUI event loop.
"""

from __future__ import annotations

import sys

# ---------------------------------------------------------------------------
# Import smoke
# ---------------------------------------------------------------------------


def test_app_main_imports_and_callable() -> None:
    """app.main.main must import and be callable."""
    import app.main
    assert hasattr(app.main, "main")
    assert callable(app.main.main)


def test_main_window_imports() -> None:
    """MainWindow must import without error."""
    from app.ui.main_window import MainWindow
    assert MainWindow is not None


def test_main_window_import_path() -> None:
    """Ensure project root is on sys.path for local imports, matching main()."""
    from pathlib import Path
    expected = str(Path(__file__).resolve().parents[1])
    assert expected in sys.path, (
        f"Project root {expected} not in sys.path — "
        "some imports may fail when running outside the project root."
    )


# ---------------------------------------------------------------------------
# Offscreen MainWindow construction smoke
# ---------------------------------------------------------------------------


def test_offscreen_main_window_construct_and_close(monkeypatch) -> None:
    """Construct and close MainWindow offscreen without starting event loop."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    app = None
    window = None
    try:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        from app.ui.main_window import MainWindow

        window = MainWindow()
        assert window.windowTitle() == "Quant Strategy Lab"
        assert window.width() > 0
        assert window.height() > 0
    finally:
        if window is not None:
            window.close()
            window.deleteLater()
        if app is not None:
            # Process pending events to flush close/delete signals.
            app.processEvents()
