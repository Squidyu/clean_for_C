"""
Whitelist Service

Manages the system file whitelist that protects critical system files from deletion.
This is a critical security service that prevents accidental system damage.
"""

import json
import os
from typing import Optional
from models.whitelist import SystemWhitelist


class WhitelistService:
    """
    Service for managing system file protection whitelist.

    This service handles loading, validating, and checking the system whitelist
    that prevents deletion of critical Windows system files and directories.
    """

    def __init__(self, whitelist_file: str = "config/system_whitelist.json"):
        """
        Initialize whitelist service.

        Args:
            whitelist_file: Path to whitelist configuration file
        """
        self.whitelist_file = whitelist_file
        self._whitelist: Optional[SystemWhitelist] = None

    @property
    def whitelist(self) -> SystemWhitelist:
        """
        Get the current whitelist, loading it if necessary.

        Returns:
            Current system whitelist
        """
        if self._whitelist is None:
            self._whitelist = self.load_whitelist()
        return self._whitelist

    def is_protected(self, path: str) -> bool:
        """
        Check if a path is protected by the system whitelist.

        This is the primary method used throughout the application to
        determine if a file can be safely presented for deletion.

        Args:
            path: Absolute path to check

        Returns:
            True if path is protected and should not be deleted
        """
        if not path:
            return False

        return self.whitelist.is_protected(path)

    def load_whitelist(self) -> SystemWhitelist:
        """
        Load whitelist from configuration file.

        Attempts to load from the configured file, falls back to default
        whitelist if file doesn't exist or is invalid.

        Returns:
            SystemWhitelist instance
        """
        try:
            if os.path.exists(self.whitelist_file):
                with open(self.whitelist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Validate required fields
                if not all(key in data for key in ['protected_paths', 'protected_patterns']):
                    raise ValueError("Invalid whitelist file format")

                return SystemWhitelist(
                    protected_paths=data['protected_paths'],
                    protected_patterns=data['protected_patterns'],
                    version=data.get('version', '1.0.0'),
                    last_updated=data.get('last_updated')
                )
            else:
                # File doesn't exist, use default
                return self.get_default_whitelist()

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Invalid file, log warning and use default
            print(f"Warning: Failed to load whitelist from {self.whitelist_file}: {e}")
            print("Using default system whitelist")
            return self.get_default_whitelist()

    def get_default_whitelist(self) -> SystemWhitelist:
        """
        Get the default system whitelist.

        This method provides a fallback whitelist with critical system paths.
        Used when the configuration file is missing or invalid.

        Returns:
            Default SystemWhitelist with critical Windows paths
        """
        return SystemWhitelist.get_default_whitelist()

    def save_whitelist(self, whitelist: SystemWhitelist) -> bool:
        """
        Save whitelist to configuration file.

        Args:
            whitelist: SystemWhitelist to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure config directory exists
            config_dir = os.path.dirname(self.whitelist_file)
            os.makedirs(config_dir, exist_ok=True)

            # Prepare data for JSON serialization
            data = {
                'protected_paths': whitelist.protected_paths,
                'protected_patterns': whitelist.protected_patterns,
                'version': whitelist.version,
                'last_updated': whitelist.last_updated.isoformat() if whitelist.last_updated else None
            }

            # Save to file
            with open(self.whitelist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Update cached whitelist
            self._whitelist = whitelist

            return True

        except Exception as e:
            print(f"Error saving whitelist: {e}")
            return False

    def reload_whitelist(self) -> SystemWhitelist:
        """
        Force reload whitelist from file.

        Returns:
            Reloaded SystemWhitelist
        """
        self._whitelist = None
        return self.load_whitelist()

    def validate_path_safety(self, paths: list) -> dict:
        """
        Validate safety of multiple paths against whitelist.

        Args:
            paths: List of paths to validate

        Returns:
            Dict mapping paths to safety status
        """
        result = {}
        for path in paths:
            result[path] = not self.is_protected(path)
        return result

    def get_protected_paths_info(self) -> dict:
        """
        Get information about protected paths for display/debugging.

        Returns:
            Dict with whitelist statistics and samples
        """
        whitelist = self.whitelist

        return {
            'total_protected_paths': len(whitelist.protected_paths),
            'total_protected_patterns': len(whitelist.protected_patterns),
            'version': whitelist.version,
            'last_updated': whitelist.last_updated.isoformat() if whitelist.last_updated else None,
            'sample_protected_paths': whitelist.protected_paths[:5],
            'sample_protected_patterns': whitelist.protected_patterns[:5]
        }


# Global instance for easy import
whitelist_service = WhitelistService()