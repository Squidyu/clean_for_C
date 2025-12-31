"""
完整扫描集成测试 - 验证扫描服务是否能正确扫描所有模块
"""

import os
import sys
import threading

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_full_scan():
    """测试完整扫描流程"""
    print("=" * 60)
    print("完整扫描集成测试")
    print("=" * 60)
    
    try:
        from services.scanner_service import scanner_service
        
        print(f"可用模块: {scanner_service.get_available_modules()}")
        print(f"共 {len(scanner_service.get_available_modules())} 个模块\n")
        
        # 执行完整扫描
        print("开始扫描所有模块...")
        cancellation_token = threading.Event()
        
        def progress_callback(module_name, completed, total, result):
            if result:
                print(f"  [{completed}/{total}] {module_name}: "
                      f"{result.file_count} 个文件, "
                      f"{result.total_size / (1024*1024):.2f} MB")
            else:
                print(f"  [{completed}/{total}] {module_name}: 扫描失败")
        
        report = scanner_service.scan_all_modules(
            cancellation_token=cancellation_token,
            progress_callback=progress_callback
        )
        
        print(f"\n扫描完成！状态: {report.status}")
        print(f"总文件数: {report.get_total_files_count()}")
        print(f"总大小: {report.total_scannable_size / (1024*1024):.2f} MB\n")
        
        # 检查每个模块的结果
        print("各模块扫描结果:")
        print("-" * 60)
        for module in report.modules:
            print(f"\n模块: {module.module_name}")
            print(f"  文件数: {module.file_count}")
            print(f"  总大小: {module.total_size / (1024*1024):.2f} MB")
            print(f"  风险等级: {module.get_risk_display()}")
            
            # 特别检查休眠文件和Windows更新残留
            if module.module_name == "休眠文件":
                print(f"  ✓ 休眠文件模块已扫描")
                if module.file_count > 0:
                    print(f"  ✓ 找到 {module.file_count} 个休眠文件")
                    for file_info in module.files:
                        print(f"    - {file_info.path}")
                        print(f"      大小: {file_info.size / (1024*1024):.2f} MB")
                else:
                    print(f"  ⚠ 未找到休眠文件（可能已禁用）")
            
            elif module.module_name == "Windows 更新残留":
                print(f"  ✓ Windows更新残留模块已扫描")
                if module.file_count > 0:
                    print(f"  ✓ 找到 {module.file_count} 个更新残留文件")
                    print(f"    总大小: {module.total_size / (1024*1024):.2f} MB")
                    # 显示前5个文件
                    for i, file_info in enumerate(module.files[:5], 1):
                        print(f"    {i}. {os.path.basename(file_info.path)} "
                              f"({file_info.size / (1024*1024):.2f} MB)")
                    if len(module.files) > 5:
                        print(f"    ... 还有 {len(module.files) - 5} 个文件")
                else:
                    print(f"  ⚠ 未找到更新残留文件（可能已清理或系统较新）")
        
        return report
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("C盘清理工具 - 完整扫描集成测试")
    print("=" * 60)
    print()
    
    report = test_full_scan()
    
    if report:
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        
        hibernation_module = None
        updates_module = None
        
        for module in report.modules:
            if module.module_name == "休眠文件":
                hibernation_module = module
            elif module.module_name == "Windows 更新残留":
                updates_module = module
        
        if hibernation_module:
            if hibernation_module.file_count > 0:
                print(f"✓ 休眠文件: 成功扫描，找到 {hibernation_module.file_count} 个文件")
            else:
                print(f"⚠ 休眠文件: 未找到文件")
        else:
            print(f"✗ 休眠文件: 模块未在扫描结果中")
        
        if updates_module:
            if updates_module.file_count > 0:
                print(f"✓ Windows更新残留: 成功扫描，找到 {updates_module.file_count} 个文件")
            else:
                print(f"⚠ Windows更新残留: 未找到文件（可能正常）")
        else:
            print(f"✗ Windows更新残留: 模块未在扫描结果中")

