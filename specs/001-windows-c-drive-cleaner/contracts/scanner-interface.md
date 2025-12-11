# Scanner Interface Contract

**Date**: 2025-12-10  
**Feature**: Windows C 盘智能清理工具

## Overview

This document defines the interface contract for cleaning module scanners. All scanner modules must implement this interface to ensure consistent behavior and modularity.

## BaseScanner Interface

All cleaning module scanners must inherit from `BaseScanner` and implement the required methods.

### Methods

#### `scan(cancellation_token: threading.Event) -> ScanResult`

Scans the C drive for files belonging to this module.

**Parameters**:
- `cancellation_token` (threading.Event): Event object to signal cancellation. Scanner must check this frequently and stop if set.

**Returns**:
- `ScanResult`: Scan result containing module name, risk level, total size, and list of files

**Behavior**:
- Must check `cancellation_token.is_set()` frequently (at least every 100 files or 1 second)
- Must respect cancellation and return partial results if cancelled
- Must filter out whitelist-protected files
- Must handle file access errors gracefully (skip locked files, continue scanning)
- Must complete within reasonable time (target: < 5 seconds per module for 30-second total)

**Errors**:
- `PermissionError`: If insufficient permissions (should be logged, not raised)
- `FileNotFoundError`: If expected directories don't exist (should return empty result, not raise)

**Thread Safety**: Must be thread-safe (can be called from multiple threads simultaneously)

#### `get_risk_level() -> str`

Returns the risk level for this module.

**Returns**:
- `str`: One of "low", "medium", "high"

**Behavior**:
- Must return a constant value (does not depend on scan results)
- Must be one of the three defined risk levels

#### `get_module_name() -> str`

Returns the human-readable name of this module.

**Returns**:
- `str`: Module name (e.g., "系统垃圾", "Windows 更新残留")

**Behavior**:
- Must return a constant value
- Must be in Chinese (per user requirements)

## Module-Specific Scanners

### SystemJunkScanner

Scans for Windows temporary files and prefetch files.

**Target Paths**:
- `C:\Windows\Temp\*`
- `C:\Windows\Prefetch\*`
- `C:\Users\<username>\AppData\Local\Temp\*`

**Risk Level**: "low"

**File Patterns**:
- `*.tmp`
- `*.log` (in temp directories only)
- `*.cache` (in temp directories only)

### WindowsUpdatesScanner

Scans for Windows Update cache and old version backups.

**Target Paths**:
- `C:\Windows\SoftwareDistribution\Download\*`
- `C:\Windows\WinSxS\Backup\*` (partial - only old backups, not active components)

**Risk Level**: "medium"

**File Patterns**:
- All files in SoftwareDistribution\Download
- Backup folders in WinSxS (must verify they are old backups)

**Special Considerations**:
- Must be careful with WinSxS - only delete confirmed old backups
- Requires administrator privileges

### BrowserCacheScanner

Scans for browser cache files from Edge, Chrome, and Firefox.

**Target Paths**:
- Edge: `C:\Users\<username>\AppData\Local\Microsoft\Edge\User Data\Default\Cache\*`
- Chrome: `C:\Users\<username>\AppData\Local\Google\Chrome\User Data\Default\Cache\*`
- Firefox: `C:\Users\<username>\AppData\Local\Mozilla\Firefox\Profiles\<profile>\cache2\*`

**Risk Level**: "low"

**File Patterns**:
- All files in cache directories

**Special Considerations**:
- Must detect which browsers are installed
- Should skip if browser is currently running (optional, can warn user)

### AppCacheScanner

Scans for third-party application cache files.

**Target Paths**:
- `C:\Users\<username>\AppData\Local\*\Cache\*`
- `C:\Users\<username>\AppData\Local\*\cache\*`
- Specific known apps: VSCode, JetBrains IDEs, WeChat, etc.

**Risk Level**: "low"

**File Patterns**:
- Cache directories in AppData\Local
- Known cache locations for popular applications

**Special Considerations**:
- Should have configurable list of known cache locations
- Should skip if application is currently running (optional)

### RecycleBinScanner

Scans for files in the Recycle Bin.

**Target Paths**:
- `C:\$Recycle.Bin\*\*` (all user recycle bins)

**Risk Level**: "low"

**File Patterns**:
- All files in Recycle Bin (already deleted, safe to permanently remove)

**Special Considerations**:
- Must handle multiple user recycle bins
- Files are already "deleted" - this is permanent removal

### LargeFilesScanner

Scans for large files (> threshold, e.g., 100MB) across C drive.

**Target Paths**:
- `C:\*` (recursive, all files)

**Risk Level**: "medium"

**File Patterns**:
- Files larger than configurable threshold (default: 100MB)

**Special Considerations**:
- Must be efficient (use os.scandir for performance)
- Should allow user to configure size threshold
- Must respect whitelist (skip protected files)
- This is the most time-consuming scan - must support cancellation well

### AppRemnantsScanner

Scans for leftover directories from uninstalled applications.

**Target Paths**:
- `C:\Program Files\*` (check for empty or orphaned directories)
- `C:\Program Files (x86)\*`
- `C:\Users\<username>\AppData\Local\*`
- `C:\Users\<username>\AppData\Roaming\*`

**Risk Level**: "medium"

**File Patterns**:
- Empty directories in Program Files
- Directories with only cache/log files
- Orphaned application data directories

**Special Considerations**:
- Must be careful - some "empty" directories may be needed by system
- Should check if application is still installed (registry check)
- Requires administrator privileges for Program Files

### HibernationScanner

Special scanner for hiberfil.sys file (not a regular module).

**Target Paths**:
- `C:\hiberfil.sys`

**Risk Level**: "high"

**Special Considerations**:
- Not part of regular module scan (handled separately)
- Must check hibernation status via `powercfg /a`
- Requires special user confirmation
- Supports rollback (restore hibernation)

## Implementation Requirements

### Error Handling

All scanners must:
- Handle `PermissionError` gracefully (log, skip, continue)
- Handle `FileNotFoundError` gracefully (return empty result)
- Handle locked files gracefully (skip, log, continue)
- Never raise unhandled exceptions that crash the application

### Performance

All scanners must:
- Support cancellation via `cancellation_token`
- Check cancellation token frequently (at least every 100 files or 1 second)
- Use efficient file system operations (`os.scandir` preferred over `os.listdir`)
- Avoid loading entire file lists into memory (use generators/iterators)

### Thread Safety

All scanners must:
- Be thread-safe (can be called from ThreadPoolExecutor)
- Not modify shared state without proper locking
- Return independent `ScanResult` objects (no shared mutable state)

### Testing

All scanners must:
- Have unit tests with mock file system
- Have integration tests with real file system (test fixtures)
- Test cancellation behavior
- Test error handling (permission errors, locked files, etc.)
- Test whitelist filtering

