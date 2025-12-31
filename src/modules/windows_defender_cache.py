"""
Windows Defender Cache Scanner

Scans for Windows Defender cache files (Windows 10/11).
These are temporary files created by Windows Defender during scans.
"""

import os
import threading
import time
from modules.base_scanner import BaseScanner
from models.scan_result import ScanResult
from models.file_info import FileInfo
from utils.file_utils import scan_directory_files
from utils.path_utils import expand_environment_variables, validate_c_drive_path
from utils.system_info import system_info, WindowsVersion


class WindowsDefenderCacheScanner(BaseScanner):
    """
    Scanner for Windows Defender cache files.
    
    Only available on Windows 10/11.
    Scans for:
    - Windows Defender scan cache
    - Windows Defender offline scan cache
    - Windows Defender definition updates cache
    """

    def get_module_name(self) -> str:
        """Get module name."""
        return "Windows Defender 缓存"

    def get_risk_level(self) -> str:
        """Get risk level - low risk for cache files."""
        return "low"

    def scan(self, cancellation_token: threading.Event) -> ScanResult:
        """
        Scan for Windows Defender cache files.
        
        Args:
            cancellation_token: Event to cancel scanning
            
        Returns:
            ScanResult with found cache files
        """
        result = ScanResult(
            module_name=self.get_module_name(),
            risk_level=self.get_risk_level()
        )

        # Only scan on Windows 10/11
        if not system_info.supports_windows_defender_offline_scan_cache():
            result.error_message = "当前 Windows 版本不支持 Windows Defender 缓存清理"
            return result

        try:
            # Windows Defender cache locations
            cache_paths = [
                # Windows Defender scan cache
                "C:\\ProgramData\\Microsoft\\Windows Defender\\Scans\\FilesStash",
                "C:\\ProgramData\\Microsoft\\Windows Defender\\Scans\\History",
                
                # Windows Defender definition cache (old definitions)
                "C:\\ProgramData\\Microsoft\\Windows Defender\\Definition Updates",
                
                # Windows Defender offline scan cache (Windows 10/11)
                "C:\\ProgramData\\Microsoft\\Windows Defender\\Support",
            ]

            # User-specific Defender cache (if exists)
            local_appdata = expand_environment_variables("%LOCALAPPDATA%")
            if local_appdata:
                user_defender_path = os.path.join(local_appdata, "Microsoft", "Windows Defender")
                if os.path.exists(user_defender_path):
                    cache_paths.append(user_defender_path)

            # Scan each location
            for cache_path in cache_paths:
                if cancellation_token.is_set():
                    break

                if not os.path.exists(cache_path):
                    continue

                try:
                    validate_c_drive_path(cache_path)
                    
                    # Scan for cache files
                    files = scan_directory_files(cache_path, "*", recursive=True)
                    
                    current_time = time.time()
                    for file_path in files:
                        if cancellation_token.is_set():
                            break

                        # Skip files modified in last 7 days (might be in use)
                        try:
                            file_mtime = os.path.getmtime(file_path)
                            if current_time - file_mtime < 7 * 86400:  # 7 days
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
            result.error_message = f"扫描 Windows Defender 缓存时出错: {e}"

        return result

