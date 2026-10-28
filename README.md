# SeniorSync - Senior Design starter

SeniorSync is a student assignment dashboard built with Flask, SQLite, and vanilla HTML/CSS/JavaScript. This is the **local prototype**, not a finished or publicly deployed app.

## Run on a Mac or PC

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>. The database is created automatically in `instance/seniorsync.sqlite3` and is ignored by git.

Run tests with `python -m unittest discover -s tests -v`.

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
