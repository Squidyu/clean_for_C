"""
Unit tests for WhitelistService
"""

import pytest
import tempfile
import json
import os
from unittest.mock import patch, mock_open

from src.services.whitelist_service import WhitelistService
from src.models.whitelist import SystemWhitelist


class TestWhitelistService:
    """Test cases for WhitelistService."""

    def test_init_default(self):
        """Test initialization with default parameters."""
        service = WhitelistService()
        assert service.whitelist_file.endswith("config/system_whitelist.json")
        assert service._whitelist is None  # Lazy loading

    def test_init_custom_file(self):
        """Test initialization with custom whitelist file."""
        custom_file = "custom_whitelist.json"
        service = WhitelistService(custom_file)
        assert service.whitelist_file == custom_file

    def test_whitelist_property_loads_default(self):
        """Test that whitelist property loads default whitelist."""
        service = WhitelistService()
        whitelist = service.whitelist

        assert isinstance(whitelist, SystemWhitelist)
        assert len(whitelist.protected_paths) > 0
        assert len(whitelist.protected_patterns) > 0

    @patch('builtins.open', new_callable=mock_open, read_data='{"protected_paths": ["C:\\test"], "protected_patterns": ["*.exe"]}')
    @patch('os.path.exists', return_value=True)
    def test_whitelist_property_loads_from_file(self, mock_exists, mock_file):
        """Test that whitelist property loads from file."""
        service = WhitelistService()
        whitelist = service.whitelist

        assert isinstance(whitelist, SystemWhitelist)
        assert "C:\\test" in whitelist.protected_paths
        assert "*.exe" in whitelist.protected_patterns

    @patch('os.path.exists', return_value=False)
    def test_whitelist_property_falls_back_to_default(self, mock_exists):
        """Test that whitelist property falls back to default when file doesn't exist."""
        service = WhitelistService("nonexistent.json")
        whitelist = service.whitelist

        assert isinstance(whitelist, SystemWhitelist)
        # Should load default whitelist
        assert len(whitelist.protected_paths) > 0

    def test_is_protected_exact_path(self):
        """Test is_protected with exact path match."""
        service = WhitelistService()
        # Create a whitelist with a test path
        whitelist = SystemWhitelist(
            protected_paths=["C:\\Windows\\test"],
            protected_patterns=[]
        )
        service._whitelist = whitelist

        assert service.is_protected("C:\\Windows\\test")
        assert not service.is_protected("C:\\Windows\\other")

    def test_is_protected_pattern_match(self):
        """Test is_protected with pattern match."""
        service = WhitelistService()
        whitelist = SystemWhitelist(
            protected_paths=[],
            protected_patterns=["*.exe"]
        )
        service._whitelist = whitelist

        assert service.is_protected("C:\\test.exe")
        assert not service.is_protected("C:\\test.txt")

    def test_is_protected_case_insensitive(self):
        """Test is_protected is case insensitive."""
        service = WhitelistService()
        whitelist = SystemWhitelist(
            protected_paths=["C:\\WINDOWS\\TEST"],
            protected_patterns=[]
        )
        service._whitelist = whitelist

        assert service.is_protected("c:\\windows\\test")
        assert service.is_protected("C:\\windows\\TEST")

    def test_is_protected_invalid_path(self):
        """Test is_protected with invalid path."""
        service = WhitelistService()
        # Use default whitelist
        service._whitelist = service.get_default_whitelist()

        assert not service.is_protected("")  # Empty path
        assert not service.is_protected("D:\\test")  # Wrong drive

    def test_get_default_whitelist(self):
        """Test get_default_whitelist returns valid whitelist."""
        service = WhitelistService()
        whitelist = service.get_default_whitelist()

        assert isinstance(whitelist, SystemWhitelist)
        assert len(whitelist.protected_paths) > 0
        assert len(whitelist.protected_patterns) > 0
        assert whitelist.version == "1.0.0"

    @patch('builtins.open')
    @patch('os.makedirs')
    def test_save_whitelist_success(self, mock_makedirs, mock_file):
        """Test successful whitelist saving."""
        service = WhitelistService("test_whitelist.json")
        whitelist = SystemWhitelist(
            protected_paths=["C:\\test"],
            protected_patterns=["*.exe"],
            version="1.1.0"
        )

        result = service.save_whitelist(whitelist)
        assert result is True
        mock_file.assert_called_once()

    @patch('builtins.open', side_effect=Exception("Write error"))
    def test_save_whitelist_failure(self, mock_file):
        """Test whitelist saving failure."""
        service = WhitelistService()
        whitelist = service.get_default_whitelist()

        result = service.save_whitelist(whitelist)
        assert result is False

    def test_reload_whitelist(self):
        """Test reload_whitelist forces reload."""
        service = WhitelistService()
        original_whitelist = service._whitelist

        # Force reload
        reloaded = service.reload_whitelist()

        assert isinstance(reloaded, SystemWhitelist)
        # Should have loaded the whitelist
        assert service._whitelist is not None

    def test_validate_path_safety(self):
        """Test validate_path_safety checks multiple paths."""
        service = WhitelistService()
        whitelist = SystemWhitelist(
            protected_paths=["C:\\protected"],
            protected_patterns=[]
        )
        service._whitelist = whitelist

        paths = ["C:\\protected", "C:\\safe"]
        result = service.validate_path_safety(paths)

        assert result["C:\\protected"] is False  # Protected
        assert result["C:\\safe"] is True  # Not protected

    def test_get_protected_paths_info(self):
        """Test get_protected_paths_info returns statistics."""
        service = WhitelistService()
        whitelist = SystemWhitelist(
            protected_paths=["C:\\test1", "C:\\test2"],
            protected_patterns=["*.exe", "*.dll"],
            version="2.0.0"
        )
        service._whitelist = whitelist

        info = service.get_protected_paths_info()

        assert info["total_protected_paths"] == 2
        assert info["total_protected_patterns"] == 2
        assert info["version"] == "2.0.0"
        assert len(info["sample_protected_paths"]) <= 5
        assert len(info["sample_protected_patterns"]) <= 5


