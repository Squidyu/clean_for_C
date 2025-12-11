"""
System Whitelist Model

Represents protected system paths that must never be deleted.
This is a critical security component that prevents accidental deletion
of system-critical files and directories.
"""

from typing import List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SystemWhitelist:
    """
    System whitelist containing protected paths and patterns.

    This class defines which files and directories are protected from deletion.
    Any file path that matches the whitelist should not be presented for cleaning
    and should not be deleted under any circumstances.
    """

    protected_paths: List[str]
    """List of absolute paths that are completely protected."""

    protected_patterns: List[str]
    """List of glob patterns for protected paths."""

    version: str = "1.0.0"
    """Version of the whitelist for updates."""

    last_updated: datetime = None
    """When the whitelist was last updated."""

    def __post_init__(self):
        """Initialize last_updated if not provided."""
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def is_protected(self, path: str) -> bool:
        """
        Check if a path is protected by the whitelist.

        Args:
            path: Absolute path to check

        Returns:
            True if path is protected, False otherwise
        """
        import os.path
        import fnmatch

        # Normalize path for consistent comparison
        normalized_path = os.path.normpath(path).lower()

        # Check exact path matches
        for protected_path in self.protected_paths:
            if normalized_path == os.path.normpath(protected_path).lower():
                return True

        # Check pattern matches
        for pattern in self.protected_patterns:
            if fnmatch.fnmatch(normalized_path, pattern.lower()):
                return True

        return False

    def get_default_whitelist() -> 'SystemWhitelist':
        """
        Create a default system whitelist with critical Windows paths.

        This method provides a fallback whitelist containing the most
        critical system paths that must always be protected.

        Returns:
            SystemWhitelist with default protected paths
        """
        try:
            from utils.system_info import system_info, SystemPaths, WindowsVersion
            
            version = system_info.get_windows_version()
            
            # Get version-specific system paths
            system_paths = SystemPaths.get_system_paths(version)
            
            protected_paths = [
                # System paths from SystemPaths utility
                *system_paths,
                
                # Critical system files
                "C:\\Windows\\explorer.exe",
                "C:\\Windows\\System32\\cmd.exe",
                "C:\\Windows\\System32\\powershell.exe",
                "C:\\Windows\\System32\\conhost.exe",
                
                # System boot files
                "C:\\bootmgr",
                "C:\\BOOTNXT",
                "C:\\NTLDR",  # Windows 7 boot file
            ]
            
            # Add version-specific paths
            if version == WindowsVersion.WINDOWS_7:
                protected_paths.extend([
                    "C:\\Windows\\winsxs",
                    "C:\\Windows\\System32\\wbem",  # WMI repository
                ])
            elif version in [WindowsVersion.WINDOWS_8, WindowsVersion.WINDOWS_8_1]:
                protected_paths.extend([
                    "C:\\Windows\\winsxs",
                    "C:\\Windows\\System32\\wbem",
                    "C:\\Windows\\AppReadiness",
                ])
            elif version in [WindowsVersion.WINDOWS_10, WindowsVersion.WINDOWS_11]:
                protected_paths.extend([
                    "C:\\Windows\\winsxs",
                    "C:\\Windows\\System32\\wbem",
                    "C:\\Windows\\SystemApps",  # UWP apps
                    "C:\\Windows\\SystemResources",  # Windows 11
                    "C:\\Windows\\System32\\DriverStore",
                    "C:\\Windows\\System32\\DriverStore\\FileRepository",
                ])
            
            # Version-specific protected patterns
            protected_patterns = [
                # Windows system directories (recursive protection)
                *[path + "\\*" for path in system_paths],
                
                # Critical file extensions
                "*.exe",
                "*.dll",
                "*.sys",
                "*.msi",  # Windows Installer
                "*.msp",  # Windows Installer patch
                "*.mst",  # Windows Installer transform
                
                # Windows Update files
                "C:\\Windows\\SoftwareDistribution\\*",
                
                # System files
                "C:\\pagefile.sys",
                "C:\\swapfile.sys",
                "C:\\hiberfil.sys",
                
                # System restore
                "C:\\System Volume Information\\*",
                
                # NTFS metadata
                "C:\\$RECYCLE.BIN\\*",
                "C:\\$Extend\\*",
                "C:\\$BitLock\\*",
            ]
            
            # Add version-specific patterns
            if version == WindowsVersion.WINDOWS_7:
                protected_patterns.extend([
                    "C:\\Windows\\winsxs\\*",
                    "C:\\Windows\\System32\\LogFiles\\WMI\\*",
                ])
            elif version in [WindowsVersion.WINDOWS_8, WindowsVersion.WINDOWS_8_1]:
                protected_patterns.extend([
                    "C:\\Windows\\winsxs\\*",
                    "C:\\Windows\\AppReadiness\\*",
                    "C:\\Windows\\System32\\LogFiles\\WMI\\*",
                ])
            elif version in [WindowsVersion.WINDOWS_10, WindowsVersion.WINDOWS_11]:
                protected_patterns.extend([
                    "C:\\Windows\\winsxs\\*",
                    "C:\\Windows\\SystemApps\\*",
                    "C:\\Windows\\SystemResources\\*",
                    "C:\\Windows\\System32\\DriverStore\\*",
                    "C:\\Windows\\Logs\\*",
                    "C:\\Windows\\ServiceProfiles\\*",
                ])
            
        except Exception:
            # Fallback to basic whitelist if system detection fails
            protected_paths = [
                "C:\\Windows",
                "C:\\Windows\\System32",
                "C:\\Windows\\SysWOW64",
                "C:\\Windows\\WinSxS",
                "C:\\Windows\\explorer.exe",
                "C:\\Windows\\System32\\cmd.exe",
                "C:\\Windows\\System32\\powershell.exe",
                "C:\\Program Files",
                "C:\\Program Files (x86)",
                "C:\\Program Files\\WindowsApps",
                "C:\\bootmgr",
                "C:\\BOOTNXT",
            ]
            
            protected_patterns = [
                "C:\\Windows\\*",
                "C:\\Windows\\System32\\*",
                "C:\\Windows\\SysWOW64\\*",
                "C:\\Program Files\\*",
                "C:\\Program Files (x86)\\*",
                "C:\\Program Files\\WindowsApps\\*",
                "*.exe",
                "*.dll",
                "*.sys",
                "*.msi",
                "*.msp",
                "C:\\Windows\\SoftwareDistribution\\*",
                "C:\\pagefile.sys",
                "C:\\swapfile.sys",
                "C:\\hiberfil.sys",
                "C:\\System Volume Information\\*",
                "C:\\$RECYCLE.BIN\\*",
                "C:\\$Extend\\*",
            ]

        return SystemWhitelist(
            protected_paths=protected_paths,
            protected_patterns=protected_patterns,
            version="2.0.0"
        )


# Default instance for import
DEFAULT_WHITELIST = SystemWhitelist.get_default_whitelist()