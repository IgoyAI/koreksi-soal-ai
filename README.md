# OCR Multiple Choice Checker

This project provides a simple web application for correcting multiple choice tests using OCR and your device's camera. It supports up to **50 questions** with answer options **A** through **E**.

![screenshot](docs/screenshot.png)

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Ensure `tesseract` is installed on your system and accessible in your PATH.
2. Run the application:
   ```bash
   python -m ocr_app.app
   ```
3. Open your browser and navigate to [http://localhost:5000](http://localhost:5000).

For detailed instructions on using the application, see [docs/user-guide.md](docs/user-guide.md).
For development notes, see [docs/developer-guide.md](docs/developer-guide.md).
