"""
Main Application Window

The main GUI window for the Windows C Drive Cleaner application.
Provides the primary user interface for scanning and cleaning operations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional
from services.scanner_service import scanner_service
from services.cleaner_service import cleaner_service
from models.scan_report import ScanReport
from models.cleaning_operation import CleaningOperation
from ui.scan_view import ScanView
from ui.cleaning_view import CleaningView


class MainWindow:
    """
    Main application window for the C Drive Cleaner.

    This window provides:
    - Scan button to initiate C drive scanning
    - Progress display during scanning
    - Results display after scanning
    - Menu bar with additional options
    """

    def __init__(self, root: tk.Tk):
        """
        Initialize the main window.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Windows C 盘智能清理工具")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        # Current scan report
        self.current_report: Optional[ScanReport] = None

        # UI components
        self.scan_button: Optional[ttk.Button] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.status_label: Optional[ttk.Label] = None
        self.scan_view: Optional[ScanView] = None
        self.cleaning_view: Optional[CleaningView] = None

        # Current cleaning operation
        self.current_cleaning_operation: Optional[CleaningOperation] = None

        # Threading
        self.scan_thread: Optional[threading.Thread] = None
        self.cleaning_thread: Optional[threading.Thread] = None
        self.cancellation_event: Optional[threading.Event] = None

        self._setup_ui()
        self._setup_menu()

    def _setup_ui(self):
        """Set up the main user interface."""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="Windows C 盘智能清理工具",
                               font=("Microsoft YaHei", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20))

        # Scan control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(1, weight=1)

        # Scan button
        self.scan_button = ttk.Button(control_frame, text="开始扫描",
                                     command=self._start_scan, width=15)
        self.scan_button.grid(row=0, column=0, padx=(0, 10))

        # Cancel button (initially hidden)
        self.cancel_button = ttk.Button(control_frame, text="取消扫描",
                                       command=self._cancel_scan, state="disabled")
        self.cancel_button.grid(row=0, column=1, padx=(0, 10))

        # Progress bar
        self.progress_bar = ttk.Progressbar(control_frame, mode='determinate',
                                           maximum=100, length=300)
        self.progress_bar.grid(row=0, column=2, padx=(0, 10))

        # Status label
        self.status_label = ttk.Label(control_frame, text="就绪")
        self.status_label.grid(row=0, column=3)

        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scan tab
        scan_frame = ttk.Frame(self.notebook)
        self.notebook.add(scan_frame, text="扫描结果")

        # Scan results view
        self.scan_view = ScanView(scan_frame, on_cleaning_callback=self._start_cleaning_from_selection)
        self.scan_view.pack(fill=tk.BOTH, expand=True)

        # Cleaning tab
        cleaning_frame = ttk.Frame(self.notebook)
        self.notebook.add(cleaning_frame, text="清理结果")

        # Cleaning view
        self.cleaning_view = CleaningView(cleaning_frame)
        self.cleaning_view.pack(fill=tk.BOTH, expand=True)

    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=self.root.quit)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="查看", menu=view_menu)
        view_menu.add_command(label="刷新", command=self._refresh_view)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)

    def _start_scan(self):
        """Start the scanning process."""
        # Disable scan button, enable cancel button
        self.scan_button.config(state="disabled")
        self.cancel_button.config(state="normal")

        # Reset progress
        self.progress_bar['value'] = 0
        self.status_label.config(text="正在扫描...")

        # Clear previous results
        if self.scan_view:
            self.scan_view.clear_results()

        # Create cancellation event
        self.cancellation_event = threading.Event()

        # Start scan in background thread
        self.scan_thread = threading.Thread(target=self._perform_scan)
        self.scan_thread.daemon = True
        self.scan_thread.start()

    def _cancel_scan(self):
        """Cancel the current scan."""
        if self.cancellation_event:
            self.cancellation_event.set()
            self.status_label.config(text="正在取消...")
            self.cancel_button.config(state="disabled")

    def _perform_scan(self):
        """Perform the actual scanning in a background thread."""
        try:
            # Perform scan
            report = scanner_service.scan_all_modules(
                cancellation_token=self.cancellation_event,
                progress_callback=self._scan_progress_callback
            )

            # Update UI on main thread
            self.root.after(0, lambda: self._scan_completed(report))

        except Exception as e:
            # Update UI on main thread
            self.root.after(0, lambda: self._scan_failed(str(e)))

    def _scan_progress_callback(self, module_name: str, completed: int, total: int, result):
        """Callback for scan progress updates."""
        def update_ui():
            percentage = (completed / total) * 100
            self.progress_bar['value'] = percentage
            self.status_label.config(text=f"扫描中: {module_name} ({completed}/{total})")

        self.root.after(0, update_ui)

    def _scan_completed(self, report: ScanReport):
        """Handle scan completion."""
        self.current_report = report

        # Update UI
        self.scan_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.progress_bar['value'] = 100

        if report.status == "completed":
            self.status_label.config(text=f"扫描完成 - 找到 {report.get_total_files_count()} 个文件")
            # Display results
            if self.scan_view:
                self.scan_view.display_scan_results(report)

            # Switch to scan tab
            if self.notebook:
                self.notebook.select(0)  # Scan tab

        elif report.status == "cancelled":
            self.status_label.config(text="扫描已取消")
        else:
            self.status_label.config(text="扫描失败")

    def _scan_failed(self, error_msg: str):
        """Handle scan failure."""
        self.scan_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.progress_bar['value'] = 0
        self.status_label.config(text="扫描失败")

        messagebox.showerror("扫描错误", f"扫描过程中发生错误:\n{error_msg}")

    def _refresh_view(self):
        """Refresh the current view."""
        if self.current_report and self.scan_view:
            self.scan_view.display_scan_results(self.current_report)

    def _show_about(self):
        """Show about dialog."""
        try:
            from utils.system_info import system_info, WindowsVersion
            
            version_info = system_info.get_version_info()
            version_name = version_info['version_string']
            build_number = version_info['build_number']
            is_64bit = version_info['is_64bit']
            
            about_text = f"""Windows C 盘智能清理工具

版本: 2.0.0 (多版本支持版)
作者: AI 辅助开发
当前系统: {version_name} ({'64位' if is_64bit else '32位'})
构建号: {build_number}

支持的 Windows 版本:
• Windows 7 - 基础功能支持
• Windows 8 / 8.1 - 增强功能支持  
• Windows 10 / 11 - 完整功能支持

主要特性:
• 智能识别系统版本，提供最佳清理策略
• 安全清理系统垃圾文件
• 支持浏览器缓存清理
• 优雅的休眠文件清理（根据系统版本调整）
• Windows 更新残留清理
• 大文件扫描和清理
• 版本特定的保护机制

一款安全、透明、可控的 C 盘清理工具，
支持模块化扫描和选择性清理。"""
        except Exception:
            # Fallback if system detection fails
            about_text = """Windows C 盘智能清理工具

版本: 2.0.0 (多版本支持版)
作者: AI 辅助开发

支持的 Windows 版本:
• Windows 7 - 基础功能支持
• Windows 8 / 8.1 - 增强功能支持  
• Windows 10 / 11 - 完整功能支持

主要特性:
• 智能识别系统版本，提供最佳清理策略
• 安全清理系统垃圾文件
• 支持浏览器缓存清理
• 优雅的休眠文件清理
• Windows 更新残留清理
• 大文件扫描和清理

一款安全、透明、可控的 C 盘清理工具，
支持模块化扫描和选择性清理。"""

        messagebox.showinfo("关于", about_text)

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()

    def _start_cleaning_from_selection(self, selected_files):
        """Start cleaning process from selected files in scan view."""
        if not selected_files or not self.current_report:
            return

        # Check for hibernation files and require special confirmation
        hibernation_files = [f for f in selected_files if f.module == "休眠文件"]
        if hibernation_files:
            if not self._confirm_hibernation_deletion():
                return

        # Create cleaning operation
        operation = CleaningOperation()
        for file_info in selected_files:
            operation.add_selected_file(file_info)

        # Predict space
        predicted_space = cleaner_service.predict_space(selected_files)
        operation.predicted_space_bytes = predicted_space

        # Create cancellation token for cleaning
        self.cancellation_event = threading.Event()

        # Set up cleaning view
        if self.cleaning_view:
            self.cleaning_view.cancellation_token = self.cancellation_event
            self.cleaning_view.start_cleaning(operation)

        # Switch to cleaning tab
        if self.notebook:
            self.notebook.select(1)  # Cleaning tab

        # Start cleaning in background thread
        self.current_cleaning_operation = operation
        self.cleaning_thread = threading.Thread(target=self._perform_cleaning)
        self.cleaning_thread.daemon = True
        self.cleaning_thread.start()

    def _perform_cleaning(self):
        """Perform the actual cleaning in a background thread."""
        if not self.current_cleaning_operation:
            return

        operation = self.current_cleaning_operation

        try:
            # Execute cleaning
            result_operation = cleaner_service.clean_files(
                operation,
                progress_callback=self._cleaning_progress_callback,
                cancellation_token=self.cancellation_event
            )

            # Update UI on main thread
            self.root.after(0, lambda: self._cleaning_completed(result_operation))

        except Exception as e:
            # Update UI on main thread
            self.root.after(0, lambda: self._cleaning_failed(str(e)))

    def _cleaning_progress_callback(self, progress_percentage: float, current_module: str, 
                                   processed_files: int, total_files: int):
        """Callback for cleaning progress updates."""
        def update_ui():
            if self.cleaning_view and self.current_cleaning_operation:
                # Update status message
                status_msg = f"正在清理 {current_module}: {processed_files}/{total_files}"
                
                self.cleaning_view.update_progress(progress_percentage, current_module, status_msg)

        self.root.after(0, update_ui)

    def _cleaning_completed(self, operation: CleaningOperation):
        """Handle cleaning completion."""
        self.current_cleaning_operation = operation

        # Update cleaning view
        if self.cleaning_view:
            self.cleaning_view.show_cleaning_results(operation)

        # Show completion message
        successful = len(operation.selected_files) - len(operation.failed_files)
        failed = len(operation.failed_files)

        from utils.size_utils import format_bytes
        freed_space = format_bytes(operation.actual_space_freed_bytes)

        if failed == 0:
            message = f"清理完成！成功删除 {successful} 个文件，释放 {freed_space} 空间。"
        else:
            message = f"清理完成！成功删除 {successful} 个文件，{failed} 个文件删除失败，释放 {freed_space} 空间。"

        messagebox.showinfo("清理完成", message)

    def _cleaning_failed(self, error_msg: str):
        """Handle cleaning failure."""
        messagebox.showerror("清理失败", f"清理过程中发生错误:\n{error_msg}")

        if self.cleaning_view:
            self.cleaning_view.update_progress(0, message="清理失败")

    def _cancel_cleaning(self):
        """Cancel the current cleaning operation."""
        if self.cancellation_event:
            self.cancellation_event.set()

        if self.cleaning_view:
            self.cleaning_view.status_label.config(text="清理已取消")

    def _confirm_hibernation_deletion(self) -> bool:
        """Show confirmation dialog for hibernation file deletion."""
        from modules.hibernation import HibernationScanner

        try:
            hibernation_scanner = HibernationScanner()
            hibernation_info = hibernation_scanner.get_hibernation_status()

            if not hibernation_info.exists:
                return True  # File doesn't exist, no need to confirm

            size_mb = hibernation_info.file_size_bytes / (1024 * 1024)

            message = f"""⚠️ 您选择了删除休眠文件 (hiberfil.sys)

文件大小: {size_mb:.1f} MB
当前休眠状态: {'已启用' if hibernation_info.hibernation_enabled else '已禁用'}

{hibernation_info.impact_description}

您确认要继续删除休眠文件吗？

注意: 此操作需要管理员权限。"""

            # Show confirmation dialog
            result = messagebox.askyesno(
                "确认删除休眠文件",
                message,
                icon="warning"
            )

            return result

        except Exception as e:
            # If we can't get hibernation info, show generic warning
            message = """⚠️ 您选择了删除休眠文件 (hiberfil.sys)

休眠文件用于 Windows 的休眠/睡眠功能。删除此文件将：
• 禁用系统的休眠功能
• 可能影响快速启动
• 需要管理员权限

您确认要继续吗？"""

            result = messagebox.askyesno(
                "确认删除休眠文件",
                message,
                icon="warning"
            )

            return result

    def cleanup(self):
        """Clean up resources before exit."""
        if self.cancellation_event:
            self.cancellation_event.set()
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=1.0)
        if self.cleaning_thread and self.cleaning_thread.is_alive():
            self.cleaning_thread.join(timeout=1.0)