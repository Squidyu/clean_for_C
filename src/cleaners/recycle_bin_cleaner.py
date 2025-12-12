#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recycle Bin Cleaner

Specialized cleaner for Windows Recycle Bin files.
These files are safe to delete since users have already deleted them once.
"""

import os
from utils.file_utils import safe_delete_path
from utils.path_utils import validate_c_drive_path


class RecycleBinCleaner:
    """
    Cleaner for Windows Recycle Bin contents.
    
    Recycle bin files are special - they're already "deleted" by users,
    so permanently deleting them is safe and expected.
    """
    
    def clean_file(self, file_info):
        """
        Clean a single recycle bin file.
        
        Args:
            file_info: FileInfo object representing the file to delete
            
        Returns:
            Dict with cleaning results:
            - success: bool - whether deletion succeeded
            - space_freed: int - bytes freed
            - error: str - error message if failed
        """
        try:
            # Recycle bin files are safe to delete - no whitelist check needed
            # They are already in the recycle bin, so user intended to delete them
            
            # Validate the path is in recycle bin
            if not file_info.path.lower().startswith("c:\\$recycle.bin"):
                return {
                    'success': False,
                    'space_freed': 0,
                    'error': '不是回收站文件路径'
                }
            
            # Validate path is safe (but allow recycle bin paths)
            try:
                validated_path = validate_c_drive_path(file_info.path)
            except ValueError as e:
                return {
                    'success': False,
                    'space_freed': 0,
                    'error': f'路径验证失败: {str(e)}'
                }
            
            # Check if file still exists
            if not os.path.exists(validated_path):
                return {
                    'success': True,
                    'space_freed': file_info.size,
                    'error': None  # File already deleted
                }
            
            # Attempt to delete the file
            if safe_delete_path(validated_path):
                return {
                    'success': True,
                    'space_freed': file_info.size,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'space_freed': 0,
                    'error': '删除操作失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'space_freed': 0,
                'error': f'删除过程中发生错误: {str(e)}'
            }
    
    def clean_all(self, files):
        """
        Clean all recycle bin files.
        
        Args:
            files: List of FileInfo objects to delete
            
        Returns:
            Dict with aggregate results
        """
        total_success = 0
        total_failed = 0
        total_space_freed = 0
        errors = []
        
        for file_info in files:
            result = self.clean_file(file_info)
            
            if result['success']:
                total_success += 1
                total_space_freed += result['space_freed']
            else:
                total_failed += 1
                error_msg = f"{os.path.basename(file_info.path)}: {result['error']}"
                errors.append(error_msg)
        
        return {
            'success': total_failed == 0,
            'total_files': len(files),
            'success_count': total_success,
            'failed_count': total_failed,
            'total_space_freed': total_space_freed,
            'errors': errors
        }