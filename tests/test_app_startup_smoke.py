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


# ---------------------------------------------------------------------------
# Subprocess desktop entrypoint smoke - Tasks 253-258
# ---------------------------------------------------------------------------


def test_subprocess_desktop_entrypoint_exits_cleanly() -> None:
    """Launch ``app/main.py`` as a subprocess with offscreen Qt platform and a
    short auto-exit timer, then assert it exits 0 within a timeout.

    If the local Qt installation cannot load the offscreen platform plugin the
    test is skipped with the captured stderr as the reason so the failure is
    actionable.
    """
    import os
    import subprocess
    import sys
    import time

    python = sys.executable
    entrypoint = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")

    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QSL_EXIT_AFTER_MS"] = "100"

    proc = subprocess.Popen(
        [python, entrypoint],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    timeout_seconds = 15
    deadline = time.monotonic() + timeout_seconds

    try:
        stdout_text, stderr_text = proc.communicate(timeout=timeout_seconds)
        elapsed = time.monotonic() - (deadline - timeout_seconds)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout_text, stderr_text = proc.communicate(timeout=5)
        elapsed = time.monotonic() - (deadline - timeout_seconds)
        assert False, (
            f"Subprocess did not exit within {timeout_seconds}s "
            f"(elapsed={elapsed:.1f}s).\n"
            f"stdout:\n{stdout_text}\n"
            f"stderr:\n{stderr_text}"
        )

    if proc.returncode != 0:
        # If the failure is a Qt platform plugin error, skip instead of fail
        # so CI or machines without the offscreen plugin get a clear signal.
        skip_reason = _check_qt_platform_error(stderr_text)
        if skip_reason:
            import pytest
            pytest.skip(skip_reason)

        assert False, (
            f"Desktop entrypoint exited with code {proc.returncode} "
            f"(elapsed={elapsed:.1f}s).\n"
            f"stdout:\n{stdout_text}\n"
            f"stderr:\n{stderr_text}"
        )


def _check_qt_platform_error(stderr: str) -> str | None:
    """Return a pytest-skip reason if *stderr* indicates a Qt platform plugin
    problem, otherwise return ``None``."""
    lower = stderr.lower()
    plugin_lookup_failed = (
        ("could not load" in lower or "could not find" in lower)
        and "platform plugin" in lower
        and "offscreen" in lower
    )
    no_platform_initialized = "no qt platform plugin could be initialized" in lower

    if plugin_lookup_failed or no_platform_initialized:
        return (
            "Qt offscreen platform plugin not available.\n"
            f"Captured stderr:\n{stderr.strip()}"
        )
    return None
