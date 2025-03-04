from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QProgressBar, QScrollArea)
from PyQt6.QtCore import Qt

class ThreadProgressBar(QProgressBar):
    def __init__(self, thread_id, parent=None):
        super().__init__(parent)
        self.thread_id = thread_id
        self.setTextVisible(True)
        self.setFormat("%v/%m - %p%")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setValue(0)
        self.setMaximum(100)
    
    def update_progress(self, current: int, total: int):
        self.setMaximum(total)
        self.setValue(current)

class ProgressPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_bars = {}  # thread_id -> progress bar
        self.init_ui()
    
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        self.status_label = QLabel("No active evaluation")
        header_layout.addWidget(self.status_label)
        header_layout.addStretch(1)
        self.layout.addLayout(header_layout)
        
        # Container for thread progress bars
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll_area)
        
        # Add a master progress bar
        master_layout = QHBoxLayout()
        master_layout.addWidget(QLabel("Overall Progress:"))
        self.master_progress = QProgressBar()
        self.master_progress.setTextVisible(True)
        self.master_progress.setFormat("%v/%m - %p%")
        master_layout.addWidget(self.master_progress)
        self.layout.addLayout(master_layout)
    
    def setup_threads(self, thread_count: int):
        """Set up progress bars for the given number of threads"""
        # Clear existing bars
        self.clear_threads()
        
        # Create new bars
        for i in range(thread_count):
            thread_layout = QHBoxLayout()
            thread_layout.addWidget(QLabel(f"Thread {i+1}:"))
            
            progress_bar = ThreadProgressBar(i)
            thread_layout.addWidget(progress_bar)
            
            self.scroll_layout.addLayout(thread_layout)
            self.thread_bars[i] = progress_bar
        
        self.status_label.setText(f"Monitoring {thread_count} threads")
        self.master_progress.setValue(0)
        self.master_progress.setMaximum(100)
    
    def clear_threads(self):
        """Clear all thread progress bars"""
        # Remove all existing bars
        self.thread_bars.clear()
        
        # Remove all widgets from scroll layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Remove all widgets from the layout
                while item.layout().count():
                    subitem = item.layout().takeAt(0)
                    if subitem.widget():
                        subitem.widget().deleteLater()
    
    def update_thread_progress(self, thread_id: int, current: int, total: int):
        """Update progress for a specific thread"""
        # Add debug output
        print(f"Updating thread {thread_id} progress: {current}/{total}")
        
        if thread_id in self.thread_bars:
            # Make sure the progress bar handles 0 safely
            if total <= 0:
                total = 1
                
            self.thread_bars[thread_id].setMaximum(total)
            self.thread_bars[thread_id].setValue(current)
    
    def update_thread_status(self, thread_statuses: dict):
        """Update status text for threads"""
        for thread_id, status in thread_statuses.items():
            if thread_id in self.thread_bars:
                # Extract contestant and problem IDs if available
                if "Evaluating" in status:
                    try:
                        contestant_id, problem_id = status.split(" - ")[1].split(" - ")
                        self.thread_bars[thread_id].setToolTip(f"Evaluating {contestant_id} - {problem_id}")
                    except:
                        self.thread_bars[thread_id].setToolTip(status)
                else:
                    self.thread_bars[thread_id].setToolTip(status)
    
    def update_master_progress(self, completed: int, total: int):
        """Update the master progress bar"""
        self.master_progress.setMaximum(total)
        self.master_progress.setValue(completed)
        self.status_label.setText(f"Progress: {completed}/{total} tasks completed")
