"""Main window for PDFZip application."""

import tempfile
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QProgressBar, QSplitter,
    QMessageBox
)

from .pdf_preview import InputPdfWidget, OutputPdfWidget
from .log_panel import LogPanel
from ..core import PdfInterleaver


class InterleaveWorker(QObject):
    """Worker for running interleave in background thread."""

    progress = Signal(int, int)  # current, total
    finished = Signal(str)  # output path
    error = Signal(str)  # error message

    def __init__(self, odd_path: Path, even_path: Path, output_path: Path,
                 reverse_odd: bool, reverse_even: bool):
        super().__init__()
        self.odd_path = odd_path
        self.even_path = even_path
        self.output_path = output_path
        self.reverse_odd = reverse_odd
        self.reverse_even = reverse_even

    def run(self):
        """Perform the interleave operation."""
        try:
            interleaver = PdfInterleaver(
                odd_path=self.odd_path,
                even_path=self.even_path,
                reverse_odd=self.reverse_odd,
                reverse_even=self.reverse_even,
                progress_callback=lambda c, t: self.progress.emit(c, t),
            )
            interleaver.save(self.output_path)
            self.finished.emit(str(self.output_path))
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self._worker_thread: Optional[QThread] = None
        self._last_directory: Optional[Path] = None
        self._temp_output: Optional[Path] = None

        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        self.setWindowTitle("PDFZip - PDF Page Interleaver")
        self.setMinimumSize(900, 700)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top section: PDF panels
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        # Odd pages input
        self.odd_input = InputPdfWidget("ODD PAGES (A)", log_callback=self._log)
        self.odd_input.file_changed.connect(self._on_input_changed)
        self.odd_input.settings_changed.connect(self._on_settings_changed)
        top_layout.addWidget(self.odd_input, 1)

        # Swap button (vertical layout for centering)
        swap_layout = QVBoxLayout()
        swap_layout.addStretch()
        self.swap_btn = QPushButton("\u21c4")  # ⇄
        self.swap_btn.setToolTip("Swap input files")
        self.swap_btn.setFixedSize(40, 40)
        self.swap_btn.setStyleSheet("font-size: 18px; border-radius: 20px;")
        self.swap_btn.clicked.connect(self._swap_inputs)
        swap_layout.addWidget(self.swap_btn)
        swap_layout.addStretch()
        top_layout.addLayout(swap_layout)

        # Even pages input
        self.even_input = InputPdfWidget("EVEN PAGES (B)", log_callback=self._log)
        self.even_input.file_changed.connect(self._on_input_changed)
        self.even_input.settings_changed.connect(self._on_settings_changed)
        top_layout.addWidget(self.even_input, 1)

        # Output preview
        self.output_preview = OutputPdfWidget(log_callback=self._log)
        self.output_preview.interleave_requested.connect(self._do_interleave)
        self.output_preview.save_requested.connect(self._save_output)
        top_layout.addWidget(self.output_preview, 1)

        splitter.addWidget(top_widget)

        # Bottom section: Log panel
        self.log_panel = LogPanel()
        splitter.addWidget(self.log_panel)

        # Set splitter sizes (80% top, 20% bottom)
        splitter.setSizes([560, 140])

        main_layout.addWidget(splitter)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

    def _setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Ctrl+1: Open odd pages file
        QShortcut(QKeySequence("Ctrl+1"), self, self.odd_input._on_open_clicked)

        # Ctrl+2: Open even pages file
        QShortcut(QKeySequence("Ctrl+2"), self, self.even_input._on_open_clicked)

        # Ctrl+I: Interleave
        QShortcut(QKeySequence("Ctrl+I"), self, self._do_interleave)

        # Ctrl+S: Save
        QShortcut(QKeySequence("Ctrl+S"), self, self._save_output)

        # Left/Right arrows: Navigate output pages
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.output_preview._prev_page)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.output_preview._next_page)

    def _log(self, message: str, level: str = "INFO"):
        """Log a message to the log panel."""
        if level == "ERROR":
            self.log_panel.error(message)
        elif level == "WARN":
            self.log_panel.warn(message)
        elif level == "SUCCESS":
            self.log_panel.success(message)
        else:
            self.log_panel.info(message)

    def _on_input_changed(self, path: str):
        """Handle input file change."""
        # Update shared last directory
        file_path = Path(path)
        self._last_directory = file_path.parent

        # Share directory between input widgets
        self.odd_input.set_last_directory(self._last_directory)
        self.even_input.set_last_directory(self._last_directory)

    def _on_settings_changed(self):
        """Handle settings change (reverse checkbox)."""
        self._log("Settings changed")

    def _swap_inputs(self):
        """Swap the odd and even input files."""
        odd_path = self.odd_input.get_file_path()
        even_path = self.even_input.get_file_path()
        odd_reversed = self.odd_input.is_reversed()
        even_reversed = self.even_input.is_reversed()

        # Clear and reload swapped
        if even_path:
            self.odd_input.load_file(even_path)
        if odd_path:
            self.even_input.load_file(odd_path)

        # Swap reverse settings
        self.odd_input.reverse_check.setChecked(even_reversed)
        self.even_input.reverse_check.setChecked(odd_reversed)

        self._log("Swapped input files")

    def _do_interleave(self):
        """Perform the interleave operation."""
        odd_path = self.odd_input.get_file_path()
        even_path = self.even_input.get_file_path()

        if not odd_path:
            self._log("Please select an odd pages PDF file", "WARN")
            return
        if not even_path:
            self._log("Please select an even pages PDF file", "WARN")
            return

        # Create temp file for output
        temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix="pdfzip_")
        self._temp_output = Path(temp_path)

        self._log(f"Interleaving: {odd_path.name} + {even_path.name}")
        self._log(f"  Odd pages: {self.odd_input.get_page_count()} pages" +
                  (" (reversed)" if self.odd_input.is_reversed() else ""))
        self._log(f"  Even pages: {self.even_input.get_page_count()} pages" +
                  (" (reversed)" if self.even_input.is_reversed() else ""))

        # Disable UI during operation
        self.output_preview.interleave_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Create worker thread
        self._worker_thread = QThread()
        self._worker = InterleaveWorker(
            odd_path=odd_path,
            even_path=even_path,
            output_path=self._temp_output,
            reverse_odd=self.odd_input.is_reversed(),
            reverse_even=self.even_input.is_reversed(),
        )
        self._worker.moveToThread(self._worker_thread)

        # Connect signals
        self._worker_thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_interleave_finished)
        self._worker.error.connect(self._on_interleave_error)

        # Start operation
        self._worker_thread.start()

    def _on_progress(self, current: int, total: int):
        """Handle progress update."""
        percent = int((current / total) * 100)
        self.progress_bar.setValue(percent)
        self.progress_bar.setFormat(f"{current}/{total} pages ({percent}%)")

    def _on_interleave_finished(self, output_path: str):
        """Handle successful interleave completion."""
        self._cleanup_worker()

        self.progress_bar.setVisible(False)
        self.output_preview.interleave_btn.setEnabled(True)

        # Load the output preview
        path = Path(output_path)
        if self.output_preview.load_file(path):
            self.output_preview.set_temp_file(path)
            total_pages = self.odd_input.get_page_count() + self.even_input.get_page_count()
            self._log(f"Created interleaved PDF: {total_pages} pages", "SUCCESS")

    def _on_interleave_error(self, error: str):
        """Handle interleave error."""
        self._cleanup_worker()

        self.progress_bar.setVisible(False)
        self.output_preview.interleave_btn.setEnabled(True)

        self._log(f"Interleave failed: {error}", "ERROR")
        QMessageBox.critical(self, "Error", f"Failed to interleave PDFs:\n{error}")

    def _cleanup_worker(self):
        """Clean up worker thread."""
        if self._worker_thread:
            self._worker_thread.quit()
            self._worker_thread.wait()
            self._worker_thread = None
            self._worker = None

    def _save_output(self):
        """Save the output file."""
        temp_file = self.output_preview.get_temp_file()
        if not temp_file or not temp_file.exists():
            self._log("No output to save", "WARN")
            return

        # Determine default filename
        odd_name = self.odd_input.get_file_path()
        even_name = self.even_input.get_file_path()

        if odd_name and even_name:
            default_name = f"{odd_name.stem}_{even_name.stem}_interleaved.pdf"
        else:
            default_name = "interleaved.pdf"

        start_dir = str(self._last_directory / default_name) if self._last_directory else default_name

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Interleaved PDF",
            start_dir,
            "PDF Files (*.pdf);;All Files (*)"
        )

        if save_path:
            save_path = Path(save_path)
            if not save_path.suffix.lower() == '.pdf':
                save_path = save_path.with_suffix('.pdf')

            try:
                # Copy temp file to destination
                import shutil
                shutil.copy2(temp_file, save_path)
                self._last_directory = save_path.parent
                self._log(f"Saved: {save_path}", "SUCCESS")

                # Update the output preview to point to saved file
                self.output_preview.load_file(save_path)

            except Exception as e:
                self._log(f"Save failed: {e}", "ERROR")
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def closeEvent(self, event):
        """Handle window close."""
        # Clean up documents
        self.odd_input.close_document()
        self.even_input.close_document()
        self.output_preview.close_document()

        # Clean up temp file
        if self._temp_output and self._temp_output.exists():
            try:
                self._temp_output.unlink()
            except Exception:
                pass

        # Clean up worker
        self._cleanup_worker()

        event.accept()
