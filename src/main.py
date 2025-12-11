"""
Main Application Entry Point

Launches the Windows C Drive Cleaner GUI application.
"""

import sys
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from ui.main_window import MainWindow
import tkinter as tk


def main():
    """Main application entry point."""
    try:
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
