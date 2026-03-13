"""Core PDF interleaving logic using pypdf."""

from pathlib import Path
from typing import Callable, Optional

from pypdf import PdfReader, PdfWriter


class PdfInterleaver:
    """Interleaves pages from two PDF files."""

    def __init__(
        self,
        odd_path: Path,
        even_path: Path,
        reverse_odd: bool = False,
        reverse_even: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ):
        """
        Initialize the interleaver.

        Args:
            odd_path: Path to PDF with odd pages (1st, 3rd, 5th, ...)
            even_path: Path to PDF with even pages (2nd, 4th, 6th, ...)
            reverse_odd: If True, reverse the page order of odd PDF
            reverse_even: If True, reverse the page order of even PDF
            progress_callback: Optional callback(current, total) for progress updates
        """
        self.odd_path = Path(odd_path)
        self.even_path = Path(even_path)
        self.reverse_odd = reverse_odd
        self.reverse_even = reverse_even
        self.progress_callback = progress_callback

    def interleave(self) -> PdfWriter:
        """
        Perform the interleaving operation.

        Returns:
            PdfWriter containing the interleaved pages
        """
        odd_reader = PdfReader(self.odd_path)
        even_reader = PdfReader(self.even_path)

        odd_pages = list(range(len(odd_reader.pages)))
        even_pages = list(range(len(even_reader.pages)))

        if self.reverse_odd:
            odd_pages.reverse()
        if self.reverse_even:
            even_pages.reverse()

        writer = PdfWriter()
        total_pages = len(odd_pages) + len(even_pages)
        current_page = 0

        # Interleave pages: odd[0], even[0], odd[1], even[1], ...
        max_len = max(len(odd_pages), len(even_pages))

        for i in range(max_len):
            # Add odd page if available
            if i < len(odd_pages):
                writer.add_page(odd_reader.pages[odd_pages[i]])
                current_page += 1
                if self.progress_callback:
                    self.progress_callback(current_page, total_pages)

            # Add even page if available
            if i < len(even_pages):
                writer.add_page(even_reader.pages[even_pages[i]])
                current_page += 1
                if self.progress_callback:
                    self.progress_callback(current_page, total_pages)

        return writer

    def save(self, output_path: Path) -> None:
        """
        Interleave and save to file.

        Args:
            output_path: Path to save the output PDF
        """
        writer = self.interleave()
        with open(output_path, "wb") as f:
            writer.write(f)


def interleave_pdfs(
    odd_path: Path,
    even_path: Path,
    output_path: Path,
    reverse_odd: bool = False,
    reverse_even: bool = False,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> None:
    """
    Convenience function to interleave two PDFs and save the result.

    Args:
        odd_path: Path to PDF with odd pages
        even_path: Path to PDF with even pages
        output_path: Path to save the output PDF
        reverse_odd: If True, reverse the page order of odd PDF
        reverse_even: If True, reverse the page order of even PDF
        progress_callback: Optional callback(current, total) for progress updates
    """
    interleaver = PdfInterleaver(
        odd_path=odd_path,
        even_path=even_path,
        reverse_odd=reverse_odd,
        reverse_even=reverse_even,
        progress_callback=progress_callback,
    )
    interleaver.save(output_path)
