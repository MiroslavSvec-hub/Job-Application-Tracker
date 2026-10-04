"""
Job Application Tracker — local Flask app.
Stores all application data in applications.csv (created automatically
in the same folder as this script on first save).

Run with:
    python app.py

Then open http://127.0.0.1:5000 in your browser.
"""

import csv
import os
import uuid
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "applications.csv")

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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/applications", methods=["GET"])
def get_applications():
    apps = read_all()
    # Most recently applied first
    apps.sort(key=lambda a: a.get("dateApplied", ""), reverse=True)
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
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
