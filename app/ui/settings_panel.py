from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
                           QTableWidget, QTableWidgetItem, QHeaderView, 
                           QGroupBox, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush

from app.models.settings import Settings, ProblemSettings
import os

class SettingsPanel(QWidget):
    settings_changed = pyqtSignal()
    
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Global settings group
        global_group = QGroupBox("Global Settings")
        global_layout = QFormLayout(global_group)
        
        # Time limit
        self.time_limit_spinner = QDoubleSpinBox()
        self.time_limit_spinner.setRange(0.1, 60.0)
        self.time_limit_spinner.setValue(self.settings.global_time_limit)
        self.time_limit_spinner.setSuffix(" seconds")
        self.time_limit_spinner.setDecimals(1)
        global_layout.addRow("Default Time Limit:", self.time_limit_spinner)
        
        # Memory limit
        self.memory_limit_spinner = QSpinBox()
        self.memory_limit_spinner.setRange(16, 4096)
        self.memory_limit_spinner.setValue(self.settings.global_memory_limit)
        self.memory_limit_spinner.setSuffix(" MB")
        global_layout.addRow("Default Memory Limit:", self.memory_limit_spinner)
        
        # IO mode
        self.io_mode_combo = QComboBox()
        self.io_mode_combo.addItems(["stdin", "file"])
        self.io_mode_combo.setCurrentText(self.settings.global_io_mode)
        global_layout.addRow("Default I/O Mode:", self.io_mode_combo)
        
        # Add global settings group to main layout
        main_layout.addWidget(global_group)
        
        # Problem-specific settings
        problem_group = QGroupBox("Problem-Specific Settings")
        problem_layout = QVBoxLayout(problem_group)
        
        # Table for problem settings
        self.problem_table = QTableWidget()
        self.problem_table.setColumnCount(4)
        self.problem_table.setHorizontalHeaderLabels(["Problem ID", "Time Limit", "Memory Limit", "I/O Mode"])
        self.problem_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        # Add/remove buttons
        button_layout = QHBoxLayout()
        self.add_problem_button = QPushButton("Add Problem")
        self.add_problem_button.clicked.connect(self.add_problem_setting)
        self.remove_problem_button = QPushButton("Remove Selected")
        self.remove_problem_button.clicked.connect(self.remove_problem_setting)
        
        button_layout.addWidget(self.add_problem_button)
        button_layout.addWidget(self.remove_problem_button)
        
        problem_layout.addWidget(self.problem_table)
        problem_layout.addLayout(button_layout)
        
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
        
        # Load settings into the table
        self.load_problem_settings()
    
    def load_problem_settings(self):
        """Load problem settings into the table"""
        self.problem_table.setRowCount(0)  # Clear table
        
        for problem_id, problem_settings in self.settings.problem_settings.items():
            row = self.problem_table.rowCount()
            self.problem_table.insertRow(row)
            
            # Problem ID
            id_item = QTableWidgetItem(problem_id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make ID non-editable
            self.problem_table.setItem(row, 0, id_item)
            
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
            memory_spinner.setValue(problem_settings.memory_limit)
            memory_spinner.setSuffix(" MB")
            self.problem_table.setCellWidget(row, 2, memory_spinner)
            
            # IO mode
            io_combo = QComboBox()
            io_combo.addItems(["stdin", "file"])
            io_combo.setCurrentText(problem_settings.io_mode)
            self.problem_table.setCellWidget(row, 3, io_combo)
    
    def add_problem_setting(self):
        """Add a new problem setting"""
        # Simple dialog to get problem ID
        problem_id, ok = QInputDialog.getText(self, "Add Problem Setting", "Problem ID:")
        
        if ok and problem_id:
            if problem_id in self.settings.problem_settings:
                QMessageBox.warning(self, "Duplicate", "Problem ID already exists!")
                return
                
            # Add to settings
            self.settings.problem_settings[problem_id] = ProblemSettings(
                time_limit=self.settings.global_time_limit,
                memory_limit=self.settings.global_memory_limit,
                io_mode=self.settings.global_io_mode
            )
            
            # Reload table
            self.load_problem_settings()
    
    def remove_problem_setting(self):
        """Remove the selected problem setting"""
        selected_rows = self.problem_table.selectedIndexes()
        if not selected_rows:
            return
            
        # Get unique row indices
        rows = set(index.row() for index in selected_rows)
        
        # Remove from settings (reverse order to avoid index issues)
        for row in sorted(rows, reverse=True):
            problem_id = self.problem_table.item(row, 0).text()
            if problem_id in self.settings.problem_settings:
                del self.settings.problem_settings[problem_id]
            
        # Reload table
        self.load_problem_settings()
    
    def save_settings(self):
        """Save all settings"""
        # Save global settings
        self.settings.global_time_limit = self.time_limit_spinner.value()
        self.settings.global_memory_limit = self.memory_limit_spinner.value()
        self.settings.global_io_mode = self.io_mode_combo.currentText()
        
        # Save problem-specific settings
        for row in range(self.problem_table.rowCount()):
            problem_id = self.problem_table.item(row, 0).text()
            
            time_limit = self.problem_table.cellWidget(row, 1).value()
            memory_limit = self.problem_table.cellWidget(row, 2).value()
            io_mode = self.problem_table.cellWidget(row, 3).currentText()
            
            self.settings.problem_settings[problem_id] = ProblemSettings(
                time_limit=time_limit,
                memory_limit=memory_limit,
                io_mode=io_mode
            )
        
        # Save to file
        self.settings.save()
        
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
        self.settings_changed.emit()
