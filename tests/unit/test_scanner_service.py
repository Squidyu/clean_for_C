"""
Unit tests for ScannerService
"""
import pytest
import threading
from unittest.mock import patch, MagicMock

from src.services.scanner_service import ScannerService
from src.models.scan_report import ScanReport
from src.models.scan_result import ScanResult
from src.models.file_info import FileInfo
from datetime import datetime


class TestScannerService:
    """Test ScannerService functionality"""

    def setup_method(self):
        """Setup before each test"""
        self.service = ScannerService()

    def test_initialization(self):
        """Test service initialization"""
        assert self.service.whitelist_service is not None
        assert self.service._executor is None

    def test_get_available_modules(self):
        """Test getting available modules"""
        modules = self.service.get_available_modules()

        assert isinstance(modules, list)
        assert len(modules) == 7  # 7 scanner modules

        # Check that all modules have required fields
        module_names = [m['name'] for m in modules]
        assert "系统垃圾" in module_names
        assert "Windows 更新残留" in module_names
        assert "浏览器缓存" in module_names
        assert "第三方应用缓存" in module_names
        assert "回收站" in module_names
        assert "大文件扫描" in module_names
        assert "应用残留" in module_names

        for module in modules:
            assert module['risk_level'] in ['low', 'medium', 'high']

    def test_scan_single_module_success(self):
        """Test scanning a single module successfully"""
        cancellation_token = threading.Event()

        result = self.service.scan_single_module("系统垃圾", cancellation_token)

        assert isinstance(result, ScanResult)
        assert result.module_name == "系统垃圾"
        assert result.risk_level == "low"
        assert hasattr(result, 'total_size')
        assert hasattr(result, 'file_count')
        assert hasattr(result, 'files')

    def test_scan_single_module_invalid_name(self):
        """Test scanning with invalid module name"""
        cancellation_token = threading.Event()

        with pytest.raises(ValueError, match="Unknown module"):
            self.service.scan_single_module("不存在的模块", cancellation_token)

    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_scan_all_modules_cancellation(self, mock_executor_class):
        """Test cancelling scan_all_modules"""
        # Mock executor
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        mock_executor_class.return_value.__exit__.return_value = None

        # Mock futures
        mock_future = MagicMock()
        mock_future.result.return_value = ScanResult(
            "测试模块", "low", 1000, 1, [], datetime.now(), 1.0
        )
        mock_executor.submit.return_value = mock_future
        mock_executor.__iter__ = MagicMock(return_value=iter([mock_future]))

        # Test cancellation
        cancellation_token = threading.Event()
        cancellation_token.set()  # Already cancelled

        report = self.service.scan_all_modules(cancellation_token)

        assert isinstance(report, ScanReport)
        assert report.status == "cancelled"

    def test_get_scanner_by_name(self):
        """Test getting scanner by name"""
        scanner = self.service._get_scanner_by_name("系统垃圾")
        assert scanner is not None
        assert scanner.get_module_name() == "系统垃圾"

        # Test invalid name
        scanner = self.service._get_scanner_by_name("不存在的模块")
        assert scanner is None

    def test_get_all_scanners(self):
        """Test getting all scanner instances"""
        scanners = self.service._get_all_scanners()

        assert isinstance(scanners, list)
        assert len(scanners) == 7

        # Check module names
        module_names = [s.get_module_name() for s in scanners]
        expected_names = [
            "系统垃圾", "Windows 更新残留", "浏览器缓存",
            "第三方应用缓存", "回收站", "大文件扫描", "应用残留"
        ]

        for expected in expected_names:
            assert expected in module_names

    def test_cancel_scan(self):
        """Test cancelling scan operations"""
        # Set up a mock executor
        mock_executor = MagicMock()
        self.service._executor = mock_executor

        self.service.cancel_scan()

        # Verify executor was shut down
        mock_executor.shutdown.assert_called_once_with(wait=False)
        assert self.service._executor is None

    def test_cancel_scan_no_executor(self):
        """Test cancelling when no executor is running"""
        self.service._executor = None

        # Should not raise exception
        self.service.cancel_scan()
