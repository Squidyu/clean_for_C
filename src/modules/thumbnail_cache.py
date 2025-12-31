"""
Thumbnail Cache Scanner

Scans for Windows thumbnail cache files.
These are cache files created by Windows Explorer for faster thumbnail display.
"""

import os
import threading
import glob
from modules.base_scanner import BaseScanner
from models.scan_result import ScanResult
from models.file_info import FileInfo
from utils.file_utils import scan_directory_files
from utils.path_utils import expand_environment_variables, validate_c_drive_path
from utils.system_info import system_info, WindowsVersion


class ThumbnailCacheScanner(BaseScanner):
    """
    Scanner for Windows thumbnail cache files.
    
    Scans for:
    - Windows thumbnail cache databases (thumbcache_*.db)
    - Icon cache databases (iconcache_*.db)
    - Legacy thumbnail cache files (thumbs.db in folders)
    """

    def get_module_name(self) -> str:
        """Get module name."""
        return "缩略图缓存"

    def get_risk_level(self) -> str:
        """Get risk level - low risk for cache files."""
        return "low"

    def scan(self, cancellation_token: threading.Event) -> ScanResult:
        """
        Scan for thumbnail cache files.
        
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
            # Windows thumbnail cache locations
            cache_paths = []
            
            # System-wide thumbnail cache (Windows 7/8/8.1/10/11)
            local_appdata = expand_environment_variables("%LOCALAPPDATA%")
            if local_appdata:
                explorer_path = os.path.join(local_appdata, "Microsoft", "Windows", "Explorer")
                if os.path.exists(explorer_path):
                    cache_paths.append(explorer_path)
            
            # Scan for thumbnail cache databases
            for cache_path in cache_paths:
                if cancellation_token.is_set():
                    break

                if not os.path.exists(cache_path):
                    continue

                try:
                    validate_c_drive_path(cache_path)
                    
                    # Look for thumbnail cache database files
                    patterns = [
                        "thumbcache_*.db",
                        "iconcache_*.db",
                        "thumbcache_idx.db",
                    ]
                    
                    for pattern in patterns:
                        if cancellation_token.is_set():
                            break
                        
                        pattern_path = os.path.join(cache_path, pattern)
                        for file_path in glob.glob(pattern_path):
                            if cancellation_token.is_set():
                                break
                            
                            file_info = self.create_file_info(file_path)
                            if file_info and not self.should_skip_file(file_info):
                                file_info.module = self.get_module_name()
                                result.add_file(file_info)

                except Exception as e:
                    continue

            # Scan for legacy thumbs.db files in common locations
            # Limit to common user directories to avoid scanning entire C drive
            common_locations = [
                os.path.join(os.path.expanduser("~"), "Pictures"),
                os.path.join(os.path.expanduser("~"), "Documents"),
                os.path.join(os.path.expanduser("~"), "Downloads"),
                os.path.join(os.path.expanduser("~"), "Videos"),
            ]
            
            for location in common_locations:
                if cancellation_token.is_set():
                    break
                
                if not os.path.exists(location):
                    continue
                
                try:
                    # Look for thumbs.db files (limit depth to avoid too many files)
                    for root, dirs, files in os.walk(location):
                        if cancellation_token.is_set():
                            break
                        
                        # Limit depth to 3 levels
                        depth = root[len(location):].count(os.sep)
                        if depth > 3:
                            dirs[:] = []  # Don't recurse further
                            continue
                        
                        if 'thumbs.db' in files:
                            thumbs_path = os.path.join(root, 'thumbs.db')
                            file_info = self.create_file_info(thumbs_path)
                            if file_info and not self.should_skip_file(file_info):
                                file_info.module = self.get_module_name()
                                result.add_file(file_info)

                except Exception:
                    continue

        except Exception as e:
            result.error_message = f"扫描缩略图缓存时出错: {e}"

        return result

