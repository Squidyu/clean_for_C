"""
Hibernation File Info Model

Represents information about the Windows hibernation file (hiberfil.sys).
This file is special as it affects system power management.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class HibernationFileInfo:
    """
    Information about the Windows hibernation file.

    This class provides detailed information about hiberfil.sys,
    which is used for Windows hibernation (sleep) functionality.
    """

    file_path: str = "C:\\hiberfil.sys"
    """Path to the hibernation file."""

    file_size_bytes: int = 0
    """Size of the hibernation file in bytes."""

    exists: bool = False
    """Whether the hibernation file exists."""

    hibernation_enabled: bool = True
    """Whether hibernation is currently enabled in Windows."""

    risk_level: str = "high"
    """Risk level (always 'high' for hibernation file)."""

    impact_description: str = ""
    """Description of what happens if the file is deleted."""

    can_delete: bool = False
    """Whether the file can be safely deleted."""

    last_checked: datetime = None
    """When this information was last checked."""

    def __post_init__(self):
        """Initialize defaults."""
        if self.last_checked is None:
            self.last_checked = datetime.now()

        if not self.impact_description:
            self.impact_description = ("删除休眠文件将导致：\n"
                                     "• 无法使用休眠功能\n"
                                     "• Fast Startup 将被关闭\n"
                                     "• 系统开机时间可能稍长")

    def check_hibernation_status(self) -> bool:
        """
        Check current hibernation status.

        Returns:
            True if hibernation is enabled, False otherwise
        """
        try:
            import subprocess
            # Run powercfg /a to check hibernation availability
            result = subprocess.run(['powercfg', '/a'],
                                  capture_output=True, text=True, timeout=10)

            # Parse output to check if hibernation is available
            output = result.stdout.lower()
            self.hibernation_enabled = 'hibernation' in output and 'available' in output
            return self.hibernation_enabled

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # If command fails, assume hibernation is enabled
            self.hibernation_enabled = True
            return True

    def update_file_info(self):
        """
        Update file information from filesystem.
        """
        import os
        try:
            if os.path.exists(self.file_path):
                stat = os.stat(self.file_path)
                self.file_size_bytes = stat.st_size
                self.exists = True
                self.can_delete = True  # Can delete if it exists
            else:
                self.file_size_bytes = 0
                self.exists = False
                self.can_delete = False

        except (OSError, IOError):
            self.file_size_bytes = 0
            self.exists = False
            self.can_delete = False

        self.last_checked = datetime.now()

    def refresh(self):
        """
        Refresh all hibernation-related information.
        """
        self.update_file_info()
        self.check_hibernation_status()

    def get_display_info(self) -> dict:
        """
        Get information suitable for display.

        Returns:
            Dict with display-friendly information
        """
        from utils.size_utils import format_bytes

        return {
            'file_path': self.file_path,
            'file_size': format_bytes(self.file_size_bytes),
            'file_size_bytes': self.file_size_bytes,
            'exists': self.exists,
            'hibernation_enabled': self.hibernation_enabled,
            'risk_level': self.risk_level,
            'impact_description': self.impact_description,
            'can_delete': self.can_delete,
            'last_checked': self.last_checked.strftime("%Y-%m-%d %H:%M:%S") if self.last_checked else "未知"
        }

    def is_ready_for_deletion(self) -> bool:
        """
        Check if hibernation file is ready for deletion.

        Returns:
            True if file exists and hibernation can be disabled
        """
        return self.exists and self.can_delete

    def __str__(self) -> str:
        """String representation."""
        status = "存在" if self.exists else "不存在"
        enabled = "启用" if self.hibernation_enabled else "禁用"
        return f"HibernationFileInfo(文件{status}, 休眠{enabled}, 大小={self.file_size_bytes})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"HibernationFileInfo(file_path='{self.file_path}', "
                f"file_size_bytes={self.file_size_bytes}, "
                f"exists={self.exists}, "
                f"hibernation_enabled={self.hibernation_enabled}, "
                f"can_delete={self.can_delete})")
