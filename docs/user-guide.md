# User Guide

This application allows you to check multiple choice answer sheets using OCR from your camera.

## Steps

1. Install the dependencies listed in `requirements.txt`. Make sure both `tesseract` and `pdflatex` are installed so OCR and PDF generation work correctly.
2. Compile the provided LaTeX answer sheet if you want a standardized form:
   ```bash
   pdflatex docs/answer-sheet.tex
   ```
   Print the generated `answer-sheet.pdf` for students to fill out.
3. Start the application:
   ```bash
   python -m ocr_app.app
   ```
4. Open your browser to `http://localhost:5000`.
5. Set the desired number of questions and select the correct answer for each using the radio buttons.
   Press **Save Answer Key** when done.
6. Below the form, use the *Upload Answer Sheet* section to capture or select one or more photos of completed sheets.
7. After uploading, the application will display a table for each file showing which questions are correct and the total score.

## Notes
- The OCR is basic and works best with clean, high-contrast images where each answer is written as `number letter` (e.g. `1 A`).

