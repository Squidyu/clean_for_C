#!/usr/bin/env python3
"""
Build script for creating Windows executable
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

def create_spec_file():
    """Create PyInstaller spec file."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Get the absolute path to the src directory
src_dir = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'src')

a = Analysis(
    ['src/main.py'],
    pathex=[src_dir],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('src', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'win32api',
        'win32con',
        'win32security',
        'win32process',
        'win32file',
        'win32gui',
        'datetime',
        'services.scanner_service',
        'services.cleaner_service',
        'services.permission_service',
        'services.whitelist_service',
        'ui.main_window',
        'ui.scan_view',
        'ui.cleaning_view',
        'models.scan_report',
        'models.scan_result',
        'models.file_info',
        'models.cleaning_operation',
        'models.whitelist',
        'models.hibernation_file_info',
        'modules.base_scanner',
        'modules.app_cache',
        'modules.app_remnants',
        'modules.browser_cache',
        'modules.hibernation',
        'modules.large_files',
        'modules.recycle_bin',
        'modules.system_junk',
        'modules.windows_updates',
        'utils.size_utils',
        'utils.file_utils',
        'utils.path_utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Windows_C_Drive_Cleaner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # You can add an icon file here if available
)
'''

    with open('cleaner.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("Created cleaner.spec file")

def build_exe():
    """Build the executable."""
    print("Building executable...")

    # Try using pyinstaller command first, then fall back to python -m
    try:
        # Use pyinstaller command directly
        cmd = ['pyinstaller', '--clean', 'cleaner.spec']
        subprocess.check_call(cmd)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to python -m pyinstaller
        try:
            cmd = [sys.executable, '-m', 'pyinstaller', '--clean', 'cleaner.spec']
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            # Last resort: try using full path
            import site
            site_packages = site.getsitepackages()[0]
            pyinstaller_path = os.path.join(site_packages, 'Scripts', 'pyinstaller.exe')
            if os.path.exists(pyinstaller_path):
                cmd = [pyinstaller_path, '--clean', 'cleaner.spec']
                subprocess.check_call(cmd)
            else:
                raise Exception("PyInstaller not found. Please reinstall: pip install pyinstaller")

    print("Build completed!")

def create_installer_script():
    """Create a simple installer script."""
    installer_content = '''@echo off
echo Installing Windows C Drive Cleaner...

REM Create installation directory
if not exist "%ProgramFiles%\\Windows C Drive Cleaner" mkdir "%ProgramFiles%\\Windows C Drive Cleaner"

REM Copy files
xcopy /Y /E "dist\\Windows_C_Drive_Cleaner" "%ProgramFiles%\\Windows C Drive Cleaner\\"

REM Create desktop shortcut (optional)
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\\Desktop\\Windows C Drive Cleaner.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%ProgramFiles%\\Windows C Drive Cleaner\\Windows_C_Drive_Cleaner.exe" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%ProgramFiles%\\Windows C Drive Cleaner" >> CreateShortcut.vbs
echo oLink.Description = "Windows C Drive Cleaner" >> CreateShortcut.vbs
echo oLink.IconLocation = "%ProgramFiles%\\Windows C Drive Cleaner\\Windows_C_Drive_Cleaner.exe" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs
del CreateShortcut.vbs

echo Installation completed!
pause
'''

    with open('install.bat', 'w', encoding='utf-8') as f:
        f.write(installer_content)

    print("Created install.bat installer script")

def main():
    """Main build process."""
    try:
        print("Starting build process for Windows C Drive Cleaner...")

        # Change to project directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Install dependencies
        install_dependencies()

        # Create spec file
        create_spec_file()

        # Build executable
        build_exe()

        # Create installer script
        create_installer_script()

        print("\\nBuild process completed successfully!")
        print("Executable created in: dist/Windows_C_Drive_Cleaner/")
        print("Run install.bat to install the application")

    except Exception as e:
        print(f"Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
