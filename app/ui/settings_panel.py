from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
                           QDoubleSpinBox, QGroupBox, QPushButton, QComboBox,
                           QInputDialog, QMessageBox, QTableWidget, QTableWidgetItem,
                           QHeaderView, QCheckBox, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QBrush

from app.models.settings import Settings, ProblemSettings
import os

class SettingsPanel(QWidget):
    settings_changed = pyqtSignal()
    
    def __init__(self, settings: Settings, main_window=None):
        super().__init__()
        self.settings = settings
        self.main_window = main_window  # Store reference to main window to access problems
        self.init_ui()
        
        # Force load problem settings after UI initialization
        QTimer.singleShot(100, self.load_problem_settings)
    
    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Global settings group
        global_group = QGroupBox("Global Settings")
        global_layout = QFormLayout(global_group)
        
        # Time limit
        self.time_limit_spinner = QDoubleSpinBox()
        self.time_limit_spinner.setRange(0.1, 60.0)
        self.time_limit_spinner.setValue(getattr(self.settings, 'global_time_limit', 1.0))
        self.time_limit_spinner.setSuffix(" seconds")
        self.time_limit_spinner.setDecimals(1)
        global_layout.addRow("Default Time Limit:", self.time_limit_spinner)
        
        # Memory limit
        self.memory_limit_spinner = QSpinBox()
        self.memory_limit_spinner.setRange(16, 4096)
        self.memory_limit_spinner.setValue(getattr(self.settings, 'global_memory_limit', 512))
        self.memory_limit_spinner.setSuffix(" MB")
        global_layout.addRow("Default Memory Limit:", self.memory_limit_spinner)
        
        # IO mode
        self.io_mode_combo = QComboBox()
        self.io_mode_combo.addItems(["Automatic Detection", "Standard I/O Only", "File I/O Only"])
        
        # Set current mode - handle potential attribute errors gracefully
        io_mode = getattr(self.settings, 'global_io_mode', 'auto')
        if io_mode == "auto":
            self.io_mode_combo.setCurrentIndex(0)
        elif io_mode == "standard":
            self.io_mode_combo.setCurrentIndex(1)
        elif io_mode == "file":
            self.io_mode_combo.setCurrentIndex(2)
        
        global_layout.addRow("Default I/O Mode:", self.io_mode_combo)
        
        # I/O Mode help text
        io_mode_help = QLabel(
            "Automatic: Detects and adapts to both standard and file I/O methods\n"
            "Standard I/O Only: Programs must use stdin/stdout\n"
            "File I/O Only: Programs must use file-based input/output"
        )
        io_mode_help.setStyleSheet("color: gray; font-size: 10px;")
        global_layout.addRow("", io_mode_help)
        
        # Add global settings group to main layout
        main_layout.addWidget(global_group)
        
        # Problem-specific settings
        problem_group = QGroupBox("Problem-Specific Settings")
        problem_layout = QVBoxLayout(problem_group)
        
        # Informational label
        info_label = QLabel("These settings override the global settings for specific problems.")
        info_label.setStyleSheet("color: gray;")
        problem_layout.addWidget(info_label)
        
        # Table for problem settings
        self.problem_table = QTableWidget()
        self.problem_table.setColumnCount(4)
        self.problem_table.setHorizontalHeaderLabels(["Problem ID", "Time Limit", "Memory Limit", "I/O Mode"])
        self.problem_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.problem_table.setMinimumHeight(200)
        
        # Refresh button
        refresh_button = QPushButton("Refresh Problem List")
        refresh_button.clicked.connect(self.refresh_problem_list)
        problem_layout.addWidget(refresh_button)
        
        problem_layout.addWidget(self.problem_table)
        
        # Apply to all problems checkbox
        apply_all_layout = QHBoxLayout()
        self.apply_all_checkbox = QCheckBox("Apply global settings to all problems when saving")
        self.apply_all_checkbox.setChecked(False)  # Default to unchecked to preserve specific settings
        apply_all_layout.addWidget(self.apply_all_checkbox)
        apply_all_layout.addStretch()
        problem_layout.addLayout(apply_all_layout)
        
        # Add problem settings group to main layout
        main_layout.addWidget(problem_group)
        
        # Save button
        save_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        save_layout.addStretch(1)
        save_layout.addWidget(self.save_button)
        
        main_layout.addLayout(save_layout)
        main_layout.addStretch(1)
    
    def refresh_problem_list(self):
        """Refresh the problem list based on loaded problems and existing settings"""
        # Get current problems from main window if available
        current_problems = []
        if self.main_window and hasattr(self.main_window, 'problems'):
            current_problems = self.main_window.problems
        
        # If no problems from main window, use existing settings
        if not current_problems and hasattr(self.settings, 'problem_settings'):
            for problem_id in self.settings.problem_settings.keys():
                current_problems.append(type('Problem', (), {'id': problem_id}))
        
        # Clear and reload problem settings
        self.load_problem_settings(current_problems)
    
    def load_problem_settings(self, additional_problems=None):
        """Load problem settings into the table, including any additional problems"""
        # Get existing problem IDs from settings
        existing_problems = set()
        if hasattr(self.settings, 'problem_settings'):
            existing_problems = set(self.settings.problem_settings.keys())
        
        # Add problem IDs from additional problems parameter
        if additional_problems:
            for problem in additional_problems:
                existing_problems.add(problem.id)
        
        # Sort problem IDs for consistent display
        sorted_problem_ids = sorted(list(existing_problems))
        
        # Clear the table and set row count
        self.problem_table.setRowCount(0)
        self.problem_table.setRowCount(len(sorted_problem_ids))
        
        # Add each problem to the table
        for row, problem_id in enumerate(sorted_problem_ids):
            # Problem ID
            id_item = QTableWidgetItem(problem_id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make ID non-editable
            self.problem_table.setItem(row, 0, id_item)
            
            # Get problem settings or create default
            if problem_id in self.settings.problem_settings:
                problem_settings = self.settings.problem_settings[problem_id]
            else:
                problem_settings = ProblemSettings(
                    time_limit=self.settings.global_time_limit,
                    memory_limit=self.settings.global_memory_limit,
                    io_mode=self.settings.global_io_mode
                )
                self.settings.problem_settings[problem_id] = problem_settings
            
            # Time limit
            time_spinner = QDoubleSpinBox()
            time_spinner.setRange(0.1, 60.0)
            time_spinner.setValue(problem_settings.time_limit)
            time_spinner.setSuffix(" s")
            time_spinner.setDecimals(1)
            self.problem_table.setCellWidget(row, 1, time_spinner)
            
            # Memory limit
            memory_spinner = QSpinBox()
            memory_spinner.setRange(16, 4096)
            memory_spinner.setValue(int(problem_settings.memory_limit))
            memory_spinner.setSuffix(" MB")
            self.problem_table.setCellWidget(row, 2, memory_spinner)
            
            # IO mode
            io_combo = QComboBox()
            io_combo.addItems(["Automatic Detection", "Standard I/O Only", "File I/O Only"])
            io_mode = getattr(problem_settings, 'io_mode', 'auto')
            if io_mode == "auto":
                io_combo.setCurrentIndex(0)
            elif io_mode == "standard":
                io_combo.setCurrentIndex(1)
            elif io_mode == "file":
                io_combo.setCurrentIndex(2)
            self.problem_table.setCellWidget(row, 3, io_combo)
        
        # Update column sizes
        self.problem_table.resizeColumnsToContents()
    
    def get_io_mode_from_index(self, index):
        """Convert combobox index to io_mode string"""
        if index == 0:
            return "auto"
        elif index == 1:
            return "standard"
        elif index == 2:
            return "file"
        return "auto"
    
    def save_settings(self):
        """Save all settings"""
        # Make sure problem_settings is initialized
        if not hasattr(self.settings, 'problem_settings'):
            self.settings.problem_settings = {}
        
        # Save global settings
        self.settings.global_time_limit = self.time_limit_spinner.value()
        self.settings.global_memory_limit = self.memory_limit_spinner.value()
        self.settings.global_io_mode = self.get_io_mode_from_index(self.io_mode_combo.currentIndex())
        
        # Save problem-specific settings from table
        for row in range(self.problem_table.rowCount()):
            problem_id = self.problem_table.item(row, 0).text()
            
            # Get values from widgets
            time_limit = self.problem_table.cellWidget(row, 1).value()
            memory_limit = self.problem_table.cellWidget(row, 2).value()
            io_mode_idx = self.problem_table.cellWidget(row, 3).currentIndex()
            io_mode = self.get_io_mode_from_index(io_mode_idx)
            
            # Update problem settings
            self.settings.problem_settings[problem_id] = ProblemSettings(
                time_limit=time_limit,
                memory_limit=memory_limit,
                io_mode=io_mode
            )
        
        # Apply global settings to all problems if checkbox is checked
        if self.apply_all_checkbox.isChecked():
            for problem_id in self.settings.problem_settings:
                self.settings.problem_settings[problem_id].time_limit = self.settings.global_time_limit
                self.settings.problem_settings[problem_id].memory_limit = self.settings.global_memory_limit
                self.settings.problem_settings[problem_id].io_mode = self.settings.global_io_mode
            
            # Update the table to reflect the changes
            self.load_problem_settings()
            
            problem_count = len(self.settings.problem_settings)
            QMessageBox.information(self, "Settings Applied", 
                                  f"Global settings (Time: {self.settings.global_time_limit}s, Memory: {self.settings.global_memory_limit}MB) "
                                  f"applied to all {problem_count} problems.")
        else:
            # Provide a simple confirmation
            QMessageBox.information(self, "Settings Saved", 
                                   "Settings saved successfully. Problem-specific settings preserved.")
        
        # Save settings to file
        self.settings.save()
        print(f"Settings saved with {len(self.settings.problem_settings)} problem-specific settings")
        
        # Emit signal to notify other components
        self.settings_changed.emit()
