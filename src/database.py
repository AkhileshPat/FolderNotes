"""
SQLite database layer for FolderNotes.

Thread-safe database access with auto-migration support.
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.constants import APP_DATA_DIR, DATABASE_PATH

logger = logging.getLogger(__name__)


class Database:
    """Thread-safe SQLite database manager."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self._db_path = db_path
        self._ensure_directories()
        self._connection: Optional[sqlite3.Connection] = None
        self._connect()
        self._migrate()

    def _ensure_directories(self):
        """Create data directories if they don't exist."""
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

    def _connect(self):
        """Establish SQLite connection with WAL mode for better concurrency."""
        try:
            self._connection = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
                timeout=10.0
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA foreign_keys=ON")
            logger.info("Database connected: %s", self._db_path)
        except sqlite3.Error as e:
            logger.error("Database connection failed: %s", e)
            raise

    def _migrate(self):
        """Create tables if they don't exist."""
        try:
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS notes (
                    note_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_path    TEXT    NOT NULL UNIQUE,
                    title          TEXT    DEFAULT '',
                    content        TEXT    DEFAULT '',
                    created_at     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                    updated_at     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                    hidden         INTEGER NOT NULL DEFAULT 0,
                    snoozed_until  TEXT    DEFAULT NULL,
                    last_dismissed TEXT    DEFAULT NULL,
                    version        INTEGER NOT NULL DEFAULT 1
                );

                CREATE INDEX IF NOT EXISTS idx_folder_path ON notes(folder_path);
            """)
            self._connection.commit()
            logger.info("Database schema verified.")
        except sqlite3.Error as e:
            logger.error("Migration failed: %s", e)
            raise

    # ── CRUD Operations ──────────────────────────────────────────────

    def get_note(self, folder_path: str) -> Optional[Dict[str, Any]]:
        """Retrieve a note by its normalized folder path."""
        try:
            cursor = self._connection.execute(
                "SELECT * FROM notes WHERE folder_path = ?",
                (folder_path,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error("Failed to get note for '%s': %s", folder_path, e)
            return None

    def upsert_note(self, folder_path: str, title: str = "",
                    content: str = "") -> Optional[int]:
        """Insert or update a note. Returns the note_id."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self._connection.execute("""
                INSERT INTO notes (folder_path, title, content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(folder_path) DO UPDATE SET
                    title = excluded.title,
                    content = excluded.content,
                    updated_at = excluded.updated_at,
                    version = version + 1
            """, (folder_path, title, content, now, now))
            self._connection.commit()

            cursor = self._connection.execute(
                "SELECT note_id FROM notes WHERE folder_path = ?",
                (folder_path,)
            )
            row = cursor.fetchone()
            return row["note_id"] if row else None
        except sqlite3.Error as e:
            logger.error("Failed to upsert note for '%s': %s", folder_path, e)
            return None

    def update_content(self, folder_path: str, content: str):
        """Update only the content of an existing note (auto-save)."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self._connection.execute("""
                UPDATE notes SET content = ?, updated_at = ?, version = version + 1
                WHERE folder_path = ?
            """, (content, now, folder_path))
            self._connection.commit()
        except sqlite3.Error as e:
            logger.error("Failed to update content for '%s': %s", folder_path, e)

    def update_title(self, folder_path: str, title: str):
        """Update only the title of an existing note."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self._connection.execute("""
                UPDATE notes SET title = ?, updated_at = ? WHERE folder_path = ?
            """, (title, now, folder_path))
            self._connection.commit()
        except sqlite3.Error as e:
            logger.error("Failed to update title for '%s': %s", folder_path, e)

    def delete_note(self, folder_path: str) -> bool:
        """Permanently delete a note."""
        try:
            self._connection.execute(
                "DELETE FROM notes WHERE folder_path = ?",
                (folder_path,)
            )
            self._connection.commit()
            logger.info("Deleted note for '%s'", folder_path)
            return True
        except sqlite3.Error as e:
            logger.error("Failed to delete note for '%s': %s", folder_path, e)
            return False

    def set_hidden(self, folder_path: str, hidden: bool):
        """Hide/unhide a note for the current session concept (persisted)."""
        try:
            self._connection.execute(
                "UPDATE notes SET hidden = ? WHERE folder_path = ?",
                (1 if hidden else 0, folder_path)
            )
            self._connection.commit()
        except sqlite3.Error as e:
            logger.error("Failed to set hidden for '%s': %s", folder_path, e)

    # ── Snooze Operations ────────────────────────────────────────────

    def snooze_note(self, folder_path: str, until: str):
        """Set the snooze-until timestamp for a folder's note."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self._connection.execute("""
                UPDATE notes SET snoozed_until = ?, last_dismissed = ?
                WHERE folder_path = ?
            """, (until, now, folder_path))
            self._connection.commit()
            logger.info("Snoozed note for '%s' until %s", folder_path, until)
        except sqlite3.Error as e:
            logger.error("Failed to snooze note for '%s': %s", folder_path, e)

    def clear_snooze(self, folder_path: str):
        """Clear the snooze for a folder's note."""
        try:
            self._connection.execute(
                "UPDATE notes SET snoozed_until = NULL WHERE folder_path = ?",
                (folder_path,)
            )
            self._connection.commit()
        except sqlite3.Error as e:
            logger.error("Failed to clear snooze for '%s': %s", folder_path, e)

    def is_snoozed(self, folder_path: str) -> bool:
        """Check if a note is currently snoozed."""
        note = self.get_note(folder_path)
        if not note or not note.get("snoozed_until"):
            return False
        try:
            snoozed_until = datetime.strptime(
                note["snoozed_until"], "%Y-%m-%d %H:%M:%S"
            )
            return datetime.now() < snoozed_until
        except (ValueError, TypeError):
            return False

    # ── Query Operations ─────────────────────────────────────────────

    def get_all_notes(self) -> List[Dict[str, Any]]:
        """Get all notes (for settings/management UI)."""
        try:
            cursor = self._connection.execute(
                "SELECT * FROM notes ORDER BY updated_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error("Failed to get all notes: %s", e)
            return []

    def note_exists(self, folder_path: str) -> bool:
        """Quick check if a note exists for a folder."""
        try:
            cursor = self._connection.execute(
                "SELECT 1 FROM notes WHERE folder_path = ?",
                (folder_path,)
            )
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            return False

    # ── Lifecycle ────────────────────────────────────────────────────

    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            logger.info("Database connection closed.")
