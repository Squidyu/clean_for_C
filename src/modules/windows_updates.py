"""
Windows Updates Scanner

Scans for Windows Update cache and old version remnants.
Supports Windows 7, 8, 8.1, 10, and 11 with version-specific locations.
"""

import os
from pathlib import Path
from typing import List
from modules.base_scanner import BaseScanner
from models.scan_result import ScanResult
from models.file_info import FileInfo
from utils.system_info import system_info, WindowsVersion, SystemPaths


class WindowsUpdatesScanner(BaseScanner):
    """
    Scanner for Windows Update leftovers and cache files.
    
    This scanner looks for:
    - Windows Update cache files
    - Old version remnants
    - Service Pack leftovers
    - Component store cleanup candidates
    """

    def __init__(self):
        """Initialize the Windows Updates scanner."""
        super().__init__()
        self.system_info = system_info
        self.version = self.system_info.get_windows_version()

    def get_module_name(self) -> str:
        """Get module name."""
        return "Windows 更新残留"

    def get_risk_level(self) -> str:
        """Get risk level - medium risk for update files."""
        return "medium"

    def scan(self, cancellation_token) -> ScanResult:
        """
        Scan for Windows Update leftovers.

        Args:
            cancellation_token: Event to cancel scanning

        Returns:
            ScanResult with Windows Update file information
        """
        from models.scan_result import ScanResult

        result = ScanResult(
            module_name=self.get_module_name(),
            risk_level=self.get_risk_level()
        )

        try:
            # Get version-specific update paths
            update_paths = self._get_update_paths()
            
            for path_info in update_paths:
                if cancellation_token and cancellation_token.is_set():
                    break
                
                path = path_info['path']
                description = path_info['description']
                is_protected = path_info.get('protected', False)
                
                if os.path.exists(path):
                    self._scan_update_path(path, description, is_protected, result, cancellation_token)

        except Exception as e:
            result.error_message = f"扫描 Windows 更新文件时出错: {e}"

        return result

    def _get_update_paths(self) -> List[dict]:
        """
        Get version-specific Windows Update paths to scan.

        Returns:
            List of paths with descriptions
        """
        paths = []
        
        # Common paths for all versions
        paths.extend([
            {
                'path': "C:\\Windows\\SoftwareDistribution\\Download",
                'description': "Windows Update 下载缓存",
                'protected': False
            },
            {
                'path': "C:\\Windows\\SoftwareDistribution\\DataStore",
                'description': "Windows Update 数据存储",
                'protected': False
            }
        ])
        
        # Version-specific paths
        if self.version == WindowsVersion.WINDOWS_7:
            paths.extend([
                {
                    'path': "C:\\Windows\\$NtUninstall*",
                    'description': "Windows 7 卸载文件夹",
                    'protected': False,
                    'is_pattern': True
                },
                {
                    'path': "C:\\Windows\\winsxs\\pending.xml.old",
                    'description': "Windows 7 更新挂起文件",
                    'protected': False
                },
                {
                    'path': "C:\\Windows\\Logs\\CBS",
                    'description': "Windows 7 CBS 日志",
                    'protected': False
                }
            ])
            
        elif self.version in [WindowsVersion.WINDOWS_8, WindowsVersion.WINDOWS_8_1]:
            paths.extend([
                {
                    'path': "C:\\Windows\\Servicing",
                    'description': "Windows 8/8.1 服务文件夹",
                    'protected': False
                },
                {
                    'path': "C:\\Windows\\Logs\\CBS",
                    'description': "Windows 8/8.1 CBS 日志",
                    'protected': False
                }
            ])
            
        elif self.version in [WindowsVersion.WINDOWS_10, WindowsVersion.WINDOWS_11]:
            paths.extend([
                {
                    'path': "C:\\Windows\\Servicing",
                    'description': "Windows 10/11 服务文件夹",
                    'protected': False
                },
                {
                    'path': "C:\\Windows\\winsxs\\backup",
                    'description': "Windows 10/11 组件存储备份",
                    'protected': False
                },
                {
                    'path': "C:\\Windows\\Logs\\CBS",
                    'description': "Windows 10/11 CBS 日志",
                    'protected': False
                },
                {
                    'path': "C:\\Windows\\Logs\\DISM",
                    'description': "Windows 10/11 DISM 日志",
                    'protected': False
                }
            ])
            
            # Windows 11 specific
            if self.version == WindowsVersion.WINDOWS_11:
                paths.extend([
                    {
                        'path': "C:\\Windows\\System32\\DriverStore\\FileRepository\\tmp",
                        'description': "Windows 11 驱动程序临时文件",
                        'protected': False
                    }
                ])
        
        return paths

    def _scan_update_path(self, path: str, description: str, is_protected: bool, 
                         result: ScanResult, cancellation_token):
        """
        Scan a specific update path.

        Args:
            path: Path to scan
            description: Description of the path
            is_protected: Whether the path is protected
            result: ScanResult to add files to
            cancellation_token: Cancellation token
        """
        try:
            # Handle wildcard patterns
            if '*' in path:
                import glob
                matching_paths = glob.glob(path)
                for matched_path in matching_paths:
                    if cancellation_token and cancellation_token.is_set():
                        break
                    self._scan_single_path(matched_path, description, is_protected, result)
            else:
                self._scan_single_path(path, description, is_protected, result)
                
        except Exception as e:
            # Log error but continue with other paths
            print(f"扫描路径 {path} 时出错: {e}")

    def _scan_single_path(self, path: str, description: str, is_protected: bool, result: ScanResult):
        """
        Scan a single path for files.

        Args:
            path: Path to scan
            description: Description of the path
            is_protected: Whether the path is protected
            result: ScanResult to add files to
        """
        try:
            if os.path.isfile(path):
                # Single file
                self._add_file_to_result(path, description, is_protected, result)
            elif os.path.isdir(path):
                # Directory - scan contents
                try:
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            self._add_file_to_result(file_path, description, is_protected, result)
                            
                        # Skip system directories within update folders
                        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'System Volume Information']
                except PermissionError:
                    # Skip directories we can't access
                    pass
                    
        except Exception as e:
            print(f"扫描 {path} 时出错: {e}")

    def _add_file_to_result(self, file_path: str, description: str, is_protected: bool, result: ScanResult):
        """
        Add a file to the scan result.

        Args:
            file_path: Path to the file
            description: Description of the file type
            is_protected: Whether the file is protected
            result: ScanResult to add to
        """
        try:
            stat = os.stat(file_path)
            
            # Skip very recent files (might be in use)
            import time
            if time.time() - stat.st_mtime < 86400:  # Less than 1 day old
                return
            
            file_info = FileInfo(
                path=file_path,
                size=stat.st_size,
                last_access_time=stat.st_atime,
                last_modified_time=stat.st_mtime,
                module=self.get_module_name()
            )
            
            file_info.is_protected = is_protected
            file_info.description = f"{description} - {os.path.basename(file_path)}"
            
            # Mark certain file types as protected
            if file_path.endswith('.log') and 'CBS' in file_path:
                file_info.is_protected = True  # Keep CBS logs for troubleshooting
            
            result.add_file(file_info)
            
        except Exception:
            # Skip files we can't stat
            pass