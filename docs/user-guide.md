# User Guide

This application allows you to check multiple choice answer sheets using OCR from your camera.

## Steps

1. Install the dependencies listed in `requirements.txt`. Make sure `tesseract` is installed on your system so `pytesseract` can invoke it.
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
5. In the *Answer Key* box, paste the correct answers as a sequence of 50 letters (only A-E are allowed). Example:
   ```
   ABCDEABCDEABCDEABCDEABCDEABCDEABCDEABCDEABCDEABCDE
   ```
   Press **Save Answer Key**.
6. Below the form, use the *Upload Answer Sheet* section to take a photo of the student's sheet. The input field will open your device camera if available.
7. After uploading, the application will display a table showing which questions are correct and the total score.

## Notes
- The OCR is basic and works best with clean, high-contrast images where each answer is written as `number letter` (e.g. `1 A`).
- Only the first 50 detected answers are used.
