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


def parse_answers_from_text(text: str, limit: int) -> Dict[int, str]:
    """Parse OCR text into a mapping of question number to answer letter."""
    pattern = re.compile(r"(\d+)\s*([ABCDEabcde])")
    answers: Dict[int, str] = {}
    for match in pattern.finditer(text):
        num = int(match.group(1))
        ans = match.group(2).upper()
        if 1 <= num <= limit:
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
    num_questions: int = 50

    @app.route('/', methods=['GET', 'POST'])
    def index():
        nonlocal answer_key, num_questions
        if request.method == 'POST':
            if 'num_questions' in request.form:
                try:
                    n = int(request.form.get('num_questions', '50'))
                    if n <= 0 or n > 100:
                        raise ValueError
                    num_questions = n
                    answer_key = []
                    flash(f'Number of questions set to {num_questions}.', 'success')
                except ValueError:
                    flash('Invalid number of questions.', 'danger')
                return redirect(url_for('index'))

            # read answer key from radio buttons
            answers: List[str] = []
            for i in range(1, num_questions + 1):
                val = request.form.get(f'q{i}')
                if val not in list('ABCDEabcde'):
                    flash('Please select answers for all questions.', 'danger')
                    return redirect(url_for('index'))
                answers.append(val.upper())
            answer_key = answers
            flash('Answer key saved. Upload answer sheet image to check.', 'success')
            return redirect(url_for('index'))

        return render_template('index.html', answer_key=answer_key, num_questions=num_questions)

    @app.route('/upload', methods=['POST'])
    def upload():
        nonlocal answer_key, num_questions
        if not answer_key:
            flash('Please submit the answer key first.', 'danger')
            return redirect(url_for('index'))
        files = request.files.getlist('files')
        valid_files = [f for f in files if f and allowed_file(f.filename)]
        if not valid_files:
            flash('No valid files uploaded.', 'danger')
            return redirect(url_for('index'))

        results_list = []
        for file in valid_files:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            text = pytesseract.image_to_string(Image.open(filepath))
            student_answers = parse_answers_from_text(text, num_questions)
            results = compare_answers(answer_key, student_answers)
            score = sum(results.values())
            results_list.append({'filename': filename, 'results': results, 'score': score})

        return render_template('result.html', results_list=results_list, total=len(answer_key))

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
