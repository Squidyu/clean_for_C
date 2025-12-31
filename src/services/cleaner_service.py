"""
Cleaner Service

Coordinates cleaning operations with safety checks and progress tracking.
"""

import threading
import time
import subprocess
import os
from typing import List, Optional, Callable, Dict
from .whitelist_service import whitelist_service
from models.cleaning_operation import CleaningOperation
from models.file_info import FileInfo
from utils.file_utils import safe_delete_file, safe_delete_directory, safe_delete_path
from utils.path_utils import validate_c_drive_path


class CleanerService:
    """
    Service for managing file cleaning operations.

    This service handles the safe deletion of files with whitelist validation,
    progress tracking, and comprehensive error handling.
    """

    def __init__(self):
        """Initialize cleaner service."""
        pass

    def predict_space(self, files: List[FileInfo]) -> int:
        """
        Calculate predicted space to be freed from selected files.

        Only includes files that pass whitelist validation.

        Args:
            files: List of files to calculate space for

        Returns:
            Predicted space in bytes
        """
        total_space = 0

        for file_info in files:
            # Skip protected files
            if whitelist_service.is_protected(file_info.path):
                continue

            # Skip files that can't be safely deleted
            if not file_info.can_delete():
                continue

            total_space += file_info.size

        return total_space

    def clean_files(self, operation: CleaningOperation,
                   progress_callback: Optional[Callable] = None,
                   cancellation_token: Optional[threading.Event] = None) -> CleaningOperation:
        """
        Execute the cleaning operation.

        Args:
            operation: Cleaning operation to execute
            progress_callback: Callback for progress updates (percentage, current_module, files_processed, total_files)
            cancellation_token: Event to signal cancellation

        Returns:
            Updated cleaning operation with results
        """
        if cancellation_token is None:
            cancellation_token = threading.Event()

        # Mark operation as in progress
        operation.status = "in_progress"
        operation.progress_percentage = 0.0

        start_time = time.time()
        total_files = len(operation.selected_files)
        processed_files = 0
        total_space_freed = 0

        try:
            # Process files by module for better progress tracking
            module_groups = self._group_files_by_module(operation.selected_files)

            # Track if we've stopped Windows Update service
            windows_update_service_stopped = False
            
            for module_name, files in module_groups.items():
                if cancellation_token.is_set():
                    operation.mark_cancelled()
                    break

                operation.current_module = module_name

                # For Windows Update files, always try to stop Windows Update service first
                if module_name == "Windows 更新残留" and not windows_update_service_stopped:
                    print(f"检测到Windows更新残留文件，尝试停止Windows Update服务...")
                    if self._try_stop_windows_update_service():
                        windows_update_service_stopped = True
                        # Wait a moment for services to fully stop
                        time.sleep(2)
                    else:
                        print("警告：无法停止Windows Update服务，文件删除可能失败")

                # Process files in batches for better performance
                batch_size = 50
                last_callback_time = time.time()
                callback_interval = 0.1  # Callback every 100ms to avoid UI lag

                for i in range(0, len(files), batch_size):
                    if cancellation_token.is_set():
                        operation.mark_cancelled()
                        break

                    batch = files[i:i + batch_size]
                    
                    # Process batch
                    for file_info in batch:
                        if cancellation_token.is_set():
                            operation.mark_cancelled()
                            break

                        # Attempt to delete the file
                        success, space_freed, error_msg = self._delete_single_file(file_info)

                        if success:
                            total_space_freed += space_freed
                        else:
                            operation.add_failed_file(file_info, error_msg)

                        processed_files += 1

                    # Update progress less frequently to avoid UI lag
                    current_time = time.time()
                    if current_time - last_callback_time >= callback_interval or processed_files == total_files:
                        progress_percentage = (processed_files / total_files) * 100.0
                        operation.update_progress(progress_percentage, module_name)

                        # Progress callback (throttled)
                        if progress_callback:
                            progress_callback(progress_percentage, module_name, processed_files, total_files)
                        last_callback_time = current_time

            # Mark operation as completed
            if not cancellation_token.is_set():
                duration = time.time() - start_time
                operation.mark_completed(total_space_freed, duration)

        except Exception as e:
            operation.mark_failed(f"Unexpected error during cleaning: {e}")

        return operation

    def _group_files_by_module(self, files: List[FileInfo]) -> dict:
        """
        Group files by their module for organized processing.

        Args:
            files: List of files to group

        Returns:
            Dict mapping module names to lists of files
        """
        groups = {}

        for file_info in files:
            module = file_info.module or "未知模块"
            if module not in groups:
                groups[module] = []
            groups[module].append(file_info)

        return groups

    def _delete_single_file(self, file_info: FileInfo) -> tuple:
        """
        Delete a single file with safety checks and detailed error reporting.

        Args:
            file_info: File to delete

        Returns:
            Tuple of (success: bool, space_freed: int, error_message: str)
        """
        try:
            # Check for specialized cleaner
            cleaner = self._get_cleaner_for_module(file_info.module)
            if cleaner:
                # Use specialized cleaner
                result = cleaner.clean_file(file_info)
                return result['success'], result['space_freed'], result.get('error', result.get('message', ''))

            # Default handling for other files
            # Final safety check - validate whitelist
            if whitelist_service.is_protected(file_info.path):
                return False, 0, "文件受保护，无法删除"

            # Validate path is within C drive
            try:
                validate_c_drive_path(file_info.path)
            except ValueError as e:
                return False, 0, str(e)

            # Check if file exists
            import os
            if not os.path.exists(file_info.path):
                return False, 0, "文件不存在"

            # Attempt deletion with detailed error handling and retry logic
            try:
                # Try to delete the file
                if os.path.isfile(file_info.path):
                    # For Windows Update files, try multiple strategies
                    if file_info.module == "Windows 更新残留":
                        return self._delete_windows_update_file(file_info)
                    else:
                        # For other files, use standard deletion with retry
                        return self._delete_file_with_retry(file_info.path, file_info.size, max_attempts=3)
                elif os.path.isdir(file_info.path):
                    import shutil
                    # For directories, try to remove read-only files first
                    try:
                        import stat
                        for root, dirs, files in os.walk(file_info.path):
                            for d in dirs:
                                dir_path = os.path.join(root, d)
                                try:
                                    os.chmod(dir_path, stat.S_IWRITE | os.stat(dir_path).st_mode)
                                except:
                                    pass
                            for f in files:
                                file_path = os.path.join(root, f)
                                try:
                                    os.chmod(file_path, stat.S_IWRITE | os.stat(file_path).st_mode)
                                except:
                                    pass
                    except Exception:
                        pass
                    
                    shutil.rmtree(file_info.path)
                    return True, file_info.size, ""
                else:
                    return False, 0, "路径既不是文件也不是目录"
                    
            except PermissionError as e:
                return False, 0, f"权限不足: {str(e)}"
            except OSError as e:
                error_msg = str(e)
                if "being used by another process" in error_msg.lower() or "被另一个程序使用" in error_msg:
                    return False, 0, "文件被其他程序占用"
                elif "access is denied" in error_msg.lower() or "拒绝访问" in error_msg:
                    return False, 0, "访问被拒绝（可能需要管理员权限）"
                else:
                    return False, 0, f"系统错误: {error_msg}"
            except Exception as e:
                return False, 0, f"删除失败: {str(e)}"

        except Exception as e:
            return False, 0, f"删除过程中发生错误: {e}"

    def _delete_file_with_retry(self, file_path: str, file_size: int, max_attempts: int = 3) -> tuple:
        """
        Delete a file with retry logic and multiple strategies.
        
        Args:
            file_path: Path to file
            file_size: Size of file
            max_attempts: Maximum retry attempts
            
        Returns:
            Tuple of (success: bool, space_freed: int, error_message: str)
        """
        import stat
        
        for attempt in range(max_attempts):
            try:
                # Strategy 1: Remove read-only attribute and delete
                try:
                    current_mode = os.stat(file_path).st_mode
                    os.chmod(file_path, stat.S_IWRITE | current_mode)
                except Exception:
                    pass
                
                os.remove(file_path)
                # Verify deletion
                if not os.path.exists(file_path):
                    return True, file_size, ""
                    
            except PermissionError as e:
                if attempt < max_attempts - 1:
                    time.sleep(0.5)
                    continue
                else:
                    # Try using subprocess as fallback
                    return self._delete_file_with_subprocess(file_path, file_size, str(e))
                    
            except OSError as e:
                error_str = str(e).lower()
                if "being used" in error_str or "被另一个程序使用" in error_str or "另一个程序正在使用" in error_str:
                    # File is locked - try subprocess immediately
                    return self._delete_file_with_subprocess(file_path, file_size, str(e))
                else:
                    if attempt < max_attempts - 1:
                        time.sleep(0.5)
                        continue
                    else:
                        # Try using subprocess as fallback
                        return self._delete_file_with_subprocess(file_path, file_size, str(e))
        
        # If os.remove failed, try subprocess as last resort
        return self._delete_file_with_subprocess(file_path, file_size, "os.remove失败")
    
    def _delete_file_with_subprocess(self, file_path: str, file_size: int, original_error: str) -> tuple:
        """
        Try to delete file using subprocess (Windows del command).
        
        Args:
            file_path: Path to file
            file_size: Size of file
            original_error: Original error message
            
        Returns:
            Tuple of (success: bool, space_freed: int, error_message: str)
        """
        try:
            # Use Windows del command with force flag
            # /F = force delete read-only files
            # /Q = quiet mode (no confirmation)
            # Use quotes around path to handle spaces
            quoted_path = f'"{file_path}"'
            result = subprocess.run(f'del /F /Q {quoted_path}',
                                  shell=True, capture_output=True, text=True, timeout=10)
            
            # Wait a moment for file system to update
            time.sleep(0.2)
            
            # Verify file was deleted
            if not os.path.exists(file_path):
                return True, file_size, ""
            elif result.returncode == 0:
                # Command succeeded but file still exists - might be a timing issue
                time.sleep(0.5)
                if not os.path.exists(file_path):
                    return True, file_size, ""
                else:
                    return False, 0, f"删除命令执行成功但文件仍存在（可能被占用）: {original_error}"
            else:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                return False, 0, f"删除命令失败: {error_msg or original_error}"
        except subprocess.TimeoutExpired:
            return False, 0, f"删除操作超时: {original_error}"
        except Exception as e:
            return False, 0, f"删除失败: {original_error} (subprocess错误: {str(e)})"
    
    def _delete_windows_update_file(self, file_info: FileInfo) -> tuple:
        """
        Delete Windows Update file with enhanced strategies and detailed logging.
        
        Args:
            file_info: File information
            
        Returns:
            Tuple of (success: bool, space_freed: int, error_message: str)
        """
        file_path = file_info.path
        last_error = None
        
        # Check if this is a database file that might be locked
        is_database_file = file_path.endswith('.edb') or 'DataStore' in file_path
        
        # For database files, we might need to skip them if they're locked
        if is_database_file:
            # Check if file is locked by trying to open it
            try:
                # Try to open file in exclusive mode to check if it's locked
                with open(file_path, 'r+b'):
                    pass
            except (PermissionError, OSError) as e:
                error_str = str(e).lower()
                if "being used" in error_str or "被另一个程序使用" in error_str or "另一个程序正在使用" in error_str:
                    return False, 0, f"文件被Windows Update服务占用，无法删除（数据库文件通常需要停止服务后删除）"
        
        # Strategy 1: Try standard deletion first (will use subprocess if file is locked)
        result = self._delete_file_with_retry(file_path, file_info.size, max_attempts=2)
        if result[0]:
            return result
        last_error = result[2] if len(result) > 2 else "标准删除失败"
        
        # Strategy 2: Use attrib to remove all attributes
        try:
            attrib_result = subprocess.run(['attrib', '-R', '-S', '-H', file_path],
                          capture_output=True, text=True, shell=True, timeout=5)
            if attrib_result.returncode == 0:
                # Try deletion again after removing attributes
                result = self._delete_file_with_retry(file_path, file_info.size, max_attempts=2)
                if result[0]:
                    return result
                last_error = result[2] if len(result) > 2 else last_error
        except Exception as e:
            pass
        
        # Strategy 3: Take ownership and grant permissions
        try:
            # Take ownership
            takeown_result = subprocess.run(['takeown', '/F', file_path],
                          capture_output=True, text=True, shell=True, timeout=5)
            # Grant full control
            icacls_result = subprocess.run(['icacls', file_path, '/grant', 'Administrators:F'],
                          capture_output=True, text=True, shell=True, timeout=5)
            # Try deletion again
            result = self._delete_file_with_retry(file_path, file_info.size, max_attempts=2)
            if result[0]:
                return result
            last_error = result[2] if len(result) > 2 else last_error
        except Exception as e:
            pass
        
        # Strategy 4: Force delete using subprocess with multiple approaches
        strategies = [
            # Approach 1: Simple del command
            f'del /F /Q "{file_path}"',
            # Approach 2: Using cmd /c
            f'cmd /c del /F /Q "{file_path}"',
            # Approach 3: Using PowerShell
            f'powershell -Command "Remove-Item -Path \'{file_path}\' -Force -ErrorAction SilentlyContinue"',
        ]
        
        for strategy_cmd in strategies:
            try:
                result = subprocess.run(strategy_cmd,
                                      shell=True, capture_output=True, text=True, timeout=10)
                time.sleep(0.3)
                if not os.path.exists(file_path):
                    return True, file_info.size, ""
            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue
        
        # Strategy 5: Try using Windows API if available
        try:
            if self._delete_file_with_win32api(file_path):
                if not os.path.exists(file_path):
                    return True, file_info.size, ""
        except Exception:
            pass
        
        # All strategies failed - provide detailed error message
        if last_error:
            if "being used" in last_error.lower() or "被另一个程序使用" in last_error or "另一个程序正在使用" in last_error:
                error_msg = f"文件被占用: {os.path.basename(file_path)} 正在被Windows Update服务使用，无法删除。建议：1) 停止Windows Update服务 2) 重启系统后删除 3) 使用Windows磁盘清理工具"
            elif "权限" in last_error or "permission" in last_error.lower():
                error_msg = f"权限不足: {os.path.basename(file_path)} 需要管理员权限或文件被系统保护"
            else:
                error_msg = f"删除失败: {last_error}"
        else:
            error_msg = "所有删除策略均失败，文件可能被系统保护或正在使用"
        
        return False, 0, error_msg
    
    def _delete_file_with_win32api(self, file_path: str) -> bool:
        """
        Try to delete file using Windows API (win32api).
        
        Args:
            file_path: Path to file
            
        Returns:
            True if deletion attempted (may still fail)
        """
        try:
            import win32api
            import win32con
            
            # Set file attributes to normal
            win32api.SetFileAttributes(file_path, win32con.FILE_ATTRIBUTE_NORMAL)
            # Delete file
            win32api.DeleteFile(file_path)
            return True
        except ImportError:
            # win32api not available
            return False
        except Exception:
            return False

    def _get_cleaner_for_module(self, module_name: str):
        """Get specialized cleaner for a module if available."""
        # Initialize cleaners if not already done
        if not hasattr(self, '_cleaners'):
            self._cleaners = {}
            try:
                from cleaners.hibernation_cleaner import HibernationCleaner
                self._cleaners["休眠文件"] = HibernationCleaner()
            except ImportError:
                pass
            try:
                from cleaners.recycle_bin_cleaner import RecycleBinCleaner
                self._cleaners["回收站"] = RecycleBinCleaner()
            except ImportError:
                pass
        
        return self._cleaners.get(module_name)
    
    def _try_stop_windows_update_service(self):
        """Try to stop Windows Update service to allow file deletion."""
        try:
            # Try to stop Windows Update service using sc command (more reliable)
            result = subprocess.run(['sc', 'stop', 'wuauserv'], 
                                  capture_output=True, text=True, shell=True, timeout=15)
            if result.returncode == 0 or "STOP_PENDING" in result.stdout:
                print("Windows Update服务正在停止...")
                # Wait for service to stop
                time.sleep(3)
                # Also stop related services
                try:
                    subprocess.run(['sc', 'stop', 'cryptSvc'], 
                                  capture_output=True, text=True, shell=True, timeout=5)
                    subprocess.run(['sc', 'stop', 'bits'], 
                                  capture_output=True, text=True, shell=True, timeout=5)
                except Exception:
                    pass
                return True
            else:
                # Try alternative method using net stop
                result = subprocess.run(['net', 'stop', 'wuauserv'], 
                                      capture_output=True, text=True, shell=True, timeout=15)
                if result.returncode == 0:
                    print("Windows Update服务已停止")
                    time.sleep(2)
                    return True
                else:
                    print(f"无法停止Windows Update服务: {result.stderr}")
                    return False
        except subprocess.TimeoutExpired:
            print("停止Windows Update服务超时")
            return False
        except Exception as e:
            print(f"停止Windows Update服务时出错: {e}")
            return False

    def _get_disk_space_info(self) -> int:
        """
        Get current disk space information.

        Returns:
            Available disk space in bytes (simplified for space calculation)
        """
        # For simplicity, return a mock value
        # In a real implementation, you'd use platform-specific APIs
        return 0

    def validate_cleaning_selection(self, files: List[FileInfo]) -> dict:
        """
        Validate that a selection of files can be safely cleaned.

        Args:
            files: Files to validate

        Returns:
            Dict with validation results
        """
        results = {
            'total_files': len(files),
            'safe_files': 0,
            'protected_files': 0,
            'unsafe_files': 0,
            'predicted_space': 0,
            'warnings': [],
            'errors': []
        }

        for file_info in files:
            # Check whitelist protection
            if whitelist_service.is_protected(file_info.path):
                results['protected_files'] += 1
                results['warnings'].append(f"受保护文件: {file_info.path}")
                continue

            # Check if file can be deleted
            if not file_info.can_delete():
                results['unsafe_files'] += 1
                results['errors'].append(f"无法安全删除: {file_info.path}")
                continue

            # File is safe to delete
            results['safe_files'] += 1
            results['predicted_space'] += file_info.size

        return results

    def delete_hiberfil_sys(self, user_confirmed: bool) -> bool:
        """
        Delete hiberfil.sys file and disable hibernation.

        Args:
            user_confirmed: Whether user confirmed understanding of risks

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If user_confirmed is False
        """
        if not user_confirmed:
            raise ValueError("必须确认已了解删除休眠文件的风险")

        try:
            import subprocess

            # Disable hibernation via powercfg
            result = subprocess.run(['powercfg', '-h', 'off'],
                                  capture_output=True, text=True, shell=True)

            if result.returncode == 0:
                # Check if hiberfil.sys exists and delete it
                hiberfil_path = "C:\\hiberfil.sys"
                if safe_delete_file(hiberfil_path):
                    return True
                else:
                    # Hibernation disabled but file deletion failed
                    # This is still considered successful since hibernation is disabled
                    return True
            else:
                return False

        except Exception as e:
            print(f"Error deleting hiberfil.sys: {e}")
            return False

    def restore_hibernation(self) -> bool:
        """
        Restore hibernation functionality.

        Returns:
            True if successful, False otherwise
        """
        try:
            import subprocess

            # Enable hibernation via powercfg
            result = subprocess.run(['powercfg', '-h', 'on'],
                                  capture_output=True, text=True, shell=True)

            return result.returncode == 0

        except Exception as e:
            print(f"Error restoring hibernation: {e}")
            return False

    def get_cleaning_recommendations(self, scan_report) -> dict:
        """
        Get cleaning recommendations based on scan results.

        Args:
            scan_report: ScanReport to analyze

        Returns:
            Dict with cleaning recommendations
        """
        recommendations = {
            'safe_to_clean': [],
            'use_caution': [],
            'not_recommended': [],
            'total_safe_space': 0,
            'total_caution_space': 0
        }

        if not scan_report or not scan_report.modules:
            return recommendations

        for module in scan_report.modules:
            if module.risk_level == "low":
                recommendations['safe_to_clean'].append({
                    'module': module.module_name,
                    'files': len(module.files),
                    'space': module.total_size
                })
                recommendations['total_safe_space'] += module.total_size

            elif module.risk_level == "medium":
                recommendations['use_caution'].append({
                    'module': module.module_name,
                    'files': len(module.files),
                    'space': module.total_size
                })
                recommendations['total_caution_space'] += module.total_size

            elif module.risk_level == "high":
                recommendations['not_recommended'].append({
                    'module': module.module_name,
                    'files': len(module.files),
                    'space': module.total_size
                })

        return recommendations


# Global instance for easy import
cleaner_service = CleanerService()