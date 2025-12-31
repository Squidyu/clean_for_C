"""
Windows Search Index Scanner

Scans for Windows Search index temporary files.
These are cache files created by Windows Search service for faster file searching.
"""

import os
import threading
from modules.base_scanner import BaseScanner
from models.scan_result import ScanResult
from models.file_info import FileInfo
from utils.file_utils import scan_directory_files
from utils.path_utils import expand_environment_variables, validate_c_drive_path


class WindowsSearchIndexScanner(BaseScanner):
    """
    Scanner for Windows Search index temporary files.
    
    Scans for:
    - Windows Search temporary index files
    - Windows Search cache files
    - Windows Search log files
    
    NOTE: Does NOT scan active index databases (Windows.edb) - those are protected
    """

    def get_module_name(self) -> str:
        """Get module name."""
        return "Windows Search 索引"

    def get_risk_level(self) -> str:
        """Get risk level - medium risk (rebuilding index may take time)."""
        return "medium"

    def scan(self, cancellation_token: threading.Event) -> ScanResult:
        """
        Scan for Windows Search index temporary files.
        
        Args:
            cancellation_token: Event to cancel scanning
            
        Returns:
            ScanResult with found index files
        """
        result = ScanResult(
            module_name=self.get_module_name(),
            risk_level=self.get_risk_level()
        )

        try:
            # Windows Search index locations
            cache_paths = []
            
            # ProgramData search index
            programdata = expand_environment_variables("%ProgramData%")
            if programdata:
                search_path = os.path.join(programdata, "Microsoft", "Search", "Data")
                if os.path.exists(search_path):
                    cache_paths.append(search_path)
            
            # User-specific search index
            appdata = expand_environment_variables("%APPDATA%")
            if appdata:
                user_search = os.path.join(appdata, "Microsoft", "Windows", "Recent", "AutomaticDestinations")
                if os.path.exists(user_search):
                    cache_paths.append(user_search)

            # Scan each location
            for cache_path in cache_paths:
                if cancellation_token.is_set():
                    break

                if not os.path.exists(cache_path):
                    continue

                try:
                    validate_c_drive_path(cache_path)
                    
                    # Scan for temporary and cache files only
                    # CRITICAL: Do NOT delete active index databases
                    for root, dirs, files in os.walk(cache_path):
                        if cancellation_token.is_set():
                            break
                        
                        for file in files:
                            if cancellation_token.is_set():
                                break
                            
                            file_path = os.path.join(root, file)
                            
                            # CRITICAL: Skip active index databases
                            if file.endswith('.edb') and 'Windows.edb' in file:
                                continue
                            
                            # Only scan temporary and cache files
                            if any(keyword in file.lower() for keyword in ['temp', 'cache', '.tmp', '.log', 'backup']):
                                file_info = self.create_file_info(file_path)
                                if file_info and not self.should_skip_file(file_info):
                                    file_info.module = self.get_module_name()
                                    file_info.description = "Windows Search 索引临时文件"
                                    result.add_file(file_info)

                except Exception as e:
                    # Skip problematic directories but continue scanning
                    continue

        except Exception as e:
            result.error_message = f"扫描 Windows Search 索引时出错: {e}"

        return result

