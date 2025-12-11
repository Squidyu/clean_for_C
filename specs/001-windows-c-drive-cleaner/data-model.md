# Data Model: Windows C 盘清理工具

**Date**: 2025-12-10  
**Feature**: Windows C 盘智能清理工具

## Overview

This document defines the core data structures and entities for the Windows C Drive Cleaner application. All entities are designed to be technology-agnostic and focus on business logic rather than implementation details.

## Core Entities

### ScanResult

Represents the output of a disk scan operation for a single cleaning module.

**Attributes**:
- `module_name` (string): Name of the cleaning module (e.g., "系统垃圾", "Windows 更新残留")
- `risk_level` (enum: "low" | "medium" | "high"): Risk level associated with cleaning this module
- `total_size` (integer): Total size in bytes of all files in this module
- `file_count` (integer): Number of files found in this module
- `files` (array of FileInfo): List of files in this module
- `scan_timestamp` (datetime): When this scan was performed
- `scan_duration_seconds` (float): How long the scan took

**Relationships**:
- Contains multiple `FileInfo` objects
- Part of a complete `ScanReport`

**Validation Rules**:
- `total_size` must equal sum of all file sizes in `files` array
- `file_count` must equal length of `files` array
- `risk_level` must be one of the defined enum values
- All file paths must be within C drive

**State Transitions**:
- `scanning` → `completed` → (can be) `expired` (if scan is too old)

### FileInfo

Represents a single file that can be cleaned.

**Attributes**:
- `path` (string): Full file system path to the file
- `size` (integer): File size in bytes
- `last_access_time` (datetime): Last time file was accessed
- `last_modified_time` (datetime): Last time file was modified
- `is_directory` (boolean): Whether this is a directory (for recursive cleaning)
- `is_protected` (boolean): Whether file is protected by whitelist (computed, not stored)
- `module` (string): Which cleaning module identified this file

**Relationships**:
- Belongs to a `ScanResult`
- Can be part of a `CleaningOperation`

**Validation Rules**:
- `path` must be absolute and within C drive
- `path` must not be in whitelist (if `is_protected` is true, file should not appear in cleanable list)
- `size` must be non-negative
- `last_access_time` and `last_modified_time` must be valid datetime values

### ScanReport

Represents a complete scan of the C drive across all modules.

**Attributes**:
- `scan_id` (string): Unique identifier for this scan
- `timestamp` (datetime): When the scan was initiated
- `duration_seconds` (float): Total scan duration
- `modules` (array of ScanResult): Results for each of the 8 modules
- `total_scannable_size` (integer): Sum of all module sizes
- `status` (enum: "in_progress" | "completed" | "cancelled" | "failed"): Scan status
- `cancellation_reason` (string, optional): Why scan was cancelled (if applicable)

**Relationships**:
- Contains 8 `ScanResult` objects (one per module)
- Can trigger multiple `CleaningOperation` objects

**Validation Rules**:
- Must contain exactly 8 modules (one for each cleaning category)
- `total_scannable_size` must equal sum of all module `total_size` values
- `status` transitions: `in_progress` → `completed` | `cancelled` | `failed`

### CleaningOperation

Represents a user-initiated cleaning action.

**Attributes**:
- `operation_id` (string): Unique identifier for this operation
- `timestamp` (datetime): When cleaning was initiated
- `selected_files` (array of FileInfo): Files user selected for cleaning
- `selected_modules` (array of string): Module names user selected
- `predicted_space_bytes` (integer): Predicted space to be freed (before cleaning)
- `actual_space_freed_bytes` (integer): Actual space freed (after cleaning)
- `status` (enum: "pending" | "in_progress" | "completed" | "cancelled" | "failed"): Operation status
- `progress_percentage` (float, 0-100): Current progress
- `current_module` (string, optional): Module currently being cleaned
- `failed_files` (array of FileInfo): Files that failed to delete
- `hiberfil_sys_deleted` (boolean): Whether hiberfil.sys was deleted in this operation
- `duration_seconds` (float): How long the operation took

**Relationships**:
- References `FileInfo` objects from a `ScanReport`
- Generates a `CleaningLog` entry

**Validation Rules**:
- `predicted_space_bytes` must equal sum of selected file sizes
- `progress_percentage` must be between 0 and 100
- `status` transitions: `pending` → `in_progress` → `completed` | `cancelled` | `failed`
- If `hiberfil_sys_deleted` is true, user confirmation must have been obtained

### CleaningLog

Represents a persistent record of a cleaning operation for audit and history.

**Attributes**:
- `log_id` (string): Unique identifier for this log entry
- `timestamp` (datetime): When the cleaning operation occurred
- `operation_id` (string): Reference to the CleaningOperation
- `modules_cleaned` (array of string): List of module names that were cleaned
- `files_deleted` (array of FileInfo): List of files that were successfully deleted
- `files_failed` (array of FileInfo): List of files that failed to delete
- `total_space_freed_bytes` (integer): Total space freed
- `hiberfil_sys_deleted` (boolean): Whether hiberfil.sys was deleted
- `hiberfil_sys_restored` (boolean, optional): Whether hibernation was later restored
- `user_confirmed_risks` (boolean): Whether user confirmed understanding of risks
- `error_messages` (array of string): Any error messages encountered

**Relationships**:
- One-to-one with `CleaningOperation`
- Part of log history (collection of CleaningLog entries)

**Validation Rules**:
- `total_space_freed_bytes` must equal sum of deleted file sizes
- If `hiberfil_sys_deleted` is true, `user_confirmed_risks` must be true
- Timestamp must be valid and in the past

