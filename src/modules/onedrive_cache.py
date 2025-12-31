"""
OneDrive Cache Scanner

Scans for Microsoft OneDrive cache files.
These are temporary files created by OneDrive sync.
"""

import os
import threading
import time
from modules.base_scanner import BaseScanner
from models.scan_result import ScanResult
from models.file_info import FileInfo
from utils.file_utils import scan_directory_files
from utils.path_utils import expand_environment_variables, validate_c_drive_path


class OneDriveCacheScanner(BaseScanner):
    """
    Scanner for Microsoft OneDrive cache files.
    
    Scans for:
    - OneDrive sync cache
    - OneDrive temporary files
    - OneDrive offline files cache
    """

    def get_module_name(self) -> str:
        """Get module name."""
        return "OneDrive 缓存"

    def get_risk_level(self) -> str:
        """Get risk level - low risk for cache files."""
        return "low"

    def scan(self, cancellation_token: threading.Event) -> ScanResult:
        """
        Scan for OneDrive cache files.
        
        Args:
            cancellation_token: Event to cancel scanning
            
        Returns:
            ScanResult with found cache files
        """
        result = ScanResult(
            module_name=self.get_module_name(),
            risk_level=self.get_risk_level()
        )

        try:
            # OneDrive cache locations
            cache_paths = []
            
            # User-specific OneDrive cache
            local_appdata = expand_environment_variables("%LOCALAPPDATA%")
            if local_appdata:
                onedrive_path = os.path.join(local_appdata, "Microsoft", "OneDrive")
                if os.path.exists(onedrive_path):
                    cache_paths.extend([
                        os.path.join(onedrive_path, "logs"),
                        os.path.join(onedrive_path, "cache"),
                        os.path.join(onedrive_path, "temp"),
                    ])
            
            # OneDrive sync cache (in user's OneDrive folder)
            appdata = expand_environment_variables("%APPDATA%")
            if appdata:
                onedrive_sync = os.path.join(appdata, "Microsoft", "OneDrive", "logs")
                if os.path.exists(onedrive_sync):
                    cache_paths.append(onedrive_sync)

            # If no OneDrive paths exist, return empty result
            if not cache_paths:
                return result

            # Scan each location
            current_time = time.time()
            for cache_path in cache_paths:
                if cancellation_token.is_set():
                    break

                if not os.path.exists(cache_path):
                    continue

                try:
                    validate_c_drive_path(cache_path)
                    
                    # Scan for cache files
                    files = scan_directory_files(cache_path, "*", recursive=True)
                    
                    for file_path in files:
                        if cancellation_token.is_set():
                            break

                        # Skip files modified in last 24 hours (might be in use)
                        try:
                            file_mtime = os.path.getmtime(file_path)
                            if current_time - file_mtime < 86400:  # 24 hours
                                continue
                        except Exception:
                            pass

                        # Create FileInfo and add to result
                        file_info = self.create_file_info(file_path)
                        if file_info and not self.should_skip_file(file_info):
                            file_info.module = self.get_module_name()
                            result.add_file(file_info)

                except Exception as e:
                    # Skip problematic directories but continue scanning
                    continue

        except Exception as e:
            result.error_message = f"扫描 OneDrive 缓存时出错: {e}"

        return result

