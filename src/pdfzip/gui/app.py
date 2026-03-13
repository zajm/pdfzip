"""Application setup and entry point for the GUI."""

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .main_window import MainWindow


def run_gui() -> int:
    """Run the GUI application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("PDFZip")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("PDFZip")

    # Use system style - no custom palette, respects system theme
    # On Linux with Qt6, this will follow the system color scheme

    # Create and show main window
    window = MainWindow()
    window.show()

    return app.exec()
