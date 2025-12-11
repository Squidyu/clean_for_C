"""
Scan Result Model

Represents the output of a disk scan operation for a single cleaning module.
This model aggregates file information from a specific scanner module.
"""

from typing import List
from dataclasses import dataclass, field
from datetime import datetime
from .file_info import FileInfo


@dataclass
class ScanResult:
    """
    Result of scanning a specific cleaning module.

    This class represents the output of a single scanner module,
    containing all files found in that category along with summary information.
    """

    module_name: str
    """Name of the cleaning module (e.g., '系统垃圾', 'Windows 更新残留')."""

    risk_level: str
    """Risk level: 'low', 'medium', or 'high'."""

    total_size: int = 0
    """Total size of all files in bytes."""

    file_count: int = 0
    """Number of files found."""

    files: List[FileInfo] = field(default_factory=list)
    """List of files found by this module."""

    scan_timestamp: datetime = field(default_factory=datetime.now)
    """When this scan was performed."""

    scan_duration_seconds: float = 0.0
    """How long the scan took."""

    def __post_init__(self):
        """Validate scan result after initialization."""
        self._validate()
        self._update_calculated_fields()

    def _validate(self):
        """Validate scan result data."""
        # Module name validation
        if not self.module_name:
            raise ValueError("Module name cannot be empty")

        # Risk level validation
        valid_risk_levels = {"low", "medium", "high"}
        if self.risk_level not in valid_risk_levels:
            raise ValueError(f"Invalid risk level: {self.risk_level}. Must be one of {valid_risk_levels}")

        # Size validation
        if self.total_size < 0:
            raise ValueError(f"Total size cannot be negative: {self.total_size}")

        # File count validation
        if self.file_count < 0:
            raise ValueError(f"File count cannot be negative: {self.file_count}")

        # Files validation
        if self.files is None:
            self.files = []

        for file_info in self.files:
            if not isinstance(file_info, FileInfo):
                raise ValueError("All files must be FileInfo instances")

    def _update_calculated_fields(self):
        """Update calculated fields based on file list."""
        self.file_count = len(self.files)
        self.total_size = sum(file.size for file in self.files)

    def add_file(self, file_info: FileInfo):
        """
        Add a file to the scan result.

        Args:
            file_info: FileInfo to add
        """
        if not isinstance(file_info, FileInfo):
            raise ValueError("Must be a FileInfo instance")

        self.files.append(file_info)
        self._update_calculated_fields()

    def remove_file(self, file_info: FileInfo):
        """
        Remove a file from the scan result.

        Args:
            file_info: FileInfo to remove
        """
        self.files.remove(file_info)
        self._update_calculated_fields()

    def get_files_by_size(self, descending: bool = True) -> List[FileInfo]:
        """
        Get files sorted by size.

        Args:
            descending: If True, sort largest first

        Returns:
            List of files sorted by size
        """
        return sorted(self.files, key=lambda f: f.size, reverse=descending)

    def get_files_by_date(self, descending: bool = True) -> List[FileInfo]:
        """
        Get files sorted by last access time.

        Args:
            descending: If True, sort most recent first

        Returns:
            List of files sorted by last access time
        """
        return sorted(self.files, key=lambda f: f.last_access_time, reverse=descending)

    def get_display_size(self) -> str:
        """
        Get human-readable total size.

        Returns:
            Formatted size string (e.g., "1.2 GB")
        """
        size = self.total_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return ".1f"
            size /= 1024.0
        return ".1f"

    def get_risk_display(self) -> str:
        """
        Get human-readable risk level.

        Returns:
            Risk level in Chinese
        """
        risk_map = {
            "low": "低",
            "medium": "中",
            "high": "高"
        }
        return risk_map.get(self.risk_level, self.risk_level)

    def can_clean_safely(self) -> bool:
        """
        Check if this module can be cleaned safely.

        For high-risk modules, this returns False and user confirmation is required.

        Returns:
            True if safe to clean without confirmation, False if confirmation needed
        """
        return self.risk_level != "high"

    def get_summary(self) -> str:
        """
        Get a human-readable summary of the scan result.

        Returns:
            Summary string suitable for display
        """
        return (f"{self.module_name}: {self.file_count} 个文件, "
                f"总大小 {self.get_display_size()}, "
                f"风险等级: {self.get_risk_display()}")

    def filter_by_predicate(self, predicate) -> 'ScanResult':
        """
        Create a new ScanResult with files filtered by predicate.

        Args:
            predicate: Function that takes FileInfo and returns bool

        Returns:
            New ScanResult with filtered files
        """
        filtered_files = [f for f in self.files if predicate(f)]

        result = ScanResult(
            module_name=self.module_name,
            risk_level=self.risk_level,
            scan_timestamp=self.scan_timestamp,
            scan_duration_seconds=self.scan_duration_seconds
        )

        for file_info in filtered_files:
            result.add_file(file_info)

        return result

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"ScanResult(module='{self.module_name}', files={self.file_count}, size={self.get_display_size()})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"ScanResult(module_name='{self.module_name}', "
                f"risk_level='{self.risk_level}', "
                f"total_size={self.total_size}, "
                f"file_count={self.file_count}, "
                f"files=[...{len(self.files)} files...], "
                f"scan_timestamp={self.scan_timestamp}, "
                f"scan_duration_seconds={self.scan_duration_seconds})")