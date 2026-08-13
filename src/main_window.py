"""Primary desktop window for FolderNotes."""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog
)

from src.rich_editor import RichEditor


class MainWindow(QWidget):
    """A normal app window for creating and editing folder notes."""

    def __init__(self, note_manager, parent=None):
        super().__init__(parent)
        self._note_manager = note_manager
        self._folder_path = ""

        self.setWindowTitle("FolderNotes")
        self.resize(560, 460)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        heading = QLabel("FolderNotes")
        heading.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(heading)

        help_text = QLabel("Choose a folder to create, open, and edit its note.")
        help_text.setStyleSheet("color: #666;")
        layout.addWidget(help_text)

        folder_row = QHBoxLayout()
        self._folder_label = QLabel("No folder selected")
        self._folder_label.setWordWrap(True)
        self._folder_label.setStyleSheet(
            "padding: 8px; background: #f4f4f4; border: 1px solid #ddd;"
        )
        self._browse_button = QPushButton("Choose folder…")
        self._browse_button.clicked.connect(self._choose_folder)
        folder_row.addWidget(self._folder_label, 1)
        folder_row.addWidget(self._browse_button)
        layout.addLayout(folder_row)

        self._open_button = QPushButton("Create / open note")
        self._open_button.setEnabled(False)
        self._open_button.clicked.connect(self._open_note)
        layout.addWidget(self._open_button)

        self._editor = RichEditor()
        self._editor.setEnabled(False)
        self._editor.content_changed.connect(self._save_content)
        layout.addWidget(self._editor, 1)

        self._status = QLabel("Select a folder to begin.")
        self._status.setStyleSheet("color: #666;")
        layout.addWidget(self._status)

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose a folder")
        if not folder:
            return
        self._folder_path = folder
        self._folder_label.setText(folder)
        self._open_button.setEnabled(True)
        self._status.setText("Ready to create or open this folder's note.")

    def _open_note(self):
        """Create the selected folder's note if needed, then load it."""
        if not self._folder_path:
            return

        # The manager window is an editor for this selected path only.  It
        # must not change the active Explorer folder or display a floating
        # note for a folder that has not been opened in Explorer.
        note = self._note_manager.get_note(self._folder_path)
        if note is None:
            self._note_manager.create_note(
                self._folder_path,
                announce=False,
            )
            note = self._note_manager.get_note(self._folder_path)

        if note is None:
            self._status.setText("Could not create a note for this folder.")
            return

        # Explicitly creating or opening a note means the user wants it to
        # appear again when this exact folder is opened in Explorer.
        self._note_manager.reactivate_note(self._folder_path)
        self._editor.set_content(note.get("content", ""))
        self._editor.setEnabled(True)
        self._editor.setFocus()
        self._status.setText("Editing note for " + os.path.basename(self._folder_path))

    def _save_content(self, content: str):
        if self._folder_path:
            self._note_manager.save_content(content, self._folder_path)
            self._status.setText("Saved")

    def closeEvent(self, event):
        """Keep FolderNotes and its floating note running in the tray."""
        event.ignore()
        self.hide()
