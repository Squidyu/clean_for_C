"""
测试Windows更新文件删除
"""

import os
import sys
import subprocess
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_delete_windows_update_file():
    """测试删除Windows更新文件"""
    print("=" * 60)
    print("测试Windows更新文件删除")
    print("=" * 60)
    
    # 检查管理员权限
    import ctypes
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    print(f"管理员权限: {'是' if is_admin else '否'}")
    
    if not is_admin:
        print("警告：需要管理员权限才能删除Windows更新文件")
    
    # 检查Windows Update服务状态
    print("\n检查Windows Update服务状态...")
    result = subprocess.run(['sc', 'query', 'wuauserv'], 
                          capture_output=True, text=True, shell=True)
    print(result.stdout)
    
    # 查找测试文件
    update_paths = [
        "C:\\Windows\\SoftwareDistribution\\Download",
        "C:\\Windows\\SoftwareDistribution\\DataStore"
    ]
    
    test_files = []
    for path in update_paths:
        if os.path.exists(path):
            print(f"\n扫描路径: {path}")
            try:
                count = 0
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if count >= 5:  # 只测试前5个文件
                            break
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            test_files.append(file_path)
                            count += 1
                    if count >= 5:
                        break
            except Exception as e:
                print(f"扫描失败: {e}")
    
    if not test_files:
        print("未找到可测试的文件")
        return
    
    print(f"\n找到 {len(test_files)} 个测试文件")
    
    # 尝试停止Windows Update服务
    print("\n尝试停止Windows Update服务...")
    stop_result = subprocess.run(['net', 'stop', 'wuauserv'], 
                                capture_output=True, text=True, shell=True, timeout=10)
    if stop_result.returncode == 0:
        print("✓ Windows Update服务已停止")
        time.sleep(2)  # 等待服务完全停止
    else:
        print(f"✗ 无法停止服务: {stop_result.stderr}")
    
    # 测试删除每个文件
    success_count = 0
    fail_count = 0
    
    for i, file_path in enumerate(test_files[:3], 1):  # 只测试前3个
        print(f"\n{'='*60}")
        print(f"测试文件 {i}/{min(3, len(test_files))}: {os.path.basename(file_path)}")
        print(f"完整路径: {file_path}")
        
        if not os.path.exists(file_path):
            print("文件不存在，跳过")
            continue
        
        # 获取文件信息
        try:
            stat = os.stat(file_path)
            print(f"文件大小: {stat.st_size:,} 字节")
        except Exception as e:
            print(f"无法获取文件信息: {e}")
            continue
        
        # 尝试多种删除方法
        deleted = False
        
        # 方法1: os.remove
        print("\n方法1: 使用os.remove...")
        try:
            import stat as stat_module
            current_mode = os.stat(file_path).st_mode
            os.chmod(file_path, stat_module.S_IWRITE | current_mode)
            os.remove(file_path)
            if not os.path.exists(file_path):
                print("✓ 删除成功（os.remove）")
                deleted = True
                success_count += 1
        except Exception as e:
            print(f"✗ 失败: {e}")
        
        if deleted:
            continue
        
        # 方法2: del命令
        print("\n方法2: 使用del命令...")
        try:
            quoted_path = f'"{file_path}"'
            result = subprocess.run(f'del /F /Q {quoted_path}',
                                  shell=True, capture_output=True, text=True, timeout=10)
            time.sleep(0.3)
            if not os.path.exists(file_path):
                print("✓ 删除成功（del命令）")
                deleted = True
                success_count += 1
            else:
                print(f"✗ 失败: 命令返回码={result.returncode}, stderr={result.stderr}")
        except Exception as e:
            print(f"✗ 失败: {e}")
        
        if deleted:
            continue
        
        # 方法3: takeown + icacls + del
        print("\n方法3: 使用takeown + icacls + del...")
        try:
            # Take ownership
            subprocess.run(['takeown', '/F', file_path],
                          capture_output=True, text=True, shell=True, timeout=5)
            # Grant permissions
            subprocess.run(['icacls', file_path, '/grant', 'Administrators:F'],
                          capture_output=True, text=True, shell=True, timeout=5)
            # Delete
            quoted_path = f'"{file_path}"'
            result = subprocess.run(f'del /F /Q {quoted_path}',
                                  shell=True, capture_output=True, text=True, timeout=10)
            time.sleep(0.3)
            if not os.path.exists(file_path):
                print("✓ 删除成功（takeown + del）")
                deleted = True
                success_count += 1
            else:
                print(f"✗ 失败: 文件仍存在")
        except Exception as e:
            print(f"✗ 失败: {e}")
        
        if not deleted:
            fail_count += 1
            print(f"\n✗ 所有方法都失败，无法删除文件")
    
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    print(f"成功删除: {success_count} 个文件")
    print(f"删除失败: {fail_count} 个文件")
    
    # 尝试重新启动Windows Update服务
    print("\n尝试重新启动Windows Update服务...")
    start_result = subprocess.run(['net', 'start', 'wuauserv'], 
                                 capture_output=True, text=True, shell=True, timeout=10)
    if start_result.returncode == 0:
        print("✓ Windows Update服务已重新启动")
    else:
        print(f"✗ 无法启动服务（可能需要手动启动）")

if __name__ == "__main__":
    test_delete_windows_update_file()

