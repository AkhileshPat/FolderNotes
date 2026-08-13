"""
Folder path resolver and normalizer for FolderNotes.

Handles path normalization, validation, and edge cases like
network paths, virtual folders, and disconnected drives.
"""

import os
import logging
from urllib.parse import unquote
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class FolderResolver:
    """Normalizes and validates folder paths from Explorer."""

    # Virtual folder CLSIDs that we cannot attach notes to
    VIRTUAL_FOLDERS = {
        "this pc", "quick access", "network", "recycle bin",
        "control panel", "desktop",
        "::{20D04FE0-3AEA-1069-A2D8-08002B30309D}",  # This PC
        "::{645FF040-5081-101B-9F08-00AA002F954E}",  # Recycle Bin
        "::{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}",  # Network
    }

    @staticmethod
    def normalize(path: str) -> str:
        """
        Normalize a folder path for consistent storage and lookup.

        - Converts to lowercase
        - Uses forward slashes
        - Strips trailing slashes
        - Handles file:// URIs
        - Handles URL-encoded characters
        """
        if not path:
            return ""

        # Handle file:// URIs from Shell.Application.LocationURL
        if path.startswith("file:///"):
            path = unquote(path[8:])  # strip 'file:///' and decode %20 etc
        elif path.startswith("file://"):
            path = unquote(path[7:])

        # Normalize separators
        path = path.replace("\\", "/")

        # Strip trailing slash (but keep root like C:/)
        if len(path) > 3 and path.endswith("/"):
            path = path.rstrip("/")

        # Lowercase for consistent lookups
        path = path.lower()

        return path

    @staticmethod
    def is_valid_folder(path: str) -> bool:
        """
        Check if a path is a real, accessible folder we can attach notes to.

        Returns False for:
        - Empty paths
        - Virtual/shell folders (by CLSID or exact name match)
        - Non-existent paths (disconnected drives, deleted folders)
        """
        if not path:
            return False

        normalized = FolderResolver.normalize(path)

        # Check against known virtual folder CLSIDs (substring match is OK for these)
        for vf in FolderResolver.VIRTUAL_FOLDERS:
            if vf.startswith("::") and vf in normalized:
                return False

        # Check if the entire path IS a virtual folder name (exact match only)
        VIRTUAL_NAMES = {"this pc", "quick access", "network", "recycle bin",
                         "control panel"}
        if normalized in VIRTUAL_NAMES:
            return False

        # Check if the path actually exists on disk
        try:
            # Reconstruct a Windows path for os.path.isdir
            win_path = normalized.replace("/", "\\")
            # Handle drive letters: c: -> C:\
            if len(win_path) >= 2 and win_path[1] == ":":
                win_path = win_path[0].upper() + win_path[1:]
            return os.path.isdir(win_path)
        except (OSError, ValueError):
            return False

    @staticmethod
    def get_folder_name(path: str) -> str:
        """Extract the display name from a folder path."""
        if not path:
            return ""
        normalized = FolderResolver.normalize(path)
        parts = normalized.rstrip("/").split("/")
        name = parts[-1] if parts else ""
        # Handle drive roots like "c:"
        if name.endswith(":"):
            name = name.upper() + "\\"
        return name

    @staticmethod
    def path_to_windows(normalized_path: str) -> str:
        """Convert a normalized path back to a Windows path."""
        if not normalized_path:
            return ""
        win_path = normalized_path.replace("/", "\\")
        if len(win_path) >= 2 and win_path[1] == ":":
            win_path = win_path[0].upper() + win_path[1:]
        return win_path
