"""
Browser Cache Scanner

Scans for web browser cache files from popular browsers.
This includes temporary internet files, cached images, and browser-specific cache.
"""

import os
import threading
from typing import List, Dict
from modules.base_scanner import BaseScanner
from models.file_info import FileInfo
from utils.file_utils import scan_directory_files
from utils.path_utils import expand_environment_variables, validate_c_drive_path


class BrowserCacheScanner(BaseScanner):
    """
    Scanner for browser cache files.

    Scans cache directories for:
    - Microsoft Edge
    - Google Chrome
    - Mozilla Firefox
    - Other Chromium-based browsers
    """

    def get_module_name(self) -> str:
        """Get module name."""
        return "浏览器缓存"

    def get_risk_level(self) -> str:
        """Get risk level - low risk for browser cache."""
        return "low"

    def scan(self, cancellation_token: threading.Event) -> 'ScanResult':
        """
        Scan for browser cache files.

        Searches in user profile directories for browser cache locations.

        Args:
            cancellation_token: Event to cancel scanning

        Returns:
            ScanResult with found browser cache files
        """
        from models.scan_result import ScanResult

        result = ScanResult(
            module_name=self.get_module_name(),
            risk_level=self.get_risk_level()
        )

        # Get browser cache locations
        cache_locations = self._get_browser_cache_locations()

        # Scan each browser's cache
        for browser_name, locations in cache_locations.items():
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
                    # Skip problematic browser locations but continue
                    continue

        return result

    def _get_browser_cache_locations(self) -> Dict[str, List[Dict]]:
        """
        Get cache locations for different browsers.

        Returns:
            Dict mapping browser names to list of cache location configs
        """
        return {
            "Microsoft Edge": [
                {
                    "path": "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Cache",
                    "patterns": ["*"],
                    "recursive": True
                },
                {
                    "path": "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Code Cache",
                    "patterns": ["*"],
                    "recursive": True
                },
                {
                    "path": "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\GPUCache",
                    "patterns": ["*"],
                    "recursive": True
                }
            ],
            "Google Chrome": [
                {
                    "path": "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache",
                    "patterns": ["*"],
                    "recursive": True
                },
                {
                    "path": "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Code Cache",
                    "patterns": ["*"],
                    "recursive": True
                },
                {
                    "path": "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\GPUCache",
                    "patterns": ["*"],
                    "recursive": True
                }
            ],
            "Mozilla Firefox": [
                {
                    "path": "%APPDATA%\\Mozilla\\Firefox\\Profiles",
                    "patterns": ["*"],
                    "recursive": True,
                    "note": "Firefox uses profile-specific cache directories"
                }
            ],
            "Chromium": [
                {
                    "path": "%LOCALAPPDATA%\\Chromium\\User Data\\Default\\Cache",
                    "patterns": ["*"],
                    "recursive": True
                }
            ],
            "Brave": [
                {
                    "path": "%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Cache",
                    "patterns": ["*"],
                    "recursive": True
                }
            ],
            "Opera": [
                {
                    "path": "%APPDATA%\\Opera Software\\Opera Stable\\Cache",
                    "patterns": ["*"],
                    "recursive": True
                }
            ]
        }