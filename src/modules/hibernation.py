"""
Hibernation File Scanner

Scans for the Windows hibernation file (hiberfil.sys).
This is a special system file that enables Windows hibernation/sleep functionality.
"""

import os
import subprocess
from modules.base_scanner import BaseScanner
from models.file_info import FileInfo
from models.hibernation_file_info import HibernationFileInfo
from utils.path_utils import validate_c_drive_path


class HibernationScanner(BaseScanner):
    """
    Scanner for Windows hibernation file.

    This scanner detects and analyzes the hiberfil.sys file,
    which is used by Windows for hibernation (sleep) functionality.
    Supports Windows 7, 8, 8.1, 10, and 11.
    """

    def __init__(self):
        """Initialize the hibernation scanner with system-specific configuration."""
        super().__init__()
        from utils.system_info import system_info
        self.system_info = system_info

    def get_module_name(self) -> str:
        """Get module name."""
        return "休眠文件"

    def get_risk_level(self) -> str:
        """Get risk level - medium risk for hibernation file (can be safely disabled)."""
        return "medium"

    def scan(self, cancellation_token) -> 'ScanResult':
        """
        Scan for hibernation file.

        Checks for hiberfil.sys existence, size, and hibernation status.

        Args:
            cancellation_token: Event to cancel scanning

        Returns:
            ScanResult with hibernation file information
        """
        from models.scan_result import ScanResult

        result = ScanResult(
            module_name=self.get_module_name(),
            risk_level=self.get_risk_level()
        )

        try:
            # Check if current Windows version supports hibernation
            if not self.system_info.supports_feature('hibernation'):
                result.error_message = "当前 Windows 版本不支持休眠功能"
                return result

            # Check hibernation file
            hibernation_info = self._check_hibernation_file()

            if hibernation_info.exists:
                # Create FileInfo for the hibernation file
                file_info = FileInfo(
                    path=hibernation_info.file_path,
                    size=hibernation_info.file_size_bytes,
                    last_access_time=hibernation_info.last_checked,
                    last_modified_time=hibernation_info.last_checked,
                    module=self.get_module_name()
                )

                # Mark as not protected - hibernation can be safely disabled
                file_info.is_protected = False

                # Add version-specific description
                version = self.system_info.get_windows_version()
                if version in [WindowsVersion.WINDOWS_7]:
                    file_info.description = "Windows 7 休眠文件 - 包含内存状态以实现快速启动"
                elif version in [WindowsVersion.WINDOWS_8, WindowsVersion.WINDOWS_8_1]:
                    file_info.description = "Windows 8/8.1 休眠文件 - 支持混合启动和休眠功能"
                elif version in [WindowsVersion.WINDOWS_10, WindowsVersion.WINDOWS_11]:
                    file_info.description = "Windows 10/11 休眠文件 - 支持快速启动和休眠恢复"

                result.add_file(file_info)

        except Exception as e:
            result.error_message = f"扫描休眠文件时出错: {e}"

        return result

    def _check_hibernation_file(self) -> HibernationFileInfo:
        """
        Check hibernation file status and information.

        Returns:
            HibernationFileInfo with current status
        """
        hibernation_info = HibernationFileInfo()

        try:
            # Check if hibernation file exists
            if os.path.exists(hibernation_info.file_path):
                hibernation_info.exists = True

                # Get file size
                try:
                    stat = os.stat(hibernation_info.file_path)
                    hibernation_info.file_size_bytes = stat.st_size
                except (OSError, IOError):
                    # If we can't get size, file might be in use
                    pass

            # Check hibernation status using powercfg
            hibernation_info.hibernation_enabled = self._check_hibernation_enabled()

            # Set impact description
            hibernation_info.impact_description = self._get_impact_description(hibernation_info)

            # Determine if can delete
            hibernation_info.can_delete = hibernation_info.exists and not hibernation_info.hibernation_enabled

        except Exception:
            # If anything fails, assume hibernation is enabled and file exists
            hibernation_info.hibernation_enabled = True
            hibernation_info.exists = True
            hibernation_info.can_delete = False

        return hibernation_info

    def _check_hibernation_enabled(self) -> bool:
        """
        Check if hibernation is currently enabled.

        Returns:
            True if hibernation is enabled, False otherwise
        """
        try:
            from utils.system_info import system_info
            
            # Get appropriate powercfg command for the current Windows version
            command = system_info.get_powercfg_command('check_status')
            
            result = subprocess.run(command,
                                  capture_output=True, text=True, shell=True)

            if result.returncode == 0:
                output = result.stdout.lower()
                # Look for hibernation in available sleep states
                return 'hibernation' in output or '休眠' in output
            else:
                # If command fails, assume hibernation is enabled (safer default)
                return True

        except Exception:
            # If anything fails, assume hibernation is enabled
            return True

    def _get_impact_description(self, hibernation_info: HibernationFileInfo) -> str:
        """
        Get description of the impact of deleting hibernation file.

        Args:
            hibernation_info: Hibernation file information

        Returns:
            Description string
        """
        if not hibernation_info.exists:
            return "休眠文件不存在，系统可能已禁用休眠功能。"

        size_mb = hibernation_info.file_size_bytes / (1024 * 1024)

        if hibernation_info.hibernation_enabled:
            return f"""删除休眠文件将禁用 Windows 休眠功能。

文件大小: {size_mb:.1f} MB

⚠️ 重要警告:
• 系统将无法进入休眠状态
• 快速启动功能可能会受影响
• 如果需要恢复休眠，需要重新启用
• 此操作需要管理员权限"""

        else:
            return f"""休眠文件存在但休眠功能已禁用。

文件大小: {size_mb:.1f} MB

此文件可以安全删除，不会影响系统功能。"""

    def get_hibernation_status(self) -> HibernationFileInfo:
        """
        Get current hibernation status.

        This is a convenience method for external access.

        Returns:
            HibernationFileInfo with current status
        """
        return self._check_hibernation_file()

    def can_delete_hibernation_file(self) -> bool:
        """
        Check if hibernation file can be safely deleted.

        Returns:
            True if file can be deleted, False otherwise
        """
        hibernation_info = self._check_hibernation_file()
        return hibernation_info.exists  # Can always delete if file exists

    def disable_hibernation_and_clean(self) -> dict:
        """
        Elegantly disable hibernation and clean up hibernation file.

        This method will:
        1. Disable hibernation using powercfg command
        2. Wait for system to delete hiberfil.sys
        3. Verify the file was removed

        Returns:
            dict with operation results:
            - success: bool - Whether operation succeeded
            - message: str - Status message
            - original_size: int - Size of file before deletion (bytes)
            - hibernation_was_enabled: bool - Whether hibernation was enabled
        """
        result = {
            'success': False,
            'message': '',
            'original_size': 0,
            'hibernation_was_enabled': False
        }

        try:
            # Check current status
            hibernation_info = self._check_hibernation_file()
            result['original_size'] = hibernation_info.file_size_bytes
            result['hibernation_was_enabled'] = hibernation_info.hibernation_enabled

            if not hibernation_info.exists:
                result['success'] = True
                result['message'] = '休眠文件不存在，无需清理'
                return result

            # Disable hibernation
            if hibernation_info.hibernation_enabled:
                # Use powercfg /h off to disable hibernation
                disable_result = subprocess.run(['powercfg', '/h', 'off'],
                                           capture_output=True, text=True, shell=True)
                
                if disable_result.returncode != 0:
                    result['message'] = f'禁用休眠功能失败: {disable_result.stderr}'
                    return result

            # Give system a moment to delete the file
            import time
            time.sleep(2)

            # Check if file was deleted
            if os.path.exists(hibernation_info.file_path):
                # File still exists, try to delete it directly
                try:
                    os.remove(hibernation_info.file_path)
                except (OSError, IOError) as e:
                    result['message'] = f'无法删除休眠文件，可能需要管理员权限: {e}'
                    return result

            # Final verification
            if not os.path.exists(hibernation_info.file_path):
                size_mb = result['original_size'] / (1024 * 1024)
                result['success'] = True
                
                if result['hibernation_was_enabled']:
                    result['message'] = f'已成功禁用休眠功能并清理 {size_mb:.1f} MB 休眠文件'
                else:
                    result['message'] = f'已成功清理 {size_mb:.1f} MB 休眠文件'
                
                # Additional info
                result['message'] += '''

提示：
• 系统将无法进入休眠状态
• 可以使用 powercfg /h on 重新启用休眠
• 快速启动功能可能会受影响'''
            else:
                result['message'] = '休眠文件删除失败'

        except Exception as e:
            result['message'] = f'清理休眠文件时发生错误: {e}'

        return result

    def reenable_hibernation(self) -> dict:
        """
        Re-enable hibernation functionality.

        Returns:
            dict with operation results:
            - success: bool - Whether operation succeeded
            - message: str - Status message
        """
        result = {'success': False, 'message': ''}

        try:
            # Use powercfg /h on to enable hibernation
            enable_result = subprocess.run(['powercfg', '/h', 'on'],
                                       capture_output=True, text=True, shell=True)

            if enable_result.returncode == 0:
                result['success'] = True
                result['message'] = '休眠功能已重新启用'
            else:
                result['message'] = f'启用休眠功能失败: {enable_result.stderr}'

        except Exception as e:
            result['message'] = f'启用休眠功能时发生错误: {e}'

        return result