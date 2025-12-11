"""
File Information Model

Represents detailed information about a file that can be cleaned.
This model captures all necessary file metadata for display and processing.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime
import os


@dataclass
class FileInfo:
    """
    Detailed information about a file.

    This class represents a file that has been identified by a scanner module
    and may be presented to the user for cleaning. It contains all metadata
    needed for display, validation, and processing.
    """

    path: str
    """Absolute file system path to the file."""

    size: int
    """File size in bytes."""

    last_access_time: datetime
    """Last time the file was accessed."""

    last_modified_time: datetime
    """Last time the file was modified."""

    is_directory: bool = False
    """Whether this is a directory (for recursive cleaning)."""

    is_protected: bool = False
    """Whether file is protected by whitelist (computed, not stored)."""

    module: str = ""
    """Which cleaning module identified this file."""

    def __post_init__(self):
        """Validate file information after initialization."""
        self._validate()

    def _validate(self):
        """Validate file information."""
        # Path validation
        if not self.path:
            raise ValueError("Path cannot be empty")

        if not os.path.isabs(self.path):
            raise ValueError(f"Path must be absolute: {self.path}")

        # Ensure path is within C drive
        if not self.path.upper().startswith("C:\\"):
            raise ValueError(f"Path must be within C drive: {self.path}")

        # Size validation
        if self.size < 0:
            raise ValueError(f"Size cannot be negative: {self.size}")

        # Timestamp validation
        if self.last_access_time > datetime.now():
            raise ValueError("Last access time cannot be in the future")

        if self.last_modified_time > datetime.now():
            raise ValueError("Last modified time cannot be in the future")

    @classmethod
    def from_path(cls, path: str, module: str = "") -> Optional['FileInfo']:
        """
        Create FileInfo from a file system path.

        Args:
            path: Absolute path to the file
            module: Scanner module that identified this file

        Returns:
            FileInfo instance or None if path doesn't exist or is invalid
        """
        try:
            if not os.path.exists(path):
                return None

            stat = os.stat(path)

            return cls(
                path=path,
                size=stat.st_size,
                last_access_time=datetime.fromtimestamp(stat.st_atime),
                last_modified_time=datetime.fromtimestamp(stat.st_mtime),
                is_directory=os.path.isdir(path),
                module=module
            )

        except (OSError, ValueError, OverflowError):
            # File may be inaccessible or have invalid metadata
            return None

    def get_display_size(self) -> str:
        """
        Get human-readable file size string.

        Returns:
            Formatted size string (e.g., "1.2 MB", "45.6 KB")
        """
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return ".1f"
            size /= 1024.0
        return ".1f"

    def get_display_path(self) -> str:
        """
        Get display-friendly path (truncated if too long).

        Returns:
            Path string suitable for display
        """
        max_length = 80
        if len(self.path) <= max_length:
            return self.path

        # Truncate middle of path
        prefix = self.path[:30]
        suffix = self.path[-30:]
        return f"{prefix}...{suffix}"

    def get_last_access_display(self) -> str:
        """
        Get formatted last access time.

        Returns:
            Formatted datetime string
        """
        return self.last_access_time.strftime("%Y-%m-%d %H:%M")

    def get_last_modified_display(self) -> str:
        """
        Get formatted last modified time.

        Returns:
            Formatted datetime string
        """
        return self.last_modified_time.strftime("%Y-%m-%d %H:%M")

    def can_delete(self) -> bool:
        """
        Check if this file can be safely deleted.

        Returns:
            True if file can be deleted, False otherwise
        """
        # Protected files cannot be deleted
        if self.is_protected:
            return False

        # Additional safety checks can be added here
        # e.g., check file age, type, etc.

        return True

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"FileInfo(path='{self.get_display_path()}', size={self.get_display_size()}, protected={self.is_protected})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"FileInfo(path='{self.path}', size={self.size}, "
                f"last_access={self.last_access_time}, "
                f"last_modified={self.last_modified_time}, "
                f"is_directory={self.is_directory}, "
                f"is_protected={self.is_protected}, "
                f"module='{self.module}')")