"""
Windows Store Cache Scanner

Scans for Windows Store (UWP) application cache files.
These are cache files created by UWP applications from Microsoft Store.
"""

import os
import threading
from modules.base_scanner import BaseScanner
from models.scan_result import ScanResult
from models.file_info import FileInfo
from utils.file_utils import scan_directory_files
from utils.path_utils import expand_environment_variables, validate_c_drive_path
from utils.system_info import system_info, WindowsVersion


class WindowsStoreCacheScanner(BaseScanner):
    """
    Scanner for Windows Store (UWP) cache files.
    
    Scans for:
    - Windows Store app cache
    - UWP application cache
    - Windows Store download cache
    """

    def get_module_name(self) -> str:
        """Get module name."""
        return "Windows Store 缓存"

    def get_risk_level(self) -> str:
        """Get risk level - low risk for cache files."""
        return "low"

    def scan(self, cancellation_token: threading.Event) -> ScanResult:
        """
        Scan for Windows Store cache files.
        
        Args:
            cancellation_token: Event to cancel scanning
            
        Returns:
            ScanResult with found cache files
        """
        result = ScanResult(
            module_name=self.get_module_name(),
            risk_level=self.get_risk_level()
        )

        # Only scan on Windows 8/8.1/10/11 (Windows Store available)
        if not system_info.supports_feature('windows_store'):
            result.error_message = "当前 Windows 版本不支持 Windows Store"
            return result

        try:
            # Windows Store cache locations
            cache_paths = []
            
            # System-wide Store cache
            programdata = expand_environment_variables("%ProgramData%")
            if programdata:
                cache_paths.extend([
                    os.path.join(programdata, "Microsoft", "Windows", "AppRepository"),
                    os.path.join(programdata, "Packages"),
                ])

            # User-specific Store cache
            local_appdata = expand_environment_variables("%LOCALAPPDATA%")
            if local_appdata:
                cache_paths.extend([
                    os.path.join(local_appdata, "Packages"),
                    os.path.join(local_appdata, "Microsoft", "Windows", "INetCache"),
                    os.path.join(local_appdata, "Microsoft", "Windows", "WebCache"),
                ])

            # Scan each location
            for cache_path in cache_paths:
                if cancellation_token.is_set():
                    break

                if not os.path.exists(cache_path):
                    continue

                try:
                    validate_c_drive_path(cache_path)
                    
                    # Look for cache directories
                    for root, dirs, files in os.walk(cache_path):
                        if cancellation_token.is_set():
                            break
                        
                        # Look for cache directories
                        for dir_name in dirs:
                            if cancellation_token.is_set():
                                break
                            
                            # Common cache directory names
                            if any(keyword in dir_name.lower() for keyword in ['cache', 'temp', 'localcache', 'ac', 'local state']):
                                dir_path = os.path.join(root, dir_name)
                                try:
                                    files_in_dir = scan_directory_files(dir_path, "*", recursive=True)
                                    for file_path in files_in_dir:
                                        if cancellation_token.is_set():
                                            break
                                        file_info = self.create_file_info(file_path)
                                        if file_info and not self.should_skip_file(file_info):
                                            file_info.module = self.get_module_name()
                                            result.add_file(file_info)
                                except Exception:
                                    continue
                        
                        # Also scan files directly in cache directories
                        for file in files:
                            if cancellation_token.is_set():
                                break
                            file_path = os.path.join(root, file)
                            # Skip system files
                            if file.startswith('.') or file.endswith('.db-shm') or file.endswith('.db-wal'):
                                continue
                            file_info = self.create_file_info(file_path)
                            if file_info and not self.should_skip_file(file_info):
                                file_info.module = self.get_module_name()
                                result.add_file(file_info)

                except Exception as e:
                    # Skip problematic directories but continue scanning
                    continue

        except Exception as e:
            result.error_message = f"扫描 Windows Store 缓存时出错: {e}"

        return result

