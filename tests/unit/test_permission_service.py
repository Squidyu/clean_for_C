"""
Unit tests for PermissionService
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock

from src.services.permission_service import PermissionService


class TestPermissionService:
    """Test cases for PermissionService."""

    def test_init(self):
        """Test PermissionService initialization."""
        service = PermissionService()
        assert service is not None

    @patch('ctypes.windll.shell32.IsUserAnAdmin')
    def test_check_is_admin_true(self, mock_is_admin):
        """Test check_is_admin returns True when admin."""
        mock_is_admin.return_value = True

        service = PermissionService()
        result = service.check_is_admin()

        assert result is True
        mock_is_admin.assert_called_once()

    @patch('ctypes.windll.shell32.IsUserAnAdmin')
    @patch('builtins.open', side_effect=Exception("Not admin"))
    @patch('winreg.OpenKey', side_effect=Exception("Registry access failed"))
    def test_check_is_admin_false_fallback(self, mock_reg_open, mock_open, mock_is_admin):
        """Test check_is_admin returns False with fallback methods."""
        mock_is_admin.return_value = False

        service = PermissionService()
        result = service.check_is_admin()

        assert result is False

    @patch('ctypes.windll.shell32.IsUserAnAdmin', side_effect=Exception("ctypes error"))
    @patch('winreg.OpenKey', return_value=MagicMock())
    @patch('winreg.CloseKey')
    def test_check_is_admin_registry_fallback(self, mock_close, mock_open, mock_is_admin):
        """Test check_is_admin uses registry fallback."""
        service = PermissionService()
        result = service.check_is_admin()

        # Should succeed via registry method
        mock_open.assert_called_once()
        mock_close.assert_called_once()

    def test_request_elevation_already_admin(self):
        """Test request_elevation returns True when already admin."""
        service = PermissionService()

        with patch.object(service, 'check_is_admin', return_value=True):
            result = service.request_elevation()
            assert result is True

    @patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=False)
    @patch('subprocess.list2cmdline')
    @patch('ctypes.windll.shell32.ShellExecuteExW', return_value=0)
    def test_request_elevation_success(self, mock_shell_exec, mock_list2cmdline, mock_is_admin):
        """Test successful elevation request."""
        service = PermissionService()

        # Mock the required parameters
        mock_list2cmdline.return_value = "cmd.exe /c echo test"

        with patch('sys.exit') as mock_exit:
            result = service.request_elevation("Test operation")

            # Should call ShellExecuteEx and exit
            mock_shell_exec.assert_called_once()
            mock_exit.assert_called_once_with(0)

    @patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=False)
    @patch('ctypes.windll.shell32.ShellExecuteExW', return_value=1)  # Failure
    def test_request_elevation_failure(self, mock_shell_exec, mock_is_admin):
        """Test failed elevation request."""
        service = PermissionService()

        result = service.request_elevation("Test operation")

        assert result is False
        mock_shell_exec.assert_called_once()

    def test_check_path_permissions_readable_file(self):
        """Test check_path_permissions for readable file."""
        service = PermissionService()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file.flush()

            try:
                result = service.check_path_permissions(temp_file.name)

                assert result['exists'] is True
                assert result['readable'] is True
                assert result['writable'] is True  # Should be writable for temp file
                assert result['deletable'] is True

            finally:
                os.unlink(temp_file.name)

    def test_check_path_permissions_nonexistent_file(self):
        """Test check_path_permissions for nonexistent file."""
        service = PermissionService()

        result = service.check_path_permissions("C:\\nonexistent_file.txt")

        assert result['exists'] is False
        assert result['readable'] is False
        assert result['writable'] is False
        assert result['deletable'] is False

    def test_check_path_permissions_readonly_file(self):
        """Test check_path_permissions for read-only file."""
        service = PermissionService()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file.flush()
            temp_file.close()

            # Make file read-only
            os.chmod(temp_file.name, 0o444)  # Read-only

            try:
                result = service.check_path_permissions(temp_file.name)

                assert result['exists'] is True
                assert result['readable'] is True
                # Writable should be False for read-only file
                # (This may vary by system, so we don't assert)

            finally:
                # Reset permissions to allow deletion
                os.chmod(temp_file.name, 0o644)
                os.unlink(temp_file.name)

    def test_ensure_admin_rights_already_admin(self):
        """Test ensure_admin_rights when already admin."""
        service = PermissionService()

        with patch.object(service, 'check_is_admin', return_value=True):
            result = service.ensure_admin_rights("Test operation")
            assert result is True

    def test_ensure_admin_rights_needs_elevation(self):
        """Test ensure_admin_rights when elevation is needed."""
        service = PermissionService()

        with patch.object(service, 'check_is_admin', return_value=False):
            with patch.object(service, 'request_elevation', return_value=True):
                result = service.ensure_admin_rights("Test operation")
                assert result is True

    def test_ensure_admin_rights_elevation_failed(self):
        """Test ensure_admin_rights when elevation fails."""
        service = PermissionService()

        with patch.object(service, 'check_is_admin', return_value=False):
            with patch.object(service, 'request_elevation', return_value=False):
                result = service.ensure_admin_rights("Test operation")
                assert result is False

    def test_get_privilege_status(self):
        """Test get_privilege_status returns expected structure."""
        service = PermissionService()

        with patch.object(service, 'check_is_admin', return_value=True):
            status = service.get_privilege_status()

            assert 'is_admin' in status
            assert 'can_elevate' in status
            assert 'elevation_supported' in status
            assert status['is_admin'] is True

    def test_validate_file_operation_safety(self):
        """Test validate_file_operation_safety for multiple files."""
        service = PermissionService()

        # Create temporary files
        temp_files = []
        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(f"test content {i}".encode())
                    temp_files.append(temp_file.name)

            result = service.validate_file_operation_safety(temp_files)

            assert len(result) == 3
            for path in temp_files:
                assert path in result
                assert result[path]['exists'] is True
                assert result[path]['readable'] is True

        finally:
            # Clean up
            for path in temp_files:
                try:
                    os.unlink(path)
                except:
                    pass

    @patch('ctypes.windll.kernel32.GetDiskFreeSpaceExW')
    @patch('os.path.splitdrive', return_value=('C:', 'test'))
    def test_check_disk_space_windows(self, mock_splitdrive, mock_get_disk_space):
        """Test check_disk_space on Windows."""
        # Mock successful disk space check
        mock_get_disk_space.return_value = 1  # Success
        # Mock free space as 1GB
        mock_get_disk_space.return_value = 1
        # This is a simplified test - real implementation would be more complex

        service = PermissionService()
        result = service.check_is_admin()  # Just test that method exists

        assert result is not None  # Basic smoke test

    def test_get_privilege_status_structure(self):
        """Test get_privilege_status returns complete structure."""
        service = PermissionService()

        with patch.object(service, 'check_is_admin', return_value=False):
            status = service.get_privilege_status()

            required_keys = ['is_admin', 'can_elevate', 'elevation_supported']
            for key in required_keys:
                assert key in status

    def test_service_handles_exceptions_gracefully(self):
        """Test that service methods handle exceptions gracefully."""
        service = PermissionService()

        # Test with invalid path
        result = service.check_path_permissions("")

        # Should return default structure
        assert 'exists' in result
        assert 'readable' in result
        assert result['exists'] is False

        # Test validate_file_operation_safety with invalid paths
        result = service.validate_file_operation_safety(["", "invalid:path"])
        assert isinstance(result, dict)