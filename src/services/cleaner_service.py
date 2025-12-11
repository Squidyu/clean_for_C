"""
Cleaner Service

Coordinates cleaning operations with safety checks and progress tracking.
"""

import threading
import time
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

            for module_name, files in module_groups.items():
                if cancellation_token.is_set():
                    operation.mark_cancelled()
                    break

                operation.current_module = module_name

                # Process files in this module
                for file_info in files:
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

                    # Update progress
                    progress_percentage = (processed_files / total_files) * 100.0
                    operation.update_progress(progress_percentage, module_name)

                    # Progress callback
                    if progress_callback:
                        progress_callback(progress_percentage, module_name, processed_files, total_files)

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
        Delete a single file with safety checks.

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

            # Attempt deletion
            space_before = self._get_disk_space_info()

            if safe_delete_path(file_info.path):
                space_after = self._get_disk_space_info()
                space_freed = space_before - space_after if space_after < space_before else file_info.size
                return True, space_freed, ""
            else:
                return False, 0, "删除操作失败"

        except Exception as e:
            return False, 0, f"删除过程中发生错误: {e}"

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
        
        return self._cleaners.get(module_name)

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