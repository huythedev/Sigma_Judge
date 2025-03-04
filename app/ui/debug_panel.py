from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTextEdit, QTabWidget, QListWidget, QPushButton,
                           QSplitter, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont

from app.models.contestant import Contestant
from app.models.problem import Problem
from app.models.submission import SubmissionResult, SubmissionStatus
from typing import List, Dict, Tuple
import os
import json
import datetime

class DebugPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.results = []  # Store all results for debugging
        self.contestants = []
        self.problems = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Thread Monitor tab
        self.thread_monitor_tab = QWidget()
        thread_layout = QVBoxLayout(self.thread_monitor_tab)
        
        self.thread_table = QTableWidget()
        self.thread_table.setColumnCount(2)
        self.thread_table.setHorizontalHeaderLabels(["Thread ID", "Status"])
        self.thread_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        thread_layout.addWidget(QLabel("Thread Activity:"))
        thread_layout.addWidget(self.thread_table)
        
        self.tab_widget.addTab(self.thread_monitor_tab, "Thread Monitor")
        
        # Results Log tab
        self.results_log_tab = QWidget()
        log_layout = QVBoxLayout(self.results_log_tab)
        
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.show_result_details)
        
        self.result_details = QTextEdit()
        self.result_details.setReadOnly(True)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.results_list)
        splitter.addWidget(self.result_details)
        splitter.setSizes([200, 400])
        
        log_layout.addWidget(splitter)
        
        # Button to export results
        export_button = QPushButton("Export Results")
        export_button.clicked.connect(self.export_results)
        log_layout.addWidget(export_button)
        
        self.tab_widget.addTab(self.results_log_tab, "Results Log")
        
        # Test Data tab
        self.test_data_tab = QWidget()
        test_layout = QVBoxLayout(self.test_data_tab)
        
        self.contestant_list = QListWidget()
        self.problem_list = QListWidget()
        
        list_layout = QHBoxLayout()
        list_layout.addWidget(QLabel("Contestants:"))
        list_layout.addWidget(self.contestant_list)
        list_layout.addWidget(QLabel("Problems:"))
        list_layout.addWidget(self.problem_list)
        
        test_layout.addLayout(list_layout)
        
        # Test data view
        self.test_data_view = QTextEdit()
        self.test_data_view.setReadOnly(True)
        test_layout.addWidget(QLabel("Test Data:"))
        test_layout.addWidget(self.test_data_view)
        
        # Button to load test data
        load_button = QPushButton("Load Test Data")
        load_button.clicked.connect(self.load_test_data)
        test_layout.addWidget(load_button)
        
        self.tab_widget.addTab(self.test_data_tab, "Test Data")
        
        main_layout.addWidget(self.tab_widget)
    
    def set_contestants_and_problems(self, contestants: List[Contestant], problems: List[Problem]):
        """Set contestant and problem lists for debug viewing"""
        self.contestants = contestants
        self.problems = problems
        
        # Update UI lists
        self.contestant_list.clear()
        for contestant in contestants:
            self.contestant_list.addItem(contestant.name)
        
        self.problem_list.clear()
        for problem in problems:
            self.problem_list.addItem(problem.id)
    
    def update_thread_status(self, status_dict: Dict[int, str]):
        """Update the thread status display"""
        self.thread_table.setRowCount(0)  # Clear table
        
        for thread_id, status in status_dict.items():
            row = self.thread_table.rowCount()
            self.thread_table.insertRow(row)
            
            # Thread ID
            id_item = QTableWidgetItem(str(thread_id))
            self.thread_table.setItem(row, 0, id_item)
            
            # Status
            status_item = QTableWidgetItem(status)
            
            # Color code by activity
            if "Evaluating" in status:
                status_item.setBackground(QBrush(QColor("#c8e6c9")))  # Light green
            elif "Waiting" in status:
                status_item.setBackground(QBrush(QColor("#ffecb3")))  # Light yellow
            elif "Stopped" in status:
                status_item.setBackground(QBrush(QColor("#ffccbc")))  # Light orange
            
            self.thread_table.setItem(row, 1, status_item)
    
    def add_result(self, result: SubmissionResult):
        """Add a result to the debug log"""
        self.results.append(result)
        
        # Add to list widget
        item_text = f"{result.contestant_id} - {result.problem_id}: {result.status.value}"
        self.results_list.addItem(item_text)
        
        # Automatically select and show the latest result
        latest_item = self.results_list.item(self.results_list.count() - 1)
        self.results_list.setCurrentItem(latest_item)
        self.show_result_details(latest_item)
    
    def show_result_details(self, item):
        """Show details for a selected result"""
        index = self.results_list.row(item)
        if index < 0 or index >= len(self.results):
            return
        
        result = self.results[index]
        
        # Format result details as JSON for easy viewing
        result_dict = {
            "contestant_id": result.contestant_id,
            "problem_id": result.problem_id,
            "status": result.status.value,
            "score": result.score,
            "max_score": result.max_score,
            "execution_time": result.execution_time,
            "memory_used": result.memory_used,
            "test_case_results": []
        }
        
        # Add test case details
        for i, tc_result in enumerate(result.test_case_results):
            test_case = {
                "id": i + 1,
                "status": tc_result.status.value,
                "execution_time": tc_result.execution_time,
                "memory_used": tc_result.memory_used,
                "error_message": tc_result.error_message
            }
            result_dict["test_case_results"].append(test_case)
        
        # Display as formatted JSON
        self.result_details.setPlainText(json.dumps(result_dict, indent=2))
    
    def export_results(self):
        """Export all results to a JSON file"""
        if not self.results:
            return
            
        # Create a timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results_{timestamp}.json"
        
        try:
            # Convert results to serializable format
            results_list = []
            for result in self.results:
                result_dict = {
                    "contestant_id": result.contestant_id,
                    "problem_id": result.problem_id,
                    "status": result.status.value,
                    "score": result.score,
                    "max_score": result.max_score,
                    "execution_time": result.execution_time,
                    "memory_used": result.memory_used,
                    "test_case_results": []
                }
                
                for i, tc_result in enumerate(result.test_case_results):
                    test_case = {
                        "id": i + 1,
                        "status": tc_result.status.value,
                        "execution_time": tc_result.execution_time,
                        "memory_used": tc_result.memory_used,
                        "error_message": tc_result.error_message
                    }
                    result_dict["test_case_results"].append(test_case)
                
                results_list.append(result_dict)
            
            # Write to file
            with open(filename, 'w') as f:
                json.dump(results_list, f, indent=2)
                
            QMessageBox.information(self, "Export Successful", f"Results exported to {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error exporting results: {str(e)}")
    
    def load_test_data(self):
        """Load and display test data for the selected problem"""
        if not self.contestants or not self.problems:
            self.test_data_view.setPlainText("No contestants or problems loaded.")
            return
            
        selected_problem_items = self.problem_list.selectedItems()
        if not selected_problem_items:
            self.test_data_view.setPlainText("Please select a problem to view its test data.")
            return
            
        problem_id = selected_problem_items[0].text()
        
        # Find the problem
        problem = None
        for p in self.problems:
            if p.id == problem_id:
                problem = p
                break
                
        if not problem:
            self.test_data_view.setPlainText(f"Problem {problem_id} not found.")
            return
            
        # Ensure test cases are loaded
        if not problem.test_cases:
            problem.load_test_cases()
            
        if not problem.test_cases:
            self.test_data_view.setPlainText(f"No test cases found for problem {problem_id}.")
            return
            
        # Display test case info
        info = []
        info.append(f"Problem: {problem_id}")
        info.append(f"Number of test cases: {len(problem.test_cases)}")
        info.append("")
        
        for i, test_case in enumerate(problem.test_cases):
            info.append(f"Test Case {i+1}:")
            info.append(f"Input file: {os.path.basename(test_case.input_path)}")
            info.append(f"Output file: {os.path.basename(test_case.output_path)}")
            info.append(f"Weight: {test_case.weight}")
            
            # Add sample of input/output
            try:
                with open(test_case.input_path, 'r') as f:
                    input_data = f.read(500)  # Read first 500 chars
                    if len(input_data) > 500:
                        input_data += "..."
                info.append("\nInput sample:")
                info.append(input_data)
                
                with open(test_case.output_path, 'r') as f:
                    output_data = f.read(500)  # Read first 500 chars
                    if len(output_data) > 500:
                        output_data += "..."
                info.append("\nOutput sample:")
                info.append(output_data)
                
            except Exception as e:
                info.append(f"Error reading test case files: {str(e)}")
                
            info.append("\n" + "-" * 50 + "\n")
            
        self.test_data_view.setPlainText("\n".join(info))
