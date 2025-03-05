import os
import tempfile
from typing import Dict, List, Tuple
from app.models.problem import Problem, TestCase
from app.models.submission import SubmissionResult, TestCaseResult, SubmissionStatus
from app.models.settings import ProblemSettings
from .compiler import Compiler
from .test_runner import TestRunner

class Processor:
    """Process submissions with intelligent cache management"""
    
    # Cache to avoid repeated detection of file I/O patterns
    _file_io_cache = {}
    
    # Cache for successful compilations
    _compilation_cache = {}
    
    @staticmethod
    def process_submission(solution_path: str, problem: Problem, problem_settings: ProblemSettings) -> SubmissionResult:
        """
        Process a submission against all test cases
        
        Args:
            solution_path: Path to the solution file
            problem: Problem object with test cases
            problem_settings: Problem settings
            
        Returns:
            SubmissionResult object with results for all test cases
        """
        # Create submission result
        result = SubmissionResult(os.path.basename(os.path.dirname(solution_path)), problem.id)
        
        # Compile if needed
        if solution_path.endswith(('.c', '.cpp')):
            # Check if already compiled successfully
            if solution_path not in Processor._compilation_cache:
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
                
                # Cache successful compilation
                Processor._compilation_cache[solution_path] = True
        
        # Cache file I/O detection
        if solution_path not in Processor._file_io_cache:
            io_details = FileIODetector.detect_file_io(solution_path, problem.id)
            Processor._file_io_cache[solution_path] = io_details
        
        # Process each test case
        for test_case in problem.test_cases:
            # Use cached I/O details for TestRunner
            tc_result = TestRunner.run_test_case(
                solution_path, 
                test_case, 
                problem_settings, 
                problem.id,
                io_details=Processor._file_io_cache.get(solution_path)
            )
            result.test_case_results.append(tc_result)
        
        # Calculate score
        weights = [tc.weight for tc in problem.test_cases]
        if result.test_case_results:
            result.calculate_score(weights)
        else:
            result.status = SubmissionStatus.PENDING
        
        return result
    
    @staticmethod
    def clear_caches():
        """Clear all caches"""
        Processor._file_io_cache.clear()
        Processor._compilation_cache.clear()
