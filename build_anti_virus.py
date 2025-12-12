#!/usr/bin/env python3
"""
Anti-Virus Friendly Build Script for Windows C Drive Cleaner
减少误报的构建脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_dependencies():
    """Install required dependencies for building."""
    print("Installing build dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def build_exe():
    """Build the executable with anti-virus friendly settings."""
    print("Building executable with anti-virus friendly settings...")
    
    # Clean previous builds
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # Build with anti-virus friendly spec
    try:
        cmd = [sys.executable, '-m', 'pyinstaller', '--clean', 'cleaner_anti_virus.spec']
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        raise

def sign_executable():
    """
    可选：数字签名可显著减少误报
    需要安装 Windows SDK 并配置代码签名证书
    """
    exe_path = os.path.join('dist', 'Windows_C_Drive_Cleaner', 'Windows_C_Drive_Cleaner.exe')
    if os.path.exists(exe_path):
        print(f"Executable built: {exe_path}")
        print("\n可选：数字签名步骤")
        print("如果您有代码签名证书，可以运行以下命令签名：")
        print(f'signtool sign /f certificate.p12 /p password /t http://timestamp.digicert.com "{exe_path}"')
        print("注意：需要安装 Windows SDK 并配置证书")

def create_readme():
    """创建使用说明"""
    readme_content = """# Windows C Drive Cleaner 使用说明

## 关于病毒误报问题

这是一个合法的系统清理工具，但由于以下原因可能被杀毒软件误报：

1. **系统文件访问**：需要访问系统目录和临时文件
2. **注册表操作**：读取系统配置信息
3. **文件删除操作**：删除大量文件的行为模式

## 解决方案

### 方法1：添加信任（推荐）
1. 将软件所在文件夹添加到杀毒软件白名单
2. 将 executable 添加到信任列表
3. 临时禁用实时防护进行安装

### 方法2：数字签名
如果您有代码签名证书，可以签名程序以减少误报：
```bash
signtool sign /f certificate.p12 /p password /t http://timestamp.digicert.com "Windows_C_Drive_Cleaner.exe"
```

### 方法3：手动验证
1. 使用 VirusTotal.com 扫描查看具体哪些杀毒软件误报
2. 大部分主流杀毒软件都不会误报
3. 可以在虚拟机中测试安全性

## 使用建议

1. **首次使用前**：建议备份重要数据
2. **谨慎操作**：仔细查看要删除的文件列表
3. **分步清理**：建议先清理浏览器缓存等安全项目
4. **定期更新**：保持软件版本最新

## 技术说明

- 源代码完全开源，可审查安全性
- 使用 Python + Tkinter 开发，无恶意代码
- 仅删除标准垃圾文件和临时数据
- 不会修改系统核心文件

## 联系支持

如有疑问，请检查源代码或联系开发者。
"""

    with open('dist/Windows_C_Drive_Cleaner/README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("Created README.txt with usage instructions")

def create_installer_script():
    """创建更安全的安装脚本"""
    installer_content = """@echo off
chcp 65001 >nul
echo ==========================================
echo Windows C Drive Cleaner 安装程序
echo ==========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [警告] 检测到管理员权限，这是不必要的
    echo [提示] 普通用户权限即可运行程序
    echo.
)

REM 检查目标目录
set "TARGET_DIR=%ProgramFiles%\\Windows C Drive Cleaner"
if not exist "%TARGET_DIR%" (
    echo 创建安装目录: %TARGET_DIR%
    mkdir "%TARGET_DIR%"
)

REM 复制文件
echo 复制程序文件...
xcopy /Y /E "dist\\Windows_C_Drive_Cleaner\\*" "%TARGET_DIR%\\"

REM 创建开始菜单快捷方式
echo 创建开始菜单快捷方式...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Windows C Drive Cleaner.lnk'); $Shortcut.TargetPath = '%TARGET_DIR%\\Windows_C_Drive_Cleaner.exe'; $Shortcut.WorkingDirectory = '%TARGET_DIR%'; $Shortcut.Description = 'Windows C Drive Cleaner'; $Shortcut.Save()"

echo.
echo ==========================================
echo 安装完成！
echo ==========================================
echo.
echo 程序已安装到: %TARGET_DIR%
echo 可从开始菜单启动程序
echo.
echo 注意：首次运行时可能需要添加到杀毒软件白名单
echo 请阅读 README.txt 了解详情
echo.
pause
"""

    with open('install_safe.bat', 'w', encoding='utf-8') as f:
        f.write(installer_content)

def main():
    """Main build process."""
    try:
        print("Starting anti-virus friendly build process...")
        print("============================================")

        # Change to project directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Install dependencies
        install_dependencies()

        # Build executable
        build_exe()

        # Create README
        create_readme()

        # Create installer
        create_installer_script()

        # Sign info
        sign_executable()

        print("\n" + "="*50)
        print("Build completed successfully!")
        print("="*50)
        print(f"Executable location: dist/Windows_C_Drive_Cleaner/")
        print("Installer script: install_safe.bat")
        print("Usage documentation: dist/Windows_C_Drive_Cleaner/README.txt")
        print("\n下一步：")
        print("1. 运行 install_safe.bat 安装程序")
        print("2. 将程序添加到杀毒软件白名单")
        print("3. 阅读 README.txt 了解使用方法")

    except Exception as e:
        print(f"Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()