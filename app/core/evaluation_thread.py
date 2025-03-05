from PyQt6.QtCore import QThread, pyqtSignal
from typing import List
import time
import traceback

from app.models.contestant import Contestant
from app.models.problem import Problem
from app.models.submission import SubmissionResult

class EvaluationThread(QThread):
    result_ready = pyqtSignal(object)  # SubmissionResult
    partial_result_ready = pyqtSignal(object, bool)  # SubmissionResult, is_partial
    test_case_ready = pyqtSignal(str, str, int, int)  # contestant_id, problem_id, completed, total
    evaluation_finished = pyqtSignal()
    
    def __init__(self, evaluator, contestants, problems, use_threads=True, thread_count=4):
        super().__init__()
        self.evaluator = evaluator
        self.contestants = contestants
        self.problems = problems
        self.use_threads = use_threads
        self.thread_count = thread_count
        self._stop_requested = False
        self._completed_tasks = {}  # Track completed evaluations to prevent duplicates
        
        # Set up callbacks
        self.evaluator.reset()  # Reset evaluator state before setting callbacks
        self.evaluator.test_case_callback = self._test_case_callback
        self.evaluator.partial_result_callback = self._partial_result_callback
    
    def _test_case_callback(self, contestant_id, problem_id, completed, total):
        """Handle test case completion updates"""
        self.test_case_ready.emit(contestant_id, problem_id, completed, total)
    
    def _partial_result_callback(self, result, is_partial=True):
        """Handle partial result updates"""
        # Only emit for partial results, full results are handled by _result_callback
        if is_partial:
            self.partial_result_ready.emit(result, is_partial)
    
    def run(self):
        """Run evaluation process"""
        self._stop_requested = False
        self._completed_tasks = {}
        
        try:
            # Configure the evaluator
            if self.use_threads:
                self.evaluator.setup_parallel(thread_count=self.thread_count)
                
                # Evaluate submissions in parallel
                for contestant in self.contestants:
                    if self._stop_requested:
                        break
                    
                    for problem in self.problems:
                        task_key = (contestant.id, problem.id)
                        if task_key in self._completed_tasks:
                            continue  # Skip if already completed
                        
                        if problem.id in contestant.solutions:
                            # Schedule evaluation task
                            self.evaluator.schedule_evaluation(contestant, problem, 
                                                              callback=self._result_callback)
                
                # Wait for evaluations to complete
                self.evaluator.wait_for_evaluations()
            else:
                # Evaluate submissions sequentially
                for contestant in self.contestants:
                    if self._stop_requested:
                        break
                    
                    for problem in self.problems:
                        task_key = (contestant.id, problem.id)
                        if task_key in self._completed_tasks:
                            continue  # Skip if already completed
                        
                        if problem.id in contestant.solutions:
                            result = self.evaluator.evaluate_submission(contestant, problem)
                            if result:
                                self._result_callback(result)
                        
                        if self._stop_requested:
                            break
        except Exception as e:
            print(f"Evaluation error: {str(e)}")
            traceback.print_exc()
        finally:
            # Cleanup
            self.evaluator.cleanup()
            self.evaluation_finished.emit()
    
    def _result_callback(self, result):
        """Handle evaluation result"""
        if result and not self._stop_requested:
            task_key = (result.contestant_id, result.problem_id)
            self._completed_tasks[task_key] = True
            # Emit final result
            self.result_ready.emit(result)
            
            # Also emit as a partial result with is_partial=False
            self.partial_result_ready.emit(result, False)
    
    def stop(self):
        """Request evaluation to stop"""
        self._stop_requested = True
        self.evaluator.stop_evaluations()
        self.wait(1000)  # Give evaluator some time to clean up
