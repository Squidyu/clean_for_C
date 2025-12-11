"""
Path Utilities

Utility functions for path validation, normalization, and manipulation.
Provides safe path handling for Windows file system operations.
"""

import os
import re
from typing import List, Optional, Set


def normalize_path(path: str) -> str:
    """
    Normalize a file system path.

    Args:
        path: Path to normalize

    Returns:
        Normalized path with consistent separators and resolved relative components
    """
    if not path:
        return path

    # Normalize separators and resolve relative components
    normalized = os.path.normpath(path)

    # Ensure consistent separator (Windows backslash)
    normalized = normalized.replace('/', '\\')

    return normalized


def ensure_absolute_path(path: str) -> str:
    """
    Ensure a path is absolute.

    Args:
        path: Path to convert to absolute

    Returns:
        Absolute path

    Raises:
        ValueError: If path cannot be made absolute
    """
    if not path:
        raise ValueError("Path cannot be empty")

    if not os.path.isabs(path):
        path = os.path.abspath(path)

    return normalize_path(path)


def is_within_drive(path: str, drive: str = "C:") -> bool:
    """
    Check if a path is within a specific drive.

    Args:
        path: Path to check
        drive: Drive letter with colon (e.g., "C:")

    Returns:
        True if path is within the specified drive
    """
    try:
        normalized_path = normalize_path(path)
        return normalized_path.upper().startswith(drive.upper())
    except:
        return False


def is_within_c_drive(path: str) -> bool:
    """
    Check if a path is within C drive.

    Args:
        path: Path to check

    Returns:
        True if path is within C drive
    """
    return is_within_drive(path, "C:")


def validate_c_drive_path(path: str) -> str:
    """
    Validate and normalize a C drive path.

    Args:
        path: Path to validate

    Returns:
        Normalized absolute path within C drive

    Raises:
        ValueError: If path is invalid or outside C drive
    """
    if not path:
        raise ValueError("Path cannot be empty")

    try:
        abs_path = ensure_absolute_path(path)

        if not is_within_c_drive(abs_path):
            raise ValueError(f"Path must be within C drive: {path}")

        # Additional Windows-specific validation
        if abs_path.startswith("C:\\$"):  # System metadata
            raise ValueError(f"System metadata paths not allowed: {path}")

        return abs_path

    except Exception as e:
        raise ValueError(f"Invalid path '{path}': {e}")


def get_parent_directory(path: str) -> Optional[str]:
    """
    Get the parent directory of a path.

    Args:
        path: Path to get parent of

    Returns:
        Parent directory path, or None if no parent
    """
    try:
        parent = os.path.dirname(normalize_path(path))
        return parent if parent and parent != path else None
    except:
        return None


def get_directory_depth(path: str) -> int:
    """
    Get the directory depth of a path (number of path separators).

    Args:
        path: Path to analyze

    Returns:
        Directory depth (0 for root, 1 for immediate children, etc.)
    """
    try:
        normalized = normalize_path(path)
        # Remove drive letter
        if ':' in normalized:
            normalized = normalized.split(':', 1)[1]

        # Count directory separators
        return normalized.count('\\')
    except:
        return 0


