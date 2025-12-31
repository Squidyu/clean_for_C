"""
诊断工具：检查文件删除失败的原因
"""

import os
import sys
import subprocess
import ctypes

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_admin():
    """检查是否以管理员权限运行"""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"管理员权限: {'是' if is_admin else '否'}")
        return is_admin
    except:
        print("无法检查管理员权限")
        return False

def test_delete_file(file_path):
    """测试删除文件"""
    print(f"\n测试删除文件: {file_path}")
    print("-" * 60)
    
    if not os.path.exists(file_path):
        print("✗ 文件不存在")
        return False
    
    # 检查文件属性
    try:
        stat = os.stat(file_path)
        print(f"文件大小: {stat.st_size:,} 字节")
        print(f"文件模式: {oct(stat.st_mode)}")
        
        # 检查只读属性
        import stat as stat_module
        is_readonly = not (stat.st_mode & stat_module.S_IWRITE)
        print(f"只读属性: {'是' if is_readonly else '否'}")
    except Exception as e:
        print(f"无法获取文件信息: {e}")
    
    # 尝试移除只读属性
    try:
        import stat as stat_module
        current_mode = os.stat(file_path).st_mode
        os.chmod(file_path, stat_module.S_IWRITE | current_mode)
        print("✓ 已移除只读属性")
    except Exception as e:
        print(f"✗ 无法移除只读属性: {e}")
    
    # 尝试删除
    try:
        os.remove(file_path)
        print("✓ 删除成功（使用os.remove）")
        return True
    except PermissionError as e:
        print(f"✗ 权限错误: {e}")
    except OSError as e:
        print(f"✗ 系统错误: {e}")
        error_str = str(e).lower()
        if "being used" in error_str or "被另一个程序使用" in error_str:
            print("  → 文件被其他程序占用")
        elif "access is denied" in error_str or "拒绝访问" in error_str:
            print("  → 访问被拒绝（可能需要管理员权限）")
    
    # 尝试使用subprocess删除
    print("\n尝试使用subprocess删除...")
    try:
        result = subprocess.run(['del', '/F', '/Q', file_path], 
                              shell=True, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓ 删除成功（使用del命令）")
            return True
        else:
            print(f"✗ 删除失败: {result.stderr}")
    except Exception as e:
        print(f"✗ 删除失败: {e}")
    
    return False

def test_hibernation_file():
    """测试休眠文件删除"""
    print("=" * 60)
    print("测试休眠文件删除")
    print("=" * 60)
    
    check_admin()
    
    hiberfil_path = "C:\\hiberfil.sys"
    
    # 检查休眠状态
    print("\n检查休眠状态...")
    result = subprocess.run(['powercfg', '/a'], 
                          capture_output=True, text=True, shell=True)
    print(result.stdout)
    
    if os.path.exists(hiberfil_path):
        return test_delete_file(hiberfil_path)
    else:
        print("休眠文件不存在（可能已删除或休眠已禁用）")
        return True

def test_windows_update_file():
    """测试Windows更新文件删除"""
    print("\n" + "=" * 60)
    print("测试Windows更新文件删除")
    print("=" * 60)
    
    check_admin()
    
    # 检查Windows Update服务
    print("\n检查Windows Update服务状态...")
    result = subprocess.run(['sc', 'query', 'wuauserv'], 
                          capture_output=True, text=True, shell=True)
    print(result.stdout)
    
    # 查找一个更新文件进行测试
    update_paths = [
        "C:\\Windows\\SoftwareDistribution\\Download",
        "C:\\Windows\\SoftwareDistribution\\DataStore"
    ]
    
    test_file = None
    for path in update_paths:
        if os.path.exists(path):
            print(f"\n扫描路径: {path}")
            try:
                for root, dirs, files in os.walk(path):
                    for file in files[:5]:  # 只测试前5个文件
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            test_file = file_path
                            break
                    if test_file:
                        break
            except Exception as e:
                print(f"扫描失败: {e}")
    
    if test_file:
        print(f"\n找到测试文件: {test_file}")
        return test_delete_file(test_file)
    else:
        print("未找到可测试的更新文件")
        return False

if __name__ == "__main__":
    print("文件删除诊断工具")
    print("=" * 60)
    
    # 测试休眠文件
    hibernation_ok = test_hibernation_file()
    
    # 测试Windows更新文件
    update_ok = test_windows_update_file()
    
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    print(f"休眠文件删除: {'✓ 成功' if hibernation_ok else '✗ 失败'}")
    print(f"Windows更新文件删除: {'✓ 成功' if update_ok else '✗ 失败'}")

