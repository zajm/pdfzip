"""PDF preview widgets with drag-drop support."""

import tempfile
from pathlib import Path
from typing import Optional, Callable

import fitz  # PyMuPDF
from PySide6.QtCore import Qt, Signal, QMimeData, QUrl, QPoint
from PySide6.QtGui import QPixmap, QImage, QDrag, QPalette
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QFileDialog, QSizePolicy, QFrame
)


class PdfPreviewLabel(QLabel):
    """A label that displays PDF pages and supports drag-drop."""

    file_dropped = Signal(str)  # Emits file path when a file is dropped
    drag_started = Signal()  # Emits when drag-out starts

    def __init__(self, parent=None, accept_drops: bool = True, allow_drag_out: bool = False):
        super().__init__(parent)
        self._accept_drops = accept_drops
        self._allow_drag_out = allow_drag_out
        self._file_path: Optional[Path] = None
        self._drag_start_pos: Optional[QPoint] = None

        self.setAcceptDrops(accept_drops)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self._apply_default_style()
        self._show_placeholder()

    def _apply_default_style(self):
        """Apply default border style."""
        self.setStyleSheet("QLabel { border: 2px dashed palette(mid); border-radius: 8px; }")

    def _apply_drag_hover_style(self):
        """Apply style when dragging over."""
        self.setStyleSheet("QLabel { border: 2px solid palette(highlight); border-radius: 8px; }")

    def _show_placeholder(self):
        """Show placeholder text."""
        if self._accept_drops:
            self.setText("Drop PDF here\nor click Open")
        else:
            self.setText("Output preview\nwill appear here")

    def set_file_path(self, path: Path) -> None:
        """Set the file path for drag-out operations."""
        self._file_path = path

    def get_file_path(self) -> Optional[Path]:
        """Get the current file path."""
        return self._file_path

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if not self._accept_drops:
            event.ignore()
            return

        mime_data = event.mimeData()
        if mime_data.hasUrls():
            urls = mime_data.urls()
            if urls and urls[0].toLocalFile().lower().endswith('.pdf'):
                event.acceptProposedAction()
                self._apply_drag_hover_style()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self._apply_default_style()

    def dropEvent(self, event):
        """Handle drop event."""
        if not self._accept_drops:
            event.ignore()
            return

        mime_data = event.mimeData()
        if mime_data.hasUrls():
            urls = mime_data.urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.pdf'):
                    self.file_dropped.emit(file_path)
                    event.acceptProposedAction()

        self._apply_default_style()

    def mousePressEvent(self, event):
        """Handle mouse press for drag-out."""
        if self._allow_drag_out and event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for drag-out."""
        if not self._allow_drag_out or not self._drag_start_pos:
            return

        if not self._file_path or not self._file_path.exists():
            return

        # Check if we've moved enough to start a drag
        if (event.pos() - self._drag_start_pos).manhattanLength() < 20:
            return

        self._drag_start_pos = None
        self.drag_started.emit()

        # Create drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(str(self._file_path))])
        drag.setMimeData(mime_data)

        # Set drag pixmap (thumbnail of the preview)
        pixmap = self.pixmap()
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(100, 140, Qt.AspectRatioMode.KeepAspectRatio)
            drag.setPixmap(scaled)
            drag.setHotSpot(QPoint(scaled.width() // 2, scaled.height() // 2))

        drag.exec(Qt.DropAction.CopyAction)

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)


class InputPdfWidget(QWidget):
    """Widget for input PDF with preview, reverse toggle, and open button."""

    file_changed = Signal(str)  # Emits file path when file changes
    settings_changed = Signal()  # Emits when reverse setting changes

    def __init__(self, title: str, parent=None, log_callback: Optional[Callable] = None):
        super().__init__(parent)
        self._title = title
        self._file_path: Optional[Path] = None
        self._doc: Optional[fitz.Document] = None
        self._log = log_callback or (lambda msg: None)
        self._last_directory: Optional[Path] = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Title
        title_label = QLabel(self._title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Preview
        self.preview = PdfPreviewLabel(accept_drops=True)
        self.preview.file_dropped.connect(self._on_file_dropped)
        layout.addWidget(self.preview, 1)

        # Controls
        controls = QHBoxLayout()
        controls.setSpacing(8)

        self.reverse_check = QCheckBox("Reverse order")
        self.reverse_check.stateChanged.connect(self._on_reverse_changed)
        controls.addWidget(self.reverse_check)

        controls.addStretch()

        self.open_btn = QPushButton("Open")
        self.open_btn.setMinimumWidth(80)
        self.open_btn.clicked.connect(self._on_open_clicked)
        controls.addWidget(self.open_btn)

        layout.addLayout(controls)

    def _on_file_dropped(self, path: str):
        """Handle file drop."""
        self.load_file(Path(path))

    def _on_open_clicked(self):
        """Handle open button click."""
        start_dir = str(self._last_directory) if self._last_directory else ""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select PDF for {self._title}",
            start_dir,
            "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self.load_file(Path(file_path))

    def _on_reverse_changed(self):
        """Handle reverse checkbox change."""
        self._update_preview()
        self.settings_changed.emit()

    def load_file(self, path: Path) -> bool:
        """Load a PDF file."""
        try:
            if self._doc:
                self._doc.close()

            self._doc = fitz.open(path)
            self._file_path = path
            self._last_directory = path.parent
            self._log(f"Loaded: {path.name} ({len(self._doc)} pages)")
            self._update_preview()
            self.file_changed.emit(str(path))
            return True
        except Exception as e:
            self._log(f"Error loading {path.name}: {e}")
            return False

    def _update_preview(self):
        """Update the preview with the current page."""
        if not self._doc or len(self._doc) == 0:
            return

        # Show first page (or last if reversed)
        page_idx = len(self._doc) - 1 if self.reverse_check.isChecked() else 0
        self._render_page(page_idx)

    def _render_page(self, page_idx: int):
        """Render a specific page to the preview."""
        if not self._doc or page_idx < 0 or page_idx >= len(self._doc):
            return

        page = self._doc[page_idx]

        # Calculate zoom to fit preview area
        preview_size = self.preview.size()
        page_rect = page.rect
        zoom_x = (preview_size.width() - 20) / page_rect.width
        zoom_y = (preview_size.height() - 20) / page_rect.height
        zoom = min(zoom_x, zoom_y, 2.0)  # Cap at 2x zoom

        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert to QPixmap
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        self.preview.setPixmap(pixmap)

    def get_file_path(self) -> Optional[Path]:
        """Get the current file path."""
        return self._file_path

    def is_reversed(self) -> bool:
        """Check if reverse order is enabled."""
        return self.reverse_check.isChecked()

    def get_page_count(self) -> int:
        """Get the number of pages in the loaded document."""
        return len(self._doc) if self._doc else 0

    def set_last_directory(self, path: Path) -> None:
        """Set the last used directory."""
        self._last_directory = path

    def get_last_directory(self) -> Optional[Path]:
        """Get the last used directory."""
        return self._last_directory

    def close_document(self):
        """Close the current document."""
        if self._doc:
            self._doc.close()
            self._doc = None


class OutputPdfWidget(QWidget):
    """Widget for output PDF preview with page navigation."""

    interleave_requested = Signal()
    save_requested = Signal()

    def __init__(self, parent=None, log_callback: Optional[Callable] = None):
        super().__init__(parent)
        self._doc: Optional[fitz.Document] = None
        self._file_path: Optional[Path] = None
        self._current_page = 0
        self._log = log_callback or (lambda msg: None)
        self._temp_file: Optional[Path] = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Title
        title_label = QLabel("OUTPUT PREVIEW")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Preview (supports drag-out)
        self.preview = PdfPreviewLabel(accept_drops=False, allow_drag_out=True)
        self.preview.drag_started.connect(self._on_drag_started)
        layout.addWidget(self.preview, 1)

        # Page navigation
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)

        nav_layout.addStretch()

        self.prev_btn = QPushButton("\u25c0")  # ◀
        self.prev_btn.setFixedWidth(40)
        self.prev_btn.clicked.connect(self._prev_page)
        self.prev_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)

        self.page_label = QLabel("No output")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setMinimumWidth(100)
        nav_layout.addWidget(self.page_label)

        self.next_btn = QPushButton("\u25b6")  # ▶
        self.next_btn.setFixedWidth(40)
        self.next_btn.clicked.connect(self._next_page)
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)

        nav_layout.addStretch()

        layout.addLayout(nav_layout)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.interleave_btn = QPushButton("Interleave")
        self.interleave_btn.setMinimumWidth(100)
        self.interleave_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        self.interleave_btn.clicked.connect(self.interleave_requested.emit)
        btn_layout.addWidget(self.interleave_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setMinimumWidth(80)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_requested.emit)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _on_drag_started(self):
        """Handle drag-out start."""
        if self._file_path:
            self._log(f"Dragging: {self._file_path.name}")

    def _prev_page(self):
        """Go to previous page."""
        if self._current_page > 0:
            self._current_page -= 1
            self._render_page()

    def _next_page(self):
        """Go to next page."""
        if self._doc and self._current_page < len(self._doc) - 1:
            self._current_page += 1
            self._render_page()

    def load_file(self, path: Path) -> bool:
        """Load a PDF file for preview."""
        try:
            if self._doc:
                self._doc.close()

            self._doc = fitz.open(path)
            self._file_path = path
            self._current_page = 0

            self.preview.set_file_path(path)
            self._render_page()
            self._update_nav_buttons()
            self.save_btn.setEnabled(True)

            return True
        except Exception as e:
            self._log(f"Error loading output: {e}")
            return False

    def _render_page(self):
        """Render the current page."""
        if not self._doc:
            return

        page = self._doc[self._current_page]

        # Calculate zoom
        preview_size = self.preview.size()
        page_rect = page.rect
        zoom_x = (preview_size.width() - 20) / page_rect.width
        zoom_y = (preview_size.height() - 20) / page_rect.height
        zoom = min(zoom_x, zoom_y, 2.0)

        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        self.preview.setPixmap(pixmap)

        self.page_label.setText(f"Page {self._current_page + 1}/{len(self._doc)}")
        self._update_nav_buttons()

    def _update_nav_buttons(self):
        """Update navigation button states."""
        if not self._doc:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        self.prev_btn.setEnabled(self._current_page > 0)
        self.next_btn.setEnabled(self._current_page < len(self._doc) - 1)

    def get_file_path(self) -> Optional[Path]:
        """Get the current output file path."""
        return self._file_path

    def set_temp_file(self, path: Path):
        """Set the temporary file path."""
        self._temp_file = path

    def get_temp_file(self) -> Optional[Path]:
        """Get the temporary file path."""
        return self._temp_file

    def close_document(self):
        """Close the current document."""
        if self._doc:
            self._doc.close()
            self._doc = None
