from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, 
                           QHBoxLayout, QVBoxLayout, QFileDialog)
from PyQt6.QtCore import pyqtSignal
import os
from app.utils.platform_utils import open_directory_dialog

class DirectoryBrowser(QWidget):
    directories_changed = pyqtSignal(str, str)  # contestants_dir, problems_dir
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Contestants directory
        contestants_layout = QHBoxLayout()
        contestants_layout.addWidget(QLabel("Contestants Directory:"))
        self.contestants_dir_edit = QLineEdit()
        contestants_layout.addWidget(self.contestants_dir_edit)
        self.contestants_browse_btn = QPushButton("Browse...")
        self.contestants_browse_btn.clicked.connect(self.browse_contestants_dir)
        contestants_layout.addWidget(self.contestants_browse_btn)
        layout.addLayout(contestants_layout)
        
        # Problems directory
        problems_layout = QHBoxLayout()
        problems_layout.addWidget(QLabel("Problems Directory:"))
        self.problems_dir_edit = QLineEdit()
        problems_layout.addWidget(self.problems_dir_edit)
        self.problems_browse_btn = QPushButton("Browse...")
        self.problems_browse_btn.clicked.connect(self.browse_problems_dir)
        problems_layout.addWidget(self.problems_browse_btn)
        layout.addLayout(problems_layout)
        
        # Load button
        self.load_button = QPushButton("Load")
        layout.addWidget(self.load_button)
    
    def browse_contestants_dir(self):
        """Open directory browser for contestants"""
        initial_dir = self.get_initial_dir(self.contestants_dir_edit.text())
        
        print(f"Opening directory browser with initial dir: {initial_dir}")
        dir_path = open_directory_dialog(
            title="Select Contestants Directory",
            initial_dir=initial_dir,
            parent=self
        )
        
        if dir_path:
            self.contestants_dir_edit.setText(dir_path)
            self.directories_changed.emit(dir_path, self.problems_dir_edit.text())
            print(f"Selected contestants directory: {dir_path}")
            
            # If problems dir is empty, suggest the same parent directory
            if not self.problems_dir_edit.text() or not os.path.exists(self.problems_dir_edit.text()):
                parent_dir = os.path.dirname(dir_path)
                problems_guess = os.path.join(parent_dir, "problems")
                if os.path.exists(problems_guess):
                    self.problems_dir_edit.setText(problems_guess)
                    print(f"Auto-set problems directory: {problems_guess}")
    
    def browse_problems_dir(self):
        """Open directory browser for problems"""
        initial_dir = self.get_initial_dir(self.problems_dir_edit.text())
        
        print(f"Opening directory browser with initial dir: {initial_dir}")
        dir_path = open_directory_dialog(
            title="Select Problems Directory",
            initial_dir=initial_dir,
            parent=self
        )
        
        if dir_path:
            self.problems_dir_edit.setText(dir_path)
            self.directories_changed.emit(self.contestants_dir_edit.text(), dir_path)
            print(f"Selected problems directory: {dir_path}")
            
            # If contestants dir is empty, suggest the same parent directory
            if not self.contestants_dir_edit.text() or not os.path.exists(self.contestants_dir_edit.text()):
                parent_dir = os.path.dirname(dir_path)
                contestants_guess = os.path.join(parent_dir, "contestants")
                if os.path.exists(contestants_guess):
                    self.contestants_dir_edit.setText(contestants_guess)
                    print(f"Auto-set contestants directory: {contestants_guess}")
    
    def get_initial_dir(self, current_path):
        """Get initial directory for file dialog based on current path"""
        # Try the current path first
        if current_path and os.path.isdir(current_path):
            return current_path
        
        # Try parent directory of current path
        if current_path and os.path.dirname(current_path) and os.path.isdir(os.path.dirname(current_path)):
            return os.path.dirname(current_path)
        
        # Try home directory 
        home_dir = os.path.expanduser("~")
        if os.path.isdir(home_dir):
            return home_dir
            
        # Last resort: current working directory
        return os.getcwd()
