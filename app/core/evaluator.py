import os
import subprocess
import time
import tempfile
import shutil
import platform
from typing import List, Dict, Tuple, Optional, Callable
import psutil
import threading
import queue
import re

# Conditionally import resource module (only available on Unix)
if platform.system() != 'Windows':
    import resource

from app.models.contestant import Contestant
from app.models.problem import Problem, TestCase
from app.models.submission import SubmissionResult, TestCaseResult, SubmissionStatus
from app.models.settings import Settings, ProblemSettings
from app.core.parallel_evaluator import ParallelEvaluator

# Import modules
from app.core.modules.compiler import Compiler
from app.core.modules.file_io_detector import FileIODetector
from app.core.modules.test_runner import TestRunner

class Evaluator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._stop_requested = False
        self._current_processes = {}  # track running processes
        self.test_case_callback = None
        self._parallel_evaluator = None
    
    def stop(self):
        """Stop all evaluations and kill any running processes"""
        self._stop_requested = True
        for process in self._current_processes.values():
            try:
                process.kill()
            except:
                pass
    
    def reset(self):
        """Reset the evaluator state"""
        self._stop_requested = False
        self.cleanup()
    
    def setup_parallel(self, thread_count=4):
        """Set up parallel evaluation"""
        self.cleanup()  # Clean up any existing parallel evaluator
        self._parallel_evaluator = ParallelEvaluator(thread_count)
        self._parallel_evaluator.start_threads()
    
    def schedule_evaluation(self, contestant, problem, callback=None):
        """Schedule a submission evaluation task"""
        if self._parallel_evaluator:
            self._parallel_evaluator.add_task(
                func=self.evaluate_submission,
                args=(contestant, problem),  # Only pass contestant and problem as args
                callback=callback  # Pass callback separately
            )
    
    def wait_for_evaluations(self):
        """Wait for all scheduled evaluations to complete"""
        if self._parallel_evaluator:
            self._parallel_evaluator.wait_completion()
    
    def stop_evaluations(self):
        """Stop all ongoing evaluations"""
        self._stop_requested = True
        if self._parallel_evaluator:
            self._parallel_evaluator.stop_all()
    
    def cleanup(self):
        """Clean up resources"""
        if self._parallel_evaluator:
            self._parallel_evaluator.stop_all()
            self._parallel_evaluator = None
    
    def evaluate_all(self, 
                    contestants: List[Contestant], 
                    problems: List[Problem],
                    result_callback: Callable[[SubmissionResult], None] = None,
                    use_threads: bool = False,
                    threads: int = 1) -> Dict[Tuple[str, str], SubmissionResult]:
        """
        Evaluate all contestants' solutions for all problems
        
        Args:
            contestants: List of contestants
            problems: List of problems
            result_callback: Function to call with each result
            use_threads: Whether to use parallel processing
            threads: Number of threads to use
            
        Returns:
            Dictionary mapping (contestant_id, problem_id) to SubmissionResult
        """
        results = {}
        
        if use_threads and threads > 1:
            from app.core.parallel import ParallelEvaluator
            parallel = ParallelEvaluator(self, threads)
            results = parallel.evaluate_all(contestants, problems, result_callback)
        else:
            # Sequential evaluation - contestant first approach
            for contestant in contestants:
                for problem in problems:
                    if self._stop_requested:
                        return results
                        
                    result = self.evaluate_submission(contestant, problem)
                    results[(contestant.id, problem.id)] = result
                    
                    if result_callback:
                        result_callback(result)
        
        return results
    
    def evaluate_submission(self, contestant: Contestant, problem: Problem) -> SubmissionResult:
        """Evaluate a single contestant's solution for a problem"""
        if self._stop_requested:
            return None

        result = SubmissionResult(contestant.id, problem.id)
        
        print(f"\nEvaluating submission: {contestant.id}/{problem.id}")
        
        if not contestant.has_solution_for(problem.id):
            print(f"No solution found for {contestant.id}/{problem.id}")
            result.status = SubmissionStatus.PENDING
            return result
        
        solution_path = contestant.get_solution_path(problem.id)
        print(f"Solution path: {solution_path}")
        
        problem_settings = self.settings.get_problem_settings(problem.id)
        
        # Ensure test cases are loaded
        if not problem.test_cases:
            print(f"Loading test cases for {problem.id}...")
            problem.load_test_cases()
        
        if not problem.test_cases:
            print(f"ERROR: No test cases found for problem {problem.id}")
            result.status = SubmissionStatus.PENDING
            return result
        
        print(f"Found {len(problem.test_cases)} test cases")
        weights = [tc.weight for tc in problem.test_cases]
        
        # Compile if needed - using Compiler module
        if solution_path.endswith('.c') or solution_path.endswith('.cpp'):
            compile_result = Compiler.compile(solution_path)
            if compile_result is not True:
                # Compilation failed
                result.test_case_results.append(TestCaseResult(
                    status=SubmissionStatus.COMPILATION_ERROR,
                    execution_time=0,
                    memory_used=0,
                    error_message=compile_result
                ))
                result.status = SubmissionStatus.COMPILATION_ERROR
                return result
        
        # Define a partial results callback
        partial_result_callback = getattr(self, 'partial_result_callback', None)
        
        # Run against each test case
        total_test_cases = len(problem.test_cases)
        for i, test_case in enumerate(problem.test_cases):
            if self._stop_requested:
                break
                
            # Run test case using TestRunner module
            tc_result = TestRunner.run_test_case(solution_path, test_case, problem_settings, problem.id)
            result.test_case_results.append(tc_result)
            
            # Issue debug information to help diagnose the problem
            print(f"Test case {i+1}/{total_test_cases} for {contestant.id}/{problem.id}: {tc_result.status.value}")
            
            if self.test_case_callback:
                self.test_case_callback(contestant.id, problem.id, i + 1, total_test_cases)
            
            # Calculate partial score and report after each test case
            if partial_result_callback and len(result.test_case_results) > 0:
                partial_weights = [tc.weight for tc in problem.test_cases[:i+1]]
                result.calculate_score(partial_weights)
                partial_result_callback(result, is_partial=True)
        
        # Make sure we have test cases and calculate final score
        if len(result.test_case_results) > 0:
            result.calculate_score(weights)
            print(f"Final status for {contestant.id}/{problem.id}: {result.status.value} (Score: {result.score}/{result.max_score})")
        else:
            result.status = SubmissionStatus.PENDING
            print(f"Warning: No test cases run for {contestant.id}/{problem.id}")
        
        return result