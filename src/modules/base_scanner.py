"""
Base Scanner Interface

Abstract base class for all cleaning module scanners.
All scanner modules must inherit from this class and implement the required methods.
"""

import threading
from abc import ABC, abstractmethod
from typing import Optional
from models.scan_result import ScanResult
from models.file_info import FileInfo
from services.whitelist_service import whitelist_service


class BaseScanner(ABC):
    """
    Abstract base class for all cleaning module scanners.

    This class defines the interface that all scanner modules must implement.
    Each scanner is responsible for finding files in a specific category that
    can potentially be cleaned.
    """

    def __init__(self):
        """Initialize the scanner."""
        pass

    @abstractmethod
    def get_module_name(self) -> str:
        """
        Get the human-readable name of this scanner module.

        Returns:
            Module name in Chinese (e.g., "系统垃圾", "Windows 更新残留")
        """
        pass

    @abstractmethod
    def get_risk_level(self) -> str:
        """
        Get the risk level for files found by this scanner.

        Returns:
            Risk level: "low", "medium", or "high"
        """
        pass

    @abstractmethod
    def scan(self, cancellation_token: threading.Event) -> ScanResult:
        """
        Scan for files in this module's category.

        This method should search for files that belong to this cleaning category,
        respecting the cancellation token and filtering out protected files.

        Args:
            cancellation_token: Event that can be set to cancel the scan

        Returns:
            ScanResult containing all found files and metadata
        """
        pass

    def create_file_info(self, path: str) -> Optional[FileInfo]:
        """
        Create a FileInfo object for the given path.

        This helper method creates FileInfo objects and marks protected files.
        Subclasses should use this method to create FileInfo instances.

        Args:
            path: File system path

        Returns:
            FileInfo instance or None if path is invalid
        """
        # Create FileInfo from path
        file_info = FileInfo.from_path(path, self.get_module_name())

        if file_info is None:
            return None

        # Check if file is protected
        file_info.is_protected = whitelist_service.is_protected(file_info.path)

        return file_info

    def should_skip_file(self, file_info: FileInfo) -> bool:
        """
        Determine if a file should be skipped during scanning.

        Files are skipped if they are:
        - Protected by whitelist
        - Cannot be accessed (permissions)
        - Invalid paths

        Args:
            file_info: File information to check

        Returns:
            True if file should be skipped, False otherwise
        """
        # Skip protected files
        if file_info.is_protected:
            return True

        # Additional checks can be added here by subclasses
        return False

    def filter_files(self, file_infos: list) -> list:
        """
        Filter a list of FileInfo objects, removing files that should be skipped.

        Args:
            file_infos: List of FileInfo objects to filter

        Returns:
            Filtered list containing only valid, non-protected files
        """
        return [fi for fi in file_infos if not self.should_skip_file(fi)]

    def scan_with_progress(self, cancellation_token: threading.Event,
                          progress_callback: Optional[callable] = None) -> ScanResult:
        """
        Scan with progress reporting.

        This method wraps the scan() method and provides progress callbacks.
        Subclasses can override this if they need custom progress reporting.

        Args:
            cancellation_token: Event to cancel the scan
            progress_callback: Optional callback(current_count, total_estimated)

        Returns:
            ScanResult from the scan
        """
        if progress_callback:
            progress_callback(0, 0)  # Indicate scan started

        result = self.scan(cancellation_token)

        if progress_callback:
            progress_callback(len(result.files), len(result.files))  # Indicate scan complete

        return result