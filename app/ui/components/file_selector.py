from PyQt6.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
import os
from app.utils.platform_utils import open_file_dialog, open_directory_dialog, get_platform

class FileSelector(QWidget):
    file_selected = pyqtSignal(str)
    
    def __init__(self, parent=None, file_types=None, select_dir=False):
        super().__init__(parent)
        self.file_types = file_types
        self.select_dir = select_dir
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Path entry
        self.path_entry = QLineEdit()
        layout.addWidget(self.path_entry)
        
        # Browse button
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self._browse)
        layout.addWidget(self.browse_button)
    
    def _browse(self):
        """Open file dialog using platform-specific implementation"""
        if self.select_dir:
            path = open_directory_dialog(
                initial_dir=self._get_initial_dir(),
                parent=self
            )
        else:
            path = open_file_dialog(
                file_types=self.file_types,
                initial_dir=self._get_initial_dir(),
                parent=self
            )
            
        if path:
            self.path_entry.setText(path)
            self.file_selected.emit(path)
    
    def _get_initial_dir(self):
        """Get initial directory for file dialog"""
        current_path = self.path_entry.text()
        if current_path and os.path.exists(current_path):
            if os.path.isdir(current_path):
                return current_path
            return os.path.dirname(current_path)
        return os.path.expanduser("~")
    
    def get_path(self):
        """Get the selected path"""
        return self.path_entry.text()
    
    def set_path(self, path):
        """Set the path"""
        self.path_entry.setText(path)
