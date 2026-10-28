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


if __name__ == '__main__':
    unittest.main()
