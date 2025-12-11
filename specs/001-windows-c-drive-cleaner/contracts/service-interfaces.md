# Service Interface Contracts

**Date**: 2025-12-10  
**Feature**: Windows C 盘智能清理工具

## Overview

This document defines the interface contracts for core business logic services. Services encapsulate business rules and coordinate between modules.

## ScannerService

Coordinates scanning operations across all cleaning modules.

### Methods

#### `scan_all_modules(cancellation_token: threading.Event) -> ScanReport`

Scans all 8 cleaning modules in parallel and returns complete scan report.

**Parameters**:
- `cancellation_token` (threading.Event): Event to signal cancellation

**Returns**:
- `ScanReport`: Complete scan report with all 8 modules

**Behavior**:
- Launches 8 parallel scanner threads (one per module)
- Waits for all scanners to complete or cancellation
- Aggregates results into `ScanReport`
- Updates progress in real-time (can be observed via callback)

**Errors**:
- Should handle individual module failures gracefully (include failed modules in report with error status)
- Should not raise exceptions (log errors, return partial results)

**Performance**:
- Target: Complete within 30 seconds on SSD
- Must support cancellation within 2 seconds

#### `scan_single_module(module_name: str, cancellation_token: threading.Event) -> ScanResult`

Scans a single module (for incremental scanning or re-scanning).

**Parameters**:
- `module_name` (str): Name of module to scan
- `cancellation_token` (threading.Event): Event to signal cancellation

**Returns**:
- `ScanResult`: Result for the specified module

**Behavior**:
- Finds appropriate scanner for module name
- Executes scan
- Returns result

**Errors**:
- `ValueError`: If module name is invalid
- Should handle scanner errors gracefully

## CleanerService

Coordinates cleaning operations.

### Methods

#### `predict_space(files: List[FileInfo]) -> int`

Calculates predicted space to be freed from selected files.

**Parameters**:
- `files` (List[FileInfo]): List of files selected for cleaning

**Returns**:
- `int`: Predicted space in bytes

**Behavior**:
- Sums sizes of all files
- Validates files are not protected (whitelist check)
- Returns total

