"""Application entrypoint for Quant Strategy Lab."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication


if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from app.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    exit_after_ms = os.environ.get("QSL_EXIT_AFTER_MS")
    if exit_after_ms:
        QTimer.singleShot(int(exit_after_ms), app.quit)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
