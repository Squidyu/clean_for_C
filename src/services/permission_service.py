"""
Permission Service

Handles Windows permissions, administrator privilege checking, and UAC elevation.
This service ensures the application can perform necessary operations safely.
"""

import os
import sys
import subprocess
import ctypes
from typing import Dict, Tuple


class PermissionService:
    """
    Service for managing Windows permissions and administrator privileges.

    This service handles privilege checking, UAC elevation requests,
    and file/directory permission validation.
    """

    def __init__(self):
        """Initialize permission service."""
        pass

    def check_is_admin(self) -> bool:
        """
        Check if the current process has administrator privileges.

        Returns:
            True if running as administrator, False otherwise
        """
        try:
            # Method 1: Use ctypes to check token
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            # Method 2: Try to access a protected registry key
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SOFTWARE\Microsoft\Windows\CurrentVersion",
                                   0, winreg.KEY_READ)
                winreg.CloseKey(key)
                return True
            except:
                return False

    def request_elevation(self, reason: str = "需要管理员权限来执行此操作") -> bool:
        """
        Request UAC elevation for the current process.

        This method will attempt to restart the application with administrator privileges.
        If successful, the current process will be replaced with an elevated one.

        Args:
            reason: Reason for elevation (displayed to user)

        Returns:
            True if elevation was successful, False if denied or failed

        Note:
            If elevation is successful, the current process exits and is replaced.
            The return value is only meaningful if elevation fails.
        """
        if self.check_is_admin():
            return True  # Already elevated

        try:
            # Get current executable and arguments
            if hasattr(sys, '_MEIPASS'):
                # Running as PyInstaller bundle
                exe = sys.executable
                args = []
            else:
                # Running as script
                exe = sys.executable
                script = sys.argv[0]
                args = [script] + sys.argv[1:]

            # Use ShellExecuteEx to request elevation
            import ctypes
            from ctypes import wintypes

            class SHELLEXECUTEINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("fMask", wintypes.ULONG),
                    ("hwnd", wintypes.HWND),
                    ("lpVerb", wintypes.LPCSTR),
                    ("lpFile", wintypes.LPCSTR),
                    ("lpParameters", wintypes.LPCSTR),
                    ("lpDirectory", wintypes.LPCSTR),
                    ("nShow", ctypes.c_int),
                    ("hInstApp", wintypes.HINSTANCE),
                    ("lpIDList", wintypes.LPVOID),
                    ("lpClass", wintypes.LPCSTR),
                    ("hkeyClass", wintypes.HKEY),
                    ("dwHotKey", wintypes.DWORD),
                    ("hIcon", wintypes.HICON),
                    ("hProcess", wintypes.HANDLE),
                ]

            sei = SHELLEXECUTEINFO()
            sei.cbSize = ctypes.sizeof(sei)
            sei.fMask = 0x00000040  # SEE_MASK_NOCLOSEPROCESS
            sei.lpVerb = b"runas"  # Request elevation
            sei.lpFile = exe.encode('utf-8')
            sei.lpParameters = subprocess.list2cmdline(args).encode('utf-8') if args else None
            sei.nShow = 1  # SW_SHOWNORMAL

            if ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei)):
                # Elevation successful, wait a moment then exit current process
                import time
                time.sleep(0.5)
                sys.exit(0)  # Current process exits, elevated process takes over
            else:
                return False  # Elevation failed or was denied

        except Exception as e:
            print(f"Elevation request failed: {e}")
            return False

    def check_path_permissions(self, path: str) -> Dict[str, bool]:
        """
        Check read, write, and delete permissions for a file or directory path.

        Args:
            path: Path to check (file or directory)

        Returns:
            Dict with 'readable', 'writable', 'deletable' boolean flags
        """
        results = {
            'readable': False,
            'writable': False,
            'deletable': False
        }

        try:
            # Check if path exists
            if not os.path.exists(path):
                return results

            # Check readability
            try:
                with open(path, 'rb') as f:
                    f.read(1)
                results['readable'] = True
            except:
                pass

            # Check writability
            try:
                # For files, try to open for writing
                if os.path.isfile(path):
                    with open(path, 'ab') as f:  # append binary
                        pass
                    results['writable'] = True
                # For directories, try to create a temp file
                elif os.path.isdir(path):
                    import tempfile
                    with tempfile.NamedTemporaryFile(dir=path, delete=True):
                        pass
                    results['writable'] = True
            except:
                pass

            # Check deletability
            try:
                # For files, check if we can rename (safe delete test)
                if os.path.isfile(path):
                    temp_name = path + '.test_delete'
                    os.rename(path, temp_name)
                    os.rename(temp_name, path)  # Rename back
                    results['deletable'] = True
                # For directories, try to create/delete a temp subdirectory
                elif os.path.isdir(path):
                    import tempfile
                    temp_dir = tempfile.mkdtemp(dir=path)
                    os.rmdir(temp_dir)
                    results['deletable'] = True
            except:
                pass

        except Exception:
            # If any error occurs, assume no permissions
            pass

        return results

    def ensure_admin_rights(self, operation: str = "此操作") -> bool:
        """
        Ensure the current process has administrator rights.

        If not elevated, attempts to request elevation.

        Args:
            operation: Description of the operation requiring elevation

        Returns:
            True if elevation successful or already elevated, False otherwise
        """
        if self.check_is_admin():
            return True

        print(f"{operation}需要管理员权限。")
        return self.request_elevation(f"{operation}需要管理员权限")

    def get_privilege_status(self) -> Dict[str, bool]:
        """
        Get comprehensive privilege status.

        Returns:
            Dict with various privilege status flags
        """
        return {
            'is_admin': self.check_is_admin(),
            'can_elevate': True,  # Assume UAC is available
            'elevation_supported': True  # Windows 10+ supports UAC
        }

    def validate_file_operation_safety(self, paths: list) -> Dict[str, Dict[str, bool]]:
        """
        Validate that file operations can be performed safely on given paths.

        Args:
            paths: List of file/directory paths to validate

        Returns:
            Dict mapping paths to permission status dicts
        """
        results = {}
        for path in paths:
            results[path] = self.check_path_permissions(path)
        return results


# Global instance for easy import
permission_service = PermissionService()