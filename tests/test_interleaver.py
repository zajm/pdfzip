"""Tests for PDF interleaving logic."""

from pathlib import Path

import pytest

from pdfzip.core import PdfInterleaver, interleave_pdfs


class TestPdfInterleaver:
    """Tests for the PdfInterleaver class."""

    def test_basic_interleave(self, create_pdf, read_pdf_labels, temp_dir):
        """Test basic interleaving of two PDFs with equal page counts."""
        odd_pdf = create_pdf("odd.pdf", ["A1", "A2"])
        even_pdf = create_pdf("even.pdf", ["B1", "B2"])
        output_pdf = temp_dir / "output.pdf"

        interleaver = PdfInterleaver(odd_pdf, even_pdf)
        interleaver.save(output_pdf)

        labels = read_pdf_labels(output_pdf)
        assert labels == ["A1", "B1", "A2", "B2"]

    def test_interleave_odd_has_more_pages(self, create_pdf, read_pdf_labels, temp_dir):
        """Test interleaving when odd PDF has more pages than even PDF."""
        odd_pdf = create_pdf("odd.pdf", ["A1", "A2", "A3"])
        even_pdf = create_pdf("even.pdf", ["B1", "B2"])
        output_pdf = temp_dir / "output.pdf"

        interleaver = PdfInterleaver(odd_pdf, even_pdf)
        interleaver.save(output_pdf)

        labels = read_pdf_labels(output_pdf)
        assert labels == ["A1", "B1", "A2", "B2", "A3"]

    def test_interleave_even_has_more_pages(self, create_pdf, read_pdf_labels, temp_dir):
        """Test interleaving when even PDF has more pages than odd PDF."""
        odd_pdf = create_pdf("odd.pdf", ["A1", "A2"])
        even_pdf = create_pdf("even.pdf", ["B1", "B2", "B3"])
        output_pdf = temp_dir / "output.pdf"

        interleaver = PdfInterleaver(odd_pdf, even_pdf)
        interleaver.save(output_pdf)

        labels = read_pdf_labels(output_pdf)
        assert labels == ["A1", "B1", "A2", "B2", "B3"]

    def test_reverse_odd_pages(self, create_pdf, read_pdf_labels, temp_dir):
        """Test interleaving with reversed odd pages."""
        odd_pdf = create_pdf("odd.pdf", ["A1", "A2", "A3"])
        even_pdf = create_pdf("even.pdf", ["B1", "B2"])
        output_pdf = temp_dir / "output.pdf"

        interleaver = PdfInterleaver(odd_pdf, even_pdf, reverse_odd=True)
        interleaver.save(output_pdf)

        labels = read_pdf_labels(output_pdf)
        assert labels == ["A3", "B1", "A2", "B2", "A1"]

    def test_reverse_even_pages(self, create_pdf, read_pdf_labels, temp_dir):
        """Test interleaving with reversed even pages."""
        odd_pdf = create_pdf("odd.pdf", ["A1", "A2"])
        even_pdf = create_pdf("even.pdf", ["B1", "B2", "B3"])
        output_pdf = temp_dir / "output.pdf"

        interleaver = PdfInterleaver(odd_pdf, even_pdf, reverse_even=True)
        interleaver.save(output_pdf)

        labels = read_pdf_labels(output_pdf)
        assert labels == ["A1", "B3", "A2", "B2", "B1"]

    def test_reverse_both(self, create_pdf, read_pdf_labels, temp_dir):
        """Test interleaving with both inputs reversed."""
        odd_pdf = create_pdf("odd.pdf", ["A1", "A2"])
        even_pdf = create_pdf("even.pdf", ["B1", "B2"])
        output_pdf = temp_dir / "output.pdf"

        interleaver = PdfInterleaver(odd_pdf, even_pdf, reverse_odd=True, reverse_even=True)
        interleaver.save(output_pdf)

        labels = read_pdf_labels(output_pdf)
        assert labels == ["A2", "B2", "A1", "B1"]

    def test_single_page_each(self, create_pdf, read_pdf_labels, temp_dir):
        """Test interleaving with single-page PDFs."""
        odd_pdf = create_pdf("odd.pdf", ["A1"])
        even_pdf = create_pdf("even.pdf", ["B1"])
        output_pdf = temp_dir / "output.pdf"

        interleaver = PdfInterleaver(odd_pdf, even_pdf)
        interleaver.save(output_pdf)

        labels = read_pdf_labels(output_pdf)
        assert labels == ["A1", "B1"]

    def test_progress_callback(self, create_pdf, temp_dir):
        """Test that progress callback is called correctly."""
        odd_pdf = create_pdf("odd.pdf", ["A1", "A2"])
        even_pdf = create_pdf("even.pdf", ["B1", "B2"])
        output_pdf = temp_dir / "output.pdf"

        progress_calls = []

        def progress_callback(current, total):
            progress_calls.append((current, total))

        interleaver = PdfInterleaver(
            odd_pdf, even_pdf, progress_callback=progress_callback
        )
        interleaver.save(output_pdf)

        assert len(progress_calls) == 4
        assert progress_calls == [(1, 4), (2, 4), (3, 4), (4, 4)]


