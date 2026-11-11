"""Add sample assignments to SeniorSync for a live demo.

Run it yourself; it never runs automatically:

    SENIORSYNC_DB=instance/demo.sqlite3 python seed_demo.py   # separate demo database
    python seed_demo.py                                       # your normal database

The script only ADDS assignments. It never deletes or edits existing rows, and
it skips any sample whose title and course are already in the database, so
running it twice does not create duplicates.

It goes through the app's own API (the same routes the web page uses), so the
sample data gets the same validation as anything typed into the form.
"""

from datetime import date, timedelta

from app import create_app

# (title, course, days from today, already completed?)
DEMO_ASSIGNMENTS = [
    ("Lab report: enzyme activity", "BIO 210", -3, False),        # overdue
    ("Reading response 4", "ENG 220", -1, False),                 # overdue
    ("Problem set 7", "MATH 251", 0, False),                      # due soon (today)
    ("Database design checkpoint", "CS 401", 1, False),           # due soon
    ("Spanish video project", "SPAN 201", 3, False),              # due soon
    ("Research paper outline", "HIST 305", 9, False),             # upcoming
    ("Senior Design final presentation", "CS 490", 21, False),    # upcoming
    ("Resume draft for career center", "CS 490", 2, True),        # completed
]


def seed(app):
    """Add any missing demo assignments to app's database. Returns (added, skipped)."""
    client = app.test_client()
    existing = {
        (row["title"], row["course"])
        for row in client.get("/api/assignments").get_json()
    }
    added = skipped = 0
    for title, course, offset, completed in DEMO_ASSIGNMENTS:
        if (title, course) in existing:
            skipped += 1
            continue
        due_date = (date.today() + timedelta(days=offset)).isoformat()
        response = client.post(
            "/api/assignments",
            json={"title": title, "course": course, "due_date": due_date},
        )
        if response.status_code != 201:
            raise RuntimeError(f"Could not add {title!r}: {response.get_json()}")
        if completed:
            new_id = response.get_json()["id"]
            client.patch(f"/api/assignments/{new_id}", json={"completed": True})
        added += 1
    return added, skipped


if __name__ == "__main__":
    demo_app = create_app()
    added, skipped = seed(demo_app)
    print(f"Database: {demo_app.config['DATABASE']}")
    print(f"Added {added} demo assignment(s); skipped {skipped} already present.")
