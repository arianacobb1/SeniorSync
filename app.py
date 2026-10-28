"""A small working skeleton for the SeniorSync senior-design proposal."""

from datetime import date, datetime
from pathlib import Path
import os
import sqlite3

from flask import Flask, jsonify, render_template, request


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config.from_mapping(
        DATABASE=os.environ.get(
            "SENIORSYNC_DB", str(Path(app.instance_path) / "seniorsync.sqlite3")
        )
    )
    if test_config:
        app.config.update(test_config)

    def database():
        conn = sqlite3.connect(app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    with database() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY,
                course_id INTEGER NOT NULL REFERENCES courses(id),
                title TEXT NOT NULL,
                due_date TEXT NOT NULL,
                completed_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS assignments_due_date_idx
                ON assignments(due_date);
            """
        )

    def decorate(row):
        item = dict(row)
        days_left = (date.fromisoformat(item["due_date"]) - date.today()).days
        item["days_left"] = days_left
        item["urgency"] = (
            "completed" if item["completed_at"] else
            "overdue" if days_left < 0 else
            "due-soon" if days_left <= 3 else "upcoming"
        )
        return item

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/api/assignments")
    def list_assignments():
        with database() as conn:
            rows = conn.execute(
                """SELECT a.id, a.title, a.due_date, a.completed_at,
                          c.name AS course
                   FROM assignments AS a JOIN courses AS c ON c.id = a.course_id
                   ORDER BY (a.completed_at IS NOT NULL), a.due_date, a.id"""
            ).fetchall()
        return jsonify([decorate(row) for row in rows])

    @app.post("/api/assignments")
    def add_assignment():
        data = request.get_json(silent=True) or {}
        title = str(data.get("title", "")).strip()
        course = str(data.get("course", "")).strip()
        due_text = str(data.get("due_date", "")).strip()
        if not title or not course or len(title) > 120 or len(course) > 80:
            return jsonify(error="Enter a title (1-120 characters) and course (1-80 characters)."), 400
        try:
            date.fromisoformat(due_text)
        except ValueError:
            return jsonify(error="Enter a valid due date (YYYY-MM-DD)."), 400
        with database() as conn:
            conn.execute("INSERT OR IGNORE INTO courses(name) VALUES (?)", (course,))
            course_id = conn.execute("SELECT id FROM courses WHERE name = ?", (course,)).fetchone()[0]
            cursor = conn.execute(
                "INSERT INTO assignments(course_id, title, due_date) VALUES (?, ?, ?)",
                (course_id, title, due_text),
            )
            new_id = cursor.lastrowid
        return jsonify(id=new_id), 201

    @app.patch("/api/assignments/<int:assignment_id>")
    def complete_assignment(assignment_id):
        data = request.get_json(silent=True) or {}
        if not isinstance(data.get("completed"), bool):
            return jsonify(error="completed must be true or false."), 400
        completed_at = datetime.now().isoformat(timespec="seconds") if data["completed"] else None
        with database() as conn:
            cursor = conn.execute(
                "UPDATE assignments SET completed_at = ? WHERE id = ?",
                (completed_at, assignment_id),
            )
        if cursor.rowcount == 0:
            return jsonify(error="Assignment not found."), 404
        return jsonify(id=assignment_id, completed=data["completed"])

    @app.get("/api/summary")
    def summary():
        with database() as conn:
            rows = conn.execute("SELECT due_date, completed_at FROM assignments").fetchall()
        decorated = [decorate(row) for row in rows]
        return jsonify(
            total=len(decorated),
            completed=sum(item["urgency"] == "completed" for item in decorated),
            due_soon=sum(item["urgency"] == "due-soon" for item in decorated),
            overdue=sum(item["urgency"] == "overdue" for item in decorated),
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
