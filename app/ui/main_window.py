from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QMessageBox,
                           QTabWidget, QFileDialog, QPushButton, QMenu, QMenuBar)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer  # Ensure QTimer is imported
from PyQt6.QtGui import QIcon, QAction

import os
import pandas as pd  # Add pandas import at the top
from typing import Dict, Tuple

from app.models.settings import Settings
from app.models.contestant import Contestant
from app.models.problem import Problem
from app.models.submission import SubmissionResult
from app.core.evaluator import Evaluator
from app.core.evaluation_thread import EvaluationThread
from app.ui.results_grid import ResultsGrid
from app.ui.settings_panel import SettingsPanel
from app.ui.debug_panel import DebugPanel
from app.ui.components.evaluation_toolbar import EvaluationToolbar
from app.ui.components.directory_browser import DirectoryBrowser
from app.ui.progress_panel import ProgressPanel

import sys
from app.utils.platform_utils import get_platform
from app.core.rejudge_thread import RejudgeThread

class MainWindow(QMainWindow):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.evaluator = Evaluator(settings)
        self.evaluation_thread = None
        self.contestants = []
        self.problems = []
        
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Sigma Judge")
        self.setMinimumSize(1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Create UI components
        self.dir_browser = DirectoryBrowser()
        self.eval_toolbar = EvaluationToolbar()
        self.results_grid = ResultsGrid()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.results_grid, "Results")
        
        # Add progress panel as a new tab
        self.progress_panel = ProgressPanel()
        self.tab_widget.addTab(self.progress_panel, "Progress")
        
        # Create settings panel with reference to main window
        self.settings_panel = SettingsPanel(self.settings, self)
        self.tab_widget.addTab(self.settings_panel, "Settings")
        self.debug_panel = DebugPanel()
        self.tab_widget.addTab(self.debug_panel, "Debug")
        
        # Add components to layout
        main_layout.addWidget(self.dir_browser)
        main_layout.addWidget(self.eval_toolbar)
        main_layout.addWidget(self.tab_widget)
        
        self.setCentralWidget(central_widget)
        
        # Set initial directories if available - Improve the logic here
        if self.settings.last_directory and os.path.isdir(self.settings.last_directory):
            base_dir = self.settings.last_directory
            print(f"Setting initial directories from: {base_dir}")
            
            # Only set if these directories actually exist
            contestants_dir = os.path.join(base_dir, "contestants")
            problems_dir = os.path.join(base_dir, "problems")
            
            if os.path.isdir(contestants_dir):
                self.dir_browser.contestants_dir_edit.setText(contestants_dir)
                print(f"Set contestants directory: {contestants_dir}")
            else:
                # Use base directory as fallback
                self.dir_browser.contestants_dir_edit.setText(base_dir)
                print(f"Contestants subdirectory not found, using: {base_dir}")
            
            if os.path.isdir(problems_dir):
                self.dir_browser.problems_dir_edit.setText(problems_dir)
                print(f"Set problems directory: {problems_dir}")
            else:
                # Use base directory as fallback
                self.dir_browser.problems_dir_edit.setText(base_dir)
                print(f"Problems subdirectory not found, using: {base_dir}")
        else:
            print(f"No valid last directory in settings: {self.settings.last_directory}")
        
        # Add Export button to toolbar
        self.eval_toolbar.export_button = QPushButton("Export Results")
        self.eval_toolbar.export_button.setIcon(QIcon.fromTheme("document-save"))
        self.eval_toolbar.export_button.setEnabled(False)
        self.eval_toolbar.export_button.clicked.connect(self.export_results)
        self.eval_toolbar.layout().insertWidget(2, self.eval_toolbar.export_button)
        
        # Configure window based on platform
        self.setup_platform_specifics()
        
        # Make settings panel refresh when selected
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def setup_platform_specifics(self):
        """Setup platform-specific configurations"""
        platform = get_platform()
        
        if platform == 'mac':
            # Mac-specific menu setup - using PyQt methods, not tkinter
            menubar = self.menuBar()
            app_menu = menubar.addMenu('Sigma Judge')
            about_action = QAction('About', self)
            app_menu.addAction(about_action)
            
            # Add separator
            app_menu.addSeparator()
            
            # Add quit action
            quit_action = QAction('Quit', self)
            quit_action.triggered.connect(self.close)
            app_menu.addAction(quit_action)
            
        elif platform == 'windows':
            # Windows-specific settings
            try:
                icon_path = self.resource_path("icon.ico")
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
            except Exception as e:
                print(f"Could not set window icon: {e}")
    
    def connect_signals(self):
        """Connect all UI signals"""
        # Directory browser signals
        self.dir_browser.load_button.clicked.connect(self.load_data)
        self.dir_browser.directories_changed.connect(self.update_directory_settings)
        
        # Evaluation toolbar signals
        self.eval_toolbar.evaluate_button.clicked.connect(self.start_evaluation)
        self.eval_toolbar.stop_button.clicked.connect(self.stop_evaluation)
        
        # Results grid signals
        self.results_grid.rejudge_requested.connect(self.rejudge_submission)
        self.results_grid.rejudge_contestant_requested.connect(self.rejudge_contestant)
    
    def update_directory_settings(self, contestants_dir, problems_dir):
        """Update and save directory settings when changed"""
        # Use the common parent directory as the last directory
        if contestants_dir and os.path.isdir(contestants_dir):
            self.settings.last_directory = os.path.dirname(contestants_dir)
            self.settings.save()
            print(f"Saved last directory: {self.settings.last_directory}")
    
    def load_data(self):
        """Load contestant and problem data from directories"""
        contestants_dir = self.dir_browser.contestants_dir_edit.text()
        problems_dir = self.dir_browser.problems_dir_edit.text()
        
        print(f"\nLoading from directories:")
        print(f"Contestants: {contestants_dir}")
        print(f"Problems: {problems_dir}")
        
        try:
            self.contestants = []
            self.problems = []
            
            # Load problems first
            if os.path.isdir(problems_dir):
                problem_dirs = []
                
                # First check for subdirectories that might be problem directories
                for item in os.listdir(problems_dir):
                    item_path = os.path.join(problems_dir, item)
                    if os.path.isdir(item_path):
                        problem_dirs.append((item, item_path))
                
                # If no subdirectories, the main directory might be the problem directory
                if not problem_dirs:
                    problem_name = os.path.basename(problems_dir)
                    print(f"No problem subdirectories found, treating '{problem_name}' as single problem")
                    problem_dirs = [(problem_name, problems_dir)]
                
                # Process each problem directory
                for problem_name, problem_dir in sorted(problem_dirs):
                    problem = Problem(id=problem_name, name=problem_name, directory=problem_dir)
                    problem.load_test_cases()
                    if problem.test_cases:
                        self.problems.append(problem)
                        print(f"Loaded problem: {problem_name} with {len(problem.test_cases)} test cases")
                    else:
                        print(f"WARNING: Problem {problem_name} has no test cases. Check the directory structure.")
                
                if not self.problems:
                    QMessageBox.warning(self, "Warning", 
                                       f"No valid problems with test cases found in {problems_dir}.\n\n"
                                       "Please check the directory structure and file naming patterns.")
            else:
                QMessageBox.warning(self, "Warning", f"Problems directory not found: {problems_dir}")
            
            # Load contestants
            if os.path.isdir(contestants_dir):
                for contestant_name in sorted(os.listdir(contestants_dir)):
                    contestant_dir = os.path.join(contestants_dir, contestant_name)
                    if os.path.isdir(contestant_dir):
                        contestant = Contestant(id=contestant_name, name=contestant_name, directory=contestant_dir)
                        self.contestants.append(contestant)
                        print(f"Loaded contestant: {contestant_name}")
            
            # Match solutions to problems
            missing_solutions = []
            for contestant in self.contestants:
                for problem in self.problems:
                    found = False
                    for ext in ['.py', '.java', '.cpp', '.c']:
                        solution_path = os.path.join(contestant.directory, f"{problem.id}{ext}")
                        if os.path.isfile(solution_path):
                            contestant.solutions[problem.id] = solution_path
                            found = True
                            print(f"Found solution: {contestant.id}/{problem.id} -> {solution_path}")
                            break
                    if not found:
                        missing_solutions.append(f"{contestant.id}/{problem.id}")
            
            if missing_solutions:
                print("\nMissing solutions:")
                for missing in missing_solutions:
                    print(f"No solution found for {missing}")
            
            # Update UI
            self.results_grid.setup_grid(self.contestants, self.problems)
            has_data = len(self.contestants) > 0 and len(self.problems) > 0
            self.eval_toolbar.evaluate_button.setEnabled(has_data)
            self.eval_toolbar.set_contestant_count(len(self.contestants))  # Add this line
            self.debug_panel.set_contestants_and_problems(self.contestants, self.problems)
            
            status_msg = f"Loaded {len(self.contestants)} contestants and {len(self.problems)} problems"
            print(f"\n{status_msg}")
            self.statusBar().showMessage(status_msg)
            
            # After successful loading, save the directory as last_directory
            if os.path.isdir(contestants_dir):
                self.settings.last_directory = os.path.dirname(contestants_dir)
                self.settings.save()
                print(f"Saved last directory: {self.settings.last_directory}")
            
            # After loading problems, refresh the settings panel's problem list
            if hasattr(self, 'settings_panel'):
                self.settings_panel.refresh_problem_list()
            
        except Exception as e:
            error_msg = f"Error loading data: {str(e)}"
            print(f"\nERROR: {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)
            self.statusBar().showMessage("Error loading data")
    
    def start_evaluation(self):
        """Start the evaluation process"""
        if not self.contestants or not self.problems:
            return
        
        # Reset results for any tasks that will be evaluated
        self.reset_pending_results()
        
        # Update UI state
        self.eval_toolbar.evaluate_button.setEnabled(False)
        self.dir_browser.load_button.setEnabled(False)
        self.eval_toolbar.stop_button.setEnabled(True)
        self.eval_toolbar.progress_bar.setVisible(True)
        self.eval_toolbar.progress_bar.setValue(0)
        
        # Setup progress panel
        thread_count = self.eval_toolbar.thread_count_spinner.value()
        if not self.eval_toolbar.threading_checkbox.isChecked():
            thread_count = 1
        thread_count = min(thread_count, len(self.contestants))
        
        self.progress_panel.setup_threads(thread_count)
        self.tab_widget.setCurrentWidget(self.progress_panel)  # Switch to progress tab
        
        # Reset evaluator state
        self.evaluator.reset()
        
        # Start evaluation thread
        self.evaluation_thread = EvaluationThread(
            self.evaluator,
            self.contestants,
            self.problems,
            self.eval_toolbar.threading_checkbox.isChecked(),
            self.eval_toolbar.thread_count_spinner.value()
        )
        
        self.evaluation_thread.result_ready.connect(self.handle_result)
        self.evaluation_thread.partial_result_ready.connect(self.handle_partial_result)
        self.evaluation_thread.test_case_ready.connect(self.handle_test_case)
        self.evaluation_thread.evaluation_finished.connect(self.evaluation_finished)
        
        if self.eval_toolbar.threading_checkbox.isChecked():
            self.debug_thread_timer = QTimer()
            self.debug_thread_timer.timeout.connect(self.update_debug_thread_status)
            self.debug_thread_timer.start(500)
        
        self.evaluation_thread.start()
        self.statusBar().showMessage("Evaluation started...")
    
    def reset_pending_results(self):
        """Reset results for tasks that will be reevaluated"""
        # This ensures we don't have stale or partial results
        for contestant in self.contestants:
            for problem in self.problems:
                if problem.id in contestant.solutions:
                    # Mark cell as pending
                    self.results_grid.reset_result(contestant.id, problem.id)
    
    @pyqtSlot(str, str, int, int)
    def handle_test_case(self, contestant_id: str, problem_id: str, completed: int, total: int):
        """Handle test case completion update"""
        # Update toolbar progress bar as before
        self.eval_toolbar.progress_bar.update_progress(completed, total)
        
        # Update progress panel - Add null check
        if hasattr(self.evaluator, '_parallel_evaluator') and self.evaluator._parallel_evaluator is not None:
            try:
                thread_status = self.evaluator._parallel_evaluator.get_thread_status()
                
                # Find which thread is processing this contestant/problem
                for thread_id, status in thread_status.items():
                    if f"Evaluating {contestant_id}" in status:
                        self.progress_panel.update_thread_progress(thread_id, completed, total)
                        break
            except Exception as e:
                print(f"Error updating thread status: {str(e)}")
        else:
            # Single-threaded mode, use thread ID 0
            self.progress_panel.update_thread_progress(0, completed, total)
        
        self.statusBar().showMessage(f"Evaluating {contestant_id}/{problem_id}: Test case {completed}/{total}")
    
    @pyqtSlot(object, bool)
    def handle_partial_result(self, result, is_partial):
        """Handle partial or complete results from test case execution"""
        # Update result in grid with partial score
        self.results_grid.update_partial_result(result, is_partial)
        
        # Only add to debug panel if it's a complete result 
        if not is_partial:
            self.debug_panel.add_result(result)
        
        # Update master progress in progress panel if it's a complete result
        if not is_partial:
            total_tasks = len(self.contestants) * len(self.problems)
            completed_tasks = len(self.results_grid.results)
            self.progress_panel.update_master_progress(completed_tasks, total_tasks)
    
    # We can keep the original handle_result method for backward compatibility
    @pyqtSlot(object)
    def handle_result(self, result):
        """Handle complete evaluation result (called at the end of a submission)"""
        # This will be called when a full submission is complete
        # We can forward to the partial handler with is_partial=False
        self.handle_partial_result(result, False)
    
    @pyqtSlot()
    def evaluation_finished(self):
        """Handle evaluation completion"""
        self.eval_toolbar.evaluate_button.setEnabled(True)
        self.dir_browser.load_button.setEnabled(True)
        self.eval_toolbar.stop_button.setEnabled(False)
        self.eval_toolbar.progress_bar.setVisible(False)
        
        if hasattr(self, 'debug_thread_timer') and self.debug_thread_timer.isActive():
            self.debug_thread_timer.stop()
        
        self.statusBar().showMessage("Evaluation completed")
        self.eval_toolbar.export_button.setEnabled(True)  # Enable export after evaluation
    
    def rejudge_submission(self, contestant_id: str, problem_id: str):
        """Rejudge a single submission"""
        contestant = next((c for c in self.contestants if c.id == contestant_id), None)
        problem = next((p for p in self.problems if p.id == problem_id), None)
        
        if contestant and problem:
            # Show progress in status bar
            self.statusBar().showMessage(f"Rejudging {contestant.id}/{problem.id}...")
            
            # Disable relevant UI elements
            self.eval_toolbar.evaluate_button.setEnabled(False)
            self.dir_browser.load_button.setEnabled(False)
            self.eval_toolbar.stop_button.setEnabled(True)
            self.eval_toolbar.progress_bar.setVisible(True)
            self.eval_toolbar.progress_bar.setValue(0)
            
            # Create and configure rejudge thread
            self.rejudge_thread = RejudgeThread(self.evaluator, contestant, problem)
            self.rejudge_thread.test_case_ready.connect(self.handle_test_case)
            self.rejudge_thread.result_ready.connect(self.handle_result)
            self.rejudge_thread.rejudge_finished.connect(self.rejudge_finished)
            
            # Start rejudge thread
            self.rejudge_thread.start()
            
            # Show progress panel
            self.progress_panel.setup_threads(1)
            self.tab_widget.setCurrentWidget(self.progress_panel)
            
            return
            
        self.statusBar().showMessage(f"Cannot rejudge: contestant or problem not found")
    
    def rejudge_contestant(self, contestant_id: str):
        """Rejudge all problems for a contestant"""
        contestant = next((c for c in self.contestants if c.id == contestant_id), None)
        if not contestant:
            return
            
        # Update UI state
        self.eval_toolbar.evaluate_button.setEnabled(False)
        self.dir_browser.load_button.setEnabled(False)
        self.eval_toolbar.stop_button.setEnabled(True)
        self.eval_toolbar.progress_bar.setVisible(True)
        self.eval_toolbar.progress_bar.setValue(0)
        self.eval_toolbar.progress_bar.setMaximum(len(self.problems))
        
        # Set up progress panel for single thread
        self.progress_panel.setup_threads(1)
        self.tab_widget.setCurrentWidget(self.progress_panel)
        
        # Create and configure rejudge thread
        self.rejudge_thread = RejudgeThread(self.evaluator, contestant, problems=self.problems)
        self.rejudge_thread.test_case_ready.connect(self.handle_test_case)
        self.rejudge_thread.result_ready.connect(self.handle_result)
        self.rejudge_thread.progress_update.connect(self.handle_rejudge_progress)
        self.rejudge_thread.rejudge_finished.connect(self.rejudge_finished)
        
        # Start rejudge thread
        self.rejudge_thread.start()
    
    @pyqtSlot(int, int)
    def handle_rejudge_progress(self, current, total):
        """Handle rejudge overall progress updates"""
        self.eval_toolbar.progress_bar.setMaximum(total)
        self.eval_toolbar.progress_bar.setValue(current)
        self.progress_panel.update_master_progress(current, total)
        
    @pyqtSlot()
    def rejudge_finished(self):
        """Handle completion of rejudging"""
        # Reset UI state
        self.eval_toolbar.evaluate_button.setEnabled(True)
        self.dir_browser.load_button.setEnabled(True)
        self.eval_toolbar.stop_button.setEnabled(False)
        self.eval_toolbar.progress_bar.setVisible(False)
        
        self.statusBar().showMessage("Rejudging completed")
        
    def stop_evaluation(self):
        """Stop the current evaluation"""
        if self.evaluation_thread and self.evaluation_thread.isRunning():
            # Stop evaluation thread
            self.evaluation_thread.stop()
        
        # Also stop rejudge thread if running
        if hasattr(self, 'rejudge_thread') and self.rejudge_thread.isRunning():
            self.rejudge_thread.stop()
            
        # Reset UI state
        self.eval_toolbar.evaluate_button.setEnabled(True)
        self.dir_browser.load_button.setEnabled(True)
        self.eval_toolbar.stop_button.setEnabled(False)
        self.eval_toolbar.progress_bar.setVisible(False)
        
        self.statusBar().showMessage("Evaluation stopped")
    
    def update_debug_thread_status(self):
        """Update thread status in debug panel"""
        if hasattr(self.evaluator, '_parallel_evaluator') and self.evaluator._parallel_evaluator is not None:
            try:
                thread_status = self.evaluator._parallel_evaluator.get_thread_status()
                self.debug_panel.update_thread_status(thread_status)
                self.progress_panel.update_thread_status(thread_status)  # Add this line
            except Exception as e:
                print(f"Error updating debug thread status: {str(e)}")
    
    def export_results(self):
        """Export results to Excel file"""
        if not self.results_grid.results:
            QMessageBox.warning(self, "Warning", "No results to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            "",
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return
            
        if not file_path.endswith('.xlsx'):
            file_path += '.xlsx'
        
        try:
            # Create data for each sheet
            overview_data = []
            details_data = []
            
            for contestant in self.contestants:
                for problem in self.problems:
                    result = self.results_grid.results.get((contestant.id, problem.id))
                    if result:
                        # Overview row
                        overview_data.append({
                            'Contestant': contestant.name,
                            'Problem': problem.id,
                            'Status': result.status.value,
                            'Score': result.score,
                            'Max Score': result.max_score,
                            'Total Time (s)': result.execution_time,
                            'Max Memory (MB)': result.memory_used
                        })
                        
                        # Details rows
                        for i, tc_result in enumerate(result.test_case_results, 1):
                            details_data.append({
                                'Contestant': contestant.name,
                                'Problem': problem.id,
                                'Test Case': i,
                                'Status': tc_result.status.value,
                                'Time (s)': tc_result.execution_time,
                                'Memory (MB)': tc_result.memory_used,
                                'Input': tc_result.input_excerpt,
                                'Expected': tc_result.expected_output,
                                'Actual': tc_result.actual_output,
                                'Error': tc_result.error_message
                            })
            
            # Create DataFrames
            overview_df = pd.DataFrame(overview_data)
            details_df = pd.DataFrame(details_data)
            
            # Create Excel writer
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                # Write sheets
                overview_df.to_excel(writer, sheet_name='Overview', index=False)
                details_df.to_excel(writer, sheet_name='Test Cases', index=False)
                
                # Get workbook and worksheets
                workbook = writer.book
                overview_sheet = writer.sheets['Overview']
                details_sheet = writer.sheets['Test Cases']
                
                # Set column widths
                for sheet in [overview_sheet, details_sheet]:
                    for i, col in enumerate(overview_df.columns):
                        sheet.set_column(i, i, 15)  # Set width to 15 for all columns
                
                # Add autofilter to both sheets
                overview_sheet.autofilter(0, 0, len(overview_df), len(overview_df.columns) - 1)
                details_sheet.autofilter(0, 0, len(details_df), len(details_df.columns) - 1)
                
                # Add color formatting
                status_format = {
                    'Correct': workbook.add_format({'bg_color': '#c8e6c9'}),
                    'Wrong Answer': workbook.add_format({'bg_color': '#ffccbc'}),
                    'Time Limit Exceeded': workbook.add_format({'bg_color': '#d1c4e9'}),
                    'Memory Limit Exceeded': workbook.add_format({'bg_color': '#bbdefb'}),
                    'Runtime Error': workbook.add_format({'bg_color': '#ffecb3'}),
                    'Compilation Error': workbook.add_format({'bg_color': '#ff8a65'})
                }
                
                # Apply conditional formatting to both sheets
                status_col_overview = overview_df.columns.get_loc('Status')
                status_col_details = details_df.columns.get_loc('Status')
                
                for status, fmt in status_format.items():
                    # Overview sheet
                    overview_sheet.conditional_format(
                        1, status_col_overview,
                        len(overview_df), status_col_overview,
                        {'type': 'text',
                         'criteria': 'containing',
                         'value': status,
                         'format': fmt}
                    )
                    
                    # Details sheet
                    details_sheet.conditional_format(
                        1, status_col_details,
                        len(details_df), status_col_details,
                        {'type': 'text',
                         'criteria': 'containing',
                         'value': status,
                         'format': fmt}
                    )
            
            QMessageBox.information(self, "Success", "Results exported successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export results: {str(e)}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.evaluation_thread and self.evaluation_thread.isRunning():
            self.evaluation_thread.stop()
            
        # Also stop rejudge thread if running
        if hasattr(self, 'rejudge_thread') and self.rejudge_thread.isRunning():
            self.rejudge_thread.stop()
        
        # Save all current settings
        self.settings.thread_count = self.eval_toolbar.thread_count_spinner.value()
        
        # Update last_directory if available
        contestants_dir = self.dir_browser.contestants_dir_edit.text()
        if contestants_dir and os.path.isdir(contestants_dir):
            self.settings.last_directory = os.path.dirname(contestants_dir)
            
        # Save settings to disk
        self.settings.save()
        print("Settings saved on application close")
        
        event.accept()
    
    def on_closing(self):
        """Proper cleanup when closing"""
        if self.evaluation_thread and self.evaluation_thread.isRunning():
            self.evaluation_thread.stop()
        self.settings.thread_count = self.eval_toolbar.thread_count_spinner.value()
        self.settings.save()
        self.close()
    
    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_path, relative_path)
        except Exception as e:
            print(f"Error in resource_path: {e}")
            return relative_path
    
    def on_tab_changed(self, index):
        """Handle tab change event"""
        # If switching to settings tab, refresh problem settings
        if index == 2:  # Assuming settings is tab index 2
            QTimer.singleShot(100, self.settings_panel.load_problem_settings)