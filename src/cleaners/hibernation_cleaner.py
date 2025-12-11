"""
Hibernation File Cleaner

Specialized cleaner for Windows hibernation file that gracefully disables
hibernation before attempting to delete the file.
"""

import os
import subprocess
from typing import Optional
from clean_holders.base_cleaner import BaseCleaner
from models.file_info import FileInfo
from modules.hibernation import HibernationScanner


class HibernationCleaner(BaseCleaner):
    """
    Cleaner for Windows hibernation file.
    
    This cleaner handles the special case of hiberfil.sys by first
    disabling hibernation, then removing the file.
    """

    def get_module_name(self) -> str:
        """Get the module name this cleaner handles."""
        return "休眠文件"

    def can_clean(self, file_info: FileInfo) -> bool:
        """
        Check if we can clean the given file.
        
        Args:
            file_info: File information
            
        Returns:
            True if can clean, False otherwise
        """
        # Can always clean hibernation files - we'll disable hibernation first
        return file_info.module == self.get_module_name()

    def clean_file(self, file_info: FileInfo, progress_callback=None) -> dict:
        """
        Clean a hibernation file by first disabling hibernation.
        
        Args:
            file_info: File information to clean
            progress_callback: Optional callback for progress updates
            
        Returns:
            dict with cleaning results
        """
        result = {
            'success': False,
            'message': '',
            'space_freed': 0,
            'error': None
        }

        try:
            from utils.system_info import system_info, WindowsVersion
            
            # Check if Windows version supports hibernation
            if not system_info.supports_feature('hibernation'):
                result['message'] = "当前 Windows 版本不支持休眠功能"
                result['error'] = "Version not supported"
                return result

            # Report progress
            if progress_callback:
                version = system_info.get_windows_version()
                version_name = {
                    WindowsVersion.WINDOWS_7: "Windows 7",
                    WindowsVersion.WINDOWS_8: "Windows 8",
                    WindowsVersion.WINDOWS_8_1: "Windows 8.1",
                    WindowsVersion.WINDOWS_10: "Windows 10",
                    WindowsVersion.WINDOWS_11: "Windows 11"
                }.get(version, "Windows")
                progress_callback(0, f"正在准备禁用 {version_name} 休眠功能...")

            # Initialize hibernation scanner
            hibernation_scanner = HibernationScanner()
            
            # Disable hibernation and clean
            clean_result = hibernation_scanner.disable_hibernation_and_clean()
            
            if clean_result['success']:
                result['success'] = True
                result['space_freed'] = clean_result['original_size']
                
                # Add version-specific information to the message
                base_message = clean_result['message']
                version_note = ""
                
                if version == WindowsVersion.WINDOWS_7:
                    version_note = "\n注意：禁用休眠后，Windows 7 的快速启动功能也会被禁用"
                elif version in [WindowsVersion.WINDOWS_8, WindowsVersion.WINDOWS_8_1]:
                    version_note = "\n注意：混合启动功能将被禁用，但可以稍后重新启用"
                elif version in [WindowsVersion.WINDOWS_10, WindowsVersion.WINDOWS_11]:
                    version_note = "\n注意：快速启动功能将被禁用，但系统启动仍保持优化"
                
                result['message'] = base_message + version_note
                
                # Report completion
                if progress_callback:
                    progress_callback(100, f"{version_name} 休眠文件清理完成")
            else:
                result['success'] = False
                result['error'] = clean_result['message']
                result['message'] = f"清理休眠文件失败: {clean_result['message']}"

        except Exception as e:
            error_msg = f"清理休眠文件时发生错误: {e}"
            result['success'] = False
            result['error'] = error_msg
            result['message'] = error_msg

        return result

    def get_cleanup_description(self, file_info: FileInfo) -> str:
        """
        Get a description of what will be cleaned.
        
        Args:
            file_info: File information
            
        Returns:
            Description string
        """
        if file_info.module != self.get_module_name():
            return ""

        scanner = HibernationScanner()
        hibernation_info = scanner.get_hibernation_status()
        
        if hibernation_info.hibernation_enabled:
            return """将禁用休眠功能并删除休眠文件：
• 使用 powercfg /h off 禁用休眠
• 系统自动删除 hiberfil.sys 文件
• 释放磁盘空间
• 如需恢复，可使用 powercfg /h on"""
        else:
            return """删除休眠文件：
• 休眠功能已禁用，可直接删除文件
• 释放磁盘空间
• 不影响系统其他功能"""

    def requires_admin_privileges(self, file_info: FileInfo) -> bool:
        """
        Check if cleaning requires administrator privileges.
        
        Args:
            file_info: File information
            
        Returns:
            True if admin privileges required
        """
        return True  # Disabling hibernation requires admin privileges

    def can_undo(self) -> bool:
        """
        Check if the cleaning operation can be undone.
        
        Returns:
            True if can undo, False otherwise
        """
        return True  # Can re-enable hibernation

    def undo_clean(self, original_file_info: FileInfo) -> dict:
        """
        Undo the cleaning operation by re-enabling hibernation.
        
        Args:
            original_file_info: Original file information
            
        Returns:
            dict with undo results
        """
        result = {
            'success': False,
            'message': '',
            'error': None
        }

        try:
            scanner = HibernationScanner()
            enable_result = scanner.reenable_hibernation()
            
            if enable_result['success']:
                result['success'] = True
                result['message'] = enable_result['message']
            else:
                result['success'] = False
                result['error'] = enable_result['message']
                result['message'] = enable_result['message']

        except Exception as e:
            error_msg = f"恢复休眠功能时发生错误: {e}"
            result['success'] = False
            result['error'] = error_msg
            result['message'] = error_msg

        return result