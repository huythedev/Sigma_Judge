from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QLineEdit)
from PyQt6.QtGui import QIcon

class DirectoryBrowser(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Contest Directories", parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Contestants directory
        contestants_layout = QHBoxLayout()
        contestants_layout.addWidget(QLabel("Contestants Directory:"))
        self.contestants_dir_edit = QLineEdit()
        self.contestants_dir_edit.setPlaceholderText("Path to contestants directory")
        contestants_layout.addWidget(self.contestants_dir_edit)
        
        self.contestants_browse_btn = QPushButton("Browse...")
        contestants_layout.addWidget(self.contestants_browse_btn)
        layout.addLayout(contestants_layout)
        
        # Problems directory
        problems_layout = QHBoxLayout()
        problems_layout.addWidget(QLabel("Problems Directory:"))
        self.problems_dir_edit = QLineEdit()
        self.problems_dir_edit.setPlaceholderText("Path to problems directory")
        problems_layout.addWidget(self.problems_dir_edit)
        
        self.problems_browse_btn = QPushButton("Browse...")
        problems_layout.addWidget(self.problems_browse_btn)
        layout.addLayout(problems_layout)
        
        # Load button
        load_btn_layout = QHBoxLayout()
        self.load_button = QPushButton("Load Data")
        self.load_button.setIcon(QIcon.fromTheme("document-open"))
        load_btn_layout.addStretch(1)
        load_btn_layout.addWidget(self.load_button)
        layout.addLayout(load_btn_layout)
