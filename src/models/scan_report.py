"""
Scan Report Model

Represents a complete scan of the C drive across all cleaning modules.
This aggregates results from all scanners into a unified report.
"""

from typing import List
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from .scan_result import ScanResult
from .file_info import FileInfo


@dataclass
class ScanReport:
    """
    Complete scan report across all cleaning modules.

    This class represents the results of scanning all 8 cleaning modules
    and provides aggregated statistics and access to all found files.
    """

    scan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for this scan."""

    timestamp: datetime = field(default_factory=datetime.now)
    """When the scan was initiated."""

    duration_seconds: float = 0.0
    """Total scan duration across all modules."""

    modules: List[ScanResult] = field(default_factory=list)
    """Results for each of the 8 modules."""

    total_scannable_size: int = 0
    """Total size of all files that can be cleaned."""

    status: str = "pending"
    """Scan status: 'pending', 'in_progress', 'completed', 'cancelled', 'failed'."""

    cancellation_reason: str = ""
    """Reason for cancellation if status is 'cancelled'."""

    def __post_init__(self):
        """Validate scan report after initialization."""
        self._validate()
        self._update_calculated_fields()

    def _validate(self):
        """Validate scan report data."""
        valid_statuses = {"pending", "in_progress", "completed", "cancelled", "failed"}
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {valid_statuses}")

        if self.duration_seconds < 0:
            raise ValueError("Duration cannot be negative")

        if self.total_scannable_size < 0:
            raise ValueError("Total size cannot be negative")

    def _update_calculated_fields(self):
        """Update calculated fields based on modules."""
        self.total_scannable_size = sum(module.total_size for module in self.modules)

    def add_module_result(self, scan_result: ScanResult):
        """
        Add a module scan result to the report.

        Args:
            scan_result: ScanResult from a completed module scan
        """
        if not isinstance(scan_result, ScanResult):
            raise ValueError("Must be a ScanResult instance")

        self.modules.append(scan_result)
        self._update_calculated_fields()

    def get_module_by_name(self, module_name: str) -> ScanResult:
        """
        Get scan result for a specific module.

        Args:
            module_name: Name of the module

        Returns:
            ScanResult for the module

        Raises:
            ValueError: If module not found
        """
        for module in self.modules:
            if module.module_name == module_name:
                return module

        raise ValueError(f"Module not found: {module_name}")

    def get_all_files(self) -> List[FileInfo]:
        """
        Get all files from all modules.

        Returns:
            List of all FileInfo objects from all modules
        """
        all_files = []
        for module in self.modules:
            all_files.extend(module.files)
        return all_files

    def get_files_by_module(self, module_name: str) -> List[FileInfo]:
        """
        Get all files from a specific module.

        Args:
            module_name: Name of the module

        Returns:
            List of FileInfo objects from the specified module
        """
        try:
            module = self.get_module_by_name(module_name)
            return module.files
        except ValueError:
            return []

    def get_files_by_risk_level(self, risk_level: str) -> List[FileInfo]:
        """
        Get all files from modules with a specific risk level.

        Args:
            risk_level: Risk level to filter by ('low', 'medium', 'high')

        Returns:
            List of FileInfo objects from modules with the specified risk level
        """
        files = []
        for module in self.modules:
            if module.risk_level == risk_level:
                files.extend(module.files)
        return files

    def get_total_files_count(self) -> int:
        """
        Get total number of files across all modules.

        Returns:
            Total file count
        """
        return sum(len(module.files) for module in self.modules)

    def get_module_summary(self) -> List[dict]:
        """
        Get summary information for each module.

        Returns:
            List of dicts with module summary info
        """
        return [{
            'name': module.module_name,
            'risk_level': module.risk_level,
            'file_count': module.file_count,
            'total_size': module.total_size,
            'size_display': module.get_display_size()
        } for module in self.modules]

    def is_complete(self) -> bool:
        """
        Check if scan is complete.

        Returns:
            True if all expected modules have completed
        """
        return self.status == "completed" and len(self.modules) >= 8

    def can_clean_safely(self) -> bool:
        """
        Check if all found files can be cleaned safely.

        Returns:
            True if all files are from low-risk modules, False otherwise
        """
        return all(module.risk_level == "low" for module in self.modules if module.files)

    def get_high_risk_modules(self) -> List[ScanResult]:
        """
        Get modules that contain high-risk files.

        Returns:
            List of ScanResult objects for high-risk modules
        """
        return [module for module in self.modules if module.risk_level == "high" and module.files]

    def get_recommended_cleanup_size(self) -> int:
        """
        Get recommended cleanup size (excluding high-risk files).

        Returns:
            Total size of files that can be safely cleaned
        """
        total = 0
        for module in self.modules:
            if module.risk_level != "high":
                total += module.total_size
        return total

    def __str__(self) -> str:
        """String representation for debugging."""
        return (f"ScanReport(id={self.scan_id[:8]}..., "
                f"modules={len(self.modules)}, "
                f"files={self.get_total_files_count()}, "
                f"size={self.total_scannable_size}, "
                f"status={self.status})")

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"ScanReport(scan_id='{self.scan_id}', "
                f"timestamp={self.timestamp}, "
                f"duration_seconds={self.duration_seconds}, "
                f"modules=[{len(self.modules)} modules], "
                f"total_scannable_size={self.total_scannable_size}, "
                f"status='{self.status}')")