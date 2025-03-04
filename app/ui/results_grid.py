from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout,
                           QHeaderView, QLabel, QHBoxLayout, QPushButton, 
                           QDialog, QGridLayout, QTextEdit, QTabWidget,
                           QGroupBox, QMenu, QMessageBox)  # Added QGroupBox and QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont, QCursor

from app.models.contestant import Contestant
from app.models.problem import Problem
from app.models.submission import SubmissionResult, SubmissionStatus
from typing import List, Dict, Tuple

class ResultsGrid(QWidget):
    rejudge_requested = pyqtSignal(str, str)  # contestant_id, problem_id
    rejudge_contestant_requested = pyqtSignal(str)  # contestant_id
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.results = {}  # (contestant_id, problem_id) -> SubmissionResult
        self.contestants = []
        self.problems = []
    
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        
        # Header with controls
        header_layout = QHBoxLayout()
        self.status_label = QLabel("No results yet")
        header_layout.addWidget(self.status_label)
        header_layout.addStretch(1)
        
        # Results table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.show_details)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # Enable custom context menu
        self.table.customContextMenuRequested.connect(self.show_context_menu)  # Connect to our handler
        
        # Add components to layout
        layout.addLayout(header_layout)
        layout.addWidget(self.table)
    
    def setup_grid(self, contestants: List[Contestant], problems: List[Problem]):
        """Set up the grid with the given contestants and problems"""
        self.table.clear()
        self.results = {}
        
        # Set up the table dimensions
        self.table.setRowCount(len(contestants))
        self.table.setColumnCount(len(problems) + 1)  # +1 for contestant names
        
        # Set up headers
        self.table.setHorizontalHeaderLabels(["Contestant"] + [p.id for p in problems])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        # Fill contestant names
        for i, contestant in enumerate(contestants):
            name_item = QTableWidgetItem(contestant.name)
            self.table.setItem(i, 0, name_item)
            
            # Set up empty cells for results
            for j, problem in enumerate(problems):
                cell = QTableWidgetItem("")
                cell.setBackground(QBrush(QColor("#f0f0f0")))  # Light gray for empty cells
                self.table.setItem(i, j + 1, cell)
        
        self.contestants = contestants
        self.problems = problems
        self.status_label.setText(f"{len(contestants)} contestants, {len(problems)} problems")
    
    def update_result(self, result: SubmissionResult):
        """Update the grid with a new result"""
        # Find the row and column
        contestant_idx = -1
        for i, contestant in enumerate(self.contestants):
            if contestant.id == result.contestant_id:
                contestant_idx = i
                break
        
        problem_idx = -1
        for j, problem in enumerate(self.problems):
            if problem.id == result.problem_id:
                problem_idx = j
                break
        
        if contestant_idx == -1 or problem_idx == -1:
            return
        
        # Store the result
        self.results[(result.contestant_id, result.problem_id)] = result
        
        # Update the cell
        cell = self.table.item(contestant_idx, problem_idx + 1)
        if not cell:
            cell = QTableWidgetItem()
            self.table.setItem(contestant_idx, problem_idx + 1, cell)
        
        # Set score text - Add more debug information
        if not result.test_case_results or result.status == SubmissionStatus.PENDING:
            cell.setText("N/A")
            print(f"Warning: Empty or PENDING result for {result.contestant_id}/{result.problem_id}")
            if not result.test_case_results:
                print("  No test case results")
            if result.status == SubmissionStatus.PENDING:
                print("  Status is PENDING")
        else:
            cell.setText(f"{result.score:.1f}/{result.max_score:.1f}")
        
        # Color code by status
        if result.status == SubmissionStatus.CORRECT:
            cell.setBackground(QBrush(QColor("#c8e6c9")))  # Light green
        elif result.status == SubmissionStatus.WRONG_ANSWER:
            cell.setBackground(QBrush(QColor("#ffccbc")))  # Light orange
        elif result.status == SubmissionStatus.TIME_LIMIT_EXCEEDED:
            cell.setBackground(QBrush(QColor("#d1c4e9")))  # Light purple
        elif result.status == SubmissionStatus.MEMORY_LIMIT_EXCEEDED:
            cell.setBackground(QBrush(QColor("#bbdefb")))  # Light blue
        elif result.status == SubmissionStatus.RUNTIME_ERROR:
            cell.setBackground(QBrush(QColor("#ffecb3")))  # Light yellow
        elif result.status == SubmissionStatus.COMPILATION_ERROR:
            cell.setBackground(QBrush(QColor("#ff8a65")))  # Darker orange
        else:
            cell.setBackground(QBrush(QColor("#f0f0f0")))  # Light gray
        
        cell.setToolTip(f"Status: {result.status.value}\nTime: {result.execution_time:.3f}s\nMemory: {result.memory_used:.2f}MB")
    
    def show_context_menu(self, pos):
        """Show context menu at the given position"""
        # Get the item under cursor
        item = self.table.itemAt(pos)
        if not item:
            return
            
        row = item.row()
        col = item.column()
        
        if col == 0:  # Contestant name column
            # Show contestant context menu
            contestant = self.contestants[row]
            menu = QMenu(self)
            menu.addAction("Rejudge All Solutions", 
                         lambda: self.rejudge_contestant_requested.emit(contestant.id))
            menu.exec(self.table.mapToGlobal(pos))
            
        else:  # Problem result column
            # Show problem context menu
            contestant = self.contestants[row]
            problem = self.problems[col - 1]
            result = self.results.get((contestant.id, problem.id))
            
            if result:
                menu = QMenu(self)
                menu.addAction("Show Details", 
                            lambda: self.show_details(row, col))
                menu.addAction("Rejudge Problem", 
                            lambda: self.rejudge_requested.emit(contestant.id, problem.id))
                menu.exec(self.table.mapToGlobal(pos))

    def show_details(self, row, col):
        """Show detailed result dialog when a cell is double-clicked"""
        if col == 0:  # Contestant name column
            return
        
        contestant = self.contestants[row]
        problem = self.problems[col - 1]
        
        # Get the result
        result = self.results.get((contestant.id, problem.id))
        if not result:
            return
        
        # Create and show the details dialog
        dialog = ResultDetailsDialog(result, self)
        dialog.setWindowTitle(f"Result Details - {contestant.name} - {problem.id}")
        dialog.exec()