def is_system_path(path: str) -> bool:
    """
    Check if a path is a Windows system path.

    Args:
        path: Path to check

    Returns:
        True if path is a system directory or file
    """
    try:
        from utils.system_info import system_info, SystemPaths
        
        normalized = normalize_path(path).upper()
        version = system_info.get_windows_version()
        
        # Get version-specific system paths
        system_paths = SystemPaths.get_system_paths(version)
        system_paths_upper = [p.upper() for p in system_paths]

        # Check exact matches
        if normalized in system_paths_upper:
            return True

        # Check if path starts with system directories
        for system_path in system_paths_upper:
            if normalized.startswith(system_path + "\\"):
                return True

        return False

    except:
        # Fallback to basic detection
        try:
            normalized = normalize_path(path).upper()

            system_paths = {
                "C:\\WINDOWS",
                "C:\\WINDOWS\\SYSTEM32",
                "C:\\WINDOWS\\SYSWOW64",
                "C:\\WINDOWS\\WINSXS",
                "C:\\PROGRAM FILES",
                "C:\\PROGRAM FILES (X86)",
                "C:\\PROGRAM FILES\\WINDOWSAPPS"
            }

            # Check exact matches
            if normalized in system_paths:
                return True

            # Check if path starts with system directories
            for system_path in system_paths:
                if normalized.startswith(system_path + "\\"):
                    return True

            return False
        except:
            return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename safe for Windows filesystem
    """
    if not filename:
        return filename

    # Windows invalid characters: < > : " | ? * \ /
    invalid_chars = '<>:"|?*\\/'

    # Replace invalid characters with underscores
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')

    # Ensure not empty and not reserved name
    if not sanitized:
        sanitized = "unnamed"

    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }

    if sanitized.upper() in reserved_names:
        sanitized += "_file"

    return sanitized


def split_path_components(path: str) -> List[str]:
    """
    Split a path into its components.

    Args:
        path: Path to split

    Returns:
        List of path components (drive, directories, filename)
    """
    try:
        normalized = normalize_path(path)
        return normalized.split('\\')
    except:
        return []


def get_file_extension(path: str) -> str:
    """
    Get the file extension from a path.

    Args:
        path: Path to analyze

    Returns:
        File extension (lowercase, without dot) or empty string
    """
    try:
        _, ext = os.path.splitext(path)
        return ext.lower().lstrip('.')
    except:
        return ""


def is_hidden_path(path: str) -> bool:
    """
    Check if a path represents a hidden file or directory.

    Args:
        path: Path to check

    Returns:
        True if path is hidden (starts with dot or has hidden attribute)
    """
    try:
        normalized = normalize_path(path)

        # Check for dot files/directories
        components = split_path_components(normalized)
        if any(comp.startswith('.') for comp in components):
            return True

        # Check for Windows hidden attribute (if file exists)
        if os.path.exists(path):
            import stat
            st = os.stat(path)
            return bool(st.st_file_attributes & 2)  # FILE_ATTRIBUTE_HIDDEN

        return False

    except:
        return False


def get_safe_display_path(path: str, max_length: int = 60) -> str:
    """
    Get a safe display version of a path (truncated if too long).

    Args:
        path: Path to display
        max_length: Maximum display length

    Returns:
        Display-safe path string
    """
    try:
        normalized = normalize_path(path)

        if len(normalized) <= max_length:
            return normalized

        # Truncate middle
        prefix_len = max_length // 2 - 2
        suffix_len = max_length // 2 - 2

        prefix = normalized[:prefix_len]
        suffix = normalized[-suffix_len:]

        return f"{prefix}...{suffix}"

    except:
        return "<invalid path>"


def expand_environment_variables(path: str) -> str:
    """
    Expand environment variables in a path.

    Args:
        path: Path with environment variables (e.g., "%USERPROFILE%\\Desktop")

    Returns:
        Path with environment variables expanded
    """
    try:
        return os.path.expandvars(path)
    except:
        return path


def get_known_folder_path(folder_name: str) -> Optional[str]:
    """
    Get the path of a known Windows folder.

    Args:
        folder_name: Name of known folder (e.g., "Desktop", "Documents")

    Returns:
        Path to the folder, or None if not found
    """
    try:
        import ctypes
        from ctypes import wintypes, windll

        # Known folder GUIDs
        FOLDERID_Desktop = "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}"
        FOLDERID_Documents = "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}"
        FOLDERID_Downloads = "{374DE290-123F-4565-9164-39C4925E467B}"
        FOLDERID_AppData = "{3EB685DB-65F9-4CF6-A03A-E3EF65729F3D}"

        folders = {
            "desktop": FOLDERID_Desktop,
            "documents": FOLDERID_Documents,
            "downloads": FOLDERID_Downloads,
            "appdata": FOLDERID_AppData,
        }

        folder_guid = folders.get(folder_name.lower())
        if not folder_guid:
            return None

        # Call SHGetKnownFolderPath
        path_ptr = wintypes.LPWSTR()
        if windll.shell32.SHGetKnownFolderPath(folder_guid, 0, None, ctypes.byref(path_ptr)) == 0:
            path = path_ptr.value
            windll.ole32.CoTaskMemFree(path_ptr)
            return path

        return None

    except:
        # Fallback to environment variables
        fallbacks = {
            "desktop": "%USERPROFILE%\\Desktop",
            "documents": "%USERPROFILE%\\Documents",
            "downloads": "%USERPROFILE%\\Downloads",
            "appdata": "%APPDATA%"
        }

        fallback = fallbacks.get(folder_name.lower())
        if fallback:
            return expand_environment_variables(fallback)

        return None