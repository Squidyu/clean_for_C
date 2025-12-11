"""
Large Files Scanner

Scans for files larger than a configurable threshold.
This helps users identify and potentially clean up large files that may be taking up significant space.
"""

import os
import threading
from typing import List
from modules.base_scanner import BaseScanner
from models.file_info import FileInfo
from utils.path_utils import validate_c_drive_path, is_within_c_drive
from utils.size_utils import get_recommended_cleanup_threshold


class LargeFilesScanner(BaseScanner):
    """
    Scanner for large files across the C drive.

    Finds files larger than a threshold (default 100MB) that users might want to review.
    This is a more comprehensive scan that recursively searches the entire C drive.
    """

    def __init__(self, size_threshold: int = None):
        """
        Initialize large files scanner.

        Args:
            size_threshold: Minimum file size in bytes (default: 100MB)
        """
        super().__init__()
        self.size_threshold = size_threshold or get_recommended_cleanup_threshold()

    def get_module_name(self) -> str:
        """Get module name."""
        return "大文件扫描"

    def get_risk_level(self) -> str:
        """Get risk level - medium risk for large files (requires user judgment)."""
        return "medium"

    def scan(self, cancellation_token: threading.Event) -> 'ScanResult':
        """
        Scan for large files across C drive.

        Recursively scans C drive looking for files larger than threshold.
        This is a comprehensive but potentially slow scan.

        Args:
            cancellation_token: Event to cancel scanning

        Returns:
            ScanResult with found large files
        """
        from models.scan_result import ScanResult

        result = ScanResult(
            module_name=self.get_module_name(),
            risk_level=self.get_risk_level()
        )

        # Start scanning from C drive root
        self._scan_directory("C:\\", result, cancellation_token)

        return result

    def _scan_directory(self, dir_path: str, result: 'ScanResult',
                       cancellation_token: threading.Event):
        """
        Recursively scan a directory for large files.

        Args:
            dir_path: Directory to scan
            result: ScanResult to add files to
            cancellation_token: Event to cancel scanning
        """
        if cancellation_token.is_set():
            return

        try:
            # Validate path is within C drive
            validate_c_drive_path(dir_path)

            # Get directory contents
            try:
                entries = os.scandir(dir_path)
            except (OSError, PermissionError):
                # Skip inaccessible directories
                return

            with entries:
                for entry in entries:
                    if cancellation_token.is_set():
                        break

                    try:
                        if entry.is_file():
                            # Check file size
                            try:
                                stat = entry.stat()
                                if stat.st_size >= self.size_threshold:
                                    # Create FileInfo for large file
                                    file_info = self.create_file_info(entry.path)
                                    if file_info and not self.should_skip_file(file_info):
                                        result.add_file(file_info)
                            except (OSError, IOError):
                                # Skip files we can't stat
                                continue

                        elif entry.is_dir():
                            # Skip certain system directories to avoid slow scanning
                            dir_name = entry.name.lower()
                            skip_dirs = {
                                'windows', 'program files', 'program files (x86)',
                                'programdata', 'system volume information',
                                '$recycle.bin', '$extend', 'recovery'
                            }

                            if dir_name not in skip_dirs:
                                # Recursively scan subdirectory
                                self._scan_directory(entry.path, result, cancellation_token)

                    except (OSError, IOError):
                        # Skip problematic entries
                        continue

        except Exception:
            # Skip problematic directories
            pass

    def get_size_threshold_mb(self) -> float:
        """
        Get the size threshold in MB for display.

        Returns:
            Threshold in megabytes
        """
        return self.size_threshold / (1024 * 1024)

    def set_size_threshold(self, threshold_bytes: int):
        """
        Set the size threshold for scanning.

        Args:
            threshold_bytes: New threshold in bytes
        """
        self.size_threshold = threshold_bytes

    def should_skip_file(self, file_info: FileInfo) -> bool:
        """
        Override base method for large files specific filtering.

        For large files, we want to be more permissive than base scanner
        since these are user files that might be legitimately large.

        Args:
            file_info: File to check

        Returns:
            True if should skip, False if should include
        """
        # Skip if protected by whitelist
        if file_info.is_protected:
            return True

        # Skip system files that are expected to be large
        path_lower = file_info.path.lower()
        skip_patterns = [
            '\\windows\\', '\\program files', '\\system volume information\\',
            '\\$extend\\', '\\hiberfil.sys', '\\pagefile.sys', '\\swapfile.sys'
        ]

        for pattern in skip_patterns:
            if pattern in path_lower:
                return True

        return False