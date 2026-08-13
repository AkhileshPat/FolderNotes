"""
Note Manager for FolderNotes.

Business logic layer: CRUD operations, snooze logic, auto-save,
and coordination between the database and the UI.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, Signal

from src.database import Database
from src.folder_resolver import FolderResolver
from src.constants import SNOOZE_DURATIONS

logger = logging.getLogger(__name__)


class NoteManager(QObject):
    """
    Manages note lifecycle: creation, retrieval, updates,
    deletion, snoozing, and session dismissal.

    Signals:
        note_ready(dict): Emitted when a note should be displayed.
        note_cleared():   Emitted when no note should be shown.
    """

    note_ready = Signal(dict)   # note data dict
    note_cleared = Signal()

    def __init__(self, database: Database, parent=None):
        super().__init__(parent)
        self._db = database
        self._resolver = FolderResolver()
        self._current_folder: str = ""
        self._session_dismissed: set = set()  # folders dismissed this session

    # ── Folder Navigation ────────────────────────────────────────────

    def on_folder_changed(self, raw_path: str):
        """
        Called when the active Explorer folder changes.
        Resolves the path, checks for notes, and emits appropriate signals.
        """
        normalized = self._resolver.normalize(raw_path)

        if not self._resolver.is_valid_folder(raw_path):
            logger.debug("Invalid/virtual folder: %s", raw_path)
            self._current_folder = ""
            self.note_cleared.emit()
            return

        self._current_folder = normalized

        # Check session dismissal
        if normalized in self._session_dismissed:
            logger.debug("Note dismissed for session: %s", normalized)
            self.note_cleared.emit()
            return

        # Check if note exists
        note = self._db.get_note(normalized)
        if not note:
            logger.debug("No note for: %s", normalized)
            self.note_cleared.emit()
            return

        # Check snooze
        if self._db.is_snoozed(normalized):
            logger.debug("Note snoozed: %s", normalized)
            self.note_cleared.emit()
            return

        # Check hidden flag
        if note.get("hidden", 0):
            self.note_cleared.emit()
            return

        # Note is ready to display
        logger.info("Showing note for: %s", normalized)
        self.note_ready.emit(dict(note))

    def on_explorer_lost(self):
        """
        Explorer lost foreground focus.

        We intentionally do NOT hide the note here. The overlay's own
        position timer already handles Explorer window closure and
        minimisation, and on_folder_changed handles folder navigation.
        Clearing state here caused the overlay to flash and disappear
        immediately after creation via the tray menu.
        """
        pass

    # ── CRUD ─────────────────────────────────────────────────────────

    def create_note(self, folder_path: str = "", title: str = "",
                    content: str = "", announce: bool = True) -> Optional[int]:
        """Create a new note for the given (or current) folder."""
        path = folder_path or self._current_folder
        if not path:
            logger.warning("Cannot create note: no folder specified.")
            return None

        normalized = self._resolver.normalize(path)
        note_id = self._db.upsert_note(normalized, title, content)
        if note_id:
            logger.info("Created note #%d for '%s'", note_id, normalized)
            if announce:
                # A note created for the active Explorer folder should become
                # the active overlay note immediately.  Manager-window edits
                # pass ``announce=False`` so they remain scoped to the
                # selected path without creating a standalone overlay.
                self._current_folder = normalized
                note = self._db.get_note(normalized)
                if note:
                    self.note_ready.emit(dict(note))
        return note_id

    def save_content(self, content: str, folder_path: str = ""):
        """Auto-save content for the supplied or current folder's note."""
        path = folder_path or self._current_folder
        if not path:
            return
        self._db.update_content(self._resolver.normalize(path), content)

    def save_title(self, title: str):
        """Save title for the current folder's note."""
        if not self._current_folder:
            return
        self._db.update_title(self._current_folder, title)

    def delete_note(self, folder_path: str = "") -> bool:
        """Permanently delete the note for the given (or current) folder."""
        path = folder_path or self._current_folder
        if not path:
            return False
        normalized = self._resolver.normalize(path)
        result = self._db.delete_note(normalized)
        if result:
            self._session_dismissed.discard(normalized)
            self.note_cleared.emit()
        return result

    # ── Session Dismiss ──────────────────────────────────────────────

    def dismiss_note(self):
        """
        Hide the note for the current folder until the app restarts.
        Does NOT delete or modify the note.
        """
        if self._current_folder:
            self._session_dismissed.add(self._current_folder)
            self.note_cleared.emit()
            logger.info("Dismissed note for session: %s", self._current_folder)

    # ── Snooze ───────────────────────────────────────────────────────

    def snooze_note(self, hours: int):
        """Snooze the current folder's note for the given number of hours."""
        if not self._current_folder:
            return
        if hours not in SNOOZE_DURATIONS:
            logger.warning("Invalid snooze duration: %d hours", hours)
            return

        until = datetime.now() + timedelta(hours=hours)
        until_str = until.strftime("%Y-%m-%d %H:%M:%S")
        self._db.snooze_note(self._current_folder, until_str)
        self.note_cleared.emit()
        logger.info("Snoozed '%s' for %d hours (until %s)",
                     self._current_folder, hours, until_str)

    # ── Query ────────────────────────────────────────────────────────

    @property
    def current_folder(self) -> str:
        return self._current_folder

    def has_note(self, folder_path: str = "") -> bool:
        path = folder_path or self._current_folder
        if not path:
            return False
        return self._db.note_exists(self._resolver.normalize(path))

    def get_current_note(self) -> Optional[Dict[str, Any]]:
        if not self._current_folder:
            return None
        return self._db.get_note(self._current_folder)

    def get_note(self, folder_path: str) -> Optional[Dict[str, Any]]:
        """Return the note belonging to exactly ``folder_path``."""
        if not folder_path:
            return None
        return self._db.get_note(self._resolver.normalize(folder_path))

    def reactivate_note(self, folder_path: str):
        """Make an explicitly opened manager note eligible for Explorer display."""
        if not folder_path:
            return

        normalized = self._resolver.normalize(folder_path)
        self._session_dismissed.discard(normalized)
        self._db.set_hidden(normalized, False)
        self._db.clear_snooze(normalized)
