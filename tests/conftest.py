"""Pytest fixtures for pdfzip tests."""

import tempfile
from pathlib import Path

import fitz
import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def create_pdf(temp_dir):
    """Factory fixture to create test PDFs with labeled pages."""
    created_files = []

    def _create_pdf(name: str, page_labels: list[str]) -> Path:
        """Create a test PDF with the given page labels."""
        filepath = temp_dir / name
        doc = fitz.open()

        for label in page_labels:
            page = doc.new_page(width=612, height=792)  # Letter size
            page.insert_text((200, 400), f"Page {label}", fontsize=48, fontname="helv")

        doc.save(filepath)
        doc.close()
        created_files.append(filepath)
        return filepath

    yield _create_pdf

    # Cleanup
    for f in created_files:
        if f.exists():
            f.unlink()


@pytest.fixture
def read_pdf_labels():
    """Factory fixture to read page labels from a PDF."""

    def _read_labels(filepath: Path) -> list[str]:
        """Extract the page labels from a test PDF."""
        doc = fitz.open(filepath)
        labels = []
        for page in doc:
            text = page.get_text().strip()
            # Extract just the label part (e.g., "Page A1" -> "A1")
            if text.startswith("Page "):
                labels.append(text[5:])
            else:
                labels.append(text)
        doc.close()
        return labels

    return _read_labels