**Errors**:
- Should log warning if protected files are included (but don't raise)

#### `clean_files(operation: CleaningOperation, progress_callback: Callable, cancellation_token: threading.Event) -> CleaningOperation`

Executes cleaning operation, deleting selected files.

**Parameters**:
- `operation` (CleaningOperation): Operation to execute
- `progress_callback` (Callable): Callback function for progress updates (called with percentage, current_module)
- `cancellation_token` (threading.Event): Event to signal cancellation

**Returns**:
- `CleaningOperation`: Updated operation with results

**Behavior**:
- Validates all files against whitelist (skip protected files)
- Deletes files module by module
- Updates progress via callback
- Handles errors gracefully (adds failed files to operation.failed_files)
- Calculates actual space freed
- Updates operation status

**Errors**:
- Should never raise exceptions (log errors, add to failed_files)
- Should handle permission errors gracefully
- Should handle locked files gracefully

**Performance**:
- Must support cancellation
- Should provide frequent progress updates (at least every 1% or 1 second)

#### `delete_hiberfil_sys(user_confirmed: bool) -> bool`

Deletes hiberfil.sys file and disables hibernation.

**Parameters**:
- `user_confirmed` (bool): Whether user confirmed understanding of risks

**Returns**:
- `bool`: True if successful, False otherwise

**Behavior**:
- Validates user_confirmed is True (raises ValueError if False)
- Executes `powercfg -h off` command
- Verifies file is deleted
- Logs operation

**Errors**:
- `ValueError`: If user_confirmed is False
- `PermissionError`: If insufficient privileges
- `RuntimeError`: If powercfg command fails

**Security**:
- MUST require user_confirmed=True
- MUST log the operation
- MUST support rollback

#### `restore_hibernation() -> bool`

Restores hibernation functionality.

**Returns**:
- `bool`: True if successful, False otherwise

**Behavior**:
- Executes `powercfg -h on` command
- Verifies hibernation is enabled
- Logs operation

**Errors**:
- `PermissionError`: If insufficient privileges
- `RuntimeError`: If powercfg command fails

## LogService

Manages cleaning operation logs.

### Methods

#### `log_operation(operation: CleaningOperation) -> CleaningLog`

Creates and persists a log entry for a cleaning operation.

**Parameters**:
- `operation` (CleaningOperation): Operation to log

**Returns**:
- `CleaningLog`: Created log entry

**Behavior**:
- Creates `CleaningLog` from `CleaningOperation`
- Appends to log file (JSONL format)
- Returns log entry

**Errors**:
- Should handle file write errors gracefully (log to application log, don't raise)

#### `get_log_history(limit: int = None) -> List[CleaningLog]`

Retrieves cleaning log history.

**Parameters**:
- `limit` (int, optional): Maximum number of entries to return (None = all)

**Returns**:
- `List[CleaningLog]`: List of log entries, most recent first

**Behavior**:
- Reads log file
- Parses JSONL entries
- Sorts by timestamp (descending)
- Returns limited results if limit specified

**Errors**:
- Should handle file read errors gracefully (return empty list, log error)
- Should handle malformed JSON gracefully (skip entry, log warning)

#### `query_logs(filters: Dict) -> List[CleaningLog]`

Queries logs with filters.

**Parameters**:
- `filters` (Dict): Filter criteria (e.g., {"module": "系统垃圾", "date_from": datetime, "date_to": datetime})

**Returns**:
- `List[CleaningLog]`: Filtered log entries

**Behavior**:
- Loads all logs
- Applies filters
- Returns matching entries

**Supported Filters**:
- `module` (str): Filter by module name
- `date_from` (datetime): Filter by start date
- `date_to` (datetime): Filter by end date
- `hiberfil_deleted` (bool): Filter by hiberfil.sys deletion

## PermissionService

Manages Windows permissions and UAC elevation.

### Methods

#### `check_is_admin() -> bool`

Checks if current process has administrator privileges.

**Returns**:
- `bool`: True if running as administrator

**Behavior**:
- Uses Windows API to check privilege level
- Returns boolean result

#### `request_elevation(reason: str) -> bool`

Requests UAC elevation for current operation.

**Parameters**:
- `reason` (str): Reason for elevation (shown to user)

**Returns**:
- `bool`: True if elevation successful, False otherwise

**Behavior**:
- Shows UAC prompt to user
- Restarts application with elevated privileges if user approves
- Returns success status

**Errors**:
- Should handle user denial gracefully (return False, don't raise)
- Should handle elevation failure gracefully

#### `check_path_permissions(path: str) -> Dict[str, bool]`

Checks permissions for a file or directory path.

**Parameters**:
- `path` (str): Path to check

**Returns**:
- `Dict[str, bool]`: Permission flags (readable, writable, deletable)

**Behavior**:
- Checks file system permissions
- Returns permission flags
- Handles errors gracefully (returns all False if path doesn't exist)

## WhitelistService

Manages system file whitelist.

### Methods

#### `is_protected(path: str) -> bool`

Checks if a path is protected by whitelist.

**Parameters**:
- `path` (str): Path to check

**Returns**:
- `bool`: True if path is protected

**Behavior**:
- Checks against whitelist paths and patterns
- Returns True if path matches any protected pattern
- Must be fast (used frequently during scanning)

#### `load_whitelist() -> SystemWhitelist`

Loads whitelist from configuration file.

**Returns**:
- `SystemWhitelist`: Loaded whitelist

**Behavior**:
- Reads whitelist JSON file
- Parses and validates
- Returns whitelist object
- Caches in memory after first load

**Errors**:
- Should handle file read errors gracefully (return default whitelist, log error)
- Should handle JSON parse errors gracefully (return default whitelist, log error)

#### `get_default_whitelist() -> SystemWhitelist`

Returns default system whitelist (fallback).

**Returns**:
- `SystemWhitelist`: Default whitelist with critical Windows paths

**Behavior**:
- Returns hardcoded default whitelist
- Used as fallback if file loading fails

