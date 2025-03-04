from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel,
                           QCheckBox, QSpinBox, QProgressBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class TestCaseProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFormat("Test Case %v/%m")
        
        # For precise progress tracking
        self.current = 0
        self.total = 100
        
        # Remove animation completely for instant updates
        self.setMaximum(100)
    
    def update_progress(self, current: int, total: int):
        """Update progress immediately without animation"""
        self.current = current
        self.total = total
        
        # Set range and value directly
        self.setMaximum(total)
        self.setValue(current)
        
        # Force immediate update
        self.update()

class EvaluationToolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self._contestant_count = 0  # Add this line
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Evaluation controls
        self.evaluate_button = QPushButton("Evaluate All")
        self.evaluate_button.setIcon(QIcon.fromTheme("system-run"))
        self.evaluate_button.setEnabled(False)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setIcon(QIcon.fromTheme("process-stop"))
        self.stop_button.setEnabled(False)
        
        # Threading options
        self.threading_checkbox = QCheckBox("Use Parallel Processing")
        self.threading_checkbox.setChecked(True)
        
        self.thread_count_spinner = QSpinBox()
        self.thread_count_spinner.setRange(1, 32)
        
        # Progress tracking
        self.progress_label = QLabel("Progress:")
        self.progress_bar = TestCaseProgressBar()  # Using custom progress bar
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumWidth(200)  # Make it wide enough
        
        # Add widgets to layout
        layout.addWidget(self.evaluate_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(QLabel("   "))  # Spacer
        layout.addWidget(self.threading_checkbox)
        layout.addWidget(QLabel("Threads:"))
        layout.addWidget(self.thread_count_spinner)
        layout.addWidget(QLabel("   "))  # Spacer
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch(1)
    
    def set_contestant_count(self, count: int):
        """Update thread spinner based on contestant count"""
        self._contestant_count = count
        self.thread_count_spinner.setRange(1, count)
        self.thread_count_spinner.setValue(min(self.thread_count_spinner.value(), count))
