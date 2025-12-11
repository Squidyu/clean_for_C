"""
Cleaning Operation Model

Represents a user-initiated cleaning action with progress tracking and results.
"""

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from .file_info import FileInfo


@dataclass
class CleaningOperation:
    """
    Represents a cleaning operation initiated by the user.

    This class tracks the entire lifecycle of a cleaning operation,
    from initial selection through completion or failure.
    """

    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for this cleaning operation."""

    timestamp: datetime = field(default_factory=datetime.now)
    """When the cleaning operation was initiated."""

    selected_files: List[FileInfo] = field(default_factory=list)
    """Files selected by user for cleaning."""

    selected_modules: List[str] = field(default_factory=list)
    """Module names selected for cleaning."""

    predicted_space_bytes: int = 0
    """Predicted space to be freed (before cleaning)."""

    actual_space_freed_bytes: int = 0
    """Actual space freed (after cleaning)."""

    status: str = "pending"
    """Operation status: 'pending', 'in_progress', 'completed', 'cancelled', 'failed'."""

    progress_percentage: float = 0.0
    """Current progress (0-100)."""

    current_module: str = ""
    """Module currently being cleaned."""

    failed_files: List[FileInfo] = field(default_factory=list)
    """Files that failed to delete."""

    hiberfil_sys_deleted: bool = False
    """Whether hiberfil.sys was deleted in this operation."""

    duration_seconds: float = 0.0
    """How long the operation took."""

    error_messages: List[str] = field(default_factory=list)
    """Any error messages encountered."""

    def __post_init__(self):
        """Validate cleaning operation after initialization."""
        self._validate()

    def _validate(self):
        """Validate cleaning operation data."""
        valid_statuses = {"pending", "in_progress", "completed", "cancelled", "failed"}
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {valid_statuses}")

        if self.progress_percentage < 0 or self.progress_percentage > 100:
            raise ValueError("Progress percentage must be between 0 and 100")

        if self.predicted_space_bytes < 0:
            raise ValueError("Predicted space cannot be negative")

        if self.actual_space_freed_bytes < 0:
            raise ValueError("Actual space freed cannot be negative")

        if self.duration_seconds < 0:
            raise ValueError("Duration cannot be negative")

    def add_selected_file(self, file_info: FileInfo):
        """
        Add a file to the selection.

        Args:
            file_info: File to add
        """
        if file_info not in self.selected_files:
            self.selected_files.append(file_info)
            self._update_calculated_fields()

    def remove_selected_file(self, file_info: FileInfo):
        """
        Remove a file from the selection.

        Args:
            file_info: File to remove
        """
        if file_info in self.selected_files:
            self.selected_files.remove(file_info)
            self._update_calculated_fields()

    def add_selected_module(self, module_name: str):
        """
        Add a module to the selection.

        Args:
            module_name: Module name to add
        """
        if module_name not in self.selected_modules:
            self.selected_modules.append(module_name)

    def remove_selected_module(self, module_name: str):
        """
        Remove a module from the selection.

        Args:
            module_name: Module name to remove
        """
        if module_name in self.selected_modules:
            self.selected_modules.remove(module_name)

    def _update_calculated_fields(self):
        """Update calculated fields based on selected files."""
        self.predicted_space_bytes = sum(f.size for f in self.selected_files)

    def add_failed_file(self, file_info: FileInfo, error_message: str = ""):
        """
        Add a file that failed to delete.

        Args:
            file_info: File that failed
            error_message: Error message (optional)
        """
        self.failed_files.append(file_info)
        if error_message:
            self.error_messages.append(f"{file_info.path}: {error_message}")

    def update_progress(self, percentage: float, current_module: str = ""):
        """
        Update operation progress.

        Args:
            percentage: Progress percentage (0-100)
            current_module: Module currently being processed
        """
        self.progress_percentage = min(100.0, max(0.0, percentage))
        if current_module:
            self.current_module = current_module

    def mark_completed(self, actual_space_freed: int, duration: float):
        """
        Mark the operation as completed.

        Args:
            actual_space_freed: Actual space freed in bytes
            duration: Operation duration in seconds
        """
        self.status = "completed"
        self.actual_space_freed_bytes = actual_space_freed
        self.duration_seconds = duration
        self.progress_percentage = 100.0

    def mark_failed(self, error_message: str = ""):
        """
        Mark the operation as failed.

        Args:
            error_message: Error message explaining the failure
        """
        self.status = "failed"
        if error_message:
            self.error_messages.append(error_message)

    def mark_cancelled(self, reason: str = "User cancelled"):
        """
        Mark the operation as cancelled.

        Args:
            reason: Reason for cancellation
        """
        self.status = "cancelled"
        self.error_messages.append(f"Operation cancelled: {reason}")

    def is_completed(self) -> bool:
        """Check if operation is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if operation failed."""
        return self.status == "failed"

    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self.status == "cancelled"

    def is_in_progress(self) -> bool:
        """Check if operation is in progress."""
        return self.status == "in_progress"

    def get_success_rate(self) -> float:
        """
        Get the success rate of file deletion.

        Returns:
            Success rate as percentage (0-100)
        """
        total_files = len(self.selected_files)
        if total_files == 0:
            return 100.0

        successful_files = total_files - len(self.failed_files)
        return (successful_files / total_files) * 100.0

    def get_cleaning_summary(self) -> dict:
        """
        Get a summary of the cleaning operation.

        Returns:
            Dict with operation summary
        """
        return {
            'operation_id': self.operation_id,
            'status': self.status,
            'files_selected': len(self.selected_files),
            'files_failed': len(self.failed_files),
            'predicted_space': self.predicted_space_bytes,
            'actual_space_freed': self.actual_space_freed_bytes,
            'duration_seconds': self.duration_seconds,
            'success_rate': self.get_success_rate(),
            'hiberfil_deleted': self.hiberfil_sys_deleted,
            'progress_percentage': self.progress_percentage,
            'current_module': self.current_module
        }

    def __str__(self) -> str:
        """String representation for debugging."""
        return (f"CleaningOperation(id={self.operation_id[:8]}..., "
                f"status={self.status}, "
                f"files={len(self.selected_files)}, "
                f"progress={self.progress_percentage:.1f}%)")

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"CleaningOperation(operation_id='{self.operation_id}', "
                f"timestamp={self.timestamp}, "
                f"selected_files=[{len(self.selected_files)} files], "
                f"status='{self.status}', "
                f"progress_percentage={self.progress_percentage}, "
                f"actual_space_freed_bytes={self.actual_space_freed_bytes})")