from PyQt6.QtCore import QThread, pyqtSignal
from typing import List

from app.models.contestant import Contestant
from app.models.problem import Problem
from app.models.submission import SubmissionResult

class EvaluationThread(QThread):
    result_ready = pyqtSignal(object)  # SubmissionResult
    test_case_ready = pyqtSignal(str, str, int, int)  # contestant_id, problem_id, completed, total
    evaluation_finished = pyqtSignal()
    
    def __init__(self, evaluator, contestants, problems, use_threads, thread_count):
        super().__init__()
        self.evaluator = evaluator
        self.contestants = contestants
        self.problems = problems
        self.use_threads = use_threads
        self.thread_count = thread_count
        
    def run(self):
        def result_callback(result):
            # Use invokeMethod to safely communicate with the main thread
            self.result_ready.emit(result)
            # Process Qt events to keep UI responsive
            QThread.msleep(10)  # Small delay to allow UI to update
        
        # Set the test case callback on the evaluator
        def tc_callback(c_id, p_id, comp, tot):
            self.test_case_ready.emit(c_id, p_id, comp, tot)
            # Process Qt events to keep UI responsive
            QThread.msleep(5)  # Even smaller delay for test cases
        
        # Assign the callback
        self.evaluator.test_case_callback = tc_callback
        
        # Start evaluation
        self.evaluator.evaluate_all(
            self.contestants, 
            self.problems, 
            result_callback,
            self.use_threads, 
            self.thread_count
        )
        
        self.evaluation_finished.emit()
    
    def stop(self):
        if self.isRunning():
            self.evaluator.stop()
            self.wait()
