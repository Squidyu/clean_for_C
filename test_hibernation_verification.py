"""
测试脚本：验证休眠文件和Windows更新残留扫描模块
"""

import os
import sys
import threading
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_hibernation_scanner():
    """测试休眠文件扫描器"""
    print("=" * 60)
    print("测试休眠文件扫描器")
    print("=" * 60)
    
    try:
        from modules.hibernation import HibernationScanner
        
        scanner = HibernationScanner()
        print(f"✓ 扫描器初始化成功")
        print(f"  模块名称: {scanner.get_module_name()}")
        print(f"  风险等级: {scanner.get_risk_level()}")
        
        # 检查休眠文件是否存在
        hiberfil_path = "C:\\hiberfil.sys"
        print(f"\n检查文件: {hiberfil_path}")
        
        if os.path.exists(hiberfil_path):
            print(f"✓ 文件存在")
            try:
                stat = os.stat(hiberfil_path)
                size_mb = stat.st_size / (1024 * 1024)
                print(f"  文件大小: {size_mb:.2f} MB ({stat.st_size:,} 字节)")
                print(f"  最后修改: {datetime.fromtimestamp(stat.st_mtime)}")
            except Exception as e:
                print(f"✗ 无法获取文件信息: {e}")
        else:
            print(f"✗ 文件不存在（可能需要管理员权限查看）")
        
        # 检查休眠状态
        print(f"\n检查休眠状态:")
        hibernation_info = scanner.get_hibernation_status()
        print(f"  文件存在: {hibernation_info.exists}")
        print(f"  休眠启用: {hibernation_info.hibernation_enabled}")
        print(f"  文件大小: {hibernation_info.file_size_bytes:,} 字节")
        print(f"  可以删除: {hibernation_info.can_delete}")
        
        # 执行扫描
        print(f"\n执行扫描...")
        cancellation_token = threading.Event()
        scan_result = scanner.scan(cancellation_token)
        
        print(f"✓ 扫描完成")
        print(f"  模块名称: {scan_result.module_name}")
        print(f"  风险等级: {scan_result.risk_level}")
        print(f"  找到文件数: {scan_result.file_count}")
        print(f"  总大小: {scan_result.total_size:,} 字节 ({scan_result.total_size / (1024*1024):.2f} MB)")
        
        if scan_result.files:
            print(f"\n扫描到的文件:")
            for file_info in scan_result.files:
                print(f"  - {file_info.path}")
                print(f"    大小: {file_info.size:,} 字节")
                print(f"    受保护: {file_info.is_protected}")
                if hasattr(file_info, 'description'):
                    print(f"    描述: {file_info.description}")
        else:
            print(f"\n⚠ 未扫描到文件")
            print(f"  可能原因:")
            print(f"  1. 文件不存在（休眠已禁用）")
            print(f"  2. 权限不足（需要管理员权限）")
            print(f"  3. 文件被系统锁定")
            print(f"  4. 代码逻辑问题")
        
        return scan_result
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_system_info():
    """检查系统信息"""
    print("=" * 60)
    print("系统信息检查")
    print("=" * 60)
    
    try:
        from utils.system_info import system_info
        
        info = system_info.get_version_info()
        print(f"Windows版本: {info['version_string']}")
        print(f"构建号: {info['build_number']}")
        print(f"64位系统: {info['is_64bit']}")
        print(f"支持休眠: {system_info.supports_feature('hibernation')}")
        
        # 检查powercfg输出
        import subprocess
        result = subprocess.run(['powercfg', '/a'], 
                              capture_output=True, text=True, shell=True)
        print(f"\nPowercfg 输出:")
        print(result.stdout)
        
    except Exception as e:
        print(f"✗ 检查失败: {e}")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("C盘清理工具 - 休眠文件模块验证测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 检查系统信息
    check_system_info()
    print()
    
    # 测试休眠文件扫描器
    hibernation_result = test_hibernation_scanner()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if hibernation_result:
        if hibernation_result.file_count > 0:
            print(f"✓ 休眠文件扫描: 成功，找到 {hibernation_result.file_count} 个文件")
            print(f"  总大小: {hibernation_result.total_size:,} 字节 ({hibernation_result.total_size / (1024*1024):.2f} MB)")
        else:
            print(f"⚠ 休眠文件扫描: 未找到文件")
            if hibernation_result.error_message:
                print(f"  错误: {hibernation_result.error_message}")
    else:
        print(f"✗ 休眠文件扫描: 测试失败")
    
    print("\n提示:")
    print("- 如果休眠文件未找到，请检查是否以管理员权限运行")
    print("- 某些系统文件可能需要管理员权限才能访问")


if __name__ == "__main__":
    main()
