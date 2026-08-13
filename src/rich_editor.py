"""
Rich Text Editor widget for FolderNotes.

A QTextEdit with a compact formatting toolbar supporting:
  - Bold, Italic, Underline
  - Bullet list, Numbered list

Auto-saves on every keystroke via a debounced signal.
"""

import logging
from PySide6.QtCore import Signal, QTimer, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton
)
from PySide6.QtGui import (
    QFont, QTextCharFormat, QTextCursor, QTextListFormat, QKeySequence,
    QShortcut
)

from src.constants import NOTE_BG_COLOR, TEXT_COLOR, TOOLBAR_BG

logger = logging.getLogger(__name__)


class RichEditor(QWidget):
    """
    Rich text editor with formatting toolbar.

    Signals:
        content_changed(str): Emitted (debounced) when content changes.
            Carries the HTML content string.
    """

    content_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)  # 300ms debounce
        self._debounce_timer.timeout.connect(self._emit_content)
        self._suppress_signals = False

        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Formatting Toolbar ───────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 4, 8, 4)
        toolbar.setSpacing(4)

        self._btn_bold = self._make_btn("B", "Bold (Ctrl+B)", bold=True)
        self._btn_italic = self._make_btn("I", "Italic (Ctrl+I)", italic=True)
        self._btn_underline = self._make_btn("U", "Underline (Ctrl+U)",
                                              underline=True)
        self._btn_bullet = self._make_btn("•", "Bullet list")
        self._btn_numbered = self._make_btn("1.", "Numbered list")

        self._btn_bold.clicked.connect(self._toggle_bold)
        self._btn_italic.clicked.connect(self._toggle_italic)
        self._btn_underline.clicked.connect(self._toggle_underline)
        self._btn_bullet.clicked.connect(self._toggle_bullet_list)
        self._btn_numbered.clicked.connect(self._toggle_numbered_list)

        for btn in [self._btn_bold, self._btn_italic, self._btn_underline,
                     self._btn_bullet, self._btn_numbered]:
            toolbar.addWidget(btn)
        toolbar.addStretch()

        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar)
        toolbar_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {TOOLBAR_BG};
                border-bottom: 1px solid #E8D44D;
            }}
        """)

        # ── Text Editor ──────────────────────────────────────────────
        self._editor = QTextEdit()
        self._editor.setAcceptRichText(True)
        self._editor.setPlaceholderText("Type your note here...")
        self._editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {NOTE_BG_COLOR};
                color: {TEXT_COLOR};
                border: none;
                padding: 10px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                selection-background-color: #FFD54F;
                selection-color: {TEXT_COLOR};
            }}
            QScrollBar:vertical {{
                width: 6px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: #D4C44A;
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        self._editor.textChanged.connect(self._on_text_changed)

        layout.addWidget(toolbar_widget)
        layout.addWidget(self._editor, 1)

    def _make_btn(self, text: str, tooltip: str, bold=False,
                  italic=False, underline=False) -> QPushButton:
        """Create a compact formatting button."""
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setFixedSize(28, 24)
        btn.setCheckable(True)

        font_weight = "bold" if bold else "normal"
        font_style = "italic" if italic else "normal"
        text_dec = "underline" if underline else "none"

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                font-weight: {font_weight};
                font-style: {font_style};
                text-decoration: {text_dec};
                font-size: 12px;
                color: {TEXT_COLOR};
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.08);
                border-color: #D4C44A;
            }}
            QPushButton:checked {{
                background-color: rgba(0, 0, 0, 0.12);
                border-color: #C0A800;
            }}
        """)
        return btn

    def _setup_shortcuts(self):
        """Keyboard shortcuts for formatting."""
        QShortcut(QKeySequence("Ctrl+B"), self, self._toggle_bold)
        QShortcut(QKeySequence("Ctrl+I"), self, self._toggle_italic)
        QShortcut(QKeySequence("Ctrl+U"), self, self._toggle_underline)

    # ── Formatting Actions ───────────────────────────────────────────

    def _toggle_bold(self):
        fmt = QTextCharFormat()
        cursor = self._editor.textCursor()
        current_weight = cursor.charFormat().fontWeight()
        new_weight = QFont.Weight.Normal if current_weight == QFont.Weight.Bold else QFont.Weight.Bold
        fmt.setFontWeight(new_weight)
        cursor.mergeCharFormat(fmt)
        self._editor.mergeCurrentCharFormat(fmt)
        self._btn_bold.setChecked(new_weight == QFont.Weight.Bold)

    def _toggle_italic(self):
        fmt = QTextCharFormat()
        cursor = self._editor.textCursor()
        is_italic = cursor.charFormat().fontItalic()
        fmt.setFontItalic(not is_italic)
        cursor.mergeCharFormat(fmt)
        self._editor.mergeCurrentCharFormat(fmt)
        self._btn_italic.setChecked(not is_italic)

    def _toggle_underline(self):
        fmt = QTextCharFormat()
        cursor = self._editor.textCursor()
        is_underline = cursor.charFormat().fontUnderline()
        fmt.setFontUnderline(not is_underline)
        cursor.mergeCharFormat(fmt)
        self._editor.mergeCurrentCharFormat(fmt)
        self._btn_underline.setChecked(not is_underline)

    def _toggle_bullet_list(self):
        cursor = self._editor.textCursor()
        current_list = cursor.currentList()
        if current_list and current_list.format().style() == QTextListFormat.Style.ListDisc:
            # Remove list
            block_fmt = cursor.blockFormat()
            block_fmt.setIndent(0)
            cursor.setBlockFormat(block_fmt)
            # Remove from list
            current_list.remove(cursor.block())
            self._btn_bullet.setChecked(False)
        else:
            cursor.createList(QTextListFormat.Style.ListDisc)
            self._btn_bullet.setChecked(True)
        self._btn_numbered.setChecked(False)

    def _toggle_numbered_list(self):
        cursor = self._editor.textCursor()
        current_list = cursor.currentList()
        if current_list and current_list.format().style() == QTextListFormat.Style.ListDecimal:
            # Remove list
            block_fmt = cursor.blockFormat()
            block_fmt.setIndent(0)
            cursor.setBlockFormat(block_fmt)
            current_list.remove(cursor.block())
            self._btn_numbered.setChecked(False)
        else:
            cursor.createList(QTextListFormat.Style.ListDecimal)
            self._btn_numbered.setChecked(True)
        self._btn_bullet.setChecked(False)

    # ── Content Management ───────────────────────────────────────────

    def _on_text_changed(self):
        """Debounced auto-save trigger."""
        if not self._suppress_signals:
            self._debounce_timer.start()

    def _emit_content(self):
        """Emit the current HTML content."""
        self.content_changed.emit(self._editor.toHtml())

    def set_content(self, html: str):
        """Set the editor content (suppresses auto-save signal)."""
        self._suppress_signals = True
        self._editor.setHtml(html)
        self._suppress_signals = False

    def get_content(self) -> str:
        """Get the current HTML content."""
        return self._editor.toHtml()

    def clear(self):
        """Clear the editor."""
        self._suppress_signals = True
        self._editor.clear()
        self._suppress_signals = False

    def set_focus(self):
        """Focus the text editor."""
        self._editor.setFocus()
