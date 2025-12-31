"""
DirectX Shader Cache Scanner

Scans for DirectX shader cache files.
These are compiled shader files cached by games and applications for faster rendering.
"""

import os
import threading
from modules.base_scanner import BaseScanner
from models.scan_result import ScanResult
from models.file_info import FileInfo
from utils.file_utils import scan_directory_files
from utils.path_utils import expand_environment_variables, validate_c_drive_path
from utils.system_info import system_info, WindowsVersion


class DirectXShaderCacheScanner(BaseScanner):
    """
    Scanner for DirectX shader cache files.
    
    Scans for:
    - DirectX shader cache
    - AMD shader cache
    - NVIDIA shader cache
    - Intel shader cache
    """

    def get_module_name(self) -> str:
        """Get module name."""
        return "DirectX Shader Cache"

    def get_risk_level(self) -> str:
        """Get risk level - low risk for cache files."""
        return "low"

    def scan(self, cancellation_token: threading.Event) -> ScanResult:
        """
        Scan for DirectX shader cache files.
        
        Args:
            cancellation_token: Event to cancel scanning
            
        Returns:
            ScanResult with found cache files
        """
        result = ScanResult(
            module_name=self.get_module_name(),
            risk_level=self.get_risk_level()
        )

        try:
            # DirectX shader cache locations (different GPU vendors)
            cache_paths = []
            
            local_appdata = expand_environment_variables("%LOCALAPPDATA%")
            if local_appdata:
                # DirectX shader cache
                d3d_cache = os.path.join(local_appdata, "D3DSCache")
                if os.path.exists(d3d_cache):
                    cache_paths.append(d3d_cache)
                
                # AMD shader cache
                amd_cache = os.path.join(local_appdata, "AMD", "DxCache")
                if os.path.exists(amd_cache):
                    cache_paths.append(amd_cache)
                
                # NVIDIA shader cache
                nvidia_cache = os.path.join(local_appdata, "NVIDIA Corporation", "NV_Cache")
                if os.path.exists(nvidia_cache):
                    cache_paths.append(nvidia_cache)
                
                # Intel shader cache
                intel_cache = os.path.join(local_appdata, "Intel", "ShaderCache")
                if os.path.exists(intel_cache):
                    cache_paths.append(intel_cache)

            # Scan each location
            for cache_path in cache_paths:
                if cancellation_token.is_set():
                    break

                if not os.path.exists(cache_path):
                    continue

                try:
                    validate_c_drive_path(cache_path)
                    
                    # Scan for shader cache files
                    files = scan_directory_files(cache_path, "*", recursive=True)
                    
                    for file_path in files:
                        if cancellation_token.is_set():
                            break

                        # Look for shader cache files
                        file_lower = os.path.basename(file_path).lower()
                        if any(keyword in file_lower for keyword in ['.cache', '.bin', 'shader', 'dxcache']):
                            file_info = self.create_file_info(file_path)
                            if file_info and not self.should_skip_file(file_info):
                                file_info.module = self.get_module_name()
                                result.add_file(file_info)

                except Exception as e:
                    # Skip problematic directories but continue scanning
                    continue

        except Exception as e:
            result.error_message = f"扫描 DirectX Shader Cache 时出错: {e}"

        return result

