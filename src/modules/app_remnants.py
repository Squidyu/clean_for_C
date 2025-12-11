"""
App Remnants Scanner

Scans for leftover directories and files from uninstalled applications.
This includes orphaned program directories, leftover registry entries, and abandoned app data.
"""

import os
import threading
from typing import List, Set
from modules.base_scanner import BaseScanner
from models.file_info import FileInfo
from utils.file_utils import scan_directory_files
from utils.path_utils import validate_c_drive_path


class AppRemnantsScanner(BaseScanner):
    """
    Scanner for application remnants after uninstallation.

    Scans for:
    - Empty directories in Program Files
    - Orphaned application data directories
    - Leftover cache directories from uninstalled apps
    - Abandoned installation directories
    """

    def get_module_name(self) -> str:
        """Get module name."""
        return "应用残留"

    def get_risk_level(self) -> str:
        """Get risk level - medium risk for app remnants."""
        return "medium"

    def scan(self, cancellation_token: threading.Event) -> 'ScanResult':
        """
        Scan for application remnants.

        Searches in:
        - C:\\Program Files and Program Files (x86) for empty directories
        - C:\\Users\\{user}\\AppData for orphaned app data
        - Common installation locations for leftover files

        Args:
            cancellation_token: Event to cancel scanning

        Returns:
            ScanResult with found application remnants
        """
        from models.scan_result import ScanResult

        result = ScanResult(
            module_name=self.get_module_name(),
            risk_level=self.get_risk_level()
        )

        # Scan different locations for remnants
        scan_areas = [
            self._scan_program_files,
            self._scan_appdata_directories,
            self._scan_common_install_dirs
        ]

        for scan_func in scan_areas:
            if cancellation_token.is_set():
                break

            try:
                scan_func(result, cancellation_token)
            except Exception:
                # Continue with other scan areas if one fails
                continue

        return result

    def _scan_program_files(self, result: 'ScanResult', cancellation_token: threading.Event):
        """
        Scan Program Files directories for empty or orphaned directories.

        Args:
            result: ScanResult to add findings to
            cancellation_token: Event to cancel scanning
        """
        program_dirs = ["C:\\Program Files", "C:\\Program Files (x86)"]

        for base_dir in program_dirs:
            if cancellation_token.is_set():
                break

            try:
                if not os.path.exists(base_dir):
                    continue

                validate_c_drive_path(base_dir)

                # Scan for subdirectories
                for item in os.scandir(base_dir):
                    if cancellation_token.is_set():
                        break

                    if item.is_dir():
                        self._analyze_program_directory(item.path, result, cancellation_token)

            except Exception:
                continue

    def _analyze_program_directory(self, dir_path: str, result: 'ScanResult',
                                  cancellation_token: threading.Event):
        """
        Analyze a program directory to determine if it's a remnant.

        Args:
            dir_path: Directory path to analyze
            result: ScanResult to add findings to
            cancellation_token: Event to cancel scanning
        """
        try:
            # Check if directory is empty
            try:
                contents = list(os.scandir(dir_path))
            except (OSError, PermissionError):
                return

            if not contents:
                # Empty directory - add to results
                dir_info = self.create_file_info(dir_path)
                if dir_info and not self.should_skip_file(dir_info):
                    result.add_file(dir_info)
                return

            # Check for directories with only cache/temp files
            cache_only_dirs = self._find_cache_only_directories(dir_path, cancellation_token)
            for cache_dir in cache_only_dirs:
                if cancellation_token.is_set():
                    break

                dir_info = self.create_file_info(cache_dir)
                if dir_info and not self.should_skip_file(dir_info):
                    result.add_file(dir_info)

        except Exception:
            pass

    def _find_cache_only_directories(self, base_path: str, cancellation_token: threading.Event) -> List[str]:
        """
        Find directories that contain only cache/temp files.

        Args:
            base_path: Base path to search
            cancellation_token: Event to cancel scanning

        Returns:
            List of directory paths that contain only cache files
        """
        cache_dirs = []

        try:
            for root, dirs, files in os.walk(base_path):
                if cancellation_token.is_set():
                    break

                # Skip if we've gone too deep (performance)
                if root.count(os.sep) - base_path.count(os.sep) > 3:
                    continue

                # Check if directory contains only cache-like files
                if self._is_cache_only_directory(root, files):
                    cache_dirs.append(root)

        except Exception:
            pass

        return cache_dirs

    def _is_cache_only_directory(self, dir_path: str, files: List[str]) -> bool:
        """
        Determine if a directory contains only cache/temp files.

        Args:
            dir_path: Directory path
            files: List of filenames in the directory

        Returns:
            True if directory appears to contain only cache files
        """
        if not files:
            return False

        cache_extensions = {'.tmp', '.cache', '.log', '.bak', '.old'}
        cache_patterns = ['temp', 'cache', 'tmp', 'log']

        # Check if all files have cache-like names
        for filename in files:
            name_lower = filename.lower()

            # Check extension
            if any(filename.lower().endswith(ext) for ext in cache_extensions):
                continue

            # Check if name contains cache patterns
            if any(pattern in name_lower for pattern in cache_patterns):
                continue

            # If we find a file that doesn't look like cache, directory is not cache-only
            return False

        return True

    def _scan_appdata_directories(self, result: 'ScanResult', cancellation_token: threading.Event):
        """
        Scan AppData directories for orphaned application data.

        Args:
            result: ScanResult to add findings to
            cancellation_token: Event to cancel scanning
        """
        import glob

        appdata_patterns = [
            "C:\\Users\\*\\AppData\\Local\\*",
            "C:\\Users\\*\\AppData\\Roaming\\*"
        ]

        for pattern in appdata_patterns:
            if cancellation_token.is_set():
                break

            try:
                dirs = glob.glob(pattern)

                for app_dir in dirs:
                    if cancellation_token.is_set():
                        break

                    # Check if this looks like orphaned app data
                    if self._is_orphaned_app_directory(app_dir):
                        dir_info = self.create_file_info(app_dir)
                        if dir_info and not self.should_skip_file(dir_info):
                            result.add_file(dir_info)

            except Exception:
                continue

    def _is_orphaned_app_directory(self, dir_path: str) -> bool:
        """
        Check if an AppData directory appears to be from an uninstalled application.

        This is a heuristic check - we look for directories that don't have
        corresponding installed applications.

        Args:
            dir_path: AppData directory path

        Returns:
            True if directory appears orphaned
        """
        try:
            dir_name = os.path.basename(dir_path).lower()

            # Common orphaned app patterns
            orphaned_patterns = [
                'temp', 'tmp', 'cache', 'old', 'backup',
                'uninstall', 'removed', 'deleted'
            ]

            if any(pattern in dir_name for pattern in orphaned_patterns):
                return True

            # Check if directory is empty or very small
            total_size = 0
            file_count = 0

            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    try:
                        total_size += os.path.getsize(os.path.join(root, file))
                        file_count += 1
                        if file_count > 10 or total_size > 1024 * 1024:  # 1MB
                            break
                    except:
                        continue
                if file_count > 10 or total_size > 1024 * 1024:
                    break

            # If directory has very few files and small size, might be remnant
            if file_count <= 2 and total_size < 10 * 1024:  # 10KB
                return True

        except Exception:
            pass

        return False

    def _scan_common_install_dirs(self, result: 'ScanResult', cancellation_token: threading.Event):
        """
        Scan common installation directories for remnants.

        Args:
            result: ScanResult to add findings to
            cancellation_token: Event to cancel scanning
        """
        common_dirs = [
            "C:\\ProgramData",
            "C:\\Users\\Default\\AppData"
        ]

        for base_dir in common_dirs:
            if cancellation_token.is_set():
                break

            try:
                if not os.path.exists(base_dir):
                    continue

                validate_c_drive_path(base_dir)

                # Look for obviously orphaned directories
                for item in os.scandir(base_dir):
                    if cancellation_token.is_set():
                        break

                    if item.is_dir():
                        dir_name = item.name.lower()
                        # Look for directories that look like uninstall remnants
                        if any(keyword in dir_name for keyword in
                              ['uninstall', 'temp', '{', '}', 'remnant', 'leftover']):
                            dir_info = self.create_file_info(item.path)
                            if dir_info and not self.should_skip_file(dir_info):
                                result.add_file(dir_info)

            except Exception:
                continue