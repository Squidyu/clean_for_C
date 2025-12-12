#!/usr/bin/env python3
"""
最终解决方案：一键处理病毒误报问题
"""

import os
import subprocess
import sys
from pathlib import Path

def print_banner():
    """打印标题"""
    print("="*60)
    print("  Windows C Drive Cleaner - 病毒误报解决方案")
    print("="*60)
    print()

def step1_build_optimized():
    """步骤1: 构建优化版本"""
    print("步骤1: 构建优化版本（减少误报）")
    print("-" * 40)
    
    try:
        subprocess.run([sys.executable, "build_anti_virus.py"], check=True)
        print("构建完成！")
        print(f"程序位置: {os.path.abspath('dist/Windows_C_Drive_Cleaner/Windows_C_Drive_Cleaner.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        return False
    
    print()

def step2_create_whitelist_script():
    """步骤2: 创建白名单添加脚本"""
    print("步骤2: 创建白名单添加脚本")
    print("-" * 40)
    
    whitelist_script = '''@echo off
chcp 65001 >nul
echo ========================================
echo Windows C Drive Cleaner 白名单配置助手
echo ========================================
echo.

echo 正在添加 Windows Defender 排除项...
powershell -Command "Add-MpPreference -ExclusionPath '%~dp0Windows_C_Drive_Cleaner.exe' -ErrorAction SilentlyContinue"
powershell -Command "Add-MpPreference -ExclusionPath '%~dp0' -ErrorAction SilentlyContinue"

echo.
echo Windows Defender 排除项已添加！
echo.
echo 如果您使用其他杀毒软件，请手动添加排除项：
echo - 360安全卫士：安全防护中心 → 信任区 → 添加
echo - 腾讯电脑管家：病毒查杀 → 设置 → 信任列表
echo - 火绒安全：安全设置 → 信任设置
echo.
echo 完成设置后，程序应该可以正常运行。
echo.
pause
'''
    
    with open('dist/Windows_C_Drive_Cleaner/add_to_whitelist.bat', 'w', encoding='utf-8') as f:
        f.write(whitelist_script)
    
    print("白名单脚本已创建: dist/Windows_C_Drive_Cleaner/add_to_whitelist.bat")
    print()

def step3_scan_info():
    """步骤3: 扫描信息说明"""
    print("步骤3: 病毒扫描说明")
    print("-" * 40)
    
    print("如果需要验证程序安全性，可以：")
    print("1. 访问 https://www.virustotal.com")
    print("2. 上传文件进行扫描")
    print("3. 或者运行: python virus_check.py")
    print()
    print("预期结果：")
    print("- 大部分主流杀毒软件: 清洁")
    print("- 少数敏感软件: 可能误报")
    print("- 添加到白名单后: 正常运行")
    print()

def step4_install():
    """步骤4: 安装说明"""
    print("步骤4: 安装程序")
    print("-" * 40)
    
    print("运行以下命令安装程序：")
    print("1. 双击: install_safe.bat")
    print("2. 或运行: dist/Windows_C_Drive_Cleaner/add_to_whitelist.bat")
    print("3. 启动程序: 开始菜单 → Windows C Drive Cleaner")
    print()

def final_summary():
    """最终总结"""
    print("解决方案总结")
    print("="*40)
    print()
    print("已完成：")
    print("   * 构建优化版本（减少误报）")
    print("   * 添加版本信息和数字签名支持")
    print("   * 创建白名单添加脚本")
    print("   * 提供详细使用说明")
    print()
    print("重要文件：")
    print(f"   * 程序文件: {os.path.abspath('dist/Windows_C_Drive_Cleaner/Windows_C_Drive_Cleaner.exe')}")
    print("   * 白名单脚本: dist/Windows_C_Drive_Cleaner/add_to_whitelist.bat")
    print("   * 安装脚本: install_safe.bat")
    print("   * 使用说明: 解决病毒误报指南.md")
    print("   * 病毒扫描工具: virus_check.py")
    print()
    print("快速使用：")
    print("   1. 运行 add_to_whitelist.bat 添加白名单")
    print("   2. 运行 install_safe.bat 安装程序")
    print("   3. 从开始菜单启动程序")
    print()
    print("如有问题：")
    print("   * 查看 '解决病毒误报指南.md' 详细说明")
    print("   * 使用 virus_check.py 进行在线扫描")
    print("   * 检查源代码确认安全性")

def main():
    """主流程"""
    print_banner()
    
    # 检查当前目录
    if not os.path.exists('src/main.py'):
        print("错误: 请在项目根目录运行此脚本")
        return
    
    # 执行步骤
    if not step1_build_optimized():
        print("构建失败，请检查错误信息")
        return
    
    step2_create_whitelist_script()
    step3_scan_info()
    step4_install()
    final_summary()

if __name__ == "__main__":
    main()