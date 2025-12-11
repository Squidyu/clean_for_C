# Tasks: Windows C 盘智能清理工具

**Input**: Design documents from `/specs/001-windows-c-drive-cleaner/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included as they are critical for a safety-focused tool like this disk cleaner.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below follow the single project structure from plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure per implementation plan (src/, tests/, logs/, config/)
- [x] T002 Initialize Python 3.11+ project with pywin32, pytest dependencies in requirements.txt
- [x] T003 [P] Configure pytest in pytest.ini with coverage settings
- [x] T004 [P] Create .gitignore with Python patterns, logs/, config/ exclusions
- [x] T005 [P] Create README.md with project overview and setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 [P] Create SystemWhitelist model in src/models/whitelist.py with protected_paths and protected_patterns
- [x] T007 [P] Create FileInfo model in src/models/file_info.py with path, size, timestamps, is_protected attributes
- [x] T008 [P] Create ScanResult model in src/models/scan_result.py with module_name, risk_level, total_size, files array
- [x] T009 Create WhitelistService in src/services/whitelist_service.py with is_protected(), load_whitelist(), get_default_whitelist() methods
- [x] T010 Create PermissionService in src/services/permission_service.py with check_is_admin(), request_elevation(), check_path_permissions() methods
- [x] T011 [P] Create utility functions in src/utils/path_utils.py for path validation and normalization
- [x] T012 [P] Create utility functions in src/utils/size_utils.py for byte formatting and size calculations
- [x] T013 [P] Create utility functions in src/utils/file_utils.py for file operations and error handling
- [x] T014 Create default whitelist configuration file config/system_whitelist.json with critical Windows paths
- [x] T015 [P] Create unit tests for WhitelistService in tests/unit/test_whitelist_service.py
- [x] T016 [P] Create unit tests for PermissionService in tests/unit/test_permission_service.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 扫描并查看 C 盘空间占用 (Priority: P1) 🎯 MVP

**Goal**: Users can scan C drive and view categorized space usage by module within 30 seconds

**Independent Test**: Launch application, click scan button, verify 8 modules are scanned and displayed within 30 seconds. Can be tested independently without any cleaning functionality.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T017 [P] [US1] Create integration test for full scan workflow in tests/integration/test_scan_flow.py
- [ ] T018 [P] [US1] Create unit tests for BaseScanner interface in tests/unit/test_base_scanner.py
- [ ] T019 [P] [US1] Create unit tests for ScannerService in tests/unit/test_scanner_service.py

### Implementation for User Story 1

- [x] T020 [P] [US1] Create BaseScanner abstract class in src/modules/base_scanner.py with scan(), get_risk_level(), get_module_name() methods
- [x] T021 [P] [US1] Create SystemJunkScanner in src/modules/system_junk.py implementing BaseScanner for Windows temp files
- [x] T022 [P] [US1] Create WindowsUpdatesScanner in src/modules/windows_updates.py implementing BaseScanner for update remnants
- [x] T023 [P] [US1] Create BrowserCacheScanner in src/modules/browser_cache.py implementing BaseScanner for Edge/Chrome/Firefox cache
- [x] T024 [P] [US1] Create AppCacheScanner in src/modules/app_cache.py implementing BaseScanner for third-party app cache
- [x] T025 [P] [US1] Create RecycleBinScanner in src/modules/recycle_bin.py implementing BaseScanner for recycle bin files
- [x] T026 [P] [US1] Create LargeFilesScanner in src/modules/large_files.py implementing BaseScanner for files > threshold
- [x] T027 [P] [US1] Create AppRemnantsScanner in src/modules/app_remnants.py implementing BaseScanner for uninstalled app leftovers
- [x] T028 [US1] Create ScanReport model in src/models/scan_report.py with scan_id, timestamp, modules array, status
- [x] T029 [US1] Create ScannerService in src/services/scanner_service.py with scan_all_modules() and scan_single_module() methods using ThreadPoolExecutor
- [x] T030 [US1] Create main application window in src/ui/main_window.py with scan button and basic layout
- [x] T031 [US1] Create scan view in src/ui/scan_view.py with module tree display, expand/collapse, file list with path/size/timestamp
- [ ] T032 [US1] Integrate ScannerService with main window, add scan button handler and progress display
- [ ] T033 [US1] Add cancellation support to scan operations with cancellation button in UI
- [ ] T034 [US1] Add error handling and logging for scan operations

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - users can scan and view results

---

## Phase 4: User Story 2 - 选择性清理安全文件 (Priority: P1)

**Goal**: Users can selectively choose files to clean and execute cleaning with progress feedback

**Independent Test**: After scan, select files from modules, verify predicted space display, execute cleaning, verify actual space freed and results display. Can be tested independently without hibernation or logging features.

### Tests for User Story 2

- [ ] T035 [P] [US2] Create integration test for cleaning workflow in tests/integration/test_clean_flow.py
- [ ] T036 [P] [US2] Create unit tests for CleanerService in tests/unit/test_cleaner_service.py

### Implementation for User Story 2

- [x] T037 [US2] Create CleaningOperation model in src/models/cleaning_operation.py with operation_id, selected_files, predicted_space, actual_space, status, progress_percentage
- [x] T038 [US2] Create CleanerService in src/services/cleaner_service.py with predict_space() and clean_files() methods
- [x] T039 [US2] Implement file selection UI in src/ui/scan_view.py with checkboxes for modules and individual files
- [x] T040 [US2] Add predicted space calculation display when files are selected in scan_view.py
- [x] T041 [US2] Create cleaning view in src/ui/cleaning_view.py with progress bar, current module display, space freed indicator
- [x] T042 [US2] Integrate CleanerService with UI, add start cleaning button handler and progress updates
- [x] T043 [US2] Implement file deletion logic in CleanerService with whitelist validation and error handling
- [x] T044 [US2] Add cancellation support to cleaning operations with cancellation button
- [x] T045 [US2] Create cleaning results display showing total space freed, module contributions, failed files list
- [x] T046 [US2] Add error handling for locked files, permission errors, and other file access issues

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can scan, select, and clean files

---

## Phase 5: User Story 3 - 安全处理高风险操作（休眠文件） (Priority: P2)

**Goal**: Users can view hiberfil.sys information, understand risks, and safely delete/restore hibernation

**Independent Test**: View hibernation info, verify risk warning display, confirm risks, delete hiberfil.sys, verify deletion and log entry, restore hibernation. Can be tested independently.

### Tests for User Story 3

- [ ] T047 [P] [US3] Create integration test for hibernation workflow in tests/integration/test_hibernation.py
- [ ] T048 [P] [US3] Create unit tests for hibernation scanner and service methods in tests/unit/test_hibernation.py

### Implementation for User Story 3

- [x] T049 [US3] Create HibernationFileInfo model in src/models/hibernation_file_info.py with file_path, file_size, exists, hibernation_enabled, risk_level, impact_description
- [x] T050 [US3] Create HibernationScanner in src/modules/hibernation.py implementing BaseScanner for hiberfil.sys detection
- [x] T051 [US3] Add delete_hiberfil_sys() method to CleanerService with user_confirmed validation and powercfg -h off execution
- [x] T052 [US3] Add restore_hibernation() method to CleanerService with powercfg -h on execution
- [x] T053 [US3] Create hibernation info display in src/ui/scan_view.py showing file size, risk level, impact description
- [x] T054 [US3] Add "I understand the risks" confirmation checkbox for hibernation deletion in UI
- [x] T055 [US3] Integrate hibernation deletion with CleanerService, add delete and restore buttons with confirmation dialogs
- [x] T056 [US3] Add hibernation status checking using powercfg /a command in HibernationScanner
- [x] T057 [US3] Add logging for hibernation operations (deletion and restoration)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - full cleaning functionality with hibernation support

---

## Phase 6: User Story 4 - 查看清理日志和历史记录 (Priority: P3)

**Goal**: Users can view detailed cleaning logs with timestamp, modules, files, failures, and hiberfil.sys status

**Independent Test**: Execute cleaning operation, view log entry, verify all details are present. View log history, verify multiple entries are displayed. Can be tested independently.

### Tests for User Story 4

- [ ] T058 [P] [US4] Create unit tests for LogService in tests/unit/test_log_service.py
- [ ] T059 [P] [US4] Create integration test for log viewing in tests/integration/test_log_viewing.py

### Implementation for User Story 4

- [ ] T060 [US4] Create CleaningLog model in src/models/cleaning_log.py with log_id, timestamp, operation_id, modules_cleaned, files_deleted, files_failed, total_space_freed, hiberfil_sys_deleted
- [ ] T061 [US4] Create LogService in src/services/log_service.py with log_operation(), get_log_history(), query_logs() methods
- [ ] T062 [US4] Implement JSONL log file format in LogService with append-only log file in logs/cleaning_logs/cleaning_history.jsonl
- [ ] T063 [US4] Integrate LogService with CleanerService to log all cleaning operations automatically
- [ ] T064 [US4] Create log view in src/ui/log_view.py with log history display, filtering, and detailed log entry view
- [ ] T065 [US4] Add log viewing menu item and window in main_window.py
- [ ] T066 [US4] Implement log filtering by module, date range, and hiberfil.sys deletion status
- [ ] T067 [US4] Add log entry detail view showing full file lists, error messages, and operation metadata

**Checkpoint**: At this point, all user stories should be independently functional - complete application with scanning, cleaning, hibernation, and logging

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T068 [P] Add comprehensive error handling and user-friendly error messages throughout application
- [ ] T069 [P] Add application logging using Python logging module with JSON formatter for structured logs
- [ ] T070 [P] Create application state persistence in config/app_state.json for window position, preferences, last scan time
- [ ] T071 [P] Add disk space check on startup in main_window.py, warn if C drive has < 100MB free
- [ ] T072 [P] Optimize scan performance with os.scandir() usage, caching, and early path filtering
- [ ] T073 [P] Add progress callbacks for real-time UI updates during scanning and cleaning
- [ ] T074 [P] Add comprehensive unit test coverage for all modules and services
- [ ] T075 [P] Add integration tests for edge cases (permission errors, locked files, cancellation)
- [ ] T076 [P] Update documentation in README.md with usage instructions and feature overview
- [ ] T077 [P] Run quickstart.md validation and ensure all setup steps work correctly
- [ ] T078 [P] Add code comments and docstrings for all public APIs and key functions
- [ ] T079 [P] Performance testing and optimization to ensure 30-second scan target is met
- [ ] T080 [P] Security review of whitelist implementation and file deletion logic

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3 → US4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (needs scan results to clean) - Should be independently testable with mock scan data
- **User Story 3 (P2)**: Can start after Foundational - May use US1 scan results but should be independently testable
- **User Story 4 (P3)**: Depends on US2 (needs cleaning operations to log) - Should be independently testable with mock operations

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before UI
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- All scanner modules (T021-T027) marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all scanner modules in parallel (T021-T027):
Task: "Create SystemJunkScanner in src/modules/system_junk.py"
Task: "Create WindowsUpdatesScanner in src/modules/windows_updates.py"
Task: "Create BrowserCacheScanner in src/modules/browser_cache.py"
Task: "Create AppCacheScanner in src/modules/app_cache.py"
Task: "Create RecycleBinScanner in src/modules/recycle_bin.py"
Task: "Create LargeFilesScanner in src/modules/large_files.py"
Task: "Create AppRemnantsScanner in src/modules/app_remnants.py"

# Launch all tests in parallel (T017-T019):
Task: "Create integration test for full scan workflow in tests/integration/test_scan_flow.py"
Task: "Create unit tests for BaseScanner interface in tests/unit/test_base_scanner.py"
Task: "Create unit tests for ScannerService in tests/unit/test_scanner_service.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Scan and View)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Scan) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Clean) → Test independently → Deploy/Demo
4. Add User Story 3 (Hibernation) → Test independently → Deploy/Demo
5. Add User Story 4 (Logs) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Scan)
   - Developer B: User Story 2 (Clean) - can start after US1 models are ready
   - Developer C: User Story 3 (Hibernation) - can start independently
3. Stories complete and integrate independently

---

## Task Summary

- **Total Tasks**: 80
- **Setup Tasks**: 5 (Phase 1)
- **Foundational Tasks**: 11 (Phase 2)
- **User Story 1 Tasks**: 18 (Phase 3)
- **User Story 2 Tasks**: 12 (Phase 4)
- **User Story 3 Tasks**: 11 (Phase 5)
- **User Story 4 Tasks**: 8 (Phase 6)
- **Polish Tasks**: 15 (Phase 7)

### Parallel Opportunities Identified

- **Phase 1**: 3 parallel tasks (T003-T005)
- **Phase 2**: 8 parallel tasks (T006-T008, T011-T013, T015-T016)
- **Phase 3**: 10 parallel tasks (7 scanners + 3 tests)
- **Phase 4**: 2 parallel tasks (tests)
- **Phase 5**: 2 parallel tasks (tests)
- **Phase 6**: 2 parallel tasks (tests)
- **Phase 7**: 15 parallel tasks (all polish tasks)

### Independent Test Criteria

- **US1**: Launch app, click scan, verify 8 modules displayed within 30 seconds
- **US2**: Select files, verify predicted space, execute cleaning, verify results
- **US3**: View hibernation info, confirm risks, delete, verify, restore
- **US4**: Execute cleaning, view log entry, verify all details present

### Suggested MVP Scope

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1 only)**

This delivers core value: users can scan and view what's taking up space on their C drive. Cleaning, hibernation, and logging can be added incrementally.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All file operations must validate against whitelist
- All operations must support cancellation
- All errors must be logged and handled gracefully

