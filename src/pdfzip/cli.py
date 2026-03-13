"""Command-line interface for pdfzip."""

import argparse
import sys
from pathlib import Path

from .core import interleave_pdfs


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="pdf-zip",
        description="Interleave pages from two PDF files into one.",
        epilog="Example: pdf-zip -a odd_pages.pdf -b even_pages.pdf -o combined.pdf",
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch graphical interface (default if no arguments provided)",
    )

    parser.add_argument(
        "-a", "--odd",
        type=Path,
        metavar="FILE",
        help="PDF file containing odd pages (1st, 3rd, 5th, ...)",
    )

    parser.add_argument(
        "-b", "--even",
        type=Path,
        metavar="FILE",
        help="PDF file containing even pages (2nd, 4th, 6th, ...)",
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        metavar="FILE",
        help="Output PDF file path",
    )

    parser.add_argument(
        "--reverse-a",
        action="store_true",
        help="Reverse page order of the odd-pages file",
    )

    parser.add_argument(
        "--reverse-b",
        action="store_true",
        help="Reverse page order of the even-pages file",
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress output except errors",
    )

    return parser


def validate_args(args: argparse.Namespace) -> bool:
    """Validate CLI arguments for headless mode."""
    if args.gui:
        return True

    # If any file argument is provided, all must be provided
    file_args = [args.odd, args.even, args.output]
    if any(file_args):
        if not all(file_args):
            print("Error: When using CLI mode, -a, -b, and -o are all required.", file=sys.stderr)
            return False

        # Check input files exist
        if not args.odd.exists():
            print(f"Error: File not found: {args.odd}", file=sys.stderr)
            return False
        if not args.even.exists():
            print(f"Error: File not found: {args.even}", file=sys.stderr)
            return False

        # Check output directory exists
        output_dir = args.output.parent
        if output_dir and not output_dir.exists():
            print(f"Error: Output directory does not exist: {output_dir}", file=sys.stderr)
            return False

    return True


def run_cli(args: argparse.Namespace) -> int:
    """Run the CLI interleave operation."""
    if not args.quiet:
        print(f"Interleaving PDFs...")
        print(f"  Odd pages:  {args.odd}")
        print(f"  Even pages: {args.even}")
        if args.reverse_a:
            print("  (Odd pages reversed)")
        if args.reverse_b:
            print("  (Even pages reversed)")

    def progress(current: int, total: int) -> None:
        if not args.quiet:
            percent = (current / total) * 100
            print(f"\r  Progress: {current}/{total} pages ({percent:.0f}%)", end="", flush=True)

    try:
        interleave_pdfs(
            odd_path=args.odd,
            even_path=args.even,
            output_path=args.output,
            reverse_odd=args.reverse_a,
            reverse_even=args.reverse_b,
            progress_callback=progress,
        )

        if not args.quiet:
            print()  # Newline after progress
            print(f"  Output: {args.output}")
            print("Done!")

        return 0

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not validate_args(args):
        return 1

    # Determine mode: GUI or CLI
    has_file_args = args.odd or args.even or args.output

    if args.gui or not has_file_args:
        # Launch GUI
        from .gui import run_gui
        return run_gui()
    else:
        # Run CLI mode
        return run_cli(args)