**Storage Format**: JSON file, one entry per line (JSONL format) for easy appending and parsing

### SystemWhitelist

Represents the protected system paths that must never be deleted.

**Attributes**:
- `protected_paths` (array of string): List of absolute paths that are protected
- `protected_patterns` (array of string): Glob patterns for protected paths (e.g., "C:\\Windows\\System32\\*")
- `version` (string): Version of the whitelist (for updates)
- `last_updated` (datetime): When whitelist was last updated

**Relationships**:
- Used by all scanner modules to filter files
- Referenced by `FileInfo.is_protected` computation

**Validation Rules**:
- All paths must be absolute and within C drive
- Patterns must be valid glob patterns
- Whitelist must include critical Windows system directories:
  - `C:\Windows\System32\`
  - `C:\Windows\SysWOW64\`
  - `C:\Windows\WinSxS\` (partial - only active components)
  - `C:\Program Files\WindowsApps\`
  - Other critical system paths

**State**: Immutable during runtime (loaded at startup, can be updated via configuration)

### HibernationFileInfo

Represents information about the hiberfil.sys file and hibernation status.

**Attributes**:
- `file_path` (string): Path to hiberfil.sys (typically "C:\hiberfil.sys")
- `file_size_bytes` (integer): Size of the hiberfil.sys file
- `exists` (boolean): Whether the file exists
- `hibernation_enabled` (boolean): Whether hibernation is currently enabled
- `risk_level` (enum: "high"): Always "high" for this file
- `impact_description` (string): Description of what happens if deleted (e.g., "无法使用休眠，Fast Startup 将被关闭")
- `can_delete` (boolean): Whether deletion is allowed (requires user confirmation)
- `last_checked` (datetime): When this information was last checked

**Relationships**:
- Special case of file cleaning (not part of regular module scan)
- Can trigger `CleaningOperation` with special handling

**Validation Rules**:
- `file_size_bytes` typically equals system RAM size (if file exists)
- `hibernation_enabled` status obtained via `powercfg /a` command
- `can_delete` can only be true if `exists` is true and user has confirmed risks

**State Transitions**:
- `exists=true, hibernation_enabled=true` → (user deletes) → `exists=false, hibernation_enabled=false`
- `exists=false, hibernation_enabled=false` → (user restores) → `exists=true, hibernation_enabled=true`

## Data Flow

### Scan Flow
1. User initiates scan → `ScanReport` created with `status="in_progress"`
2. Each module scanner runs in parallel → Creates `ScanResult` for each module
3. `ScanResult` objects contain `FileInfo` objects for each file
4. All `ScanResult` objects added to `ScanReport.modules`
5. `ScanReport.status` updated to `"completed"`
6. `ScanReport` displayed to user

### Cleaning Flow
1. User selects files from `ScanReport` → `CleaningOperation` created with `status="pending"`
2. `CleaningOperation.predicted_space_bytes` calculated from selected files
3. Operation starts → `status="in_progress"`
4. Files deleted one by one → `CleaningOperation.progress_percentage` updated
5. Failed files added to `CleaningOperation.failed_files`
6. Operation completes → `status="completed"`, `actual_space_freed_bytes` calculated
7. `CleaningLog` entry created from `CleaningOperation`
8. `CleaningLog` appended to log file

### Hibernation Flow
1. Scan detects hiberfil.sys → `HibernationFileInfo` created
2. User views hibernation info → `HibernationFileInfo.impact_description` shown
3. User confirms risks → `CleaningOperation.user_confirmed_risks = true`
4. `powercfg -h off` executed → File deleted, `HibernationFileInfo.exists = false`
5. `CleaningLog.hiberfil_sys_deleted = true`
6. (Later) User restores → `powercfg -h on` executed → `HibernationFileInfo.exists = true`

## Data Persistence

### Scan Results
- **Storage**: In-memory only (not persisted)
- **Lifetime**: Until user starts new scan or closes application
- **Reason**: Scan results can be regenerated, no need to persist

### Cleaning Logs
- **Storage**: JSONL file (`logs/cleaning_logs/cleaning_history.jsonl`)
- **Format**: One `CleaningLog` JSON object per line
- **Append-only**: New entries appended, never modified
- **Query**: Read entire file, parse JSON lines, filter as needed

### Whitelist
- **Storage**: JSON configuration file (`config/system_whitelist.json`)
- **Format**: Single JSON object with `SystemWhitelist` structure
- **Updates**: Manual edit or application update
- **Load**: At application startup

### Application State
- **Storage**: JSON file (`config/app_state.json`)
- **Contents**: Last scan timestamp, user preferences, window position, etc.
- **Updates**: On application close or state change

## Validation and Error Handling

### File Path Validation
- All paths must be absolute (start with drive letter)
- All paths must be within C drive
- Paths must be normalized (no `..`, `.`, or redundant separators)
- Whitelist check must occur before any delete operation

### Size Calculation Validation
- File sizes must be non-negative
- Total sizes must equal sum of component sizes
- Size calculations must handle very large files (use appropriate integer types)

### State Transition Validation
- Only valid state transitions allowed
- Invalid transitions should log error and maintain previous state
- User should be notified of state transition failures

## Performance Considerations

### Memory Management
- `FileInfo` objects should be lightweight (store paths, not file contents)
- Large file lists should use generators/iterators where possible
- Completed scan results can be cleared from memory when new scan starts

### Serialization
- JSON serialization for logs should be efficient
- Consider streaming large log files rather than loading entirely
- Use compact JSON (no pretty-printing) for log files

### Caching
- Whitelist should be cached in memory after first load
- File metadata (size, timestamps) can be cached during scan to avoid repeated stat calls

