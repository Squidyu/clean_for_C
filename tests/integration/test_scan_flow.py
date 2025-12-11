"""
Integration tests for the complete scan workflow
"""
import pytest
import threading
import tempfile
import os
from unittest.mock import patch

from src.services.scanner_service import ScannerService
from src.models.scan_report import ScanReport


class TestScanFlow:
    """Test the complete scanning workflow"""

    def setup_method(self):
        """Setup before each test"""
        self.service = ScannerService()

    def test_full_scan_workflow(self):
        """Test the complete scan workflow"""
        # Create cancellation token
        cancellation_token = threading.Event()

        # Perform scan
        report = self.service.scan_all_modules(cancellation_token)

        # Verify report structure
        assert isinstance(report, ScanReport)
        assert report.scan_id is not None
        assert report.timestamp is not None
        assert report.duration_seconds >= 0
        assert isinstance(report.modules, list)

        # Should have 7 modules (not 8, hibernation scanner is separate)
        assert len(report.modules) == 7

        # Verify each module has required fields
        for module in report.modules:
            assert hasattr(module, 'module_name')
            assert hasattr(module, 'risk_level')
            assert hasattr(module, 'total_size')
            assert hasattr(module, 'file_count')
            assert hasattr(module, 'files')
            assert hasattr(module, 'scan_timestamp')
            assert hasattr(module, 'scan_duration_seconds')

            # Risk level should be valid
            assert module.risk_level in ['low', 'medium', 'high']

    def test_scan_cancellation(self):
        """Test that scan can be cancelled"""
        cancellation_token = threading.Event()

        # Start scan in background
        import threading
        result = [None]
        exception = [None]

        def scan_worker():
            try:
                result[0] = self.service.scan_all_modules(cancellation_token)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=scan_worker)
        thread.start()

        # Cancel immediately
        cancellation_token.set()

        # Wait for completion
        thread.join(timeout=5.0)

        # Verify scan was cancelled or completed normally
        if result[0]:
            assert result[0].status in ['completed', 'cancelled']
        assert exception[0] is None

    def test_get_available_modules(self):
        """Test getting available modules"""
        modules = self.service.get_available_modules()

        assert isinstance(modules, list)
        assert len(modules) == 7  # 7 scanner modules

        for module in modules:
            assert 'name' in module
            assert 'risk_level' in module
            assert module['risk_level'] in ['low', 'medium', 'high']

    def test_scan_single_module(self):
        """Test scanning a single module"""
        cancellation_token = threading.Event()

        # Test scanning system junk module
        result = self.service.scan_single_module("系统垃圾", cancellation_token)

        assert result.module_name == "系统垃圾"
        assert result.risk_level == "low"
        assert hasattr(result, 'total_size')
        assert hasattr(result, 'file_count')
        assert hasattr(result, 'files')

    def test_scan_invalid_module(self):
        """Test scanning an invalid module name"""
        cancellation_token = threading.Event()

        with pytest.raises(ValueError, match="Unknown module"):
            self.service.scan_single_module("不存在的模块", cancellation_token)

    @patch('src.services.scanner_service.SystemJunkScanner.scan')
    def test_scan_with_module_error(self, mock_scan):
        """Test handling of individual module scan errors"""
        # Mock one scanner to raise an exception
        mock_scan.side_effect = Exception("Mock scan error")

        cancellation_token = threading.Event()
        report = self.service.scan_all_modules(cancellation_token)

        # Report should still be created, but one module should have empty results
        assert isinstance(report, ScanReport)
        assert len(report.modules) == 7

        # Check that error was handled gracefully
        system_junk_module = None
        for module in report.modules:
            if module.module_name == "系统垃圾":
                system_junk_module = module
                break

        assert system_junk_module is not None
        # Module should have empty results due to mock error
        assert system_junk_module.file_count == 0
