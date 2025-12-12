"""
Main Application Entry Point

Launches the Windows C Drive Cleaner GUI application.
"""

import sys
import os
from datetime import datetime

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from ui.main_window import MainWindow
import tkinter as tk
import tkinter.messagebox as messagebox


def check_usage_limit():
    """Check if the application is still within the usage period."""
    # Set expiration date: December 21, 2025, 00:00:00
    expiration_date = datetime(2025, 12, 21, 0, 0, 0)
    current_date = datetime.now()
    
    if current_date >= expiration_date:
        return False
    return True


def main():
    """Main application entry point."""
    try:
        # Check usage limit first
        if not check_usage_limit():
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            error_message = "此应用程序的使用期限已到。\n请联系游语获取更新版本。\n\n到期时间: 2025年12月21日 00:00"
            messagebox.showerror("使用期限已到", error_message)
            root.destroy()
            sys.exit(1)
        
        # Create root window
        root = tk.Tk()

        # Create main application window
        app = MainWindow(root)

        # Handle cleanup on exit
        def on_closing():
            app.cleanup()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Start the application
        app.run()

    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()