"""
App Cache Scanner

Scans for third-party application cache files.
This includes cache directories from development tools, productivity apps, etc.
"""

import os
import threading
from typing import List, Dict
from modules.base_scanner import BaseScanner
from models.file_info import FileInfo
from utils.file_utils import scan_directory_files
from utils.path_utils import expand_environment_variables, validate_c_drive_path


class AppCacheScanner(BaseScanner):
    """
    Scanner for third-party application cache files.

    Scans for cache files from popular applications:
    - Development tools (VS Code, JetBrains IDEs)
    - Productivity apps (WeChat, etc.)
    - Media applications
    - System utilities
    """

    def get_module_name(self) -> str:
        """Get module name."""
        return "第三方应用缓存"

    def get_risk_level(self) -> str:
        """Get risk level - low risk for app cache."""
        return "low"

    def scan(self, cancellation_token: threading.Event) -> 'ScanResult':
        """
        Scan for application cache files.

        Searches in user AppData directories for known application cache locations.

        Args:
            cancellation_token: Event to cancel scanning

        Returns:
            ScanResult with found application cache files
        """
        from models.scan_result import ScanResult

        result = ScanResult(
            module_name=self.get_module_name(),
            risk_level=self.get_risk_level()
        )

        # Get application cache locations
        cache_locations = self._get_app_cache_locations()

        # Scan each application's cache
        for app_name, locations in cache_locations.items():
            if cancellation_token.is_set():
                break

            for location in locations:
                if cancellation_token.is_set():
                    break

                try:
                    # Expand environment variables in path
                    expanded_path = expand_environment_variables(location["path"])

                    # Check if path exists
                    if not os.path.exists(expanded_path):
                        continue

                    # Validate path is within C drive
                    try:
                        validate_c_drive_path(expanded_path)
                    except ValueError:
                        continue

                    # Scan for cache files
                    for pattern in location["patterns"]:
                        if cancellation_token.is_set():
                            break

                        try:
                            files = scan_directory_files(expanded_path, pattern,
                                                       recursive=location.get("recursive", True))
                            for file_path in files:
                                if cancellation_token.is_set():
                                    break

                                # Create FileInfo and add to result
                                file_info = self.create_file_info(file_path)
                                if file_info and not self.should_skip_file(file_info):
                                    result.add_file(file_info)

                        except Exception:
                            # Skip problematic patterns but continue
                            continue

                except Exception:
                    # Skip problematic app locations but continue
                    continue

        return result

    def _get_app_cache_locations(self) -> Dict[str, List[Dict]]:
        """
        Get cache locations for popular applications.

        Returns:
            Dict mapping app names to list of cache location configs
        """
        return {
            "Visual Studio Code": [
                {
                    "path": "%APPDATA%\\Code\\CachedData",
                    "patterns": ["*"],
                    "recursive": True
                },
                {
                    "path": "%APPDATA%\\Code\\Cache",
                    "patterns": ["*"],
                    "recursive": True
                },
                {
                    "path": "%APPDATA%\\Code\\CachedExtensions",
                    "patterns": ["*.vsix"],
                    "recursive": True
                }
            ],
            "JetBrains IDEs": [
                {
                    "path": "%LOCALAPPDATA%\\JetBrains",
                    "patterns": ["*.log", "idea*.tmp", "*.hprof"],
                    "recursive": True
                }
            ],
            "WeChat": [
                {
                    "path": "%APPDATA%\\Tencent\\WeChat\\XPlugin\\Cache",
                    "patterns": ["*"],
                    "recursive": True
                }
            ],
            "Steam": [
                {
                    "path": "%PROGRAMFILES(X86)%\\Steam\\appcache",
                    "patterns": ["*.tmp", "*.cache"],
                    "recursive": True
                }
            ],
            "Adobe Products": [
                {
                    "path": "%TEMP%\\Adobe",
                    "patterns": ["*.tmp", "*.cache"],
                    "recursive": True
                }
            ],
            "NVIDIA": [
                {
                    "path": "%PROGRAMDATA%\\NVIDIA Corporation\\NV_Cache",
                    "patterns": ["*"],
                    "recursive": True
                }
            ],
            "Intel": [
                {
                    "path": "%PROGRAMDATA%\\Intel",
                    "patterns": ["*.tmp", "*.cache"],
                    "recursive": True
                }
            ],
            "Microsoft Office": [
                {
                    "path": "%LOCALAPPDATA%\\Microsoft\\Office",
                    "patterns": ["*.tmp", "*.cache"],
                    "recursive": True
                }
            ]
        }