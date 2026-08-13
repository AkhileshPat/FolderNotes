"""
FolderNotes Application Controller.

Wires together all components:
  Explorer Monitor ↔ Note Manager ↔ Overlay Window ↔ System Tray
"""

import sys
import os
import logging
from datetime import datetime

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QTimer

from src.constants import APP_NAME, APP_DATA_DIR, LOG_DIR
from src.database import Database
from src.settings import Settings
from src.explorer_monitor import ExplorerMonitor
from src.note_manager import NoteManager
from src.overlay_window import OverlayWindow
from src.main_window import MainWindow
from src.system_tray import SystemTray

logger = logging.getLogger(__name__)


class FolderNotesApp:
    """
    Main application controller.

    Lifecycle:
    1. Init QApplication
    2. Create all components
    3. Wire signals
    4. Start Explorer monitor
    5. Run event loop
    """

    def __init__(self):
        self._setup_logging()

        # Create QApplication
        self._app = QApplication(sys.argv)
        # FolderNotes is a background utility. Closing its manager window
        # must not stop the event loop that owns the floating note.
        self._app.setQuitOnLastWindowClosed(False)
        self._app.setApplicationName(APP_NAME)

        # Initialize components
        self._settings = Settings()
        self._database = Database()
        self._note_manager = NoteManager(self._database)
        self._explorer_monitor = ExplorerMonitor()
        self._overlay = OverlayWindow()
        self._main_window = MainWindow(self._note_manager)
        self._tray = SystemTray()

        # Current tracked Explorer HWND
        self._current_hwnd: int = 0

        self._wire_signals()

    def _setup_logging(self):
        """Configure logging to file and console."""
        os.makedirs(LOG_DIR, exist_ok=True)
        log_file = os.path.join(
            LOG_DIR,
            f"foldernotes_{datetime.now().strftime('%Y%m%d')}.log"
        )

        handlers = [logging.FileHandler(log_file, encoding="utf-8")]
        # pythonw.exe has no console streams. Keep logging to the file when
        # the app has detached from the terminal.
        if sys.stdout is not None:
            handlers.append(logging.StreamHandler(sys.stdout))

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=handlers,
        )
        logger.info("=" * 50)
        logger.info("FolderNotes starting up...")

    def _wire_signals(self):
        """Connect all component signals."""

        # Explorer Monitor → Note Manager
        self._explorer_monitor.folder_changed.connect(
            self._on_folder_changed
        )
        self._explorer_monitor.explorer_lost.connect(
            self._on_explorer_lost
        )

        # Note Manager → Overlay
        self._note_manager.note_ready.connect(self._on_note_ready)
        self._note_manager.note_cleared.connect(self._on_note_cleared)

        # Overlay → Note Manager (auto-save)
        self._overlay.content_saved.connect(
            self._note_manager.save_content
        )
        self._overlay.close_requested.connect(
            self._note_manager.dismiss_note
        )
        self._overlay.delete_requested.connect(
            self._on_delete_requested
        )
        self._overlay.snooze_requested.connect(
            self._note_manager.snooze_note
        )

        # The tray owns the explicit application exit action. Closing the
        # manager window merely hides it, leaving existing notes available.
        self._tray.quit_triggered.connect(self._on_quit)
        self._tray.show_about_triggered.connect(self._on_about)
        self._tray.create_note_triggered.connect(self._on_create_note)
        self._tray.show_window_triggered.connect(self._show_main_window)

    # ── Signal Handlers ──────────────────────────────────────────────

    def _on_folder_changed(self, folder_path: str, hwnd: int, rect: tuple):
        """Explorer navigated to a new folder."""
        logger.info("App: folder_changed -> path='%s', hwnd=%s", folder_path, hwnd)
        self._current_hwnd = hwnd
        self._note_manager.on_folder_changed(folder_path)

    def _on_explorer_lost(self):
        """Explorer is no longer the foreground window."""
        logger.debug("App: explorer_lost")
        # Don't clear _current_hwnd here — we keep it so that if
        # note_ready fires (e.g. from create_note), we still have the hwnd.
        # The overlay's position tracker will handle hiding when the
        # Explorer window is actually gone.
        self._note_manager.on_explorer_lost()

    def _on_note_ready(self, note_data: dict):
        """A note should be displayed."""
        # Use current hwnd, or fall back to the last known Explorer hwnd
        hwnd = self._current_hwnd or self._explorer_monitor.get_active_explorer_hwnd()
        logger.info("App: note_ready for '%s', using hwnd=%s",
                     note_data.get("folder_path", "?"), hwnd)
        # A tray action can run while Explorer has temporarily lost focus.
        # OverlayWindow has a centered fallback for that case, so a saved
        # note is always immediately visible and editable.
        self._overlay.show_note(note_data, hwnd)

    def _on_note_cleared(self):
        """No note should be shown."""
        self._overlay.hide_note()

    def _on_create_note(self):
        """User wants to create a note for the current folder."""
        # The tray menu takes foreground focus before this callback runs, so
        # resolve Explorer directly instead of relying only on the poll cache.
        target_folder, target_hwnd = self._explorer_monitor.get_note_target()

        logger.info("App: create_note requested — folder='%s', hwnd=%s",
                     target_folder, target_hwnd)

        if not target_folder:
            return

        if self._note_manager.has_note(target_folder):
            # "Create" doubles as "show" for the one-note-per-folder model.
            self._current_hwnd = target_hwnd or self._current_hwnd
            self._note_manager.on_folder_changed(target_folder)
            QTimer.singleShot(0, self._show_current_note)
            return

        # Keep the most recently tracked Explorer handle as a fallback.  The
        # tray menu itself temporarily takes focus, so querying the foreground
        # window at this point may not yield Explorer.
        self._current_hwnd = target_hwnd or self._current_hwnd

        note_id = self._note_manager.create_note(target_folder)
        if note_id:
            # Let the tray menu close before raising the top-level overlay.
            # Without this, Windows can leave the new Tool window behind the
            # menu even though the note was successfully created.
            QTimer.singleShot(0, self._show_current_note)

    def _show_current_note(self):
        """Show the active note once the tray action has completed."""
        note = self._note_manager.get_current_note()
        hwnd = (self._explorer_monitor.get_active_explorer_hwnd()
                or self._current_hwnd)
        if note and hwnd:
            self._current_hwnd = hwnd
            self._overlay.show_note(note, hwnd)

    def _on_delete_requested(self):
        """User wants to permanently delete a note."""
        msg = QMessageBox()
        msg.setWindowTitle("Delete Note")
        msg.setText("Are you sure you want to permanently delete this note?")
        msg.setInformativeText("This action cannot be undone.")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #FFFDE7;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            self._note_manager.delete_note()
            QMessageBox.information(None, APP_NAME, "Note deleted.")

    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            None,
            f"About {APP_NAME}",
            f"<h3>{APP_NAME} v1.0.0</h3>"
            f"<p>Lightweight folder-attached notes for Windows.</p>"
            f"<p>One note per folder. Always there when you need it.</p>"
            f"<hr>"
            f"<p style='color: #888; font-size: 11px;'>"
            f"Built with Python + PySide6</p>"
        )

    def _on_quit(self):
        """Clean shutdown."""
        logger.info("FolderNotes shutting down...")
        self._tray.hide()
        self._explorer_monitor.stop()
        self._overlay.hide_note()
        self._database.close()
        self._app.quit()

    # ── Run ──────────────────────────────────────────────────────────

    def _show_main_window(self):
        """Restore the manager window from the system tray."""
        self._main_window.show()
        self._main_window.raise_()
        self._main_window.activateWindow()

    def run(self) -> int:
        """Start the application event loop."""
        self._explorer_monitor.start()
        self._tray.show()
        self._main_window.show()
        logger.info("Application ready. Entering event loop.")
        exit_code = self._app.exec()
        self._explorer_monitor.stop()
        self._tray.hide()
        self._overlay.hide_note()
        self._database.close()
        return exit_code
