"""Unit tests for SafeSteps security helpers and core learning logic."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from source_code import app


class PasswordTests(unittest.TestCase):
    def test_password_hash_verifies_original_password(self):
        stored = app.hash_password("correct horse")
        self.assertTrue(app.password_matches("correct horse", stored))

    def test_password_hash_rejects_wrong_password(self):
        stored = app.hash_password("correct horse")
        self.assertFalse(app.password_matches("wrong horse", stored))

    def test_password_verifier_rejects_malformed_hash(self):
        self.assertFalse(app.password_matches("anything", "not-a-hash"))


class LearningLogicTests(unittest.TestCase):
    def test_assessment_score_counts_correct_answers(self):
        self.assertEqual(app.score_answers([1, 0, 2]), 3)
        self.assertEqual(app.score_answers([0, 2, 1]), 0)

    def test_assessment_rejects_missing_or_out_of_range_answers(self):
        for answers in ([1, 0], [1, 0, 3]):
            with self.subTest(answers=answers), self.assertRaises(ValueError):
                app.score_answers(answers)

    def test_only_approved_simulation_scenarios_are_accepted(self):
        self.assertTrue(app.approved_scenario("shared_file"))
        self.assertFalse(app.approved_scenario("unknown"))

    def test_only_safe_event_types_are_accepted(self):
        self.assertTrue(app.valid_simulation_event("reported"))
        self.assertTrue(app.valid_simulation_event("clicked"))
        self.assertFalse(app.valid_simulation_event("password"))


class DatabaseTests(unittest.TestCase):
    def test_initialize_seeds_demo_accounts_idempotently(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "prototype.sqlite3"
            with patch.object(app, "DB", database):
                app.initialize()
                app.initialize()
                db = app.dbopen()
                users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                employees = db.execute("SELECT COUNT(*) FROM users WHERE role='employee'").fetchone()[0]
                db.close()
            self.assertEqual(users, 7)
            self.assertEqual(employees, 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
