"""
System Information Utilities

Provides Windows version detection and system-specific configurations.
Supports Windows 7, 8, 10, and 11.
"""

import platform
import subprocess
import os
import re
from typing import Dict, List, Optional, Tuple
from enum import Enum


class WindowsVersion(Enum):
    """Windows version enumeration."""
    WINDOWS_7 = "Windows 7"
    WINDOWS_8 = "Windows 8"
    WINDOWS_8_1 = "Windows 8.1"
    WINDOWS_10 = "Windows 10"
    WINDOWS_11 = "Windows 11"
    UNKNOWN = "Unknown"


class SystemPaths:
    """System-specific paths for different Windows versions."""
    
    @staticmethod
    def get_system_paths(version: WindowsVersion) -> List[str]:
        """
        Get system paths for the specified Windows version.
        
        Args:
            version: Windows version
            
        Returns:
            List of system paths to protect
        """
        base_paths = [
            "C:\\Windows",
            "C:\\Windows\\System32",
        ]
        
        # Add version-specific paths
        if version in [WindowsVersion.WINDOWS_7, WindowsVersion.WINDOWS_8, WindowsVersion.WINDOWS_8_1]:
            base_paths.extend([
                "C:\\Windows\\SysWOW64",
                "C:\\Windows\\WinSxS",
                "C:\\Windows\\winsxs",  # Lowercase variant in some systems
            ])
        elif version in [WindowsVersion.WINDOWS_10, WindowsVersion.WINDOWS_11]:
            base_paths.extend([
                "C:\\Windows\\SysWOW64",
                "C:\\Windows\\WinSxS",
                "C:\\Windows\\SystemApps",  # Windows 10/11 UWP apps
                "C:\\Windows\\SystemResources",  # Windows 11
                "C:\\Windows\\System32\\DriverStore",  # Driver repository
            ])
        
        # Common paths for all versions
        base_paths.extend([
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            "C:\\Program Files\\WindowsApps",
        ])
        
        return base_paths
    
    @staticmethod
    def get_temp_directories(version: WindowsVersion) -> List[str]:
        """
        Get temporary directories for the specified Windows version.
        
        Args:
            version: Windows version
            
        Returns:
            List of temp directories to clean
        """
        temp_dirs = [
            "C:\\Windows\\Temp",
            os.path.expandvars("%TEMP%"),
            os.path.expandvars("%LOCALAPPDATA%\\Temp"),
        ]
        
        # Add version-specific temp directories
        if version == WindowsVersion.WINDOWS_7:
            temp_dirs.extend([
                "C:\\Windows\\SoftwareDistribution\\Download",
                "C:\\Windows\\Prefetch",
            ])
        elif version in [WindowsVersion.WINDOWS_8, WindowsVersion.WINDOWS_8_1]:
            temp_dirs.extend([
                "C:\\Windows\\SoftwareDistribution\\Download",
                "C:\\Windows\\Prefetch",
                "C:\\Windows\\AppReadiness",  # Windows 8+ app readiness cache
            ])
        elif version in [WindowsVersion.WINDOWS_10, WindowsVersion.WINDOWS_11]:
            temp_dirs.extend([
                "C:\\Windows\\SoftwareDistribution\\Download",
                "C:\\Windows\\Prefetch",
                "C:\\Windows\\AppReadiness",
                "C:\\Windows\\DeliveryOptimization",  # Windows 10/11
                "C:\\Windows\\System32\\DriverStore\\Temp",  # Windows 10/11
                "C:\\Windows\\Logs",  # Windows 10/11 logs
            ])
        
        return temp_dirs
    
    @staticmethod
    def get_update_cache_directories(version: WindowsVersion) -> List[str]:
        """
        Get Windows Update cache directories for the specified version.
        
        Args:
            version: Windows version
            
        Returns:
            List of update cache directories
        """
        cache_dirs = [
            "C:\\Windows\\SoftwareDistribution\\Download",
            "C:\\Windows\\SoftwareDistribution\\DataStore",
        ]
        
        if version in [WindowsVersion.WINDOWS_10, WindowsVersion.WINDOWS_11]:
            cache_dirs.extend([
                "C:\\Windows\\Servicing",
                "C:\\Windows\\winsxs\\backup",  # Component store backup
                "C:\\Windows\\Logs\\CBS",  # Component-Based Servicing
            ])
        elif version == WindowsVersion.WINDOWS_7:
            cache_dirs.extend([
                "C:\\Windows\\winsxs\\pending.xml.old",  # Update remnants
            ])
        
        return cache_dirs


