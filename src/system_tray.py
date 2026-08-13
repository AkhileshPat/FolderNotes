"""
System Tray icon and menu for FolderNotes.
"""

import logging

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PySide6.QtCore import Signal, Qt

from src.constants import APP_NAME, APP_VERSION

logger = logging.getLogger(__name__)


class SystemTray(QSystemTrayIcon):
    """
    System tray icon with context menu.

    Signals:
        create_note_triggered(): User wants to create a note for current folder.
        quit_triggered():        User wants to exit the app.
        show_about_triggered():  User wants to see about info.
    """

    create_note_triggered = Signal()
    quit_triggered = Signal()
    show_about_triggered = Signal()
    show_window_triggered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._setup_icon()
        self._setup_menu()
        self.setToolTip(f"{APP_NAME} v{APP_VERSION}")
        self.setVisible(True)

    def _setup_icon(self):
        """Create a simple programmatic tray icon (📌 on yellow)."""
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Yellow circle background
        painter.setBrush(QColor("#FFD600"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, size - 8, size - 8)

        # "FN" text
        painter.setPen(QColor("#3E2723"))
        font = QFont("Segoe UI", 20, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "FN")
        painter.end()

        self.setIcon(QIcon(pixmap))

    def _setup_menu(self):
        """Build the context menu."""
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFDE7;
                border: 1px solid #F9E066;
                border-radius: 6px;
                padding: 4px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
                color: #3E2723;
            }
            QMenu::item:selected {
                background-color: #FFF59D;
            }
            QMenu::separator {
                height: 1px;
                background-color: #E8D44D;
                margin: 4px 8px;
            }
        """)

        # Create note action
        create_action = menu.addAction("📝  Create note for current folder")
        create_action.triggered.connect(self.create_note_triggered.emit)

        menu.addSeparator()

        show_action = menu.addAction("Open FolderNotes")
        show_action.triggered.connect(self.show_window_triggered.emit)

        # About
        about_action = menu.addAction(f"ℹ️  About {APP_NAME}")
        about_action.triggered.connect(self.show_about_triggered.emit)

        menu.addSeparator()

        # Quit
        quit_action = menu.addAction("❌  Quit")
        quit_action.triggered.connect(self.quit_triggered.emit)

        self.setContextMenu(menu)

    def show_notification(self, title: str, message: str):
        """Show a system notification."""
        self.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)
