"""
Cleaning View

Displays cleaning progress and results.
Shows deleted files, space savings, and real-time cleaning progress.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Callable
from models.cleaning_operation import CleaningOperation
from models.file_info import FileInfo
from utils.size_utils import format_bytes


class CleaningView(ttk.Frame):
    """
    View for displaying cleaning results.

    Features:
    - Deleted files list with details
    - Space calculation
    - Real-time cleaning progress
    - Results display after cleaning
    """

    def __init__(self, parent):
        """
        Initialize cleaning view.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Current operation
        self.current_operation: Optional[CleaningOperation] = None
        self.deleted_files: List[FileInfo] = []

        # UI components
        self.files_tree: Optional[ttk.Treeview] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.status_label: Optional[ttk.Label] = None
        self.results_text: Optional[tk.Text] = None



        self._setup_ui()
        
        # Schedule a delayed update to ensure headings are set after window is displayed
        self.after(100, self._ensure_headings)

    def _setup_ui(self):
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Deleted files section
        deleted_frame = ttk.LabelFrame(main_frame, text="已删除的文件", padding=10)
        deleted_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Files tree
        tree_frame = ttk.Frame(deleted_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("size", "module", "status")
        self.files_tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", height=10)

        # Configure columns first
        self.files_tree.column("#0", width=500, minwidth=300, anchor="w")
        self.files_tree.column("size", width=100, anchor="e")
        self.files_tree.column("module", width=120, anchor="w")
        self.files_tree.column("status", width=100, anchor="center")
        
        # Then set headings with explicit state update
        self.files_tree.heading("#0", text="文件路径")
        self.files_tree.heading("size", text="大小")
        self.files_tree.heading("module", text="模块")
        self.files_tree.heading("status", text="状态")
        
        # Force update
        self.files_tree.update_idletasks()

        # Columns already configured above

        # Scrollbars for tree
        tree_scrollbar_v = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        tree_scrollbar_h = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=tree_scrollbar_v.set, xscrollcommand=tree_scrollbar_h.set)

        # Tree with scrollbars
        self.files_tree.grid(row=0, column=0, sticky="nsew")
        tree_scrollbar_v.grid(row=0, column=1, sticky="ns")
        tree_scrollbar_h.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Summary label
        self.summary_label = ttk.Label(deleted_frame, text="暂无删除的文件")
        self.summary_label.pack(anchor="w", pady=(10, 0))

        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="清理进度", padding=10)
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        # Progress controls
        controls_frame = ttk.Frame(progress_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 5))

        self.status_label = ttk.Label(controls_frame, text="准备就绪")
        self.status_label.pack(side=tk.LEFT, anchor="w")

        self.cancel_button = ttk.Button(controls_frame, text="取消清理",
                                       command=self._cancel_cleaning, state="disabled")
        self.cancel_button.pack(side=tk.RIGHT)

        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="清理结果", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)

        results_scroll = ttk.Scrollbar(results_frame)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_text = tk.Text(results_frame, height=8, wrap=tk.WORD,
                                   yscrollcommand=results_scroll.set)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        results_scroll.config(command=self.results_text.yview)
        
        # Ensure headings are set after all UI setup
        self.after(50, self._force_set_headings)

    def _force_set_headings(self):
        """Forcefully set headings with different approach"""
        if self.files_tree:
            # Clear and reset headings completely
            self.files_tree.heading("#0", text="")  # Clear first
            self.files_tree.heading("size", text="")
            self.files_tree.heading("module", text="")
            self.files_tree.heading("status", text="")
            
            # Force update
            self.files_tree.update_idletasks()
            
            # Set again with correct text
            self.files_tree.heading("#0", text="文件路径")
            self.files_tree.heading("size", text="大小")
            self.files_tree.heading("module", text="模块")
            self.files_tree.heading("status", text="状态")
            
            # Final update
            self.files_tree.update_idletasks()
    
    def _ensure_headings(self):
        """Ensure headings are correctly set after window is displayed"""
        self._force_set_headings()



    def set_deleted_files(self, files: List[FileInfo]):
        """
        Set the list of deleted files to display.

        Args:
            files: List of deleted files
        """
        # Clear existing items
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        self.deleted_files = files

        # Create mapping from tree item to file object
        self._file_mapping = {}  # Map item_id to FileInfo

        # Add files to tree
        for file_info in files:
            # Use full path as display name
            display_name = file_info.path
            if file_info.is_directory:
                if not display_name.endswith("\\"):
                    display_name += "\\"

            # Add to tree
            item_id = self.files_tree.insert("", "end",
                                           text=display_name,
                                           values=(format_bytes(file_info.size),
                                                  file_info.module,
                                                  "已删除"))

            # Store file info reference in mapping
            self._file_mapping[item_id] = file_info
            self.files_tree.item(item_id, tags=(f"file_{item_id}",))

        self._update_summary()

    def get_freed_space(self) -> int:
        """
        Get total space freed from deleted files.

        Returns:
            Total size in bytes
        """
        return sum(f.size for f in self.deleted_files)

    def start_cleaning(self, operation: CleaningOperation):
        """
        Start displaying cleaning progress.

        Args:
            operation: Cleaning operation to track
        """
        self.current_operation = operation
        self.progress_bar['value'] = 0
        self.status_label.config(text="开始清理...")
        self.cancel_button.config(state="normal")
        self.results_text.delete(1.0, tk.END)

    def update_progress(self, percentage: float, current_module: str = "", message: str = ""):
        """
        Update cleaning progress display.

        Args:
            percentage: Progress percentage (0-100)
            current_module: Current module being cleaned
            message: Status message
        """
        self.progress_bar['value'] = percentage

        status_parts = []
        if message:
            status_parts.append(message)
        if current_module:
            status_parts.append(f"当前模块: {current_module}")
        status_parts.append(f"{percentage:.1f}%")

        self.status_label.config(text=" | ".join(status_parts))

    def show_cleaning_results(self, operation: CleaningOperation):
        """
        Display cleaning results.

        Args:
            operation: Completed cleaning operation
        """
        self.current_operation = operation

        # Update progress to 100%
        self.progress_bar['value'] = 100
        self.status_label.config(text="清理完成")
        self.cancel_button.config(state="disabled")

        # Set deleted files in the tree view
        successfully_deleted_files = [f for f in operation.selected_files 
                                   if f not in operation.failed_files]
        self.set_deleted_files(successfully_deleted_files)

        # Format results
        results = f"""清理完成！

总文件数: {len(operation.selected_files)}
成功删除: {len(successfully_deleted_files)}
删除失败: {len(operation.failed_files)}

预测释放空间: {format_bytes(operation.predicted_space_bytes)}
实际释放空间: {format_bytes(operation.actual_space_freed_bytes)}

清理用时: {operation.duration_seconds:.1f} 秒

"""

        if operation.hiberfil_sys_deleted:
            results += "\n已删除休眠文件 (hiberfil.sys)\n"

        if operation.failed_files:
            results += "\n删除失败的文件:\n"
            for failed_file in operation.failed_files[:10]:  # Show first 10
                results += f"• {failed_file.path.split(chr(92))[-1]}\n"
            if len(operation.failed_files) > 10:
                results += f"... 还有 {len(operation.failed_files) - 10} 个文件\n"

        self.results_text.insert(tk.END, results)
        self.results_text.see(tk.END)



    def _update_summary(self):
        """Update the summary label."""
        if self.deleted_files:
            total_size = sum(f.size for f in self.deleted_files)
            count = len(self.deleted_files)
            self.summary_label.config(
                text=f"已删除 {count} 个文件，释放空间：{format_bytes(total_size)}"
            )
        else:
            self.summary_label.config(text="暂无删除的文件")

    def _cancel_cleaning(self):
        """Cancel the current cleaning operation."""
        if not self.current_operation:
            return

        # Set cancellation flag
        if hasattr(self, 'cancellation_token') and self.cancellation_token:
            self.cancellation_token.set()

        # Update UI
        self.cancel_button.config(state="disabled")
        self.status_label.config(text="正在取消清理...")

        # Emit signal to parent window
        if hasattr(self, 'master') and hasattr(self.master, '_cancel_cleaning'):
            self.master._cancel_cleaning()


