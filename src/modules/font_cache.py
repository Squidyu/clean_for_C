"""
Font Cache Scanner

Scans for Windows font cache files.
These are cache files created by Windows for faster font preview and rendering.
"""

import os
import threading
from modules.base_scanner import BaseScanner
from models.scan_result import ScanResult
from models.file_info import FileInfo
from utils.file_utils import scan_directory_files
from utils.path_utils import expand_environment_variables, validate_c_drive_path


class FontCacheScanner(BaseScanner):
    """
    Scanner for Windows font cache files.
    
    Scans for:
    - Font cache database files
    - Font preview cache files
    - Temporary font files
    """

    def get_module_name(self) -> str:
        """Get module name."""
        return "字体缓存"

    def get_risk_level(self) -> str:
        """Get risk level - low risk for cache files."""
        return "low"

    def scan(self, cancellation_token: threading.Event) -> ScanResult:
        """
        Scan for font cache files.
        
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
            # Font cache locations
            cache_paths = []
            
            # User font cache
            local_appdata = expand_environment_variables("%LOCALAPPDATA%")
            if local_appdata:
                font_cache_user = os.path.join(local_appdata, "Microsoft", "Windows", "Fonts")
                if os.path.exists(font_cache_user):
                    cache_paths.append(font_cache_user)
                
                font_cache_local = os.path.join(local_appdata, "FontCache")
                if os.path.exists(font_cache_local):
                    cache_paths.append(font_cache_local)
            
            # System font cache (requires admin, but try anyway)
            system_font_cache = "C:\\Windows\\ServiceProfiles\\LocalService\\AppData\\Local\\FontCache"
            if os.path.exists(system_font_cache):
                cache_paths.append(system_font_cache)

            # Scan each location
            for cache_path in cache_paths:
                if cancellation_token.is_set():
                    break

                if not os.path.exists(cache_path):
                    continue

                try:
                    validate_c_drive_path(cache_path)
                    
                    # Scan for cache files
                    for root, dirs, files in os.walk(cache_path):
                        if cancellation_token.is_set():
                            break
                        
                        for file in files:
                            if cancellation_token.is_set():
                                break
                            
                            file_path = os.path.join(root, file)
                            
                            # Look for cache files (not actual font files)
                            if any(keyword in file.lower() for keyword in ['cache', '.tmp', '.log', '.db']):
                                # Skip actual font files
                                if file.endswith(('.ttf', '.otf', '.ttc', '.fon')):
                                    continue
                                
                                file_info = self.create_file_info(file_path)
                                if file_info and not self.should_skip_file(file_info):
                                    file_info.module = self.get_module_name()
                                    result.add_file(file_info)

                except PermissionError:
                    # Skip if no permission (system font cache)
                    continue
                except Exception as e:
                    # Skip problematic directories but continue scanning
                    continue

        except Exception as e:
            result.error_message = f"扫描字体缓存时出错: {e}"

        return result

