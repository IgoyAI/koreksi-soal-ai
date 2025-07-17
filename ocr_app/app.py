import os
import re
import uuid
from typing import Dict, List, Any

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    session,
)
from werkzeug.utils import secure_filename

import pytesseract
from PIL import Image

from . import data

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def login_required(func):
    """Simple login required decorator using session."""
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


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

    store = data.load_data()

    project_name: str | None = None
    exam_name: str | None = None
    answer_key: List[str] = []
    num_questions: int = 50

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            if username == "admin" and password == "admin123":
                session["logged_in"] = True
                flash("Logged in successfully", "success")
                return redirect(url_for("dashboard"))
            flash("Invalid credentials", "danger")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Logged out", "success")
        return redirect(url_for("login"))

    @app.route("/", methods=["GET", "POST"])
    @login_required
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
                    # create project if not exists
                    if not any(p["name"] == name for p in store["projects"]):
                        store["projects"].append({"name": name, "exams": []})
                        data.save_data(store)
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
                # ensure exam entry exists
                for proj in store["projects"]:
                    if proj["name"] == project_name:
                        proj["exams"].append(
                            {
                                "name": exam_name,
                                "num_questions": num_questions,
                                "answer_key": [],
                                "results": [],
                            }
                        )
                        data.save_data(store)
                        break
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
            # save answer key into store
            for proj in store["projects"]:
                if proj["name"] == project_name:
                    for exam in proj["exams"]:
                        if exam["name"] == exam_name:
                            exam["answer_key"] = answer_key
                            exam["num_questions"] = num_questions
                            data.save_data(store)
                            break
                    break
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
    @login_required
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

            # persist results
            for proj in store["projects"]:
                if proj["name"] == project_name:
                    for exam in proj["exams"]:
                        if exam["name"] == exam_name:
                            exam.setdefault("results", []).append(
                                {
                                    "filename": filename,
                                    "score": score,
                                }
                            )
                            data.save_data(store)
                            break
                    break

        return render_template(
            "result.html", results_list=results_list, total=len(answer_key)
        )

    @app.route("/download")
    @login_required
    def download_sheet():
        nonlocal exam_name, num_questions, answer_key
        if not exam_name:
            flash("Exam details not set.", "danger")
            return redirect(url_for("index"))
        try:
            n = int(request.args.get("num_students", "1"))
        except ValueError:
            n = 1
        n = max(1, min(n, 500))
        codes = [uuid.uuid4().hex[:8] for _ in range(n)]
        tex = render_template(
            "answer_sheet.tex",
            exam_name=exam_name,
            num_questions=num_questions,
            answer_key=answer_key,
            codes=codes,
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

    @app.route("/dashboard")
    @login_required
    def dashboard():
        data_store = data.load_data()
        return render_template("dashboard.html", projects=data_store.get("projects", []))

    @app.route("/project/new", methods=["POST"])
    @login_required
    def create_project():
        name = request.form.get("name", "").strip()
        if not name:
            flash("Project name required", "danger")
            return redirect(url_for("dashboard"))
        data_store = data.load_data()
        if any(p.get("name") == name for p in data_store.get("projects", [])):
            flash("Project already exists", "danger")
            return redirect(url_for("dashboard"))
        data_store.setdefault("projects", []).append({"name": name, "exams": []})
        data.save_data(data_store)
        flash("Project created", "success")
        return redirect(url_for("dashboard"))

    @app.route("/project/<int:pid>/exam/new", methods=["POST"])
    @login_required
    def create_exam(pid: int):
        data_store = data.load_data()
        if pid < 0 or pid >= len(data_store.get("projects", [])):
            flash("Project not found", "danger")
            return redirect(url_for("dashboard"))
        project = data_store["projects"][pid]
        name = request.form.get("name", "").strip()
        try:
            num = int(request.form.get("num_questions", "0"))
        except ValueError:
            num = 0
        if not name or num <= 0:
            flash("Invalid exam data", "danger")
            return redirect(url_for("dashboard"))
        project.setdefault("exams", []).append({"name": name, "num_questions": num, "answer_key": [], "results": []})
        data.save_data(data_store)
        flash("Exam created", "success")
        return redirect(url_for("dashboard"))

    @app.route("/project/<int:pid>")
    @login_required
    def view_project(pid: int):
        data_store = data.load_data()
        if pid < 0 or pid >= len(data_store.get("projects", [])):
            flash("Project not found", "danger")
            return redirect(url_for("dashboard"))
        project = data_store["projects"][pid]
        return render_template("project_view.html", project=project, pid=pid)

    @app.route("/project/<int:pid>/edit", methods=["GET", "POST"])
    @login_required
    def edit_project(pid: int):
        data_store = data.load_data()
        if pid < 0 or pid >= len(data_store.get("projects", [])):
            flash("Project not found", "danger")
            return redirect(url_for("dashboard"))
        project = data_store["projects"][pid]
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            if not name:
                flash("Name required", "danger")
            else:
                project["name"] = name
                data.save_data(data_store)
                flash("Project updated", "success")
                return redirect(url_for("view_project", pid=pid))
        return render_template("project_edit.html", project=project, pid=pid)

    @app.route("/project/<int:pid>/delete", methods=["POST"])
    @login_required
    def delete_project(pid: int):
        data_store = data.load_data()
        if 0 <= pid < len(data_store.get("projects", [])):
            data_store["projects"].pop(pid)
            data.save_data(data_store)
            flash("Project deleted", "success")
        else:
            flash("Project not found", "danger")
        return redirect(url_for("dashboard"))

    @app.route("/project/<int:pid>/exam/<int:eid>")
    @login_required
    def view_exam(pid: int, eid: int):
        data_store = data.load_data()
        if pid < 0 or pid >= len(data_store.get("projects", [])):
            flash("Project not found", "danger")
            return redirect(url_for("dashboard"))
        project = data_store["projects"][pid]
        if eid < 0 or eid >= len(project.get("exams", [])):
            flash("Exam not found", "danger")
            return redirect(url_for("view_project", pid=pid))
        exam = project["exams"][eid]
        return render_template("exam_view.html", exam=exam, pid=pid)

    @app.route("/project/<int:pid>/exam/<int:eid>/ocr")
    @login_required
    def ocr_exam(pid: int, eid: int):
        """Load an existing exam into the main OCR workflow."""
        nonlocal project_name, exam_name, answer_key, num_questions
        data_store = data.load_data()
        if pid < 0 or pid >= len(data_store.get("projects", [])):
            flash("Project not found", "danger")
            return redirect(url_for("dashboard"))
        project = data_store["projects"][pid]
        if eid < 0 or eid >= len(project.get("exams", [])):
            flash("Exam not found", "danger")
            return redirect(url_for("view_project", pid=pid))
        exam = project["exams"][eid]

        project_name = project["name"]
        exam_name = exam["name"]
        answer_key = exam.get("answer_key", [])
        num_questions = exam.get("num_questions", 50)

        flash("Loaded exam into OCR checker", "success")
        return redirect(url_for("index"))

    @app.route("/project/<int:pid>/exam/<int:eid>/edit", methods=["GET", "POST"])
    @login_required
    def edit_exam(pid: int, eid: int):
        data_store = data.load_data()
        if pid < 0 or pid >= len(data_store.get("projects", [])):
            flash("Project not found", "danger")
            return redirect(url_for("dashboard"))
        project = data_store["projects"][pid]
        if eid < 0 or eid >= len(project.get("exams", [])):
            flash("Exam not found", "danger")
            return redirect(url_for("view_project", pid=pid))
        exam = project["exams"][eid]
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            try:
                n = int(request.form.get("num_questions", "0"))
            except ValueError:
                n = 0
            if not name or n <= 0:
                flash("Invalid input", "danger")
            else:
                exam["name"] = name
                exam["num_questions"] = n
                data.save_data(data_store)
                flash("Exam updated", "success")
                return redirect(url_for("view_project", pid=pid))
        return render_template("exam_edit.html", exam=exam, pid=pid)

    @app.route("/project/<int:pid>/exam/<int:eid>/delete", methods=["POST"])
    @login_required
    def delete_exam(pid: int, eid: int):
        data_store = data.load_data()
        if pid < 0 or pid >= len(data_store.get("projects", [])):
            flash("Project not found", "danger")
            return redirect(url_for("dashboard"))
        project = data_store["projects"][pid]
        if 0 <= eid < len(project.get("exams", [])):
            project["exams"].pop(eid)
            data.save_data(data_store)
            flash("Exam deleted", "success")
        else:
            flash("Exam not found", "danger")
        return redirect(url_for("view_project", pid=pid))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
