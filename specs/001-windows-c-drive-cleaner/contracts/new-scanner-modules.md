# New Scanner Modules Specification

**Date**: 2025-12-30  
**Feature**: Windows C 盘智能清理工具 - 新增清理模块

## Overview

This document defines the specification for 8 new cleaning module scanners to be added to the Windows C Drive Cleaner application.

## Module Specifications

### 1. WindowsDefenderCacheScanner

**Module Name**: "Windows Defender 缓存"

**Risk Level**: "low"

**Target Paths**:
- `C:\ProgramData\Microsoft\Windows Defender\Scans\FilesStash\*`
- `C:\ProgramData\Microsoft\Windows Defender\Scans\History\*`
- `C:\ProgramData\Microsoft\Windows Defender\Definition Updates\*`
- `C:\ProgramData\Microsoft\Windows Defender\Support\*` (Windows 10/11 offline scan cache)
- `%LOCALAPPDATA%\Microsoft\Windows Defender\*` (user-specific cache)

**File Patterns**:
- All files in cache directories
- Temporary scan files
- Old definition update files

**Windows Version Support**:
- Windows 10: Full support
- Windows 11: Full support
- Windows 7/8/8.1: Not supported (return empty result with message)

**Special Considerations**:
- Only scan on Windows 10/11
- Skip active definition files (check modification date)
- Cache files are safe to delete (will be regenerated)

**Implementation Requirements**:
- Must check Windows version before scanning
- Must skip files modified in last 7 days (might be in use)
- Must handle permission errors gracefully

---

### 2. WindowsStoreCacheScanner

**Module Name**: "Windows Store 缓存"

**Risk Level**: "low"

**Target Paths**:
- `%ProgramData%\Microsoft\Windows\AppRepository\*`
- `%ProgramData%\Packages\*`
- `%LOCALAPPDATA%\Packages\*` (UWP app cache)
- `%LOCALAPPDATA%\Microsoft\Windows\INetCache\*`
- `%LOCALAPPDATA%\Microsoft\Windows\WebCache\*`

**File Patterns**:
- Cache directories in Packages folder
- Temporary UWP app files
- Web cache for UWP apps

**Windows Version Support**:
- Windows 8: Partial support
- Windows 8.1: Partial support
- Windows 10: Full support
- Windows 11: Full support
- Windows 7: Not supported

**Special Considerations**:
- Focus on cache directories (look for 'cache', 'temp', 'localcache' in directory names)
- Skip active app databases
- Cache files are safe to delete (apps will regenerate)

**Implementation Requirements**:
- Must detect Windows Store availability
- Must scan cache directories efficiently
- Must skip system-protected files

---

### 3. OneDriveCacheScanner

**Module Name**: "OneDrive 缓存"

**Risk Level**: "low"

**Target Paths**:
- `%LOCALAPPDATA%\Microsoft\OneDrive\logs\*`
- `%LOCALAPPDATA%\Microsoft\OneDrive\cache\*`
- `%LOCALAPPDATA%\Microsoft\OneDrive\temp\*`
- `%APPDATA%\Microsoft\OneDrive\logs\*`

**File Patterns**:
- Log files
- Cache files
- Temporary sync files

**Windows Version Support**:
- All Windows versions (if OneDrive is installed)

**Special Considerations**:
- Only scan if OneDrive is installed
- Log files are safe to delete
- Cache files will be regenerated
- Skip active sync files (check if OneDrive is running - optional)

**Implementation Requirements**:
- Must check if OneDrive directory exists
- Must skip files modified in last 24 hours (might be in use)
- Must handle missing OneDrive gracefully

---

### 4. TeamsCacheScanner

**Module Name**: "Microsoft Teams 缓存"

**Risk Level**: "low"

**Target Paths**:
- `%APPDATA%\Microsoft\Teams\*`
- `%LOCALAPPDATA%\Microsoft\Teams\*`
- `%LOCALAPPDATA%\Microsoft\Teams\media-stack\*`

**File Patterns**:
- Cache directories: 'cache', 'logs', 'temp', 'blob_storage', 'gpucache', 'code cache'
- Temporary files
- Media cache files

**Windows Version Support**:
- All Windows versions (if Teams is installed)

**Special Considerations**:
- Only scan if Teams is installed
- Skip active database files (IndexedDB)
- Cache files are safe to delete (will be regenerated)
- Should skip if Teams is running (optional, can warn user)

**Implementation Requirements**:
- Must detect Teams installation
- Must focus on cache directories
- Must skip active databases
- Must handle missing Teams gracefully

---

### 5. WindowsSearchIndexScanner

**Module Name**: "Windows Search 索引"

**Risk Level**: "medium"

