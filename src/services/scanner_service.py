"""
Scanner Service

Coordinates scanning operations across all cleaning modules.
Provides parallel scanning capabilities and progress reporting.
"""

import threading
import concurrent.futures
from typing import List, Optional, Callable, Dict
from models.scan_report import ScanReport
from models.scan_result import ScanResult
from modules.system_junk import SystemJunkScanner
from modules.windows_updates import WindowsUpdatesScanner
from modules.browser_cache import BrowserCacheScanner
from modules.app_cache import AppCacheScanner
from modules.recycle_bin import RecycleBinScanner
from modules.large_files import LargeFilesScanner
from modules.app_remnants import AppRemnantsScanner
from modules.hibernation import HibernationScanner
from modules.windows_defender_cache import WindowsDefenderCacheScanner
from modules.windows_store_cache import WindowsStoreCacheScanner
from modules.onedrive_cache import OneDriveCacheScanner
from modules.teams_cache import TeamsCacheScanner
from modules.windows_search_index import WindowsSearchIndexScanner
from modules.thumbnail_cache import ThumbnailCacheScanner
from modules.font_cache import FontCacheScanner
from modules.directx_shader_cache import DirectXShaderCacheScanner


class ScannerService:
    """
    Service for coordinating scanning operations across all modules.

    This service manages the parallel execution of all 9 cleaning module scanners,
    aggregates results, and provides progress reporting.
    """

    def __init__(self, max_workers: int = 8):
        """
        Initialize scanner service.

        Args:
            max_workers: Maximum number of parallel scanner threads
        """
        self.max_workers = max_workers
        self._scanners = self._create_scanners()

    def _create_scanners(self) -> Dict[str, 'BaseScanner']:
        """
        Create instances of all scanner modules.

        Returns:
            Dict mapping module names to scanner instances
        """
        return {
            "系统垃圾": SystemJunkScanner(),
            "Windows 更新残留": WindowsUpdatesScanner(),
            "浏览器缓存": BrowserCacheScanner(),
            "第三方应用缓存": AppCacheScanner(),
            "回收站": RecycleBinScanner(),
            "大文件扫描": LargeFilesScanner(),
            "应用残留": AppRemnantsScanner(),
            "休眠文件": HibernationScanner(),
            "Windows Defender 缓存": WindowsDefenderCacheScanner(),
            "Windows Store 缓存": WindowsStoreCacheScanner(),
            "OneDrive 缓存": OneDriveCacheScanner(),
            "Microsoft Teams 缓存": TeamsCacheScanner(),
            "Windows Search 索引": WindowsSearchIndexScanner(),
            "缩略图缓存": ThumbnailCacheScanner(),
            "字体缓存": FontCacheScanner(),
            "DirectX Shader Cache": DirectXShaderCacheScanner()
        }

    def scan_all_modules(self, cancellation_token: Optional[threading.Event] = None,
                        progress_callback: Optional[Callable] = None) -> ScanReport:
        """
        Scan all cleaning modules in parallel.

        Args:
            cancellation_token: Event to signal cancellation
            progress_callback: Callback function(current_module, total_modules, module_result)

        Returns:
            Complete ScanReport with results from all modules
        """
        if cancellation_token is None:
            cancellation_token = threading.Event()

        report = ScanReport()
        report.status = "in_progress"

        total_modules = len(self._scanners)
        completed_count = 0

        try:
            # Use ThreadPoolExecutor for parallel scanning
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all scan tasks
                future_to_module = {
                    executor.submit(self._scan_single_module_safe, module_name, scanner, cancellation_token):
                    module_name
                    for module_name, scanner in self._scanners.items()
                }

                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_module):
                    if cancellation_token.is_set():
                        break

                    module_name = future_to_module[future]
                    completed_count += 1

                    try:
                        scan_result = future.result()
                        if scan_result:
                            report.add_module_result(scan_result)

                        # Progress callback
                        if progress_callback:
                            progress_callback(module_name, completed_count, total_modules, scan_result)

                    except Exception as e:
                        # Log error but continue with other modules
                        print(f"Error scanning module {module_name}: {e}")
                        continue

            # Update report status
            if cancellation_token.is_set():
                report.status = "cancelled"
                report.cancellation_reason = "User cancelled"
            else:
                report.status = "completed"

        except Exception as e:
            report.status = "failed"
            print(f"Scan failed: {e}")

        return report

    def _scan_single_module_safe(self, module_name: str, scanner: 'BaseScanner',
                                cancellation_token: threading.Event) -> Optional[ScanResult]:
        """
        Safely scan a single module with error handling.

        Args:
            module_name: Name of the module
            scanner: Scanner instance
            cancellation_token: Cancellation event

        Returns:
            ScanResult or None if scan failed
        """
        try:
            return scanner.scan(cancellation_token)
        except Exception as e:
            print(f"Module {module_name} scan failed: {e}")
            # Return empty result for failed module
            from models.scan_result import ScanResult
            return ScanResult(module_name=module_name, risk_level="low")  # Default risk level

    def scan_single_module(self, module_name: str,
                          cancellation_token: Optional[threading.Event] = None) -> Optional[ScanResult]:
        """
        Scan a single module.

        Args:
            module_name: Name of the module to scan
            cancellation_token: Event to signal cancellation

        Returns:
            ScanResult for the module, or None if module not found

        Raises:
            ValueError: If module name is invalid
        """
        if module_name not in self._scanners:
            raise ValueError(f"Unknown module: {module_name}")

        if cancellation_token is None:
            cancellation_token = threading.Event()

        scanner = self._scanners[module_name]
        return self._scan_single_module_safe(module_name, scanner, cancellation_token)

    def get_available_modules(self) -> List[str]:
        """
        Get list of available module names.

        Returns:
            List of module names
        """
        return list(self._scanners.keys())

    def get_module_info(self, module_name: str) -> Optional[Dict]:
        """
        Get information about a specific module.

        Args:
            module_name: Name of the module

        Returns:
            Dict with module info, or None if not found
        """
        if module_name not in self._scanners:
            return None

        scanner = self._scanners[module_name]

        return {
            'name': module_name,
            'risk_level': scanner.get_risk_level(),
            'description': self._get_module_description(module_name)
        }

    def _get_module_description(self, module_name: str) -> str:
        """
        Get human-readable description for a module.

        Args:
            module_name: Name of the module

        Returns:
            Description string
        """
        descriptions = {
            "系统垃圾": "Windows 临时文件、预读取文件等系统垃圾",
            "Windows 更新残留": "Windows 更新缓存、旧版本备份文件",
            "浏览器缓存": "Edge、Chrome、Firefox 等浏览器缓存文件",
            "第三方应用缓存": "VSCode、JetBrains、微信等应用的缓存文件",
            "回收站": "已删除但仍可恢复的文件",
            "大文件扫描": "超过设定大小阈值的大文件",
            "应用残留": "卸载后残留的目录和文件",
            "休眠文件": "Windows 休眠文件 (hiberfil.sys)",
            "Windows Defender 缓存": "Windows Defender 扫描缓存和定义更新缓存 (Windows 10/11)",
            "Windows Store 缓存": "Windows Store (UWP) 应用缓存文件",
            "OneDrive 缓存": "Microsoft OneDrive 同步缓存和日志文件",
            "Microsoft Teams 缓存": "Microsoft Teams 应用缓存、媒体缓存和日志",
            "Windows Search 索引": "Windows Search 索引临时文件和缓存 (不包括活动数据库)",
            "缩略图缓存": "Windows 缩略图缓存数据库 (thumbcache_*.db, thumbs.db)",
            "字体缓存": "Windows 字体预览缓存和临时字体文件",
            "DirectX Shader Cache": "DirectX 着色器缓存 (游戏和应用渲染缓存)"
        }

        return descriptions.get(module_name, f"{module_name} 模块")

    def estimate_scan_time(self) -> float:
        """
        Estimate total scan time for all modules.

        Returns:
            Estimated time in seconds
        """
        # Rough estimate: 2-3 seconds per module
        return len(self._scanners) * 2.5

    def get_scan_progress_info(self, report: ScanReport) -> Dict:
        """
        Get detailed progress information for a scan.

        Args:
            report: Current scan report

        Returns:
            Dict with progress statistics
        """
        total_modules = len(self._scanners)
        completed_modules = len(report.modules)

        module_details = []
        for module in report.modules:
            module_details.append({
                'name': module.module_name,
                'files_found': module.file_count,
                'size_found': module.total_size,
                'risk_level': module.risk_level
            })

        return {
            'total_modules': total_modules,
            'completed_modules': completed_modules,
            'completion_percentage': (completed_modules / total_modules) * 100 if total_modules > 0 else 0,
            'total_files_found': report.get_total_files_count(),
            'total_size_found': report.total_scannable_size,
            'module_details': module_details,
            'status': report.status
        }


# Global instance for easy import
scanner_service = ScannerService()