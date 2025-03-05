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

# Conditionally import resource module (only available on Unix)
if platform.system() != 'Windows':
    import resource

from app.models.contestant import Contestant
from app.models.problem import Problem, TestCase
from app.models.submission import SubmissionResult, TestCaseResult, SubmissionStatus
from app.models.settings import Settings, ProblemSettings

class Evaluator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._stop_requested = False
        self._current_processes = {}  # track running processes
        self.test_case_callback = None
    
    def stop(self):
        """Stop all evaluations and kill any running processes"""
        self._stop_requested = True
        for process in self._current_processes.values():
            try:
                process.kill()
            except:
                pass
    
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
        
        # Compile if needed
        if solution_path.endswith('.c') or solution_path.endswith('.cpp'):
            compile_result = self._compile(solution_path)
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
        
        # Run against each test case
        total_test_cases = len(problem.test_cases)
        for i, test_case in enumerate(problem.test_cases):
            if self._stop_requested:
                break
                
            tc_result = self._run_test_case(solution_path, test_case, problem_settings)
            result.test_case_results.append(tc_result)
            
            # Issue debug information to help diagnose the problem
            print(f"Test case {i+1}/{total_test_cases} for {contestant.id}/{problem.id}: {tc_result.status.value}")
            
            if self.test_case_callback:
                self.test_case_callback(contestant.id, problem.id, i + 1, total_test_cases)
        
        # Make sure we have test cases and calculate score
        if len(result.test_case_results) > 0:
            result.calculate_score(weights)
            print(f"Final status for {contestant.id}/{problem.id}: {result.status.value} (Score: {result.score}/{result.max_score})")
        else:
            result.status = SubmissionStatus.PENDING
            print(f"Warning: No test cases run for {contestant.id}/{problem.id}")
        
        return result
    
    def _compile(self, solution_path: str) -> bool or str:
        """Compile the solution if needed"""
        ext = os.path.splitext(solution_path)[1]
        executable_path = os.path.splitext(solution_path)[0]
        
        # Platform-specific executable extension
        if platform.system() == 'Windows':
            executable_path += '.exe'
        
        try:
            if ext == '.c':
                # Use platform-appropriate compiler flags
                compile_cmd = ['gcc', solution_path, '-o', executable_path]
                if platform.system() != 'Windows':
                    compile_cmd.append('-lm')  # Link math library on Unix
                
                process = subprocess.run(
                    compile_cmd,
                    capture_output=True, text=True
                )
            elif ext == '.cpp':
                compile_cmd = ['g++', '-std=c++20', solution_path, '-o', executable_path]
                if platform.system() != 'Windows':
                    compile_cmd.append('-lm')
                
                process = subprocess.run(
                    compile_cmd,
                    capture_output=True, text=True
                )
            else:
                # No compilation needed
                return True
                
            if process.returncode != 0:
                return process.stderr
            return True
        except Exception as e:
            return str(e)
    
    def _run_test_case(self, solution_path: str, test_case: TestCase, settings: ProblemSettings) -> TestCaseResult:
        """Run the solution against a test case and return results"""
        try:
            # Determine how to run the program
            ext = os.path.splitext(solution_path)[1]
            cmd = []
            
            if ext == '.py':
                cmd = ['python', solution_path]
            elif ext == '.java':
                cmd = ['java', solution_path]
            elif ext in ['.c', '.cpp']:
                executable_path = os.path.splitext(solution_path)[0]
                if os.name == 'nt':  # Windows
                    executable_path += '.exe'
                cmd = [executable_path]
            else:
                return TestCaseResult(
                    status=SubmissionStatus.RUNTIME_ERROR,
                    execution_time=0,
                    memory_used=0,
                    error_message=f"Unsupported file extension: {ext}"
                )
            
            # Read input
            with open(test_case.input_path, 'r') as f:
                input_data = f.read()
            
            # Read expected output
            with open(test_case.output_path, 'r') as f:
                expected_output = f.read().strip()
            
            # Run the solution
            start_time = time.time()
            temp_in_path = None
            
            # Create a timer thread to force kill after time limit
            kill_timer = None
            def kill_on_timeout():
                try:
                    if process and process.poll() is None:
                        process.kill()
                        print(f"Process killed due to timeout: {solution_path}")
                except Exception as e:
                    print(f"Error killing process: {e}")
            
            try:
                # Handle large inputs to prevent blocking
                input_size = len(input_data)
                if input_size > 1024*1024:  # If input > 1MB
                    # Write input to a temporary file instead
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_in:
                        temp_in.write(input_data)
                        temp_in_path = temp_in.name
                    
                    # Start process with input from file
                    process = subprocess.Popen(
                        cmd,
                        stdin=open(temp_in_path, 'r'),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                else:
                    # Start process with direct input
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                
                self._current_processes[solution_path] = process
                
                # Track memory usage
                max_memory = 0
                memory_thread_stop = threading.Event()
                
                def memory_monitor():
                    nonlocal max_memory
                    try:
                        while not memory_thread_stop.is_set():
                            try:
                                proc = psutil.Process(process.pid)
                                mem_info = proc.memory_info()
                                max_memory = max(max_memory, mem_info.rss / (1024 * 1024))  # Convert to MB
                            except:
                                pass
                            time.sleep(0.05)  # Check every 50ms
                    except:
                        pass
                
                # Start memory monitoring thread
                memory_thread = threading.Thread(target=memory_monitor)
                memory_thread.daemon = True  # Make it a daemon thread
                memory_thread.start()
                
                # Start kill timer thread with extra margin
                timeout = settings.time_limit * 1.2  # 20% margin
                kill_timer = threading.Timer(timeout, kill_on_timeout)
                kill_timer.daemon = True
                kill_timer.start()
                
                # Communicate with process
                if input_size > 1024*1024:
                    # Process already has input from file
                    stdout, stderr = process.communicate(timeout=settings.time_limit)
                else:
                    # Send input directly
                    stdout, stderr = process.communicate(input=input_data, timeout=settings.time_limit)
                
                # Cancel timer if process completed
                kill_timer.cancel()
                
                # Stop memory monitoring
                memory_thread_stop.set()
                memory_thread.join(0.1)  # Don't block for too long
                
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                print(f"Time limit exceeded: {solution_path}")
                
                memory_thread_stop.set()
                memory_thread.join(0.1)
                
                if solution_path in self._current_processes:
                    del self._current_processes[solution_path]
                
                return TestCaseResult(
                    status=SubmissionStatus.TIME_LIMIT_EXCEEDED,
                    execution_time=settings.time_limit,
                    memory_used=max_memory,
                    error_message="Time limit exceeded",
                    input_excerpt=input_data[:100] + "..." if len(input_data) > 100 else input_data,
                    expected_output=expected_output[:100] + "..." if len(expected_output) > 100 else expected_output,
                    actual_output=""
                )
                
            finally:
                # Clean up temporary file if used
                if temp_in_path and os.path.exists(temp_in_path):
                    try:
                        os.unlink(temp_in_path)
                    except:
                        pass
                
                # Ensure timer is canceled if still running
                if kill_timer and kill_timer.is_alive():
                    kill_timer.cancel()
            
            execution_time = time.time() - start_time
            
            if solution_path in self._current_processes:
                del self._current_processes[solution_path]
            
            # Check memory limit
            if max_memory > settings.memory_limit:
                return TestCaseResult(
                    status=SubmissionStatus.MEMORY_LIMIT_EXCEEDED,
                    execution_time=execution_time,
                    memory_used=max_memory,
                    error_message="Memory limit exceeded",
                    input_excerpt=input_data[:100] + "..." if len(input_data) > 100 else input_data,
                    expected_output=expected_output[:100] + "..." if len(expected_output) > 100 else expected_output,
                    actual_output=stdout[:100] + "..." if len(stdout) > 100 else stdout
                )
            
            # Check for runtime error
            if process.returncode != 0:
                return TestCaseResult(
                    status=SubmissionStatus.RUNTIME_ERROR,
                    execution_time=execution_time,
                    memory_used=max_memory,
                    error_message=stderr,
                    input_excerpt=input_data[:100] + "..." if len(input_data) > 100 else input_data,
                    expected_output=expected_output[:100] + "..." if len(expected_output) > 100 else expected_output,
                    actual_output=stdout[:100] + "..." if len(stdout) > 100 else stdout
                )
            
            # Check output
            actual_output = stdout.strip()
            if self._compare_output(actual_output, expected_output):
                return TestCaseResult(
                    status=SubmissionStatus.CORRECT,
                    execution_time=execution_time,
                    memory_used=max_memory,
                    input_excerpt=input_data[:100] + "..." if len(input_data) > 100 else input_data,
                    expected_output=expected_output[:100] + "..." if len(expected_output) > 100 else expected_output,
                    actual_output=actual_output[:100] + "..." if len(actual_output) > 100 else actual_output
                )
            else:
                return TestCaseResult(
                    status=SubmissionStatus.WRONG_ANSWER,
                    execution_time=execution_time,
                    memory_used=max_memory,
                    input_excerpt=input_data[:100] + "..." if len(input_data) > 100 else input_data,
                    expected_output=expected_output[:100] + "..." if len(expected_output) > 100 else expected_output,
                    actual_output=actual_output[:100] + "..." if len(actual_output) > 100 else actual_output
                )
        
        except Exception as e:
            # Handle any errors
            return TestCaseResult(
                status=SubmissionStatus.RUNTIME_ERROR,
                execution_time=0,
                memory_used=0,
                error_message=str(e),
                input_excerpt="",
                expected_output="",
                actual_output=""
            )
    
    def _compare_output(self, actual: str, expected: str) -> bool:
        """Compare actual and expected output, ignoring whitespace differences"""
        actual_lines = actual.strip().split('\n')
        expected_lines = expected.strip().split('\n')
        
        if len(actual_lines) != len(expected_lines):
            return False
        
        for a_line, e_line in zip(actual_lines, expected_lines):
            if a_line.strip() != e_line.strip():
                return False
                
        return True
