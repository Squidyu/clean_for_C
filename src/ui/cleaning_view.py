"""
Cleaning View

Displays cleaning progress and results.
Shows selected files, predicted space savings, and real-time cleaning progress.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Callable
from models.cleaning_operation import CleaningOperation
from models.file_info import FileInfo
from utils.size_utils import format_bytes


class CleaningView(ttk.Frame):
    """
    View for displaying cleaning operations.

    Features:
    - Selected files list with checkboxes
    - Predicted space calculation
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
        self.selected_files: List[FileInfo] = []

        # UI components
        self.files_tree: Optional[ttk.Treeview] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.status_label: Optional[ttk.Label] = None
        self.results_text: Optional[tk.Text] = None

        # Callbacks
        self.on_selection_changed: Optional[Callable] = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Selection section
        selection_frame = ttk.LabelFrame(main_frame, text="选择要清理的文件", padding=10)
        selection_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Files tree
        tree_frame = ttk.Frame(selection_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("size", "module", "selected")
        self.files_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)

        self.files_tree.heading("#0", text="文件名")
        self.files_tree.heading("size", text="大小")
        self.files_tree.heading("module", text="模块")
        self.files_tree.heading("selected", text="选择")

        self.files_tree.column("#0", width=300, minwidth=200)
        self.files_tree.column("size", width=100, anchor="e")
        self.files_tree.column("module", width=120)
        self.files_tree.column("selected", width=80, anchor="center")

        # Scrollbar for tree
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=tree_scrollbar.set)

        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Selection controls
        controls_frame = ttk.Frame(selection_frame)
        controls_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(controls_frame, text="全选", command=self._select_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="取消全选", command=self._select_none).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="反选", command=self._invert_selection).pack(side=tk.LEFT)

        # Summary label
        self.summary_label = ttk.Label(selection_frame, text="未选择文件")
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

        # Bind events
        self.files_tree.bind("<Button-1>", self._on_tree_click)

    def set_files_to_clean(self, files: List[FileInfo]):
        """
        Set the list of files available for cleaning.

        Args:
            files: List of files that can be cleaned
        """
        # Clear existing items
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        self.selected_files = []
        
        # Create mapping from tree item to file object
        self._file_mapping = {}  # Map item_id to FileInfo

        # Add files to tree
        for file_info in files:
            # Get display name (filename only)
            display_name = file_info.path.split("\\")[-1]
            if file_info.is_directory:
                display_name += "/"

            # Add to tree
            item_id = self.files_tree.insert("", "end",
                                           text=display_name,
                                           values=(format_bytes(file_info.size),
                                                  file_info.module,
                                                  "☐"))

            # Store file info reference in mapping
            self._file_mapping[item_id] = file_info
            self.files_tree.item(item_id, tags=(f"file_{item_id}",))

        self._update_summary()

    def get_selected_files(self) -> List[FileInfo]:
        """
        Get currently selected files for cleaning.

        Returns:
            List of selected FileInfo objects
        """
        return self.selected_files.copy()

    def get_predicted_space(self) -> int:
        """
        Get predicted space to be freed from selected files.

        Returns:
            Total size in bytes
        """
        return sum(f.size for f in self.selected_files)

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

        # Format results
        results = f"""清理完成！

总文件数: {len(operation.selected_files)}
成功删除: {len(operation.selected_files) - len(operation.failed_files)}
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

    def _on_tree_click(self, event):
        """Handle tree view click events."""
        region = self.files_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.files_tree.identify_column(event.x)
            item = self.files_tree.identify_row(event.y)
            if not item:
                return
            
            # Check if clicked on "selected" column (#4) or on the text column (#0)
            if column == "#4":  # Selected column
                self._toggle_selection(item)
            elif column == "#0":  # Text column - toggle selection on file name click
                # Get item bounds for better click detection
                bbox = self.files_tree.bbox(item, column)
                if bbox:
                    # Toggle selection when clicking on file names for better UX
                    self._toggle_selection(item)

    def _toggle_selection(self, item_id: str):
        """Toggle selection state of an item."""
        current_values = self.files_tree.item(item_id, "values")
        current_selected = current_values[2] if len(current_values) > 2 else "☐"

        if current_selected == "☐":
            new_selected = "☑"
            # Add to selected files
            self._add_to_selection(item_id)
        else:
            new_selected = "☐"
            # Remove from selected files
            self._remove_from_selection(item_id)

        # Update tree
        new_values = list(current_values)
        new_values[2] = new_selected
        self.files_tree.item(item_id, values=new_values)

        self._update_summary()

    def _add_to_selection(self, item_id: str):
        """Add file to selection list."""
        if not hasattr(self, '_file_mapping'):
            return
        
        file_info = self._file_mapping.get(item_id)
        if file_info and file_info not in self.selected_files:
            self.selected_files.append(file_info)

    def _remove_from_selection(self, item_id: str):
        """Remove file from selection list."""
        if not hasattr(self, '_file_mapping'):
            return
        
        file_info = self._file_mapping.get(item_id)
        if file_info and file_info in self.selected_files:
            self.selected_files.remove(file_info)

    def _select_all(self):
        """Select all files."""
        if not hasattr(self, '_file_mapping'):
            return
        
        self.selected_files = []
        
        for item in self.files_tree.get_children():
            values = list(self.files_tree.item(item, "values"))
            if len(values) > 2:
                values[2] = "☑"
                self.files_tree.item(item, values=values)
                
                # Add to selection list
                file_info = self._file_mapping.get(item)
                if file_info:
                    self.selected_files.append(file_info)
        
        self._update_summary()

    def _select_none(self):
        """Deselect all files."""
        for item in self.files_tree.get_children():
            values = list(self.files_tree.item(item, "values"))
            if len(values) > 2:
                values[2] = "☐"
                self.files_tree.item(item, values=values)

        self.selected_files = []
        self._update_summary()

    def _invert_selection(self):
        """Invert current selection."""
        for item in self.files_tree.get_children():
            self._toggle_selection(item)

    def _update_summary(self):
        """Update selection summary display."""
        if not self.selected_files:
            self.summary_label.config(text="未选择文件")
            return

        total_size = sum(f.size for f in self.selected_files)
        file_count = len(self.selected_files)

        summary = f"已选择 {file_count} 个文件，预计释放 {format_bytes(total_size)} 空间"

        self.summary_label.config(text=summary)

        # Notify callback if set
        if self.on_selection_changed:
            self.on_selection_changed()

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

    def set_selection_callback(self, callback: Callable):
        """
        Set callback for selection changes.

        Args:
            callback: Function to call when selection changes
        """
        self.on_selection_changed = callback
