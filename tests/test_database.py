"""Unit tests for the database layer."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.database import Database


class TestDatabase(unittest.TestCase):

    def setUp(self):
        """Create a temporary database for each test."""
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test.db")
        self.db = Database(self.db_path)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.tmp_dir)

    def test_create_and_get_note(self):
        note_id = self.db.upsert_note("c:/users/test/documents", "My Note", "Hello")
        self.assertIsNotNone(note_id)

        note = self.db.get_note("c:/users/test/documents")
        self.assertIsNotNone(note)
        self.assertEqual(note["title"], "My Note")
        self.assertEqual(note["content"], "Hello")
        self.assertEqual(note["folder_path"], "c:/users/test/documents")

    def test_update_content(self):
        self.db.upsert_note("c:/test", "", "original")
        self.db.update_content("c:/test", "updated")

        note = self.db.get_note("c:/test")
        self.assertEqual(note["content"], "updated")
        self.assertEqual(note["version"], 2)

    def test_delete_note(self):
        self.db.upsert_note("c:/test", "", "")
        self.assertTrue(self.db.note_exists("c:/test"))

        self.db.delete_note("c:/test")
        self.assertFalse(self.db.note_exists("c:/test"))

    def test_upsert_updates_existing(self):
        self.db.upsert_note("c:/test", "Title 1", "Content 1")
        self.db.upsert_note("c:/test", "Title 2", "Content 2")

        note = self.db.get_note("c:/test")
        self.assertEqual(note["title"], "Title 2")
        self.assertEqual(note["content"], "Content 2")

    def test_nonexistent_note_returns_none(self):
        note = self.db.get_note("c:/nonexistent")
        self.assertIsNone(note)

    def test_snooze(self):
        from datetime import datetime, timedelta

        self.db.upsert_note("c:/test", "", "")

        # Snooze for 1 hour in the future
        until = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        self.db.snooze_note("c:/test", until)
        self.assertTrue(self.db.is_snoozed("c:/test"))

        # Clear snooze
        self.db.clear_snooze("c:/test")
        self.assertFalse(self.db.is_snoozed("c:/test"))

    def test_snooze_expired(self):
        from datetime import datetime, timedelta

        self.db.upsert_note("c:/test", "", "")

        # Snooze until the past
        until = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        self.db.snooze_note("c:/test", until)
        self.assertFalse(self.db.is_snoozed("c:/test"))

    def test_get_all_notes(self):
        self.db.upsert_note("c:/folder1", "Note 1", "")
        self.db.upsert_note("c:/folder2", "Note 2", "")
        self.db.upsert_note("c:/folder3", "Note 3", "")

        notes = self.db.get_all_notes()
        self.assertEqual(len(notes), 3)

    def test_hidden_flag(self):
        self.db.upsert_note("c:/test", "", "")
        self.db.set_hidden("c:/test", True)

        note = self.db.get_note("c:/test")
        self.assertEqual(note["hidden"], 1)

        self.db.set_hidden("c:/test", False)
        note = self.db.get_note("c:/test")
        self.assertEqual(note["hidden"], 0)


if __name__ == "__main__":
    unittest.main()