**Target Paths**:
- `%ProgramData%\Microsoft\Search\Data\*` (temporary index files)
- `%APPDATA%\Microsoft\Windows\Recent\AutomaticDestinations\*` (jump list cache)

**File Patterns**:
- Temporary index files (*.tmp)
- Cache files (*.cache)
- Log files (*.log)
- **NOT** active index databases (Windows.edb)

**Windows Version Support**:
- All Windows versions

**Special Considerations**:
- **CRITICAL**: Must NOT delete active index database (Windows.edb)
- Only delete temporary and cache files
- Deleting index will require rebuilding (takes time)
- Risk level is "medium" because rebuilding index may take time

**Implementation Requirements**:
- Must skip Windows.edb and other active databases
- Must only scan for temporary/cache files
- Must provide clear description of impact

---

### 6. ThumbnailCacheScanner

**Module Name**: "缩略图缓存"

**Risk Level**: "low"

**Target Paths**:
- `%LOCALAPPDATA%\Microsoft\Windows\Explorer\thumbcache_*.db` (Windows 7/8/8.1)
- `%LOCALAPPDATA%\Microsoft\Windows\Explorer\*` (Windows 10/11 thumbnail cache)
- System-wide: `C:\Users\<username>\AppData\Local\Microsoft\Windows\Explorer\*`
- Individual folders: `**\thumbs.db` (legacy thumbnail cache)

**File Patterns**:
- `thumbcache_*.db` (Windows thumbnail cache database)
- `iconcache_*.db` (icon cache database)
- `thumbs.db` (legacy thumbnail cache in folders)

**Windows Version Support**:
- All Windows versions

**Special Considerations**:
- Thumbnail cache files are safe to delete (will be regenerated)
- May need to close Windows Explorer to delete some files
- Legacy thumbs.db files are in individual folders

**Implementation Requirements**:
- Must scan both system-wide and per-folder thumbnail caches
- Must handle locked files gracefully
- Must scan for thumbs.db in common locations

---

### 7. FontCacheScanner

**Module Name**: "字体缓存"

**Risk Level**: "low"

**Target Paths**:
- `%LOCALAPPDATA%\Microsoft\Windows\Fonts\*` (font cache)
- `C:\Windows\ServiceProfiles\LocalService\AppData\Local\FontCache\*` (system font cache)
- `%LOCALAPPDATA%\FontCache\*` (user font cache)

**File Patterns**:
- Font cache database files
- Font preview cache files
- Temporary font files

**Windows Version Support**:
- All Windows versions

**Special Considerations**:
- Font cache files are safe to delete (will be regenerated)
- May need to close applications using fonts
- System font cache requires admin privileges

**Implementation Requirements**:
- Must scan both user and system font cache
- Must handle permission errors gracefully
- Must skip active font files

---

### 8. DirectXShaderCacheScanner

**Module Name**: "DirectX Shader Cache"

**Risk Level**: "low"

**Target Paths**:
- `%LOCALAPPDATA%\D3DSCache\*` (DirectX shader cache)
- `%LOCALAPPDATA%\AMD\DxCache\*` (AMD shader cache)
- `%LOCALAPPDATA%\NVIDIA Corporation\NV_Cache\*` (NVIDIA shader cache)
- `%LOCALAPPDATA%\Intel\ShaderCache\*` (Intel shader cache)

**File Patterns**:
- Shader cache files (*.cache, *.bin)
- Compiled shader files
- GPU-specific cache files

**Windows Version Support**:
- Windows 10: Full support
- Windows 11: Full support
- Windows 7/8/8.1: Partial support (DirectX 11+)

**Special Considerations**:
- Shader cache files are safe to delete (will be regenerated, may cause slight performance impact on first run)
- Different GPU vendors have different cache locations
- Cache files can be large (several GB)

**Implementation Requirements**:
- Must scan multiple GPU vendor cache locations
- Must handle missing directories gracefully
- Must provide description of impact (slight performance impact on first run after deletion)

---

## Implementation Checklist

For each new scanner module:

- [ ] Create scanner class inheriting from `BaseScanner`
- [ ] Implement `get_module_name()` returning Chinese name
- [ ] Implement `get_risk_level()` returning "low", "medium", or "high"
- [ ] Implement `scan()` method with proper error handling
- [ ] Add Windows version checks where applicable
- [ ] Handle cancellation token properly
- [ ] Filter out protected files using whitelist
- [ ] Register module in `ScannerService._create_scanners()`
- [ ] Add module description in `ScannerService._get_module_description()`
- [ ] Test with real file system
- [ ] Handle edge cases (missing directories, permission errors, etc.)

## Integration Requirements

All new modules must be:
1. Registered in `src/services/scanner_service.py`
2. Listed in module descriptions
3. Tested for Windows version compatibility
4. Documented with proper error handling

