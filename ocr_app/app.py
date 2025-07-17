import os
import re
from typing import Dict, List

from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename

import pytesseract
from PIL import Image

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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


def compare_answers(
    answer_key: List[str], student_answers: Dict[int, str]
) -> Dict[int, bool]:
    results: Dict[int, bool] = {}
    for i in range(1, len(answer_key) + 1):
        key = answer_key[i - 1].upper()
        student = student_answers.get(i, "")
        results[i] = key == student
    return results


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "change-this-secret"
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    project_name: str | None = None
    exam_name: str | None = None
    answer_key: List[str] = []
    num_questions: int = 50

    @app.route("/", methods=["GET", "POST"])
    def index():
        nonlocal project_name, exam_name, answer_key, num_questions
        if request.method == "POST":
            # Step 1: project creation
            if "project_name" in request.form:
                name = request.form.get("project_name", "").strip()
                if not name:
                    flash("Project name is required.", "danger")
                else:
                    project_name = name
                    flash("Project created.", "success")
                return redirect(url_for("index"))

            # Step 2: exam details
            if "exam_name" in request.form:
                name = request.form.get("exam_name", "").strip()
                try:
                    n = int(request.form.get("num_questions", "50"))
                    if n <= 0 or n > 100:
                        raise ValueError
                except ValueError:
                    flash("Invalid number of questions.", "danger")
                    return redirect(url_for("index"))
                if not name:
                    flash("Exam name is required.", "danger")
                    return redirect(url_for("index"))
                exam_name = name
                num_questions = n
                answer_key = []
                flash("Exam details saved.", "success")
                return redirect(url_for("index"))

            # Step 3: answer key
            answers: List[str] = []
            for i in range(1, num_questions + 1):
                val = request.form.get(f"q{i}")
                if val not in list("ABCDEabcde"):
                    flash("Please select answers for all questions.", "danger")
                    return redirect(url_for("index"))
                answers.append(val.upper())
            answer_key = answers
            flash("Answer key saved. Upload answer sheet image to check.", "success")
            return redirect(url_for("index"))

        return render_template(
            "index.html",
            project_name=project_name,
            exam_name=exam_name,
            answer_key=answer_key,
            num_questions=num_questions,
        )

    @app.route("/upload", methods=["POST"])
    def upload():
        nonlocal project_name, exam_name, answer_key, num_questions
        if not exam_name or not answer_key:
            flash("Please submit exam details and answer key first.", "danger")
            return redirect(url_for("index"))
        files = request.files.getlist("files")
        valid_files = [f for f in files if f and allowed_file(f.filename)]
        if not valid_files:
            flash("No valid files uploaded.", "danger")
            return redirect(url_for("index"))

        results_list = []
        for file in valid_files:

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            text = pytesseract.image_to_string(Image.open(filepath))
            student_answers = parse_answers_from_text(text, num_questions)
            results = compare_answers(answer_key, student_answers)
            score = sum(results.values())
            results_list.append(
                {"filename": filename, "results": results, "score": score}
            )

        return render_template(
            "result.html", results_list=results_list, total=len(answer_key)
        )

    @app.route("/download")
    def download_sheet():
        nonlocal exam_name, num_questions
        if not exam_name:
            flash("Exam details not set.", "danger")
            return redirect(url_for("index"))
        tex = render_template(
            "answer_sheet.tex", exam_name=exam_name, num_questions=num_questions
        )
        tmpdir = os.path.join(app.root_path, "tmp")
        os.makedirs(tmpdir, exist_ok=True)
        tex_path = os.path.join(tmpdir, "sheet.tex")
        pdf_path = os.path.join(tmpdir, "sheet.pdf")
        with open(tex_path, "w") as f:
            f.write(tex)
        os.system(f"pdflatex -output-directory {tmpdir} {tex_path} >/dev/null 2>&1")
        return send_file(
            pdf_path, as_attachment=True, download_name=f"{exam_name}_answer_sheet.pdf"
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
