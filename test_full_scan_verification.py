"""
完整扫描测试：验证休眠文件和Windows更新残留在扫描服务中是否正常工作
"""

import os
import sys
import threading

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_full_scan():
    """测试完整扫描流程"""
    print("=" * 60)
    print("完整扫描服务测试")
    print("=" * 60)
    
    try:
        from services.scanner_service import scanner_service
        
        print(f"✓ 扫描服务初始化成功")
        print(f"  可用模块: {', '.join(scanner_service.get_available_modules())}")
        print()
        
        # 执行完整扫描
        print("开始执行完整扫描...")
        cancellation_token = threading.Event()
        
        def progress_callback(module_name, completed, total, result):
            print(f"  [{completed}/{total}] {module_name}: 找到 {result.file_count} 个文件, "
                  f"总大小 {result.total_size / (1024*1024):.2f} MB")
        
        report = scanner_service.scan_all_modules(
            cancellation_token=cancellation_token,
            progress_callback=progress_callback
        )
        
        print()
        print("=" * 60)
        print("扫描结果汇总")
        print("=" * 60)
        print(f"扫描状态: {report.status}")
        print(f"总文件数: {report.get_total_files_count()}")
        print(f"总大小: {report.total_scannable_size / (1024*1024):.2f} MB")
        print()
        
        # 检查休眠文件模块
        print("检查休眠文件模块:")
        hibernation_module = None
        for module in report.modules:
            if module.module_name == "休眠文件":
                hibernation_module = module
                break
        
        if hibernation_module:
            print(f"  ✓ 找到休眠文件模块")
            print(f"    文件数: {hibernation_module.file_count}")
            print(f"    总大小: {hibernation_module.total_size / (1024*1024):.2f} MB")
            print(f"    风险等级: {hibernation_module.get_risk_display()}")
            if hibernation_module.files:
                for file_info in hibernation_module.files:
                    print(f"    - {file_info.path}")
                    print(f"      大小: {file_info.size / (1024*1024):.2f} MB")
        else:
            print(f"  ✗ 未找到休眠文件模块")
        
        print()
        
        # 检查Windows更新残留模块
        print("检查Windows更新残留模块:")
        updates_module = None
        for module in report.modules:
            if module.module_name == "Windows 更新残留":
                updates_module = module
                break
        
        if updates_module:
            print(f"  ✓ 找到Windows更新残留模块")
            print(f"    文件数: {updates_module.file_count}")
            print(f"    总大小: {updates_module.total_size / (1024*1024):.2f} MB")
            print(f"    风险等级: {updates_module.get_risk_display()}")
            if updates_module.files:
                print(f"    前5个文件:")
                for i, file_info in enumerate(updates_module.files[:5], 1):
                    print(f"      {i}. {file_info.path}")
                    print(f"         大小: {file_info.size / (1024*1024):.2f} MB")
                if len(updates_module.files) > 5:
                    print(f"      ... 还有 {len(updates_module.files) - 5} 个文件")
            else:
                print(f"    ⚠ 未找到文件（可能正常，如果没有更新缓存）")
        else:
            print(f"  ✗ 未找到Windows更新残留模块")
        
        print()
        print("=" * 60)
        print("所有模块扫描结果")
        print("=" * 60)
        for module in report.modules:
            print(f"  {module.module_name}: {module.file_count} 个文件, "
                  f"{module.total_size / (1024*1024):.2f} MB")
        
        return report
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("完整扫描服务验证测试")
    print("=" * 60)
    print()
    
    report = test_full_scan()
    
    if report:
        print()
        print("=" * 60)
        print("测试总结")
        print("=" * 60)
        
        hibernation_found = any(m.module_name == "休眠文件" and m.file_count > 0 
                               for m in report.modules)
        updates_found = any(m.module_name == "Windows 更新残留" and m.file_count > 0 
                           for m in report.modules)
        
        if hibernation_found:
            print("✓ 休眠文件扫描: 正常工作")
        else:
            print("⚠ 休眠文件扫描: 未找到文件（检查休眠是否启用）")
        
        if updates_found:
            print("✓ Windows更新残留扫描: 正常工作")
        else:
            print("⚠ Windows更新残留扫描: 未找到文件（可能正常，如果没有更新缓存）")
    else:
        print("✗ 测试失败")
