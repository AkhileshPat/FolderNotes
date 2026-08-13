"""
Settings manager for FolderNotes.

JSON-based persistent settings.
"""

import json
import os
import logging
from typing import Any, Dict

from src.constants import SETTINGS_PATH, APP_DATA_DIR

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    "start_with_windows": False,
    "overlay_opacity": 0.95,
    "overlay_width": 320,
    "overlay_height": 280,
    "show_notifications": True,
    "theme": "yellow",  # Reserved for future themes
}


class Settings:
    """JSON-based settings manager with auto-save."""

    def __init__(self, path: str = SETTINGS_PATH):
        self._path = path
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """Load settings from disk, creating defaults if missing."""
        os.makedirs(os.path.dirname(self._path), exist_ok=True)

        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                logger.info("Settings loaded from %s", self._path)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load settings, using defaults: %s", e)
                self._data = dict(DEFAULT_SETTINGS)
                self._save()
        else:
            self._data = dict(DEFAULT_SETTINGS)
            self._save()
            logger.info("Created default settings at %s", self._path)

    def _save(self):
        """Persist current settings to disk."""
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except IOError as e:
            logger.error("Failed to save settings: %s", e)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value and auto-save."""
        self._data[key] = value
        self._save()

    @property
    def data(self) -> Dict[str, Any]:
        return dict(self._data)
