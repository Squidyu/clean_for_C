# Quick Start Guide: Windows C 盘清理工具

**Date**: 2025-12-10  
**Feature**: Windows C 盘智能清理工具

## Overview

This guide provides a quick start for developers working on the Windows C Drive Cleaner application. It covers setup, basic usage, and key development workflows.

## Prerequisites

- **Python**: 3.11 or higher
- **Windows**: Windows 10 or later
- **Git**: For version control
- **IDE**: Recommended: VS Code or PyCharm

## Initial Setup

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd clean_for_C
git checkout 001-windows-c-drive-cleaner
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install pywin32 pytest pytest-cov
```

### 4. Verify Installation

```bash
python --version  # Should be 3.11+
pytest --version
```

## Project Structure

```
clean_for_C/
├── src/
│   ├── models/          # Data models
│   ├── modules/         # Cleaning module scanners
│   ├── services/        # Business logic services
│   ├── ui/              # User interface
│   └── utils/           # Utility functions
├── tests/               # Test suite
├── logs/                # Application logs (gitignored)
├── config/              # Configuration files
└── specs/               # Specification documents
```

## Running the Application

### Development Mode

```bash
python src/ui/main_window.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_scanners.py
```

## Key Development Workflows

### Adding a New Cleaning Module

1. **Create Scanner Class**:
   ```python
   # src/modules/my_module.py
   from .base_scanner import BaseScanner
   
   class MyModuleScanner(BaseScanner):
       def get_module_name(self) -> str:
           return "我的模块"
       
       def get_risk_level(self) -> str:
           return "low"
       
       def scan(self, cancellation_token):
           # Implementation
           pass
   ```

2. **Register in ScannerService**:
   ```python
   # src/services/scanner_service.py
   from .modules.my_module import MyModuleScanner
   
   MODULES = {
       "我的模块": MyModuleScanner,
       # ... other modules
   }
   ```

3. **Add Tests**:
   ```python
   # tests/unit/test_my_module.py
   def test_my_module_scan():
       scanner = MyModuleScanner()
       result = scanner.scan(threading.Event())
       assert result.module_name == "我的模块"
   ```

### Modifying Whitelist

1. **Edit Configuration**:
   ```json
   // config/system_whitelist.json
   {
     "protected_paths": [
       "C:\\Windows\\System32",
       "C:\\Windows\\SysWOW64"
     ],
     "protected_patterns": [
       "C:\\Windows\\System32\\*"
     ]
   }
   ```

2. **Reload in Application**:
   - Whitelist is loaded at startup
   - Changes require application restart

### Adding UI Components

1. **Create View Class**:
   ```python
   # src/ui/my_view.py
   import tkinter as tk
   
   class MyView(tk.Frame):
       def __init__(self, parent):
           super().__init__(parent)
           # UI setup
   ```

2. **Integrate in Main Window**:
   ```python
   # src/ui/main_window.py
   from .my_view import MyView
   
   class MainWindow:
       def __init__(self):
           self.my_view = MyView(self.root)
   ```

## Testing Guidelines

### Unit Tests

- Test individual components in isolation
- Use mocks for file system operations
- Test error handling and edge cases

**Example**:
```python
def test_scanner_handles_missing_directory():
    scanner = SystemJunkScanner()
    # Mock file system to return FileNotFoundError
    result = scanner.scan(threading.Event())
    assert result.file_count == 0
```

### Integration Tests

- Test with real file system (use test fixtures)
- Test complete workflows (scan → select → clean)
- Test cancellation behavior

**Example**:
```python
def test_full_clean_workflow():
    # Create test files
    create_test_files()
    
    # Run scan
    report = scanner_service.scan_all_modules()
    
    # Select files
    operation = create_operation(report)
    
    # Clean
    result = cleaner_service.clean_files(operation)
    
    # Verify
    assert result.status == "completed"
```

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

1. **Permission Errors**:
   - Run as administrator
   - Check UAC settings
   - Verify file permissions

2. **Scan Timeout**:
   - Check cancellation token is being checked
   - Verify multi-threading is working
   - Profile slow operations

3. **Whitelist Issues**:
   - Verify whitelist is loaded correctly
   - Check path matching logic
   - Review protected paths list

## Code Style

- Follow PEP 8 Python style guide
- Use type hints for all function signatures
- Document public APIs with docstrings
- Keep functions focused and small

**Example**:
```python
def scan_directory(path: str, cancellation_token: threading.Event) -> List[FileInfo]:
    """
    Scans a directory for cleanable files.
    
    Args:
        path: Directory path to scan
        cancellation_token: Event to signal cancellation
        
    Returns:
        List of FileInfo objects for found files
        
    Raises:
        PermissionError: If directory is not accessible
    """
    # Implementation
    pass
```

## Performance Tips

1. **Use `os.scandir()` instead of `os.listdir()`** for better performance
2. **Check cancellation token frequently** (every 100 files or 1 second)
3. **Use generators** for large file lists to save memory
4. **Cache file metadata** to avoid repeated stat calls
5. **Parallel processing** for independent operations

## Next Steps

- Read [data-model.md](./data-model.md) for data structure details
- Read [contracts/](./contracts/) for interface specifications
- Review [spec.md](./spec.md) for feature requirements
- Check [plan.md](./plan.md) for implementation plan

## Getting Help

- Review specification documents in `specs/001-windows-c-drive-cleaner/`
- Check test files for usage examples
- Review constitution in `.specify/memory/constitution.md` for design principles

