from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app import create_app


class SeniorSyncTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()
        self.app = create_app({"TESTING": True, "DATABASE": str(Path(self.tempdir.name) / "test.db")})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_add_prioritize_complete(self):
        due_date = (date.today() + timedelta(days=2)).isoformat()
        create = self.client.post('/api/assignments', json={
            "title": "Spanish project", "course": "SPAN 201", "due_date": due_date,
        })
        self.assertEqual(create.status_code, 201)
        assignments = self.client.get('/api/assignments').get_json()
        self.assertEqual(len(assignments), 1)
        self.assertEqual(assignments[0]['urgency'], 'due-soon')
        self.assertEqual(self.client.get('/api/summary').get_json()['due_soon'], 1)
        mark = self.client.patch(f"/api/assignments/{assignments[0]['id']}", json={"completed": True})
        self.assertEqual(mark.status_code, 200)
        self.assertEqual(self.client.get('/api/summary').get_json()['completed'], 1)

    def test_invalid_input_is_rejected(self):
        response = self.client.post('/api/assignments', json={
            "title": "Test", "course": "CS", "due_date": "not-a-date",
        })
        self.assertEqual(response.status_code, 400)

    def test_overdue_and_future_dates(self):
        cases = [
            ((date.today() - timedelta(days=1)).isoformat(), 'overdue'),
            ((date.today() + timedelta(days=10)).isoformat(), 'upcoming'),
        ]
        for due_date, expected in cases:
            response = self.client.post('/api/assignments', json={
                "title": expected, "course": "Senior Design", "due_date": due_date,
            })
            self.assertEqual(response.status_code, 201)
        statuses = {row['title']: row['urgency'] for row in self.client.get('/api/assignments').get_json()}
        self.assertEqual(statuses, {'overdue': 'overdue', 'upcoming': 'upcoming'})

    # --- Helpers for the tests below ---

    def add(self, title, days_from_today):
        due_date = (date.today() + timedelta(days=days_from_today)).isoformat()
        response = self.client.post('/api/assignments', json={
            "title": title, "course": "CS 401", "due_date": due_date,
        })
        self.assertEqual(response.status_code, 201)
        return response.get_json()['id']

    def complete(self, assignment_id):
        response = self.client.patch(f"/api/assignments/{assignment_id}", json={"completed": True})
        self.assertEqual(response.status_code, 200)

    # --- Sorting ---

    def test_assignments_sorted_by_due_date(self):
        # Added out of order on purpose.
        self.add("Later", 10)
        self.add("Overdue", -2)
        self.add("Today", 0)
        self.add("Tomorrow", 1)
        rows = self.client.get('/api/assignments').get_json()
        self.assertEqual([r['title'] for r in rows], ["Overdue", "Today", "Tomorrow", "Later"])
        self.assertEqual([r['days_left'] for r in rows], [-2, 0, 1, 10])

    def test_completed_assignments_sort_last(self):
        early = self.add("Early but done", -5)
        self.add("Later", 7)
        self.add("Soon", 1)
        self.complete(early)
        rows = self.client.get('/api/assignments').get_json()
        self.assertEqual([r['title'] for r in rows], ["Soon", "Later", "Early but done"])
        self.assertEqual(rows[-1]['urgency'], 'completed')

    def test_due_soon_boundary_is_three_days(self):
        self.add("Three days", 3)
        self.add("Four days", 4)
        statuses = {r['title']: r['urgency'] for r in self.client.get('/api/assignments').get_json()}
        self.assertEqual(statuses, {"Three days": "due-soon", "Four days": "upcoming"})

    # --- Summary counters ---

    def test_summary_empty(self):
        summary = self.client.get('/api/summary').get_json()
        self.assertEqual(summary, {"total": 0, "completed": 0, "due_soon": 0, "overdue": 0})

    def test_summary_counts_each_category(self):
        self.add("Overdue 1", -3)
        self.add("Overdue 2", -1)
        self.add("Due today", 0)
        self.add("Due in 3", 3)
        self.add("Upcoming", 12)
        done = self.add("Finished", -4)  # overdue date, but completed
        self.complete(done)
        summary = self.client.get('/api/summary').get_json()
        self.assertEqual(summary, {"total": 6, "completed": 1, "due_soon": 2, "overdue": 2})

    def test_summary_updates_when_completed_and_reopened(self):
        assignment_id = self.add("Essay", -1)
        self.assertEqual(self.client.get('/api/summary').get_json()['overdue'], 1)
        self.complete(assignment_id)
        summary = self.client.get('/api/summary').get_json()
        self.assertEqual((summary['overdue'], summary['completed']), (0, 1))
        self.client.patch(f"/api/assignments/{assignment_id}", json={"completed": False})
        summary = self.client.get('/api/summary').get_json()
        self.assertEqual((summary['overdue'], summary['completed']), (1, 0))

    def test_complete_unknown_assignment_returns_404(self):
        response = self.client.patch('/api/assignments/999', json={"completed": True})
        self.assertEqual(response.status_code, 404)


class SeedDemoTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()
        self.app = create_app({"TESTING": True, "DATABASE": str(Path(self.tempdir.name) / "demo.db")})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_seed_keeps_existing_data_and_skips_duplicates(self):
        from seed_demo import DEMO_ASSIGNMENTS, seed
        self.client.post('/api/assignments', json={
            "title": "My real assignment", "course": "CS 401", "due_date": date.today().isoformat(),
        })
        added, skipped = seed(self.app)
        self.assertEqual((added, skipped), (len(DEMO_ASSIGNMENTS), 0))
        # Running it again adds nothing new.
        self.assertEqual(seed(self.app), (0, len(DEMO_ASSIGNMENTS)))
        rows = self.client.get('/api/assignments').get_json()
        self.assertEqual(len(rows), len(DEMO_ASSIGNMENTS) + 1)
        self.assertIn("My real assignment", [r['title'] for r in rows])
        # Every dashboard category has at least one example.
        summary = self.client.get('/api/summary').get_json()
        for key in ("completed", "due_soon", "overdue"):
            self.assertGreater(summary[key], 0, key)
        self.assertIn('upcoming', {r['urgency'] for r in rows})


if __name__ == '__main__':
    unittest.main()
