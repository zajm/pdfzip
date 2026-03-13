"""Log panel widget for displaying debug messages."""

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget, QLabel


class LogPanel(QWidget):
    """A panel that displays log messages with timestamps."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Header label
        header = QLabel("Log Output")
        header.setStyleSheet("font-weight: bold;")
        layout.addWidget(header)

        # Text area for log messages
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(
            "font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 11px;"
        )
        layout.addWidget(self.text_edit)

        self.log("Ready.")

    def _is_dark_theme(self) -> bool:
        """Check if the current theme is dark based on window background color."""
        palette = self.palette()
        bg_color = palette.color(QPalette.ColorRole.Window)
        # Calculate luminance - if less than 128, it's a dark theme
        luminance = (bg_color.red() * 0.299 + bg_color.green() * 0.587 + bg_color.blue() * 0.114)
        return luminance < 128

    def _get_colors(self) -> dict[str, str]:
        """Get appropriate colors based on current theme."""
        if self._is_dark_theme():
            return {
                "timestamp": "#6a9955",  # Muted green
                "INFO": "#d4d4d4",       # Light gray
                "WARN": "#dcdcaa",       # Yellow
                "ERROR": "#f14c4c",      # Red
                "SUCCESS": "#4ec9b0",    # Teal
            }
        else:
            return {
                "timestamp": "#098658",  # Dark green
                "INFO": "#333333",       # Dark gray
                "WARN": "#795e26",       # Brown/orange
                "ERROR": "#a31515",      # Dark red
                "SUCCESS": "#0b7261",    # Dark teal
            }

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Add a log message with timestamp.

        Args:
            message: The message to log
            level: Log level (INFO, WARN, ERROR, SUCCESS)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = self._get_colors()

        timestamp_color = colors["timestamp"]
        message_color = colors.get(level, colors["INFO"])

        html = f'<span style="color: {timestamp_color};">[{timestamp}]</span> <span style="color: {message_color};">{message}</span>'
        self.text_edit.append(html)

        # Auto-scroll to bottom
        scrollbar = self.text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def info(self, message: str) -> None:
        """Log an info message."""
        self.log(message, "INFO")

    def warn(self, message: str) -> None:
        """Log a warning message."""
        self.log(message, "WARN")

    def error(self, message: str) -> None:
        """Log an error message."""
        self.log(message, "ERROR")

    def success(self, message: str) -> None:
        """Log a success message."""
        self.log(message, "SUCCESS")

    def clear(self) -> None:
        """Clear all log messages."""
        self.text_edit.clear()
