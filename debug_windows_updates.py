#!/usr/bin/env python3
"""
调试Windows更新模块为什么没有找到文件
"""

import sys
import os
import threading
import time

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if os.path.join(current_dir, 'src') not in sys.path:
    sys.path.insert(0, os.path.join(current_dir, 'src'))

from modules.windows_updates import WindowsUpdatesScanner
from utils.size_utils import format_bytes


def debug_windows_updates():
    """详细调试Windows更新模块"""
    print("🔍 详细调试Windows更新模块")
    print("=" * 60)

    scanner = WindowsUpdatesScanner()

    # 获取扫描路径
    update_paths = scanner._get_update_paths()
    print(f"扫描路径配置 ({len(update_paths)}个):")
    for i, path_info in enumerate(update_paths, 1):
        path = path_info['path']
        exists = os.path.exists(path)
        print(f"  {i}. {'✓' if exists else '✗'} {path}")
        print(f"     描述: {path_info['description']}")
        print(f"     保护: {path_info.get('protected', False)}")

        # 如果路径存在，检查内容
        if exists:
            if os.path.isfile(path):
                try:
                    stat = os.stat(path)
                    size = stat.st_size
                    mtime = stat.st_mtime
                    age_days = (time.time() - mtime) / 86400

                    print(f"     类型: 文件")
                    print(f"     大小: {format_bytes(size)}")
                    print(f"     修改时间: {time.ctime(mtime)} ({age_days:.1f}天前)")

                    # 检查时间过滤
                    time_threshold = 7 * 86400  # 7 days
                    would_skip = time.time() - mtime < time_threshold
                    print(f"     时间过滤: {'跳过' if would_skip else '保留'} (阈值: 7天)")

                except Exception as e:
                    print(f"     错误: {e}")

            elif os.path.isdir(path):
                try:
                    # 统计目录内容
                    total_files = 0
                    total_size = 0
                    recent_files = 0
                    old_files = 0

                    for root, dirs, files in os.walk(path):
                        for file in files:
                            total_files += 1
                            file_path = os.path.join(root, file)
                            try:
                                stat = os.stat(file_path)
                                total_size += stat.st_size
                                age_days = (time.time() - stat.st_mtime) / 86400

                                if age_days < 7:
                                    recent_files += 1
                                else:
                                    old_files += 1
                            except:
                                pass

                    print(f"     类型: 目录")
                    print(f"     总文件数: {total_files}")
                    print(f"     总大小: {format_bytes(total_size)}")
                    print(f"     最近7天文件: {recent_files}")
                    print(f"     7天前文件: {old_files}")

                except Exception as e:
                    print(f"     错误: {e}")
        print()

    # 执行实际扫描
    print("执行模块扫描...")
    cancellation_token = threading.Event()
    result = scanner.scan(cancellation_token)

    print("扫描结果:")
    print(f"  文件数: {result.file_count}")
    print(f"  总大小: {format_bytes(result.total_size)}")

    if result.file_count > 0:
        print("  文件列表:")
        for i, file_info in enumerate(result.files[:5], 1):  # 只显示前5个
            print(f"    {i}. {file_info.path} ({format_bytes(file_info.size)})")
    else:
        print("  未找到任何文件")

    # 检查可能的过滤原因
    print("\n可能的过滤原因分析:")
    print("1. 时间过滤: 7天内文件被跳过")
    print("2. 权限问题: 无法访问某些目录")
    print("3. 白名单过滤: 文件被标记为受保护")
    print("4. 路径验证失败")

    # 测试具体路径
    print("\n测试具体路径扫描:")
    test_path = "C:\\Windows\\SoftwareDistribution\\Download"
    if os.path.exists(test_path):
        print(f"测试路径: {test_path}")

        # 手动遍历文件并测试_add_file_to_result
        print("手动测试文件添加:")
        for root, dirs, files in os.walk(test_path):
            for file in files:
                file_path = os.path.join(root, file)
                print(f"  测试文件: {os.path.basename(file_path)}")

                try:
                    stat = os.stat(file_path)
                    age_days = (time.time() - stat.st_mtime) / 86400
                    print(f"    大小: {format_bytes(stat.st_size)}")
                    print(f"    修改时间: {age_days:.1f}天前")

                    # 测试时间过滤
                    time_threshold = 7 * 86400
                    would_skip_time = time.time() - stat.st_mtime < time_threshold
                    print(f"    时间过滤: {'跳过' if would_skip_time else '保留'}")

                    if not would_skip_time:
                        # 尝试调用_add_file_to_result
                        try:
                            # 创建一个新的result对象来测试
                            from models.scan_result import ScanResult
                            test_result = ScanResult(module_name="测试", risk_level="low")

                            # 手动创建FileInfo对象来测试
                            from models.file_info import FileInfo
                            manual_file_info = FileInfo(
                                path=file_path,
                                size=stat.st_size,
                                last_access_time=stat.st_atime,
                                last_modified_time=stat.st_mtime,
                                module="测试"
                            )
                            manual_file_info.is_protected = False
                            manual_file_info.description = f"手动测试 - {os.path.basename(file_path)}"

                            print(f"    手动FileInfo创建: {manual_file_info.path}, 大小: {format_bytes(manual_file_info.size)}")
                            test_result.add_file(manual_file_info)
                            print(f"    手动添加结果: 成功 (文件数: {test_result.file_count})")

                            # 测试scanner的_add_file_to_result方法
                            scanner._add_file_to_result(file_path, "测试", False, result)

                        except Exception as e:
                            print(f"    添加结果: 失败 - {e}")
                    else:
                        print("    被时间过滤跳过")

                except Exception as e:
                    print(f"    状态检查失败: {e}")

                print()

        print(f"最终文件数: {result.file_count}")


if __name__ == "__main__":
    debug_windows_updates()
