import os
import re
from typing import Dict, List

from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

import pytesseract
from PIL import Image

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_answers_from_text(text: str) -> Dict[int, str]:
    """Parse OCR text into a mapping of question number to answer letter."""
    pattern = re.compile(r"(\d+)\s*([ABCDEabcde])")
    answers: Dict[int, str] = {}
    for match in pattern.finditer(text):
        num = int(match.group(1))
        ans = match.group(2).upper()
        if 1 <= num <= 50:
            answers[num] = ans
    return answers


def compare_answers(answer_key: List[str], student_answers: Dict[int, str]) -> Dict[int, bool]:
    results: Dict[int, bool] = {}
    for i in range(1, len(answer_key) + 1):
        key = answer_key[i - 1].upper()
        student = student_answers.get(i, '')
        results[i] = (key == student)
    return results


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = 'change-this-secret'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    answer_key: List[str] = []

    @app.route('/', methods=['GET', 'POST'])
    def index():
        nonlocal answer_key
        if request.method == 'POST':
            # read answer key from form
            key_input = request.form.get('answer_key', '')
            key = re.findall(r'[ABCDEabcde]', key_input)
            if len(key) != 50:
                flash('Answer key must contain 50 letters A-E.', 'danger')
                return redirect(url_for('index'))
            answer_key = [k.upper() for k in key]
            flash('Answer key saved. Upload answer sheet image to check.', 'success')
            return redirect(url_for('index'))
        return render_template('index.html', answer_key=answer_key)

    @app.route('/upload', methods=['POST'])
    def upload():
        nonlocal answer_key
        if not answer_key:
            flash('Please submit the answer key first.', 'danger')
            return redirect(url_for('index'))
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('index'))
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('index'))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            text = pytesseract.image_to_string(Image.open(filepath))
            student_answers = parse_answers_from_text(text)
            results = compare_answers(answer_key, student_answers)
            score = sum(results.values())
            return render_template('result.html', results=results, score=score, total=len(answer_key))
        flash('Invalid file type', 'danger')
        return redirect(url_for('index'))

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
