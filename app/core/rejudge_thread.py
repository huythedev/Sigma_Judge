from PyQt6.QtCore import QThread, pyqtSignal
from typing import List, Dict, Tuple
import time

from app.models.contestant import Contestant
from app.models.problem import Problem
from app.models.submission import SubmissionResult
from app.core.evaluator import Evaluator

class RejudgeThread(QThread):
    """Thread for handling rejudge operations to prevent UI freezing"""
    
    # Signals to update UI
    result_ready = pyqtSignal(object)  # SubmissionResult
    test_case_ready = pyqtSignal(str, str, int, int)  # contestant_id, problem_id, completed, total
    progress_update = pyqtSignal(int, int)  # current, total (for overall progress)
    rejudge_finished = pyqtSignal()
    
    def __init__(self, evaluator: Evaluator, 
                contestant: Contestant = None, 
                problem: Problem = None,
                problems: List[Problem] = None):
        super().__init__()
        self.evaluator = evaluator
        self.contestant = contestant
        self.problem = problem
        self.problems = problems
        self._stop_requested = False
        
        # Mode selection
        self.mode = "single"  # single or multi
        if contestant and not problem and problems:
            self.mode = "multi"  # Rejudging multiple problems for one contestant
    
    def run(self):
        """Execute the rejudging process"""
        try:
            if self.mode == "single" and self.contestant and self.problem:
                self._rejudge_single()
            elif self.mode == "multi" and self.contestant and self.problems:
                self._rejudge_multiple()
            else:
                print("Error: Invalid rejudge configuration")
        finally:
            self.rejudge_finished.emit()
            
    def _rejudge_single(self):
        """Rejudge a single submission"""
        # Set up callback for test case progress
        original_callback = self.evaluator.test_case_callback
        self.evaluator.test_case_callback = self._test_case_callback
        
        # Rejudge
        result = self.evaluator.evaluate_submission(self.contestant, self.problem)
        
        # Restore callback
        self.evaluator.test_case_callback = original_callback
        
        # Emit result
        if result:
            self.result_ready.emit(result)
    
    def _rejudge_multiple(self):
        """Rejudge multiple problems for a contestant"""
        original_callback = self.evaluator.test_case_callback
        total = len(self.problems)
        
        for idx, problem in enumerate(self.problems):
            if self._stop_requested:
                break
                
            # Update overall progress
            self.progress_update.emit(idx, total)
            
            # Set callback for this problem
            def test_case_progress(c_id, p_id, comp, tot):
                self._test_case_callback(c_id, p_id, comp, tot)
                # Process events if needed
                self.yieldToUI()
            
            self.evaluator.test_case_callback = test_case_progress
            
            # Evaluate submission
            result = self.evaluator.evaluate_submission(self.contestant, problem)
            
            # Emit result
            if result:
                self.result_ready.emit(result)
            
            # Yield to UI between problems
            self.yieldToUI()
        
        # Restore callback
        self.evaluator.test_case_callback = original_callback
    
    def _test_case_callback(self, contestant_id, problem_id, completed, total):
        """Handle test case progress updates"""
        self.test_case_ready.emit(contestant_id, problem_id, completed, total)
        
        # Yield to UI periodically to keep it responsive
        if completed % 5 == 0:  # Every 5 test cases
            self.yieldToUI()
    
    def yieldToUI(self):
        """Yield execution to UI thread briefly to keep it responsive"""
        # Sleep briefly to allow UI to process events
        self.msleep(1)  # 1ms sleep to yield to UI thread
    
    def stop(self):
        """Request the thread to stop"""
        self._stop_requested = True
        self.evaluator.stop()
