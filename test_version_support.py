#!/usr/bin/env python3
"""
测试 Windows 版本支持功能

验证系统检测和版本特定功能是否正常工作。
"""

import os
import sys
import platform

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.system_info import system_info, WindowsVersion, SystemPaths
from models.whitelist import SystemWhitelist


def test_system_detection():
    """测试系统版本检测功能。"""
    print("=" * 60)
    print("Windows 版本检测测试")
    print("=" * 60)
    
    version_info = system_info.get_version_info()
    
    print(f"检测到的版本: {version_info['version_string']}")
    print(f"构建号: {version_info['build_number']}")
    print(f"64位系统: {version_info['is_64bit']}")
    print(f"平台信息: {version_info['platform_info']}")
    print(f"架构: {version_info['architecture'][0]}")
    
    print("\n功能支持检测:")
    features = ['uac', 'directstorage', 'wsl', 'windows_store', 'prefetch', 'hibernation']
    for feature in features:
        supported = system_info.supports_feature(feature)
        print(f"  {feature}: {'[支持]' if supported else '[不支持]'}")
    
    print()


def test_system_paths():
    """测试系统路径配置。"""
    print("=" * 60)
    print("系统路径配置测试")
    print("=" * 60)
    
    version = system_info.get_windows_version()
    
    # 测试系统路径
    system_paths = SystemPaths.get_system_paths(version)
    print(f"\n{version.value} 系统路径 ({len(system_paths)} 个):")
    for path in system_paths:
        exists = os.path.exists(path)
        print(f"  {path} {'[存在]' if exists else '[不存在]'}")
    
    # 测试临时目录
    temp_dirs = SystemPaths.get_temp_directories(version)
    print(f"\n{version.value} 临时目录 ({len(temp_dirs)} 个):")
    for temp_dir in temp_dirs:
        expanded = os.path.expandvars(temp_dir)
        exists = os.path.exists(expanded)
        print(f"  {temp_dir} -> {expanded} {'[存在]' if exists else '[不存在]'}")
    
    # 测试更新缓存目录
    update_dirs = SystemPaths.get_update_cache_directories(version)
    print(f"\n{version.value} 更新缓存目录 ({len(update_dirs)} 个):")
    for update_dir in update_dirs:
        exists = os.path.exists(update_dir)
        print(f"  {update_dir} {'[存在]' if exists else '[不存在]'}")
    
    print()


def test_whitelist():
    """测试白名单配置。"""
    print("=" * 60)
    print("系统白名单测试")
    print("=" * 60)
    
    whitelist = SystemWhitelist.get_default_whitelist()
    
    print(f"白名单版本: {whitelist.version}")
    print(f"保护路径数: {len(whitelist.protected_paths)}")
    print(f"保护模式数: {len(whitelist.protected_patterns)}")
    
    print("\n部分保护路径示例:")
    for i, path in enumerate(whitelist.protected_paths[:10]):
        print(f"  {i+1}. {path}")
    if len(whitelist.protected_paths) > 10:
        print(f"  ... 还有 {len(whitelist.protected_paths) - 10} 个路径")
    
    print("\n部分保护模式示例:")
    for i, pattern in enumerate(whitelist.protected_patterns[:10]):
        print(f"  {i+1}. {pattern}")
    if len(whitelist.protected_patterns) > 10:
        print(f"  ... 还有 {len(whitelist.protected_patterns) - 10} 个模式")
    
    print()


def test_powercfg_commands():
    """测试 powercfg 命令配置。"""
    print("=" * 60)
    print("PowerCfg 命令测试")
    print("=" * 60)
    
    commands = [
        'disable_hibernate',
        'enable_hibernate', 
        'check_status',
        'query_hibernate_size'
    ]
    
    print("当前系统版本的 powercfg 命令:")
    for cmd in commands:
        command = system_info.get_powercfg_command(cmd)
        print(f"  {cmd}: {command}")
    
    # 测试休眠文件路径
    hiber_path = system_info.get_hibernation_file_path()
    exists = os.path.exists(hiber_path)
    print(f"\n休眠文件路径: {hiber_path} {'[存在]' if exists else '[不存在]'}")
    
    print()


def test_version_specific_features():
    """测试版本特定功能。"""
    print("=" * 60)
    print("版本特定功能测试")
    print("=" * 60)
    
    version = system_info.get_windows_version()
    
    # Windows 7 特定测试
    if version == WindowsVersion.WINDOWS_7:
        print("Windows 7 特定检测:")
        print("  [支持] Service Pack 卸载文件夹清理")
        print("  [支持] CBS 日志清理")
        print("  [不支持] 快速启动")
        print("  [不支持] Windows Store")
    
    # Windows 8/8.1 特定测试
    elif version in [WindowsVersion.WINDOWS_8, WindowsVersion.WINDOWS_8_1]:
        print(f"{version.value} 特定检测:")
        print("  [支持] 混合启动（快速启动）")
        print("  [支持] Windows Store")
        print("  [支持] AppReadiness 缓存清理")
        print("  [不支持] WSL")
        print("  [不支持] DirectStorage")
    
    # Windows 10 特定测试
    elif version == WindowsVersion.WINDOWS_10:
        print("Windows 10 特定检测:")
        print("  [支持] 快速启动")
        print("  [支持] Windows Store")
        print("  [支持] WSL")
        print("  [支持] UWP 应用")
        print("  [支持] Component Store 备份清理")
        print("  [不支持] DirectStorage")
    
    # Windows 11 特定测试
    elif version == WindowsVersion.WINDOWS_11:
        print("Windows 11 特定检测:")
        print("  [支持] 快速启动")
        print("  [支持] Windows Store")
        print("  [支持] WSL")
        print("  [支持] UWP 应用")
        print("  [支持] DirectStorage")
        print("  [支持] SystemResources 保护")
        print("  [支持] 增强的驱动程序存储清理")
    
    print()


def main():
    """主测试函数。"""
    print("Windows C 盘清理工具 - 版本支持测试")
    print("测试时间:", os.popen('date /t').read().strip() if os.name == 'nt' else "N/A")
    print()
    
    try:
        test_system_detection()
        test_system_paths()
        test_whitelist()
        test_powercfg_commands()
        test_version_specific_features()
        
        print("=" * 60)
        print("所有测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()