"""
System Junk Scanner

Scans for Windows temporary files and system junk that can be safely deleted.
This includes temp files, prefetch files, and other system-generated temporary content.
"""

import os
import threading
from typing import List
from modules.base_scanner import BaseScanner
from models.file_info import FileInfo
from utils.file_utils import scan_directory_files
from utils.path_utils import expand_environment_variables, validate_c_drive_path


class SystemJunkScanner(BaseScanner):
    """
    Scanner for Windows system junk files.

    Scans common locations for temporary files that are safe to delete:
    - Windows Temp directory
    - User temp directories
    - Prefetch files
    - Temporary internet files
    """

    def get_module_name(self) -> str:
        """Get module name."""
        return "系统垃圾"

    def get_risk_level(self) -> str:
        """Get risk level - low risk for temp files."""
        return "low"

    def scan(self, cancellation_token: threading.Event) -> 'ScanResult':
        """
        Scan for system junk files.

        Searches in:
        - C:\\Windows\\Temp
        - C:\\Users\\<username>\\AppData\\Local\\Temp
        - C:\\Windows\\Prefetch (if exists)

        Args:
            cancellation_token: Event to cancel scanning

        Returns:
            ScanResult with found temp files
        """
        from models.scan_result import ScanResult

        result = ScanResult(
            module_name=self.get_module_name(),
            risk_level=self.get_risk_level()
        )

        # Define scan locations and patterns
        scan_configs = [
            # Windows system temp
            {
                "path": "C:\\Windows\\Temp",
                "patterns": ["*.tmp", "*.log", "*.cache", "*.tmp.*"]
            },
            # User temp directories
            {
                "path": expand_environment_variables("%TEMP%"),
                "patterns": ["*.tmp", "*.log", "*.cache", "temp_*", "~*"]
            },
            {
                "path": expand_environment_variables("%TMP%"),
                "patterns": ["*.tmp", "*.log", "*.cache", "temp_*", "~*"]
            },
            # Prefetch files (Windows optimization data, safe to delete)
            {
                "path": "C:\\Windows\\Prefetch",
                "patterns": ["*.pf"]  # Prefetch files
            }
        ]

        # Scan each location
        for config in scan_configs:
            if cancellation_token.is_set():
                break

            try:
                path = config["path"]

                # Validate path exists and is within C drive
                if not os.path.exists(path):
                    continue

                validate_c_drive_path(path)

                # Scan for each pattern
                for pattern in config["patterns"]:
                    if cancellation_token.is_set():
                        break

                    try:
                        files = scan_directory_files(path, pattern, recursive=False)
                        for file_path in files:
                            if cancellation_token.is_set():
                                break

                            # Create FileInfo and add to result
                            file_info = self.create_file_info(file_path)
                            if file_info and not self.should_skip_file(file_info):
                                result.add_file(file_info)

                    except Exception:
                        # Skip problematic patterns but continue scanning
                        continue

            except Exception:
                # Skip problematic directories but continue scanning
                continue

        return result