class TestInterleavePdfsFunction:
    """Tests for the interleave_pdfs convenience function."""

    def test_convenience_function(self, create_pdf, read_pdf_labels, temp_dir):
        """Test the interleave_pdfs convenience function."""
        odd_pdf = create_pdf("odd.pdf", ["A1", "A2"])
        even_pdf = create_pdf("even.pdf", ["B1", "B2"])
        output_pdf = temp_dir / "output.pdf"

        interleave_pdfs(odd_pdf, even_pdf, output_pdf)

        labels = read_pdf_labels(output_pdf)
        assert labels == ["A1", "B1", "A2", "B2"]

    def test_convenience_function_with_reverse(self, create_pdf, read_pdf_labels, temp_dir):
        """Test the interleave_pdfs function with reverse options."""
        odd_pdf = create_pdf("odd.pdf", ["A1", "A2"])
        even_pdf = create_pdf("even.pdf", ["B1", "B2"])
        output_pdf = temp_dir / "output.pdf"

        interleave_pdfs(odd_pdf, even_pdf, output_pdf, reverse_odd=True)

        labels = read_pdf_labels(output_pdf)
        assert labels == ["A2", "B1", "A1", "B2"]


class TestEdgeCases:
    """Tests for edge cases."""

    def test_many_pages(self, create_pdf, read_pdf_labels, temp_dir):
        """Test interleaving PDFs with many pages."""
        odd_labels = [f"A{i}" for i in range(1, 51)]  # 50 pages
        even_labels = [f"B{i}" for i in range(1, 51)]  # 50 pages
        odd_pdf = create_pdf("odd.pdf", odd_labels)
        even_pdf = create_pdf("even.pdf", even_labels)
        output_pdf = temp_dir / "output.pdf"

        interleaver = PdfInterleaver(odd_pdf, even_pdf)
        interleaver.save(output_pdf)

        labels = read_pdf_labels(output_pdf)
        assert len(labels) == 100

        # Check interleaving pattern
        for i in range(50):
            assert labels[i * 2] == f"A{i + 1}"
            assert labels[i * 2 + 1] == f"B{i + 1}"

    def test_file_not_found(self, temp_dir):
        """Test handling of non-existent files."""
        odd_pdf = temp_dir / "nonexistent_odd.pdf"
        even_pdf = temp_dir / "nonexistent_even.pdf"
        output_pdf = temp_dir / "output.pdf"

        interleaver = PdfInterleaver(odd_pdf, even_pdf)

        with pytest.raises(Exception):  # pypdf raises FileNotFoundError or similar
            interleaver.save(output_pdf)
