#!/usr/bin/env python3
"""
测试休眠文件和Windows更新模块的功能
"""

import sys
import os
import threading

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if os.path.join(current_dir, 'src') not in sys.path:
    sys.path.insert(0, os.path.join(current_dir, 'src'))

from modules.hibernation import HibernationScanner
from modules.windows_updates import WindowsUpdatesScanner
from utils.size_utils import format_bytes


def test_hibernation_module():
    """测试休眠文件模块"""
    print("=" * 60)
    print("🔍 测试休眠文件模块")
    print("=" * 60)

    try:
        scanner = HibernationScanner()
        print(f"模块名称: {scanner.get_module_name()}")
        print(f"风险等级: {scanner.get_risk_level()}")

        # 获取休眠文件状态
        hibernation_info = scanner.get_hibernation_status()
        print("\n休眠文件状态:")
        print(f"  文件存在: {hibernation_info.exists}")
        print(f"  文件路径: {hibernation_info.file_path}")
        if hibernation_info.exists:
            print(f"  文件大小: {format_bytes(hibernation_info.file_size_bytes)}")
        print(f"  休眠已启用: {hibernation_info.hibernation_enabled}")
        print(f"  可以删除: {hibernation_info.can_delete}")
        print(f"  影响描述: {hibernation_info.impact_description}")

        # 执行扫描
        print("\n执行扫描...")
        cancellation_token = threading.Event()
        result = scanner.scan(cancellation_token)

        print("扫描结果:")
        print(f"  找到文件数: {result.file_count}")
        print(f"  总大小: {format_bytes(result.total_size)}")

        if result.files:
            print("  文件列表:")
            for i, file_info in enumerate(result.files, 1):
                print(f"    {i}. {file_info.path} ({format_bytes(file_info.size)})")
        else:
            print("  未找到任何文件")

        # ScanResult没有error_message属性，移除这个检查

        return result

    except Exception as e:
        print(f"❌ 休眠文件模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_windows_updates_module():
    """测试Windows更新残留模块"""
    print("\n" + "=" * 60)
    print("🔍 测试Windows更新残留模块")
    print("=" * 60)

    try:
        scanner = WindowsUpdatesScanner()
        print(f"模块名称: {scanner.get_module_name()}")
        print(f"风险等级: {scanner.get_risk_level()}")

        # 执行扫描
        print("\n执行扫描...")
        cancellation_token = threading.Event()
        result = scanner.scan(cancellation_token)

        print("扫描结果:")
        print(f"  找到文件数: {result.file_count}")
        print(f"  总大小: {format_bytes(result.total_size)}")

        if result.files:
            print("  文件列表 (前10个):")
            for i, file_info in enumerate(result.files[:10], 1):
                print(f"    {i}. {os.path.basename(file_info.path)} ({format_bytes(file_info.size)})")
                if hasattr(file_info, 'description') and file_info.description:
                    print(f"       描述: {file_info.description}")
        else:
            print("  未找到任何文件")

        # ScanResult没有error_message属性，移除这个检查

        # 显示扫描的路径
        try:
            update_paths = scanner._get_update_paths()
            print(f"\n扫描路径 ({len(update_paths)}个):")
            for path_info in update_paths:
                path = path_info['path']
                exists = os.path.exists(path)
                print(f"  {'✓' if exists else '✗'} {path} - {path_info['description']}")
                if exists:
                    if os.path.isfile(path):
                        try:
                            size = os.path.getsize(path)
                            print(f"    文件大小: {format_bytes(size)}")
                        except:
                            pass
                    elif os.path.isdir(path):
                        try:
                            files = []
                            for root, dirs, files_in_dir in os.walk(path):
                                files.extend([os.path.join(root, f) for f in files_in_dir])
                            print(f"    包含 {len(files)} 个文件")
                        except:
                            print("    无法访问目录")
        except Exception as e:
            print(f"  获取路径信息失败: {e}")

        return result

    except Exception as e:
        print(f"❌ Windows更新模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_system_info():
    """分析系统信息"""
    print("\n" + "=" * 60)
    print("🔍 系统信息分析")
    print("=" * 60)

    try:
        from utils.system_info import system_info
        info = system_info.get_version_info()

        print(f"Windows版本: {info['version'].value}")
        print(f"版本字符串: {info['version_string']}")
        print(f"构建号: {info['build_number']}")
        print(f"架构: {'64位' if info['is_64bit'] else '32位'}")
        print(f"平台信息: {info['platform_info']}")

        # 检查一些关键功能
        print("\n功能支持:")
        features_to_check = ['hibernation', 'windows_store', 'prefetch']
        for feature in features_to_check:
            supported = system_info.supports_feature(feature)
            print(f"  {feature}: {'✓' if supported else '✗'}")

    except Exception as e:
        print(f"❌ 获取系统信息失败: {e}")


def check_paths_existence():
    """检查关键路径是否存在"""
    print("\n" + "=" * 60)
    print("🔍 关键路径检查")
    print("=" * 60)

    paths_to_check = [
        ("C:\\hiberfil.sys", "休眠文件"),
        ("C:\\Windows\\SoftwareDistribution\\Download", "Windows Update下载缓存"),
        ("C:\\Windows\\SoftwareDistribution\\DataStore", "Windows Update数据存储"),
        ("C:\\Windows\\Servicing", "Windows服务文件夹"),
        ("C:\\Windows\\winsxs\\backup", "组件存储备份"),
        ("C:\\Windows\\Logs\\CBS", "CBS日志"),
        ("C:\\Windows\\Prefetch", "预读取文件"),
        ("C:\\$Recycle.Bin", "回收站"),
    ]

    for path, description in paths_to_check:
        exists = os.path.exists(path)
        print(f"  {'✓' if exists else '✗'} {path} - {description}")

        if exists:
            try:
                if os.path.isfile(path):
                    size = os.path.getsize(path)
                    print(f"    文件大小: {format_bytes(size)}")
                elif os.path.isdir(path):
                    # 粗略统计文件数量
                    file_count = 0
                    total_size = 0
                    try:
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                file_count += 1
                                try:
                                    total_size += os.path.getsize(os.path.join(root, file))
                                except:
                                    pass
                            if file_count > 1000:  # 避免遍历过多文件
                                break
                        print(f"    约 {file_count} 个文件, 总计 {format_bytes(total_size)}")
                    except:
                        print("    无法访问目录内容")
            except:
                pass


def main():
    """主测试函数"""
    print("🧹 Windows C盘清理工具 - 模块测试")
    print("开始测试休眠文件和Windows更新残留模块...\n")

    # 分析系统信息
    analyze_system_info()

    # 检查关键路径
    check_paths_existence()

    # 测试休眠文件模块
    hibernation_result = test_hibernation_module()

    # 测试Windows更新模块
    updates_result = test_windows_updates_module()

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    hibernation_files = hibernation_result.file_count if hibernation_result else 0
    updates_files = updates_result.file_count if updates_result else 0

    print(f"休眠文件模块: {'✓' if hibernation_files > 0 else '✗'} ({hibernation_files} 个文件)")
    print(f"Windows更新模块: {'✓' if updates_files > 0 else '✗'} ({updates_files} 个文件)")
    print(f"总计找到文件: {hibernation_files + updates_files} 个")

    if hibernation_files == 0 and updates_files == 0:
        print("\n⚠️  两个模块都没有找到文件，可能的原因:")
        print("  1. 系统确实很干净")
        print("  2. 模块代码存在bug")
        print("  3. 权限不足")
        print("  4. 路径不存在或为空")
    else:
        print("\n✅ 模块工作正常，已找到可清理的文件")

    print("\n测试完成！")


if __name__ == "__main__":
    main()
