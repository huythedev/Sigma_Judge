import sys
import os
import platform
from PyQt6.QtWidgets import QApplication
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
    app = QApplication(sys.argv)
    
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
    
    # Load settings
    settings = Settings()
    settings.load()
    
    # Create and show main window
    window = MainWindow(settings)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