class ResultDetailsDialog(QDialog):
    def __init__(self, result: SubmissionResult, parent=None):
        super().__init__(parent)
        self.result = result
        self.init_ui()
        self.resize(800, 600)
    
    def init_ui(self):
        """Initialize the UI for the details dialog"""
        layout = QVBoxLayout(self)
        
        # Summary section
        summary_layout = QGridLayout()
        summary_layout.addWidget(QLabel("Status:"), 0, 0)
        status_label = QLabel(self.result.status.value)
        status_font = QFont()
        status_font.setBold(True)
        status_label.setFont(status_font)
        
        # Color code status label
        if self.result.status == SubmissionStatus.CORRECT:
            status_label.setStyleSheet("color: green;")
        elif self.result.status in [SubmissionStatus.WRONG_ANSWER, SubmissionStatus.COMPILATION_ERROR]:
            status_label.setStyleSheet("color: red;")
        elif self.result.status == SubmissionStatus.TIME_LIMIT_EXCEEDED:
            status_label.setStyleSheet("color: purple;")
        elif self.result.status == SubmissionStatus.MEMORY_LIMIT_EXCEEDED:
            status_label.setStyleSheet("color: blue;")
        else:
            status_label.setStyleSheet("color: orange;")
            
        summary_layout.addWidget(status_label, 0, 1)
        
        # Score
        summary_layout.addWidget(QLabel("Score:"), 1, 0)
        score_label = QLabel(f"{self.result.score:.1f} / {self.result.max_score:.1f}")
        score_font = QFont()
        score_font.setBold(True)
        score_label.setFont(score_font)
        summary_layout.addWidget(score_label, 1, 1)
        
        # Execution time
        summary_layout.addWidget(QLabel("Time:"), 0, 2)
        summary_layout.addWidget(QLabel(f"{self.result.execution_time:.3f} seconds"), 0, 3)
        
        # Memory usage
        summary_layout.addWidget(QLabel("Memory:"), 1, 2)
        summary_layout.addWidget(QLabel(f"{self.result.memory_used:.2f} MB"), 1, 3)
        
        # Add summary layout to main layout
        layout.addLayout(summary_layout)
        
        # Create tab widget for test case details
        self.tab_widget = QTabWidget()
        
        # Add a tab for each test case
        for i, test_result in enumerate(self.result.test_case_results):
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            
            # Test case status and metrics
            info_layout = QGridLayout()
            info_layout.addWidget(QLabel("Status:"), 0, 0)
            
            tc_status_label = QLabel(test_result.status.value)
            tc_status_font = QFont()
            tc_status_font.setBold(True)
            tc_status_label.setFont(tc_status_font)
            
            # Color code test case status
            if test_result.status == SubmissionStatus.CORRECT:
                tc_status_label.setStyleSheet("color: green;")
            elif test_result.status in [SubmissionStatus.WRONG_ANSWER, SubmissionStatus.COMPILATION_ERROR]:
                tc_status_label.setStyleSheet("color: red;")
            elif test_result.status == SubmissionStatus.TIME_LIMIT_EXCEEDED:
                tc_status_label.setStyleSheet("color: purple;")
            elif test_result.status == SubmissionStatus.MEMORY_LIMIT_EXCEEDED:
                tc_status_label.setStyleSheet("color: blue;")
            else:
                tc_status_label.setStyleSheet("color: orange;")
                
            info_layout.addWidget(tc_status_label, 0, 1)
            
            # Time and memory
            info_layout.addWidget(QLabel("Time:"), 0, 2)
            info_layout.addWidget(QLabel(f"{test_result.execution_time:.3f} seconds"), 0, 3)
            info_layout.addWidget(QLabel("Memory:"), 0, 4)
            info_layout.addWidget(QLabel(f"{test_result.memory_used:.2f} MB"), 0, 5)
            
            tab_layout.addLayout(info_layout)
            
            # Error message if any
            if test_result.error_message:
                error_group = QGroupBox("Error")
                error_layout = QVBoxLayout(error_group)
                error_text = QTextEdit()
                error_text.setReadOnly(True)
                error_text.setPlainText(test_result.error_message)
                error_layout.addWidget(error_text)
                tab_layout.addWidget(error_group)
            
            # Input section
            input_group = QGroupBox("Input")
            input_layout = QVBoxLayout(input_group)
            input_text = QTextEdit()
            input_text.setReadOnly(True)
            input_text.setPlainText(test_result.input_excerpt)
            input_layout.addWidget(input_text)
            tab_layout.addWidget(input_group)
            
            # Expected vs Actual Output
            if test_result.status != SubmissionStatus.COMPILATION_ERROR:
                output_group = QGroupBox("Output")
                output_layout = QGridLayout(output_group)
                
                # Expected output
                output_layout.addWidget(QLabel("Expected:"), 0, 0)
                expected_text = QTextEdit()
                expected_text.setReadOnly(True)
                expected_text.setPlainText(test_result.expected_output)
                output_layout.addWidget(expected_text, 1, 0)
                
                # Actual output
                output_layout.addWidget(QLabel("Actual:"), 0, 1)
                actual_text = QTextEdit()
                actual_text.setReadOnly(True)
                actual_text.setPlainText(test_result.actual_output)
                output_layout.addWidget(actual_text, 1, 1)
                
                tab_layout.addWidget(output_group)
            
            # Add tab to tab widget
            self.tab_widget.addTab(tab, f"Test Case {i+1}")
        
        # Add tab widget to layout if there are test cases
        if len(self.result.test_case_results) > 0:
            layout.addWidget(self.tab_widget)
        else:
            no_tests_label = QLabel("No test cases run")
            no_tests_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_tests_label)
        
        # Add a close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)