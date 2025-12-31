"""
测试性能优化效果
"""

import os
import sys
import time
import threading

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_selection_performance():
    """测试选择性能"""
    print("=" * 60)
    print("测试选择性能优化")
    print("=" * 60)
    
    try:
        from ui.scan_view import ScanView
        from models.scan_report import ScanReport
        from models.scan_result import ScanResult
        from models.file_info import FileInfo
        from datetime import datetime
        import tkinter as tk
        
        # 创建测试窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        
        scan_view = ScanView(root)
        
        # 创建模拟扫描报告，包含大量文件
        report = ScanReport()
        report.status = "completed"
        
        # 创建Windows更新残留模块，包含大量文件
        updates_module = ScanResult(
            module_name="Windows 更新残留",
            risk_level="medium"
        )
        
        # 添加1000个模拟文件
        print("创建1000个模拟文件...")
        for i in range(1000):
            file_info = FileInfo(
                path=f"C:\\Windows\\SoftwareDistribution\\Download\\file_{i}.tmp",
                size=1024 * 100,  # 100KB each
                last_access_time=datetime.now(),
                last_modified_time=datetime.now(),
                module="Windows 更新残留"
            )
            updates_module.add_file(file_info)
        
        report.add_module_result(updates_module)
        
        # 显示扫描结果
        print("显示扫描结果...")
        start_time = time.time()
        scan_view.display_scan_results(report)
        display_time = time.time() - start_time
        print(f"显示耗时: {display_time:.2f} 秒")
        
        # 测试全选性能
        print("\n测试全选性能...")
        start_time = time.time()
        scan_view._select_all()
        select_time = time.time() - start_time
        print(f"全选耗时: {select_time:.2f} 秒")
        print(f"选中文件数: {len(scan_view.selected_files)}")
        
        # 测试取消选择性能
        print("\n测试取消选择性能...")
        start_time = time.time()
        scan_view._select_none()
        deselect_time = time.time() - start_time
        print(f"取消选择耗时: {deselect_time:.2f} 秒")
        
        # 测试查找性能
        print("\n测试查找性能...")
        # 先选中一些文件
        scan_view._select_all()
        
        # 测试查找性能（使用集合）
        start_time = time.time()
        for i in range(100):
            test_path = f"C:\\Windows\\SoftwareDistribution\\Download\\file_{i}.tmp"
            normalized = test_path.replace("\\\\", "\\")
            found = normalized in scan_view._selected_file_paths
        lookup_time = time.time() - start_time
        print(f"100次查找耗时: {lookup_time:.4f} 秒 (使用集合)")
        
        root.destroy()
        
        print("\n性能测试总结:")
        print(f"  显示扫描结果: {display_time:.2f} 秒")
        print(f"  全选操作: {select_time:.2f} 秒")
        print(f"  取消选择: {deselect_time:.2f} 秒")
        print(f"  查找性能: {lookup_time:.4f} 秒 (100次查找)")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_windows_updates_scan_limit():
    """测试Windows更新残留扫描限制"""
    print("\n" + "=" * 60)
    print("测试Windows更新残留扫描限制")
    print("=" * 60)
    
    try:
        from modules.windows_updates import WindowsUpdatesScanner
        
        scanner = WindowsUpdatesScanner()
        print(f"最大文件数限制: {scanner.max_total_files}")
        print(f"每目录最大文件数: {scanner.max_files_per_directory}")
        
        # 执行扫描
        print("\n执行扫描...")
        cancellation_token = threading.Event()
        start_time = time.time()
        result = scanner.scan(cancellation_token)
        scan_time = time.time() - start_time
        
        print(f"扫描耗时: {scan_time:.2f} 秒")
        print(f"找到文件数: {result.file_count}")
        print(f"总大小: {result.total_size / (1024*1024):.2f} MB")
        
        if result.file_count >= scanner.max_total_files:
            print(f"⚠ 已达到文件数量限制 ({scanner.max_total_files})")
        else:
            print(f"✓ 文件数量在限制范围内")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("性能优化验证测试")
    print("=" * 60)
    print()
    
    # 测试选择性能
    test_selection_performance()
    
    # 测试Windows更新残留扫描限制
    test_windows_updates_scan_limit()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

