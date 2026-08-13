"""Unit tests for the FolderResolver."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.folder_resolver import FolderResolver


class TestFolderResolver(unittest.TestCase):

    def test_normalize_basic_path(self):
        self.assertEqual(
            FolderResolver.normalize("C:\\Users\\Admin\\Documents"),
            "c:/users/admin/documents"
        )

    def test_normalize_trailing_slash(self):
        self.assertEqual(
            FolderResolver.normalize("C:\\Users\\Admin\\Documents\\"),
            "c:/users/admin/documents"
        )

    def test_normalize_file_uri(self):
        self.assertEqual(
            FolderResolver.normalize("file:///C:/Users/Admin/Documents"),
            "c:/users/admin/documents"
        )

    def test_normalize_encoded_uri(self):
        self.assertEqual(
            FolderResolver.normalize("file:///C:/My%20Documents"),
            "c:/my documents"
        )

    def test_normalize_root_drive(self):
        result = FolderResolver.normalize("C:\\")
        self.assertEqual(result, "c:/")

    def test_normalize_empty(self):
        self.assertEqual(FolderResolver.normalize(""), "")

    def test_is_valid_folder_existing(self):
        # Test with a folder that definitely exists
        self.assertTrue(FolderResolver.is_valid_folder(os.environ.get("TEMP", "C:\\Windows")))

    def test_is_valid_folder_nonexistent(self):
        self.assertFalse(FolderResolver.is_valid_folder("Z:\\NonExistent\\Path"))

    def test_is_valid_folder_virtual(self):
        self.assertFalse(FolderResolver.is_valid_folder("This PC"))
        self.assertFalse(FolderResolver.is_valid_folder("::{20D04FE0-3AEA-1069-A2D8-08002B30309D}"))

    def test_is_valid_folder_empty(self):
        self.assertFalse(FolderResolver.is_valid_folder(""))

    def test_get_folder_name(self):
        self.assertEqual(
            FolderResolver.get_folder_name("c:/users/admin/documents"),
            "documents"
        )

    def test_get_folder_name_drive_root(self):
        self.assertEqual(
            FolderResolver.get_folder_name("c:/"),
            "C:\\"
        )

    def test_path_to_windows(self):
        self.assertEqual(
            FolderResolver.path_to_windows("c:/users/admin/documents"),
            "C:\\users\\admin\\documents"
        )


if __name__ == "__main__":
    unittest.main()
