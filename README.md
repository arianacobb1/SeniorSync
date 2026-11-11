# SeniorSync - Senior Design starter

SeniorSync is a student assignment dashboard built with Flask, SQLite, and vanilla HTML/CSS/JavaScript. This is the **local prototype**, not a finished or publicly deployed app.

## Run on a Mac or PC

First-time setup (run from the `SeniorSync` folder):

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the app on port 5001 (either command works):

```bash
python app.py
# or
flask --app app run --debug --port 5001
```

Open <http://127.0.0.1:5001>. Press `Ctrl+C` in the terminal to stop the server. Next time, you only need to `cd` into the folder, run `source .venv/bin/activate`, and start the app.

**Why port 5001?** On macOS, the AirPlay Receiver already uses port 5000, so `http://localhost:5000` shows a "403 Forbidden" page from AirPlay instead of SeniorSync. Port 5001 avoids that conflict. Use `127.0.0.1` rather than `localhost` in the address bar.

The database is created automatically in `instance/seniorsync.sqlite3` and is ignored by git.

Run tests with `python -m unittest discover -s tests -v`.

## Optional demo data

`seed_demo.py` adds eight sample assignments (overdue, due soon, upcoming and completed) with due dates calculated from today. It **only adds rows**: it never deletes or changes existing assignments, and if you run it twice it skips assignments it already added. It never runs automatically.

**Recommended: use a separate demo database** so your real assignments are untouched. `SENIORSYNC_DB` tells the app which SQLite file to use:

```bash
SENIORSYNC_DB=instance/demo.sqlite3 python seed_demo.py
SENIORSYNC_DB=instance/demo.sqlite3 python app.py
```

Use the same `SENIORSYNC_DB=...` prefix both times so the app opens the database you just filled. To start the demo over, stop the app, delete `instance/demo.sqlite3`, and run both commands again. Your normal database (`instance/seniorsync.sqlite3`) is not affected.

To add the sample assignments to your normal database instead, run `python seed_demo.py` with no prefix.

## Working features

- Create an assignment with its course and due date.
- List assignments ordered by due date and highlight overdue or due-soon items.
- Mark an assignment complete and show summary counts.

## API

| Request | Purpose |
| --- | --- |
| `GET /api/assignments` | Read the list with calculated urgency |
| `POST /api/assignments` | Add an assignment |
| `PATCH /api/assignments/<id>` | Mark complete or incomplete |
| `GET /api/summary` | Return total, completed, overdue and due-soon counts |

No accounts, Canvas access, notifications, or third-party services are used. This prototype stores only user-entered assignment data locally. Before public deployment, add authentication and proper per-user data isolation.

## Proposal proof-of-work notes

The source has an executable Flask app and automated end-to-end API test. A **GitHub repository URL and hosted deployment are not yet available**. Push this folder to your own GitHub repository, then include its actual link in the proposal. Do not claim it has been deployed.
