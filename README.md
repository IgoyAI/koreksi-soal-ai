# OCR Multiple Choice Checker
This project provides a simple web application for correcting multiple choice tests using OCR and your device's camera. The number of questions can be configured and each question has answer options **A** through **E**.

![screenshot](docs/screenshot.png)

Printable answer sheets can be generated from the LaTeX template in `docs/answer-sheet.tex`.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Ensure `tesseract` is installed on your system and accessible in your PATH.
   To generate printable answer sheets you also need `pdflatex` and the LaTeX
   `barcode` package available. Install the package with `tlmgr install barcode`
   (running `tlmgr update --self` first if required) or
   `apt-get install texlive-barcodes` depending on your TeX setup.
2. Run the application:
   ```bash
   python -m ocr_app.app
   ```
3. Open your browser and navigate to [http://localhost:5000](http://localhost:5000).

For detailed instructions on using the application, see [docs/user-guide.md](docs/user-guide.md).
For development notes, see [docs/developer-guide.md](docs/developer-guide.md).
