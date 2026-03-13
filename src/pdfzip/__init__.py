"""PDFZip - Interleave PDF pages with GUI and CLI support."""

__version__ = "0.1.0"


def main() -> int:
    """Main entry point for the application."""
    from .cli import main as cli_main
    return cli_main()


def main_gui() -> int:
    """GUI-specific entry point."""
    from .gui import run_gui
    return run_gui()
