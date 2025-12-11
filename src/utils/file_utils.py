"""
File Utilities

Utility functions for safe file operations with comprehensive error handling.
Provides Windows-specific file system operations for the cleaning tool.
"""

import os
import shutil
import threading
from typing import Optional, List, Callable, Any
from .path_utils import validate_c_drive_path, normalize_path


class FileOperationError(Exception):
    """Base exception for file operation errors."""
    pass


class FileNotFoundError(FileOperationError):
    """File or directory not found."""
    pass


class PermissionDeniedError(FileOperationError):
    """Insufficient permissions for file operation."""
    pass


class FileLockedError(FileOperationError):
    """File is locked by another process."""
    pass


class DiskSpaceError(FileOperationError):
    """Insufficient disk space for operation."""
    pass


def safe_delete_file(file_path: str, raise_errors: bool = False) -> bool:
    """
    Safely delete a file with comprehensive error handling.

    Args:
        file_path: Path to file to delete
        raise_errors: If True, raise exceptions on errors; if False, return False

    Returns:
        True if deleted successfully, False otherwise

    Raises:
        FileOperationError: If raise_errors is True and deletion fails
    """
    try:
        # Validate path
        validated_path = validate_c_drive_path(file_path)

        # Check if file exists
        if not os.path.exists(validated_path):
            if raise_errors:
                raise FileNotFoundError(f"File not found: {file_path}")
            return False

        # Check if it's actually a file
        if not os.path.isfile(validated_path):
            if raise_errors:
                raise FileOperationError(f"Path is not a file: {file_path}")
            return False

        # Attempt deletion
        os.remove(validated_path)
        return True

    except PermissionError:
        if raise_errors:
            raise PermissionDeniedError(f"Permission denied: {file_path}")
        return False
    except OSError as e:
        if raise_errors:
            if "being used by another process" in str(e).lower():
                raise FileLockedError(f"File locked: {file_path}")
            else:
                raise FileOperationError(f"OS error deleting file: {e}")
        return False
    except Exception as e:
        if raise_errors:
            raise FileOperationError(f"Unexpected error deleting file: {e}")
        return False


def safe_delete_directory(dir_path: str, raise_errors: bool = False) -> bool:
    """
    Safely delete a directory with comprehensive error handling.

    Args:
        dir_path: Path to directory to delete
        raise_errors: If True, raise exceptions on errors; if False, return False

    Returns:
        True if deleted successfully, False otherwise

    Raises:
        FileOperationError: If raise_errors is True and deletion fails
    """
    try:
        # Validate path
        validated_path = validate_c_drive_path(dir_path)

        # Check if directory exists
        if not os.path.exists(validated_path):
            if raise_errors:
                raise FileNotFoundError(f"Directory not found: {dir_path}")
            return False

        # Check if it's actually a directory
        if not os.path.isdir(validated_path):
            if raise_errors:
                raise FileOperationError(f"Path is not a directory: {dir_path}")
            return False

        # Attempt deletion (recursive)
        shutil.rmtree(validated_path)
        return True

    except PermissionError:
        if raise_errors:
            raise PermissionDeniedError(f"Permission denied: {dir_path}")
        return False
    except OSError as e:
        if raise_errors:
            if "being used by another process" in str(e).lower():
                raise FileLockedError(f"Directory locked: {dir_path}")
            else:
                raise FileOperationError(f"OS error deleting directory: {e}")
        return False
    except Exception as e:
        if raise_errors:
            raise FileOperationError(f"Unexpected error deleting directory: {e}")
        return False


def safe_delete_path(path: str, raise_errors: bool = False) -> bool:
    """
    Safely delete a file or directory (auto-detect type).

    Args:
        path: Path to delete
        raise_errors: If True, raise exceptions on errors; if False, return False

    Returns:
        True if deleted successfully, False otherwise

    Raises:
        FileOperationError: If raise_errors is True and deletion fails
    """
    try:
        validated_path = validate_c_drive_path(path)

        if os.path.isfile(validated_path):
            return safe_delete_file(validated_path, raise_errors)
        elif os.path.isdir(validated_path):
            return safe_delete_directory(validated_path, raise_errors)
        else:
            if raise_errors:
                raise FileOperationError(f"Path is neither file nor directory: {path}")
            return False

    except Exception as e:
        if raise_errors:
            raise FileOperationError(f"Error determining path type: {e}")
        return False


def get_directory_size(dir_path: str) -> int:
    """
    Calculate total size of a directory recursively.

    Args:
        dir_path: Directory path

    Returns:
        Total size in bytes, or 0 if error
    """
    total_size = 0

    try:
        validated_path = validate_c_drive_path(dir_path)

        for root, dirs, files in os.walk(validated_path):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                except (OSError, IOError):
                    # Skip files we can't access
                    continue

    except Exception:
        return 0

    return total_size


def scan_directory_files(dir_path: str, pattern: str = "*", recursive: bool = True,
                        max_files: int = None) -> List[str]:
    """
    Scan directory for files matching pattern.

    Args:
        dir_path: Directory to scan
        pattern: File pattern (glob style, e.g., "*.tmp")
        recursive: If True, scan subdirectories
        max_files: Maximum files to return (None for unlimited)

    Returns:
        List of matching file paths
    """
    import fnmatch
    import glob

    files = []

    try:
        validated_path = validate_c_drive_path(dir_path)

        if recursive:
            # Recursive scan
            for root, dirs, filenames in os.walk(validated_path):
                for filename in filenames:
                    if fnmatch.fnmatch(filename, pattern):
                        files.append(os.path.join(root, filename))
                        if max_files and len(files) >= max_files:
                            return files
        else:
            # Non-recursive scan
            pattern_path = os.path.join(validated_path, pattern)
            files = glob.glob(pattern_path)
            if max_files:
                files = files[:max_files]

    except Exception:
        return []

    return files