class SystemInfo:
    """System information detector for Windows versions."""
    
    def __init__(self):
        """Initialize system information detector."""
        self._version: Optional[WindowsVersion] = None
        self._build_number: Optional[int] = None
        self._is_64bit: Optional[bool] = None
        self._detect_system_info()
    
    def _detect_system_info(self):
        """Detect Windows version and system information."""
        try:
            # Get version from platform module
            version_info = platform.version()
            system_info = platform.system()
            
            if system_info != "Windows":
                self._version = WindowsVersion.UNKNOWN
                return
            
            # Parse version info
            major, minor, build = map(int, version_info.split('.'))
            self._build_number = build
            self._is_64bit = platform.machine().endswith('64')
            
            # Determine Windows version
            if major == 6:
                if minor == 1:
                    self._version = WindowsVersion.WINDOWS_7
                elif minor == 2:
                    self._version = WindowsVersion.WINDOWS_8
                elif minor == 3:
                    self._version = WindowsVersion.WINDOWS_8_1
            elif major == 10:
                if build >= 22000:
                    self._version = WindowsVersion.WINDOWS_11
                else:
                    self._version = WindowsVersion.WINDOWS_10
            elif major >= 10:
                self._version = WindowsVersion.WINDOWS_10  # Conservative estimate
            else:
                self._version = WindowsVersion.UNKNOWN
            
            # Fallback: Try using ver command if platform detection failed
            if self._version == WindowsVersion.UNKNOWN:
                self._detect_with_ver_command()
        
        except Exception:
            # Fallback detection
            self._detect_with_ver_command()
    
    def _detect_with_ver_command(self):
        """Fallback detection using Windows ver command."""
        try:
            result = subprocess.run('ver', shell=True, capture_output=True, text=True)
            output = result.stdout
            
            # Parse version string
            if "Windows 11" in output:
                self._version = WindowsVersion.WINDOWS_11
            elif "Windows 10" in output:
                self._version = WindowsVersion.WINDOWS_10
            elif "Windows 8.1" in output:
                self._version = WindowsVersion.WINDOWS_8_1
            elif "Windows 8" in output:
                self._version = WindowsVersion.WINDOWS_8
            elif "Windows 7" in output:
                self._version = WindowsVersion.WINDOWS_7
            else:
                self._version = WindowsVersion.UNKNOWN
            
            # Detect architecture
            self._is_64bit = "x64" in output or platform.machine().endswith('64')
        
        except Exception:
            self._version = WindowsVersion.UNKNOWN
            self._is_64bit = platform.machine().endswith('64')
    
    def get_windows_version(self) -> WindowsVersion:
        """Get detected Windows version."""
        return self._version or WindowsVersion.UNKNOWN
    
    def get_build_number(self) -> int:
        """Get Windows build number."""
        return self._build_number or 0
    
    def is_64bit(self) -> bool:
        """Check if system is 64-bit."""
        return self._is_64bit or False
    
    def get_version_info(self) -> Dict[str, any]:
        """
        Get complete version information.
        
        Returns:
            Dict with version details
        """
        return {
            'version': self.get_windows_version(),
            'version_string': self.get_windows_version().value,
            'build_number': self.get_build_number(),
            'is_64bit': self.is_64bit(),
            'platform_info': platform.platform(),
            'architecture': platform.architecture(),
        }
    
    def supports_feature(self, feature: str) -> bool:
        """
        Check if the current Windows version supports a specific feature.
        
        Args:
            feature: Feature to check (e.g., 'uac', 'directstorage', 'wsl')
            
        Returns:
            True if feature is supported
        """
        version = self.get_windows_version()
        
        features = {
            'uac': version in [WindowsVersion.WINDOWS_7, WindowsVersion.WINDOWS_8, 
                             WindowsVersion.WINDOWS_8_1, WindowsVersion.WINDOWS_10, 
                             WindowsVersion.WINDOWS_11],
            'directstorage': version in [WindowsVersion.WINDOWS_10, WindowsVersion.WINDOWS_11],
            'wsl': version in [WindowsVersion.WINDOWS_10, WindowsVersion.WINDOWS_11],
            'windows_store': version in [WindowsVersion.WINDOWS_8, WindowsVersion.WINDOWS_8_1,
                                       WindowsVersion.WINDOWS_10, WindowsVersion.WINDOWS_11],
            'prefetch': True,  # All supported versions have prefetch
            'hibernation': True,  # All supported versions have hibernation
        }
        
        return features.get(feature.lower(), False)
    
    def get_powercfg_command(self, action: str) -> str:
        """
        Get the appropriate powercfg command for the Windows version.
        
        Args:
            action: Action to perform (e.g., 'disable_hibernate', 'check_status')
            
        Returns:
            Command string
        """
        version = self.get_windows_version()
        
        commands = {
            'disable_hibernate': 'powercfg /h off',
            'enable_hibernate': 'powercfg /h on',
            'check_status': 'powercfg /a',
            'query_hibernate_size': 'powercfg /h /type',
        }
        
        # All versions use the same powercfg commands
        return commands.get(action, 'powercfg /a')
    
    def get_hibernation_file_path(self) -> str:
        """
        Get the hibernation file path for the current Windows version.
        
        Returns:
            Path to hiberfil.sys
        """
        # All Windows versions store hiberfil.sys in C:\
        return "C:\\hiberfil.sys"
    
    def supports_windows_defender_offline_scan_cache(self) -> bool:
        """Check if Windows Defender offline scan cache is supported."""
        return self.get_windows_version() in [WindowsVersion.WINDOWS_10, WindowsVersion.WINDOWS_11]
    
    def supports_microsoft_edge_cache(self) -> bool:
        """Check if Microsoft Edge cache cleaning is supported."""
        return self.get_windows_version() in [WindowsVersion.WINDOWS_10, WindowsVersion.WINDOWS_11]


# Global instance for easy import
system_info = SystemInfo()