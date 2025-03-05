#!/usr/bin/env python3
"""
Main entry point for the Sigma Judge application
"""

import os
import sys
import platform
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QFile, QTextStream

# Add parent directory to path if needed
if __name__ == "__main__":
    # When running directly, adjust the path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Now import local modules
from app.ui.main_window import MainWindow
from app.models.settings import Settings

def main():
    """Main application entry point"""
    # Initialize settings
    settings = Settings.load()
    
    # Debug output
    print(f"Loaded settings from disk:")
    print(f"- Thread count: {settings.thread_count}")
    print(f"- Global time limit: {settings.global_time_limit}")
    print(f"- Global memory limit: {settings.global_memory_limit}")
    print(f"- Last directory: {settings.last_directory}")
    print(f"- Has {len(settings.problem_settings)} problem settings")
    
    # Create the application
    app = QApplication(sys.argv)
    app.setApplicationName("Sigma Judge")
    
    # Set application icon if available
    icon_path = os.path.join("resources", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Set platform-specific style
    if platform.system() == "Darwin":  # macOS
        app.setStyle("macintosh")
    elif platform.system() == "Windows":
        app.setStyle("windowsvista")
    else:  # Linux and others
        app.setStyle("fusion")  # Fusion looks good everywhere
    
    # Load application stylesheet for modern UI
    # Use absolute path to resources directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    style_file_path = os.path.join(base_dir, "resources", "styles.qss")
    style_file = QFile(style_file_path)
    
    if style_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
        stream = QTextStream(style_file)
        app.setStyleSheet(stream.readAll())
    
    # Create and show the main window
    window = MainWindow(settings)
    window.show()
    
    # Start the application event loop
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
