"""
Microsoft Teams Cache Scanner

Scans for Microsoft Teams cache files.
These are temporary files created by Microsoft Teams application.
"""

import os
import threading
from modules.base_scanner import BaseScanner
from models.scan_result import ScanResult
from models.file_info import FileInfo
from utils.file_utils import scan_directory_files
from utils.path_utils import expand_environment_variables, validate_c_drive_path


class TeamsCacheScanner(BaseScanner):
    """
    Scanner for Microsoft Teams cache files.
    
    Scans for:
    - Teams application cache
    - Teams media cache
    - Teams logs
    - Teams temporary files
    """

    def get_module_name(self) -> str:
        """Get module name."""
        return "Microsoft Teams 缓存"

    def get_risk_level(self) -> str:
        """Get risk level - low risk for cache files."""
        return "low"

    def scan(self, cancellation_token: threading.Event) -> ScanResult:
        """
        Scan for Microsoft Teams cache files.
        
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
            # Microsoft Teams cache locations
            cache_paths = []
            
            # User-specific Teams cache
            appdata = expand_environment_variables("%APPDATA%")
            if appdata:
                teams_path = os.path.join(appdata, "Microsoft", "Teams")
                if os.path.exists(teams_path):
                    cache_paths.append(teams_path)
            
            local_appdata = expand_environment_variables("%LOCALAPPDATA%")
            if local_appdata:
                teams_local = os.path.join(local_appdata, "Microsoft", "Teams")
                if os.path.exists(teams_local):
                    cache_paths.append(teams_local)
                
                # Teams media cache
                teams_media = os.path.join(local_appdata, "Microsoft", "Teams", "media-stack")
                if os.path.exists(teams_media):
                    cache_paths.append(teams_media)

            # If Teams is not installed, return empty result
            if not cache_paths:
                return result

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
                        
                        # Common Teams cache directory names
                        for dir_name in dirs:
                            if cancellation_token.is_set():
                                break
                            
                            if any(keyword in dir_name.lower() for keyword in ['cache', 'logs', 'temp', 'blob_storage', 'gpucache', 'code cache', 'local storage']):
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
                        
                        # Also scan files in cache directories
                        for file in files:
                            if cancellation_token.is_set():
                                break
                            file_path = os.path.join(root, file)
                            # Skip database files that might be in use (except IndexedDB which is in cache)
                            if file.endswith('.db') and 'IndexedDB' not in root and 'cache' not in root.lower():
                                continue
                            file_info = self.create_file_info(file_path)
                            if file_info and not self.should_skip_file(file_info):
                                file_info.module = self.get_module_name()
                                result.add_file(file_info)

                except Exception as e:
                    # Skip problematic directories but continue scanning
                    continue

        except Exception as e:
            result.error_message = f"扫描 Microsoft Teams 缓存时出错: {e}"

        return result

