# Developer Guide

This section provides information for developers who want to modify or extend the application.

## Project Structure
```
ocr_app/
    app.py            # Flask application
    __init__.py
    templates/
        index.html    # Main page for answer key and uploads
        result.html   # Displays grading result
static/
docs/
    user-guide.md
    developer-guide.md
    answer-sheet.tex
requirements.txt
```

## Key Functions
- `parse_answers_from_text(text)`
  - Uses a regular expression to extract pairs of question number and answer letter.
  - Only numbers 1-50 and letters A-E are considered.
- `compare_answers(answer_key, student_answers)`
  - Compares the parsed answers against the provided key and returns per-question correctness.

## Running Locally
1. Install dependencies: `pip install -r requirements.txt`.
2. Ensure `tesseract` is installed and available in your PATH.
3. Run the application with `python -m ocr_app.app`.
4. The Flask development server will start on port 5000.

## Extending
- Modify the HTML templates under `ocr_app/templates` for custom styling or layout.
- If your answer sheet format differs, update `parse_answers_from_text` to match your layout.
- To deploy in production, run the app with a WSGI server such as `gunicorn`:
  ```bash
  gunicorn ocr_app.app:create_app
  ```
