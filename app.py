"""
Job Application Tracker — local Flask app.
Stores all application data in applications.csv (created automatically
in the same folder as this script on first save). Uploaded documents are
stored in documents/<application id>/.

Run with:
    python app.py

Then open http://127.0.0.1:5000 in your browser.
"""

import csv
import os
import shutil
import uuid
from flask import Flask, jsonify, request, render_template, send_from_directory, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB per upload request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "applications.csv")
DOCS_DIR = os.path.join(BASE_DIR, "documents")

FIELDNAMES = ["id", "company", "role", "dateApplied", "status", "matchQuality", "matchReason", "salary", "link", "notes"]

# Optional field — empty string means "not set"
MATCH_QUALITIES = {"low", "medium", "strong"}


def clean_match_quality(value):
    """Return a valid match quality, or "" if missing/unknown.
    Accepts both the stored key ("strong") and the label ("Strong match")."""
    value = (value or "").strip().lower()
    if value.endswith(" match"):
        value = value[: -len(" match")].strip()
    return value if value in MATCH_QUALITIES else ""


def read_all():
    """Read all applications from the CSV file. Returns a list of dicts."""
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
    for row in rows:
        row["matchQuality"] = clean_match_quality(row.get("matchQuality"))
    return rows


def write_all(applications):
    """Overwrite the CSV file with the given list of application dicts."""
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for app_row in applications:
            # Only keep known fields, in the right order
            writer.writerow({k: app_row.get(k, "") for k in FIELDNAMES})


def app_exists(app_id):
    return any(a["id"] == app_id for a in read_all())


def docs_path(app_id):
    """Folder holding the documents for one application."""
    return os.path.join(DOCS_DIR, secure_filename(app_id))


def list_documents(app_id):
    folder = docs_path(app_id)
    if not os.path.isdir(folder):
        return []
    return sorted(
        name for name in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, name))
    )


def unique_filename(folder, original):
    """Sanitise an uploaded filename and avoid overwriting existing files."""
    stem, ext = os.path.splitext(original)
    # secure_filename drops non-ASCII characters, so a name can end up empty
    base = secure_filename(stem) or "document"
    ext = secure_filename(ext)
    ext = "." + ext if ext else ""
    candidate = base + ext
    n = 1
    while os.path.exists(os.path.join(folder, candidate)):
        candidate = f"{base}_{n}{ext}"
        n += 1
    return candidate


def valid_document(app_id, filename):
    """True if filename is a safe name of an existing document of this application."""
    return (
        filename == secure_filename(filename)
        and os.path.isfile(os.path.join(docs_path(app_id), filename))
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/applications", methods=["GET"])
def get_applications():
    apps = read_all()
    # Most recently applied first
    apps.sort(key=lambda a: a.get("dateApplied", ""), reverse=True)
    for a in apps:
        a["documents"] = list_documents(a["id"])
    return jsonify(apps)


@app.route("/api/applications", methods=["POST"])
def create_application():
    data = request.get_json(force=True)
    company = (data.get("company") or "").strip()
    role = (data.get("role") or "").strip()
    if not company or not role:
        return jsonify({"error": "Company and role are required."}), 400

    new_app = {
        "id": uuid.uuid4().hex[:12],
        "company": company,
        "role": role,
        "dateApplied": data.get("dateApplied", ""),
        "status": data.get("status", "applied"),
        "matchQuality": clean_match_quality(data.get("matchQuality")),
        "matchReason": data.get("matchReason", ""),
        "salary": data.get("salary", ""),
        "link": data.get("link", ""),
        "notes": data.get("notes", ""),
    }

    apps = read_all()
    apps.append(new_app)
    write_all(apps)
    return jsonify(new_app), 201


@app.route("/api/applications/<app_id>", methods=["PUT"])
def update_application(app_id):
    data = request.get_json(force=True)
    company = (data.get("company") or "").strip()
    role = (data.get("role") or "").strip()
    if not company or not role:
        return jsonify({"error": "Company and role are required."}), 400

    apps = read_all()
    found = False
    for a in apps:
        if a["id"] == app_id:
            a["company"] = company
            a["role"] = role
            a["dateApplied"] = data.get("dateApplied", "")
            a["status"] = data.get("status", "applied")
            a["matchQuality"] = clean_match_quality(data.get("matchQuality"))
            a["matchReason"] = data.get("matchReason", "")
            a["salary"] = data.get("salary", "")
            a["link"] = data.get("link", "")
            a["notes"] = data.get("notes", "")
            found = True
            break

    if not found:
        return jsonify({"error": "Application not found."}), 404

    write_all(apps)
    return jsonify({"ok": True})


@app.route("/api/applications/<app_id>", methods=["DELETE"])
def delete_application(app_id):
    apps = read_all()
    remaining = [a for a in apps if a["id"] != app_id]
    if len(remaining) == len(apps):
        return jsonify({"error": "Application not found."}), 404
    write_all(remaining)
    shutil.rmtree(docs_path(app_id), ignore_errors=True)
    return jsonify({"ok": True})


@app.route("/api/applications/<app_id>/documents", methods=["POST"])
def upload_documents(app_id):
    if not app_exists(app_id):
        return jsonify({"error": "Application not found."}), 404
    files = [f for f in request.files.getlist("files") if f and f.filename]
    if not files:
        return jsonify({"error": "No files uploaded."}), 400

    folder = docs_path(app_id)
    os.makedirs(folder, exist_ok=True)
    saved = []
    for f in files:
        name = unique_filename(folder, f.filename)
        f.save(os.path.join(folder, name))
        saved.append(name)
    return jsonify({"saved": saved, "documents": list_documents(app_id)}), 201


@app.route("/api/applications/<app_id>/documents/<filename>", methods=["GET"])
def get_document(app_id, filename):
    if not valid_document(app_id, filename):
        abort(404)
    return send_from_directory(docs_path(app_id), filename)


@app.route("/api/applications/<app_id>/documents/<filename>", methods=["DELETE"])
def delete_document(app_id, filename):
    if not valid_document(app_id, filename):
        return jsonify({"error": "Document not found."}), 404
    os.remove(os.path.join(docs_path(app_id), filename))
    folder = docs_path(app_id)
    if not os.listdir(folder):
        os.rmdir(folder)
    return jsonify({"ok": True, "documents": list_documents(app_id)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
