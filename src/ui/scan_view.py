"""
Scan View

Displays scan results in a tree-like structure with expandable modules.
Shows file details, sizes, and allows selection for cleaning.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from models.scan_report import ScanReport
from models.scan_result import ScanResult
from models.file_info import FileInfo
from utils.size_utils import format_bytes


class ScanView(ttk.Frame):
    """
    View for displaying scan results.

    Features:
    - Tree view of modules and files
    - Expandable/collapsible modules
    - File details (path, size, date)
    - Risk level indicators
    - Selection checkboxes for cleaning
    """

    def __init__(self, parent, on_cleaning_callback=None):
        """
        Initialize scan view.

        Args:
            parent: Parent widget
            on_cleaning_callback: Callback function when cleaning starts
        """
        super().__init__(parent)

        # Callback for cleaning
        self.on_cleaning_callback = on_cleaning_callback

        # Current scan report
        self.current_report: Optional[ScanReport] = None

        # UI components
        self.tree: Optional[ttk.Treeview] = None
        self.scrollbar: Optional[ttk.Scrollbar] = None
        self.summary_label: Optional[ttk.Label] = None
        self.selection_label: Optional[ttk.Label] = None
        self.clean_button: Optional[ttk.Button] = None

        # Selection tracking
        self.selected_files: List[FileInfo] = []
        self.selected_modules: List[str] = []

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Summary label
        self.summary_label = ttk.Label(self, text="尚未进行扫描")
        self.summary_label.pack(pady=(0, 5), anchor="w")

        # Selection summary label
        self.selection_label = ttk.Label(self, text="未选择任何文件")
        self.selection_label.pack(pady=(0, 10), anchor="w")

        # Control buttons frame
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # Select All button
        self.select_all_btn = ttk.Button(button_frame, text="全选", command=self._select_all)
        self.select_all_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Select None button
        self.select_none_btn = ttk.Button(button_frame, text="取消选择", command=self._select_none)
        self.select_none_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Clean button (initially disabled)
        self.clean_button = ttk.Button(button_frame, text="开始清理",
                                     command=self._start_cleaning, state="disabled")
        self.clean_button.pack(side=tk.RIGHT)

        # Tree view frame
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Tree view
        columns = ("size", "date", "risk", "selected")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", height=20)

        # Configure columns
        self.tree.heading("#0", text="项目")
        self.tree.heading("size", text="大小")
        self.tree.heading("date", text="修改时间")
        self.tree.heading("risk", text="风险等级")
        self.tree.heading("selected", text="选择")

        # Set column widths
        self.tree.column("#0", width=400, minwidth=200)
        self.tree.column("size", width=100, anchor="e")
        self.tree.column("date", width=150)
        self.tree.column("risk", width=80, anchor="center")
        self.tree.column("selected", width=60, anchor="center")

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Pack tree and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Button-1>", self._on_tree_click)

    def display_scan_results(self, report: ScanReport):
        """
        Display scan results in the tree view.

        Args:
            report: ScanReport to display
        """
        # Clear results but preserve the report
        self._clear_tree_only()

        if not report or report.status != "completed":
            self.summary_label.config(text="扫描未完成或失败")
            self.current_report = None
            self.clean_button.config(state="disabled")  # 确保清理按钮被禁用
            return

        self.current_report = report

        # Update summary
        total_files = report.get_total_files_count()
        total_size = format_bytes(report.total_scannable_size)
        self.summary_label.config(text=f"扫描完成 - 找到 {total_files} 个文件，可清理 {total_size}")

        # Add modules to tree
        for module in report.modules:
            self._add_module_to_tree("", module)
        
        # 确保清理按钮的初始状态是正确的
        self._update_clean_button_state()

    def _add_module_to_tree(self, parent: str, module: ScanResult):
        """
        Add a module and its files to the tree.

        Args:
            parent: Parent tree node
            module: Module scan result
        """
        # Add module node
        module_text = f"{module.module_name} ({module.file_count} 个文件)"
        module_node = self.tree.insert(parent, "end", text=module_text,
                                      values=("", "", module.get_risk_display(), ""))

        # Set module node color based on risk
        self._set_risk_color(module_node, module.risk_level)

        # Add files under module
        for file_info in module.files:
            self._add_file_to_tree(module_node, file_info)
        
        # Expand module node to show files
        self.tree.item(module_node, open=True)

    def _add_file_to_tree(self, parent: str, file_info: FileInfo):
        """
        Add a file to the tree under its module.

        Args:
            parent: Parent module node
            file_info: File information
        """
        # File display name (just filename, full path in tooltip)
        display_name = file_info.path.split("\\")[-1]
        if file_info.is_directory:
            display_name += "/"

        # Default values
        size_display = format_bytes(file_info.size)
        date_display = file_info.get_last_modified_display()
        
        # Risk display for hibernation files
        if file_info.module == "休眠文件":
            risk_display = "中"
        elif file_info.is_protected:
            risk_display = "高"
        else:
            risk_display = ""

        # Special handling for hibernation files
        if file_info.module == "休眠文件":
            # Get hibernation info for detailed display
            try:
                from modules.hibernation import HibernationScanner
                hibernation_scanner = HibernationScanner()
                hibernation_info = hibernation_scanner.get_hibernation_status()

                if hibernation_info.exists:
                    size_display = format_bytes(hibernation_info.file_size_bytes)
                    date_display = "需要管理员权限"
                    # Add hibernation status to display name
                    status_text = " (休眠已启用)" if hibernation_info.hibernation_enabled else " (休眠已禁用)"
                    display_name += status_text
                else:
                    size_display = "文件不存在"
                    risk_display = "无风险"
                    date_display = "N/A"
            except Exception:
                # Keep default values
                pass

        # Add file node
        file_node = self.tree.insert(parent, "end", text=display_name,
                                    values=(size_display, date_display, risk_display, "☐"))

        # Set tooltip with full path
        self._add_tooltip(file_node, file_info.path)

        # Color based on protection status and store file path
        if file_info.is_protected:
            self.tree.item(file_node, tags=("protected",))
        else:
            self.tree.item(file_node, tags=("cleanable",))
            
        # Store file path reference for easier selection tracking
        current_tags = self.tree.item(file_node, "tags") or ()
        self.tree.item(file_node, tags=current_tags + (f"path:{file_info.path}",))

    def _set_risk_color(self, item_id: str, risk_level: str):
        """Set color for tree item based on risk level."""
        if risk_level == "high":
            self.tree.item(item_id, tags=("high_risk",))
        elif risk_level == "medium":
            self.tree.item(item_id, tags=("medium_risk",))
        else:
            self.tree.item(item_id, tags=("low_risk",))

        # Configure tag colors
        self.tree.tag_configure("high_risk", foreground="red")
        self.tree.tag_configure("medium_risk", foreground="orange")
        self.tree.tag_configure("low_risk", foreground="green")
        self.tree.tag_configure("protected", foreground="gray")
        self.tree.tag_configure("cleanable", foreground="black")

    def _add_tooltip(self, item_id: str, tooltip_text: str):
        """Add tooltip to tree item."""
        # Simple tooltip implementation
        def show_tooltip(event):
            # Could implement a proper tooltip widget here
            pass

        # For now, just store the tooltip text
        current_tags = self.tree.item(item_id, "tags") or ()
        self.tree.item(item_id, tags=current_tags + (f"tooltip:{tooltip_text}",))

    def _clear_tree_only(self):
        """Clear only the tree view, preserving data."""
        if self.tree:
            for item in self.tree.get_children():
                self.tree.delete(item)

        self.selected_files = []
        self.selected_modules = []
        self.selection_label.config(text="未选择任何文件")
        
        # 确保清理按钮被禁用
        if self.clean_button:
            self.clean_button.config(state="disabled")

    def clear_results(self):
        """Clear all scan results from the view."""
        self._clear_tree_only()
        self.current_report = None
        self.summary_label.config(text="尚未进行扫描")

    def get_selected_files(self) -> List[FileInfo]:
        """
        Get list of files selected for cleaning.

        Returns:
            List of selected FileInfo objects
        """
        return self.selected_files.copy()

    def get_selected_file_count(self) -> int:
        """Get count of selected files."""
        return len(self.selected_files)

    def get_selected_total_size(self) -> int:
        """Get total size of selected files."""
        return sum(f.size for f in self.selected_files)

    def _on_tree_select(self, event):
        """Handle tree selection event."""
        # Could implement file selection logic here
        pass

    def _on_tree_double_click(self, event):
        """Handle tree double-click event."""
        item = self.tree.identify_row(event.y)
        if item:
            # Toggle expansion
            if self.tree.item(item, "open"):
                self.tree.item(item, open=False)
            else:
                self.tree.item(item, open=True)

    def _on_tree_click(self, event):
        """Handle tree click event for selection."""
        region = self.tree.identify_region(event.x, event.y)
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        
        if region == "cell" and item:
            # Get item bounds for checkbox detection
            bbox = self.tree.bbox(item, column)
            if not bbox:
                return
            
            # Check if clicked on "selected" column (#4)
            if column == "#4":
                self._toggle_item_selection(item)
                return
            
            # Also allow clicking on the item text area for selection
            elif column == "#0":
                # Check if this is a file (has size info)
                values = self.tree.item(item, "values")
                if values and len(values) >= 4 and values[0]:  # Has size = file
                    # Toggle selection when clicking on file names
                    self._toggle_item_selection(item)
                elif values and not values[0]:  # No size = module header
                    # Toggle module selection
                    self._toggle_item_selection(item)

    def _toggle_item_selection(self, item_id: str):
        """Toggle selection state of an item."""
        if not self.current_report:
            return

        # Get item values
        values = self.tree.item(item_id, "values")
        if not values or len(values) < 4:
            return

        # Check if this is a file item (has file path in tree text)
        item_text = self.tree.item(item_id, "text")

        # If it's a module header (no size/date values), select all files in module
        if not values[0] or values[0] == "":  # Size column empty = module header
            self._toggle_module_selection(item_id, item_text)
        else:
            # It's a file item
            self._toggle_file_selection(item_id, item_text)

        # Update UI immediately
        self._update_selection_display()
        self._update_clean_button_state()

    def _toggle_module_selection(self, module_item_id: str, module_name: str):
        """Toggle selection of all files in a module."""
        # Extract clean module name (remove count info)
        clean_module_name = module_name.split(" (")[0]
        
        if clean_module_name in self.selected_modules:
            # Deselect module
            self.selected_modules.remove(clean_module_name)
            # Remove all files from this module
            self.selected_files = [f for f in self.selected_files if f.module != clean_module_name]
        else:
            # Select module
            self.selected_modules.append(clean_module_name)
            # Add all files from this module that aren't protected
            if self.current_report:
                for module_result in self.current_report.modules:
                    if module_result.module_name == clean_module_name:
                        for file_info in module_result.files:
                            if not file_info.is_protected and file_info not in self.selected_files:
                                self.selected_files.append(file_info)
                        break

        # Update tree display
        self._update_module_selection_display(module_item_id, clean_module_name in self.selected_modules)

    def _toggle_file_selection(self, file_item_id: str, file_display_name: str):
        """Toggle selection of a single file."""
        # Find the file in current report
        if not self.current_report:
            return

        # Get the full path from the item (stored in tags)
        item_tags = self.tree.item(file_item_id, "tags") or []
        file_path = None
        
        # Try both tooltip and path tags
        for tag in item_tags:
            if tag.startswith("tooltip:"):
                file_path = tag[8:]  # Remove "tooltip:" prefix
                break
            elif tag.startswith("path:"):
                file_path = tag[5:]  # Remove "path:" prefix
                break

        # Fallback: try to find by display name if path extraction fails
        if not file_path:
            display_name = self.tree.item(file_item_id, "text")
            # Remove trailing slash for directories and status text
            clean_name = display_name.rstrip("/").split(" (")[0]
            
            for module_result in self.current_report.modules:
                for file_info in module_result.files:
                    if file_info.path.split("\\")[-1] == clean_name:
                        file_path = file_info.path
                        break
                if file_path:
                    break

        if not file_path:
            print(f"Debug: Could not find file path for item {file_item_id}")
            return

        # Find the file in our data - handle path normalization
        target_file = None
        normalized_path = file_path.replace("\\\\", "\\")  # Normalize path
        
        for module_result in self.current_report.modules:
            for file_info in module_result.files:
                if file_info.path == normalized_path or file_info.path.replace("\\\\", "\\") == normalized_path:
                    target_file = file_info
                    break
            if target_file:
                break

        if not target_file:
            return

        if target_file.is_protected:
            return

        # Toggle selection
        was_selected = target_file in self.selected_files
        if was_selected:
            self.selected_files.remove(target_file)
        else:
            self.selected_files.append(target_file)

        # Update tree display
        self._update_file_selection_display(file_item_id, not was_selected)

    def _update_module_selection_display(self, module_item_id: str, is_selected: bool):
        """Update the display of a module's selection state."""
        # Update all child items (only non-protected files)
        for child_id in self.tree.get_children(module_item_id):
            # Check if this file is protected
            item_tags = self.tree.item(child_id, "tags") or []
            is_protected = "protected" in item_tags
            
            child_values = list(self.tree.item(child_id, "values"))
            if len(child_values) >= 4:
                # Protected files should never be shown as selected
                if is_protected:
                    child_values[3] = "☐"
                else:
                    child_values[3] = "☑" if is_selected else "☐"
                self.tree.item(child_id, values=child_values)

    def _update_file_selection_display(self, file_item_id: str, is_selected: bool):
        """Update the display of a file's selection state."""
        values = list(self.tree.item(file_item_id, "values"))
        if len(values) >= 4:
            values[3] = "☑" if is_selected else "☐"
            self.tree.item(file_item_id, values=values)

    def _select_all(self):
        """Select all available files."""
        if not self.current_report:
            return

        self.selected_files.clear()
        self.selected_modules.clear()

        for module_result in self.current_report.modules:
            # Check if module has any non-protected files
            has_selectable_files = any(not f.is_protected for f in module_result.files)
            if has_selectable_files:
                self.selected_modules.append(module_result.module_name)
            
            for file_info in module_result.files:
                if not file_info.is_protected:
                    self.selected_files.append(file_info)

        self._update_all_selection_display()
        self._update_selection_display()
        self._update_clean_button_state()

    def _select_none(self):
        """Deselect all files."""
        self.selected_files.clear()
        self.selected_modules.clear()

        self._update_all_selection_display()
        self._update_selection_display()
        self._update_clean_button_state()

    def _update_all_selection_display(self):
        """Update the selection display for all items."""
        def update_items(parent=""):
            for item_id in self.tree.get_children(parent):
                values = self.tree.item(item_id, "values")
                if values and len(values) >= 4:
                    # Check if this item should be selected
                    item_text = self.tree.item(item_id, "text")
                    is_selected = self._is_item_selected(item_id, item_text)
                    values = list(values)
                    # Ensure we have 4 columns
                    if len(values) == 3:
                        values.append("")
                    values[3] = "☑" if is_selected else "☐"
                    self.tree.item(item_id, values=values)

                # Recursively update children
                update_items(item_id)

        update_items()

    def _is_item_selected(self, item_id: str, item_text: str) -> bool:
        """Check if an item is currently selected."""
        # Check if it's a module
        values = self.tree.item(item_id, "values")
        if not values or not values[0]:  # Module header
            # Extract clean module name (remove count info)
            clean_module_name = item_text.split(" (")[0]
            return clean_module_name in self.selected_modules

        # It's a file - check if the file is in selected_files
        item_tags = self.tree.item(item_id, "tags") or []
        file_path = None
        
        # Try both tooltip and path tags
        for tag in item_tags:
            if tag.startswith("tooltip:"):
                file_path = tag[8:]
                break
            elif tag.startswith("path:"):
                file_path = tag[5:]
                break
        
        # If we found a path, check if it's in selected_files
        if file_path:
            for selected_file in self.selected_files:
                # Handle path normalization for comparison
                if (selected_file.path == file_path or 
                    selected_file.path.replace("\\\\", "\\") == file_path.replace("\\\\", "\\")):
                    return True

        return False

    def _update_selection_display(self):
        """Update the selection summary display."""
        if not self.selection_label:
            return

        file_count = len(self.selected_files)
        if file_count == 0:
            self.selection_label.config(text="未选择任何文件")
            return

        total_size = sum(f.size for f in self.selected_files)
        size_str = format_bytes(total_size)

        module_count = len(self.selected_modules)
        if module_count > 0:
            self.selection_label.config(text=f"已选择 {file_count} 个文件 ({size_str}) 来自 {module_count} 个模块")
        else:
            self.selection_label.config(text=f"已选择 {file_count} 个文件 ({size_str})")

    def _update_clean_button_state(self):
        """Update the clean button enabled state."""
        if self.clean_button:
            has_selection = len(self.selected_files) > 0
            self.clean_button.config(state="normal" if has_selection else "disabled")

    def _start_cleaning(self):
        """Start the cleaning process."""
        if not self.selected_files:
            return

        # Call the cleaning callback if provided
        if self.on_cleaning_callback:
            self.on_cleaning_callback(self.selected_files)

    def expand_all_modules(self):
        """Expand all module nodes."""
        for item in self.tree.get_children():
            self.tree.item(item, open=True)

    def collapse_all_modules(self):
        """Collapse all module nodes."""
        for item in self.tree.get_children():
            self.tree.item(item, open=False)

    def show_module_details(self, module_name: str):
        """
        Show detailed information about a module.

        Args:
            module_name: Name of module to show details for
        """
        if not self.current_report:
            return

        module = self.current_report.get_module_by_name(module_name)
        if not module:
            return

        details = f"""模块: {module_name}
风险等级: {module.get_risk_display()}
文件数量: {module.file_count}
总大小: {module.get_display_size()}

文件列表:
"""

        for file_info in module.files[:10]:  # Show first 10 files
            details += f"• {file_info.path.split('\\')[-1]} ({format_bytes(file_info.size)})\n"

        if len(module.files) > 10:
            details += f"... 还有 {len(module.files) - 10} 个文件"

        messagebox.showinfo("模块详情", details)