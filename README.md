# PDFZip

A cross-platform tool to interleave pages from two PDF files, with both GUI and CLI support.

Perfect for combining separately scanned odd and even pages from double-sided documents.

## Features

- **Interleave PDF pages**: Combine two PDFs by alternating pages (A1, B1, A2, B2, ...)
- **Reverse page order**: Handle documents scanned in reverse order
- **Drag & drop**: Drop PDF files directly onto the preview panes
- **Drag out**: Drag the output file from the preview to save it anywhere
- **Preserves quality**: No recompression - original PDF streams are preserved
- **Cross-platform**: Works on Linux and Windows
- **CLI support**: Scriptable command-line interface for automation

## Installation

### From pip

```bash
pip install pdfzip
```

### From source

```bash
git clone https://github.com/yourusername/pdfzip.git
cd pdfzip
pip install -e .
```

## Usage

### GUI Mode

Simply run:

```bash
pdf-zip
```

Or with Python:

```bash
python -m pdfzip
```

### CLI Mode

```bash
pdf-zip -a odd_pages.pdf -b even_pages.pdf -o combined.pdf
```

#### CLI Options

| Option | Description |
|--------|-------------|
| `-a, --odd FILE` | PDF with odd pages (1st, 3rd, 5th, ...) |
| `-b, --even FILE` | PDF with even pages (2nd, 4th, 6th, ...) |
| `-o, --output FILE` | Output PDF file path |
| `--reverse-a` | Reverse page order of odd-pages file |
| `--reverse-b` | Reverse page order of even-pages file |
| `-q, --quiet` | Suppress output except errors |
| `--gui` | Force GUI mode |

### Keyboard Shortcuts (GUI)

| Shortcut | Action |
|----------|--------|
| `Ctrl+1` | Open odd pages file |
| `Ctrl+2` | Open even pages file |
| `Ctrl+I` | Interleave |
| `Ctrl+S` | Save output |
| `←` / `→` | Navigate output pages |

## Building Standalone Executables

### Linux

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name PDFZip src/pdfzip/__main__.py
```

### Windows

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name PDFZip src/pdfzip/__main__.py
```

## Dependencies

- Python 3.9+
- PySide6 (Qt for Python)
- pypdf (PDF manipulation)
- PyMuPDF (PDF rendering)

## License

MIT License