def check_disk_space(path: str, required_bytes: int) -> bool:
    """
    Check if there's enough disk space at the given path.

    Args:
        path: Path to check disk space for
        required_bytes: Required free space in bytes

    Returns:
        True if sufficient space, False otherwise
    """
    try:
        stat = os.statvfs(path)
        free_bytes = stat.f_frsize * stat.f_bavail
        return free_bytes >= required_bytes
    except AttributeError:
        # Windows doesn't have statvfs, use different approach
        try:
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)

            # Get free space for the drive
            drive = os.path.splitdrive(path)[0] + "\\"
            result = ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(drive),
                None,  # lpFreeBytesAvailableToCaller
                None,  # lpTotalNumberOfBytes
                ctypes.byref(free_bytes)  # lpTotalNumberOfFreeBytes
            )

            if result:
                return free_bytes.value >= required_bytes

        except Exception:
            pass

    # Fallback: assume sufficient space
    return True


def move_to_recycle_bin(file_path: str) -> bool:
    """
    Move file to Windows Recycle Bin instead of permanent deletion.

    Args:
        file_path: Path to file to recycle

    Returns:
        True if moved successfully, False otherwise
    """
    try:
        import winshell

        validated_path = validate_c_drive_path(file_path)
        winshell.delete_file(validated_path, no_confirm=True, silent=True)
        return True

    except ImportError:
        # winshell not available, use alternative method
        try:
            # This is a simplified approach - real implementation would need more work
            # For now, just return False to indicate recycle bin not available
            return False
        except Exception:
            return False

    except Exception:
        return False


def get_file_info_safe(file_path: str) -> Optional[dict]:
    """
    Get file information safely, handling all errors.

    Args:
        file_path: Path to file

    Returns:
        Dict with file info, or None if error
    """
    try:
        validated_path = validate_c_drive_path(file_path)
        stat = os.stat(validated_path)

        return {
            'size': stat.st_size,
            'modified_time': stat.st_mtime,
            'access_time': stat.st_atime,
            'is_file': os.path.isfile(validated_path),
            'is_directory': os.path.isdir(validated_path),
            'exists': True
        }

    except Exception:
        return None


def validate_file_access(file_path: str) -> dict:
    """
    Validate file access permissions.

    Args:
        file_path: Path to validate

    Returns:
        Dict with access flags
    """
    result = {
        'exists': False,
        'readable': False,
        'writable': False,
        'deletable': False,
        'locked': False
    }

    try:
        validated_path = validate_c_drive_path(file_path)
        result['exists'] = os.path.exists(validated_path)

        if not result['exists']:
            return result

        # Test readability
        try:
            with open(validated_path, 'rb') as f:
                f.read(1)
            result['readable'] = True
        except:
            pass

        # Test writability (for files)
        if os.path.isfile(validated_path):
            try:
                with open(validated_path, 'ab') as f:
                    pass
                result['writable'] = True
            except:
                result['locked'] = True

        # Test deletability (safe test)
        try:
            temp_name = validated_path + '.test_access'
            os.rename(validated_path, temp_name)
            os.rename(temp_name, validated_path)
            result['deletable'] = True
        except:
            result['locked'] = True

    except Exception:
        pass

    return result


def batch_delete_files(file_paths: List[str], progress_callback: Optional[Callable] = None,
                      cancellation_token: Optional[threading.Event] = None) -> dict:
    """
    Batch delete multiple files with progress reporting.

    Args:
        file_paths: List of file paths to delete
        progress_callback: Optional callback(current_index, total, success_count, error_count)
        cancellation_token: Optional cancellation event

    Returns:
        Dict with operation results
    """
    total = len(file_paths)
    success_count = 0
    error_count = 0
    errors = []

    for i, file_path in enumerate(file_paths):
        # Check cancellation
        if cancellation_token and cancellation_token.is_set():
            break

        # Attempt deletion
        if safe_delete_file(file_path):
            success_count += 1
        else:
            error_count += 1
            errors.append(file_path)

        # Progress callback
        if progress_callback:
            progress_callback(i + 1, total, success_count, error_count)

    return {
        'total': total,
        'successful': success_count,
        'failed': error_count,
        'errors': errors,
        'cancelled': cancellation_token.is_set() if cancellation_token else False
    }


# Convenience functions for common operations
def delete_temp_files(temp_dir: str = "C:\\Windows\\Temp") -> dict:
    """Delete temporary files from Windows Temp directory."""
    files = scan_directory_files(temp_dir, "*.tmp")
    return batch_delete_files(files)


def delete_old_logs(log_dir: str, max_age_days: int = 30) -> dict:
    """Delete log files older than specified days."""
    import time

    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
    old_files = []

    for file_path in scan_directory_files(log_dir, "*.log"):
        try:
            if os.path.getmtime(file_path) < cutoff_time:
                old_files.append(file_path)
        except:
            continue

    return batch_delete_files(old_files)