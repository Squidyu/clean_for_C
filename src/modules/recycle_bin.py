"""
Recycle Bin Scanner

Scans for files in the Windows Recycle Bin.
These are files that have already been "deleted" by users but are recoverable.
"""

import os
import threading
from modules.base_scanner import BaseScanner
from models.file_info import FileInfo
from utils.file_utils import scan_directory_files
from utils.path_utils import validate_c_drive_path


class RecycleBinScanner(BaseScanner):
    """
    Scanner for Windows Recycle Bin contents.

    The Recycle Bin contains files that users have deleted but can still recover.
    These files are safe to permanently delete as they are already "gone" from user perspective.
    """

    def get_module_name(self) -> str:
        """Get module name."""
        return "回收站"

    def get_risk_level(self) -> str:
        """Get risk level - low risk for recycle bin files."""
        return "low"

    def scan(self, cancellation_token: threading.Event) -> 'ScanResult':
        """
        Scan for files in Recycle Bin.

        Searches in C:\\$Recycle.Bin for all user recycle bins.
        The Recycle Bin structure is: $Recycle.Bin\\{SID}\\{files}

        Args:
            cancellation_token: Event to cancel scanning

        Returns:
            ScanResult with found recycle bin files
        """
        from models.scan_result import ScanResult

        result = ScanResult(
            module_name=self.get_module_name(),
            risk_level=self.get_risk_level()
        )

        recycle_bin_path = "C:\\$Recycle.Bin"

        try:
            # Check if recycle bin exists
            if not os.path.exists(recycle_bin_path):
                return result

            # Validate path
            validate_c_drive_path(recycle_bin_path)

            # Get all user SID directories in recycle bin
            try:
                sid_dirs = [d for d in os.listdir(recycle_bin_path)
                           if os.path.isdir(os.path.join(recycle_bin_path, d))]
            except (OSError, PermissionError):
                return result

            # Scan each user's recycle bin
            for sid_dir in sid_dirs:
                if cancellation_token.is_set():
                    break

                user_recycle_path = os.path.join(recycle_bin_path, sid_dir)

                try:
                    # Scan for all files in this user's recycle bin
                    files = scan_directory_files(user_recycle_path, "*", recursive=True)

                    for file_path in files:
                        if cancellation_token.is_set():
                            break

                        # Create FileInfo and add to result
                        file_info = self.create_file_info(file_path)
                        if file_info:
                            # Recycle bin files are safe to delete (user already deleted them)
                            file_info.is_protected = False
                            if not self.should_skip_file(file_info):
                                result.add_file(file_info)

                except (OSError, PermissionError):
                    # Skip inaccessible user recycle bins
                    continue

        except Exception:
            # If recycle bin scanning fails entirely, return empty result
            pass

        return result

    def should_skip_file(self, file_info: FileInfo) -> bool:
        """
        Override base method for recycle bin specific filtering.

        Recycle bin files are generally safe to delete since they're already
        "deleted" from user perspective. We override whitelist protection for
        recycle bin files.

        Args:
            file_info: File to check

        Returns:
            True if should skip, False if should include
        """
        # Recycle bin files are safe to delete since they're already "deleted"
        # We override whitelist protection for recycle bin content
        if file_info.path.lower().startswith("c:\\$recycle.bin"):
            return False
        
        # For other files, use the default whitelist protection
        return file_info.is_protected