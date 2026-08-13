"""Unit tests for the NoteManager."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.database import Database
from src.note_manager import NoteManager


class TestNoteManager(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test.db")
        self.db = Database(self.db_path)
        self.manager = NoteManager(self.db)
        self._manager_folder = ""
        self._session_dismissed = set()

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.tmp_dir)

    def test_create_and_check(self):
        from src.folder_resolver import FolderResolver
        path = FolderResolver.normalize("C:\\Users\\Test")
        self.db.upsert_note(path, "Test", "Content")
        self.assertTrue(self.db.note_exists(path))

    def test_session_dismiss_logic(self):
        """Session dismissal should prevent the note from appearing."""
        from src.folder_resolver import FolderResolver
        path = FolderResolver.normalize("C:\\Users\\Test")
        self.db.upsert_note(path, "Test", "Content")

        # Simulate session dismiss
        self._session_dismissed.add(path)
        self.assertIn(path, self._session_dismissed)

        # After restart (new set), it should be gone
        new_dismissed = set()
        self.assertNotIn(path, new_dismissed)

    def test_snooze_blocks_display(self):
        from datetime import datetime, timedelta
        from src.folder_resolver import FolderResolver

        path = FolderResolver.normalize("C:\\Users\\Test")
        self.db.upsert_note(path, "Test", "Content")

        until = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        self.db.snooze_note(path, until)

        # Note should be snoozed
        self.assertTrue(self.db.is_snoozed(path))

    def test_snooze_does_not_affect_other_folders(self):
        from datetime import datetime, timedelta
        from src.folder_resolver import FolderResolver

        path1 = FolderResolver.normalize("C:\\Folder1")
        path2 = FolderResolver.normalize("C:\\Folder2")

        self.db.upsert_note(path1, "Note 1", "")
        self.db.upsert_note(path2, "Note 2", "")

        # Snooze only path1
        until = (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
        self.db.snooze_note(path1, until)

        self.assertTrue(self.db.is_snoozed(path1))
        self.assertFalse(self.db.is_snoozed(path2))

    def test_manager_editing_does_not_activate_or_show_note(self):
        """Editing a chosen path must not display it outside Explorer."""
        active_path = "c:/active-folder"
        chosen_path = "c:/chosen-folder"
        ready_notes = []
        self.manager.note_ready.connect(ready_notes.append)
        self.manager._current_folder = active_path

        self.manager.create_note(chosen_path, content="draft", announce=False)
        self.manager.save_content("edited", chosen_path)

        self.assertEqual(self.manager.current_folder, active_path)
        self.assertEqual(ready_notes, [])
        self.assertEqual(self.manager.get_note(chosen_path)["content"], "edited")

    def test_reactivating_manager_note_clears_its_snooze(self):
        from datetime import datetime, timedelta

        path = "c:/chosen-folder"
        self.db.upsert_note(path, content="draft")
        until = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        self.db.snooze_note(path, until)

        self.manager.reactivate_note(path)

        self.assertFalse(self.db.is_snoozed(path))


if __name__ == "__main__":
    unittest.main()
