#!/usr/bin/env python3
"""Entry point script for PyInstaller builds.

This script uses absolute imports to avoid the relative import issues
that occur when PyInstaller runs __main__.py directly.
"""

import sys
from pdfzip import main

if __name__ == "__main__":
    sys.exit(main())