class TestSystemWhitelist:
    """Test cases for SystemWhitelist model."""

    def test_init_default(self):
        """Test SystemWhitelist initialization."""
        whitelist = SystemWhitelist()
        assert isinstance(whitelist.protected_paths, list)
        assert isinstance(whitelist.protected_patterns, list)
        assert whitelist.version == "1.0.0"
        assert whitelist.last_updated is not None

    def test_is_protected_path_match(self):
        """Test is_protected method with path matching."""
        whitelist = SystemWhitelist(
            protected_paths=["C:\\Windows", "C:\\Program Files"],
            protected_patterns=[]
        )

        assert whitelist.is_protected("C:\\Windows")
        assert whitelist.is_protected("C:\\Program Files")
        assert not whitelist.is_protected("C:\\Users")

    def test_is_protected_pattern_match(self):
        """Test is_protected method with pattern matching."""
        whitelist = SystemWhitelist(
            protected_paths=[],
            protected_patterns=["*.exe", "C:\\Windows\\*"]
        )

        assert whitelist.is_protected("notepad.exe")
        assert whitelist.is_protected("C:\\Windows\\system32\\cmd.exe")
        assert not whitelist.is_protected("readme.txt")

    def test_get_default_whitelist_has_content(self):
        """Test default whitelist has expected content."""
        whitelist = SystemWhitelist.get_default_whitelist()

        assert len(whitelist.protected_paths) > 0
        assert len(whitelist.protected_patterns) > 0

        # Should include critical Windows paths
        assert "C:\\Windows" in whitelist.protected_paths
        assert "C:\\Windows\\System32" in whitelist.protected_paths
        assert "*.exe" in whitelist.protected_patterns