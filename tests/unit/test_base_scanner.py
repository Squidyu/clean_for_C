"""
Unit tests for BaseScanner
"""
import pytest
import threading
from datetime import datetime

from src.modules.base_scanner import BaseScanner
from src.models.scan_result import ScanResult
from src.models.file_info import FileInfo
from src.services.whitelist_service import WhitelistService


class MockScanner(BaseScanner):
    """Mock scanner for testing BaseScanner functionality"""

    def __init__(self, test_files=None, whitelist_service=None):
        super().__init__(whitelist_service)
        self.test_files = test_files or []
        self.scan_called = False

    def get_module_name(self):
        return "测试模块"

    def get_risk_level(self):
        return "low"

    def _scan_files(self, cancellation_token):
        self.scan_called = True

        # Check cancellation
        if cancellation_token.is_set():
            raise KeyboardInterrupt("Cancelled")

        return self.test_files


class TestBaseScanner:
    """Test BaseScanner functionality"""

    def test_initialization(self):
        """Test scanner initialization"""
        scanner = MockScanner()
        assert scanner.get_module_name() == "测试模块"
        assert scanner.get_risk_level() == "low"

    def test_scan_success(self):
        """Test successful scan"""
        test_files = [
            FileInfo("C:\\test\\file1.txt", 1000, datetime.now(), datetime.now(), module="测试模块"),
            FileInfo("C:\\test\\file2.txt", 2000, datetime.now(), datetime.now(), module="测试模块")
        ]

        scanner = MockScanner(test_files)
        cancellation_token = threading.Event()

        result = scanner.scan(cancellation_token)

        assert isinstance(result, ScanResult)
        assert result.module_name == "测试模块"
        assert result.risk_level == "low"
        assert result.file_count == 2
        assert result.total_size == 3000
        assert len(result.files) == 2
        assert scanner.scan_called == True

    def test_scan_with_cancellation(self):
        """Test scan with cancellation"""
        scanner = MockScanner()
        cancellation_token = threading.Event()
        cancellation_token.set()  # Cancel immediately

        result = scanner.scan(cancellation_token)

        # Should return empty result when cancelled
        assert isinstance(result, ScanResult)
        assert result.file_count == 0
        assert result.total_size == 0

    def test_scan_with_whitelist_filtering(self):
        """Test that protected files are filtered out"""
        # Create a mock whitelist service
        whitelist_service = WhitelistService.__new__(WhitelistService)
        whitelist_service.is_protected = lambda path: path.endswith("protected.txt")

        test_files = [
            FileInfo("C:\\test\\normal.txt", 1000, datetime.now(), datetime.now(), module="测试模块"),
            FileInfo("C:\\test\\protected.txt", 2000, datetime.now(), datetime.now(), module="测试模块")
        ]

        scanner = MockScanner(test_files, whitelist_service)
        cancellation_token = threading.Event()

        result = scanner.scan(cancellation_token)

        assert result.file_count == 1  # Protected file filtered out
        assert result.total_size == 1000
        assert len(result.files) == 1
        assert result.files[0].path == "C:\\test\\normal.txt"

    def test_scan_error_handling(self):
        """Test error handling in scan"""

        class ErrorScanner(MockScanner):
            def _scan_files(self, cancellation_token):
                raise Exception("Test error")

        scanner = ErrorScanner()
        cancellation_token = threading.Event()

        result = scanner.scan(cancellation_token)

        # Should return empty result on error
        assert isinstance(result, ScanResult)
        assert result.file_count == 0
        assert result.total_size == 0

    def test_create_file_info(self):
        """Test _create_file_info helper method"""
        scanner = MockScanner()

        # Create temp file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            file_info = scanner._create_file_info(temp_path)

            assert file_info.path == temp_path
            assert file_info.size == len(b"test content")
            assert isinstance(file_info.last_access_time, datetime)
            assert isinstance(file_info.last_modified_time, datetime)
            assert file_info.module == "测试模块"

        finally:
            os.unlink(temp_path)

    def test_create_file_info_invalid_path(self):
        """Test _create_file_info with invalid path"""
        scanner = MockScanner()

        file_info = scanner._create_file_info("C:\\nonexistent\\file.txt")

        assert file_info.path == "C:\\nonexistent\\file.txt"
        assert file_info.size == 0  # Default size for missing files
