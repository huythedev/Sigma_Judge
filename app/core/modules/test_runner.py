import os
import time
import platform
from app.models.submission import TestCaseResult, SubmissionStatus
from app.models.settings import ProblemSettings
from app.models.problem import TestCase
from .file_io_detector import FileIODetector
from .process_manager import ProcessManager

class TestRunner:
    """Module for running test cases on solutions"""
    
    @staticmethod
    def run_test_case(solution_path: str, test_case: TestCase, settings: ProblemSettings, 
                     problem_id: str = None, io_details: dict = None) -> TestCaseResult:
        """
        Run the solution against a test case and return results
        
        Args:
            solution_path: Path to the solution
            test_case: Test case to run
            settings: Problem settings
            problem_id: ID of the problem
            io_details: Cached I/O details (optional)
            
        Returns:
            TestCaseResult object containing the results
        """
        try:
            # Get file extension
            ext = os.path.splitext(solution_path)[1]
            
            # Configure command based on file extension
            cmd = TestRunner._get_command_for_solution(solution_path, ext)
            if not cmd:
                return TestCaseResult(
                    status=SubmissionStatus.RUNTIME_ERROR,
                    execution_time=0,
                    memory_used=0,
                    error_message=f"Unsupported file extension: {ext}"
                )
            
            # Detect file I/O patterns (or use cached details)
            if io_details is None:
                io_details = FileIODetector.detect_file_io(solution_path, problem_id)
                
            io_mode = getattr(settings, 'io_mode', 'auto')
            
            # Check if I/O patterns are compatible with mode setting
            if not TestRunner._check_io_compatibility(io_details, io_mode):
                return TestCaseResult(
                    status=SubmissionStatus.RUNTIME_ERROR,
                    execution_time=0,
                    memory_used=0,
                    error_message=TestRunner._get_incompatibility_error(io_details, io_mode),
                    input_excerpt="",
                    expected_output="",
                    actual_output=""
                )
            
            # Read input and expected output
            input_data, expected_output = TestRunner._read_test_files(test_case)
            
            # Prepare running environment
            run_config = TestRunner._prepare_run_config(solution_path, io_details, io_mode, input_data)
            
            # Run the solution with monitoring
            stdout, stderr, execution_time, max_memory, returncode = ProcessManager.run_with_memory_monitoring(
                cmd=cmd,
                input_data=run_config['input_data'],
                timeout=settings.time_limit,
                cwd=os.path.dirname(solution_path),
                stdin_file=run_config['stdin_file'],
                use_stdin_pipe=run_config['use_stdin_pipe'],
                temp_files=run_config['temp_files']
            )
            
            # Handle timeout case
            if returncode == -1 and execution_time >= settings.time_limit:
                return TestCaseResult(
                    status=SubmissionStatus.TIME_LIMIT_EXCEEDED,
                    execution_time=settings.time_limit,
                    memory_used=max_memory,
                    error_message="Time limit exceeded",
                    input_excerpt=input_data[:100] + "..." if len(input_data) > 100 else input_data,
                    expected_output=expected_output[:100] + "..." if len(expected_output) > 100 else expected_output,
                    actual_output=""
                )
            
            # Get actual output (either from file or stdout)
            actual_output = TestRunner._get_actual_output(
                stdout, run_config['output_file'], io_details, io_mode
            )
            
            # Check memory limit
            if max_memory > settings.memory_limit:
                return TestCaseResult(
                    status=SubmissionStatus.MEMORY_LIMIT_EXCEEDED,
                    execution_time=execution_time,
                    memory_used=max_memory,
                    error_message="Memory limit exceeded",
                    input_excerpt=input_data[:100] + "..." if len(input_data) > 100 else input_data,
                    expected_output=expected_output[:100] + "..." if len(expected_output) > 100 else expected_output,
                    actual_output=actual_output[:100] + "..." if len(actual_output) > 100 else actual_output
                )
            
            # Check for runtime error
            if returncode != 0:
                return TestCaseResult(
                    status=SubmissionStatus.RUNTIME_ERROR,
                    execution_time=execution_time,
                    memory_used=max_memory,
                    error_message=stderr,
                    input_excerpt=input_data[:100] + "..." if len(input_data) > 100 else input_data,
                    expected_output=expected_output[:100] + "..." if len(expected_output) > 100 else expected_output,
                    actual_output=actual_output[:100] + "..." if len(actual_output) > 100 else actual_output
                )
            
            # Check output correctness
            if TestRunner._compare_output(actual_output, expected_output):
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
            import traceback
            traceback.print_exc()
            return TestCaseResult(
                status=SubmissionStatus.RUNTIME_ERROR,
                execution_time=0,
                memory_used=0,
                error_message=str(e),
                input_excerpt="",
                expected_output="",
                actual_output=""
            )
    
    @staticmethod
    def _get_command_for_solution(solution_path: str, ext: str) -> list:
        """Get the command to run a solution based on file extension"""
        if ext == '.py':
            return ['python', solution_path]
        elif ext == '.java':
            return ['java', solution_path]
        elif ext in ['.c', '.cpp']:
            executable_path = os.path.splitext(solution_path)[0]
            if os.name == 'nt':  # Windows
                executable_path += '.exe'
            return [executable_path]
        else:
            return None  # Unsupported extension
    
    @staticmethod
    def _check_io_compatibility(io_details: dict, io_mode: str) -> bool:
        """Check if IO details are compatible with the specified IO mode"""
        # Extract information from io_details
        uses_file_io = bool(io_details.get('input'))
        is_adaptive = io_details.get('adaptive', False)
        
        # Adaptive programs are always compatible (they can adjust)
        if is_adaptive:
            return True
            
        # For non-adaptive programs, check compatibility
        if io_mode == "standard" and uses_file_io:
            return False  # Non-adaptive file IO program can't run in standard mode
        elif io_mode == "file" and not uses_file_io:
            return False  # Standard IO program can't run in file mode
            
        return True
    
    @staticmethod
    def _get_incompatibility_error(io_details: dict, io_mode: str) -> str:
        """Get error message for incompatible IO mode"""
        uses_file_io = bool(io_details.get('input'))
        io_methods = io_details.get('methods', [])
        input_file_name = io_details.get('input')
        output_file_name = io_details.get('output')
        
        if io_mode == "standard" and uses_file_io:
            return (f"Program uses file I/O ({', '.join(io_methods)}) but standard I/O mode is enabled. "
                    f"Files used: Input={input_file_name}, Output={output_file_name}")
        elif io_mode == "file" and not uses_file_io:
            return "Program uses standard I/O but file I/O mode is enabled"
            
        return "Unknown IO compatibility issue"
    
    @staticmethod
    def _read_test_files(test_case: TestCase) -> tuple:
        """Read input and expected output from test case files"""
        # Read input
        with open(test_case.input_path, 'r') as f:
            input_data = f.read()
        
        # Read expected output
        with open(test_case.output_path, 'r') as f:
            expected_output = f.read().strip()
            
        return input_data, expected_output
    
    @staticmethod
    def _prepare_run_config(solution_path: str, io_details: dict, io_mode: str, input_data: str) -> dict:
        """
        Prepare configuration for running the solution
        """
        config = {
            'input_data': None,         # Data to send to stdin
            'temp_files': [],           # Files to clean up
            'stdin_file': None,         # File to use as stdin
            'use_stdin_pipe': True,     # Whether to use stdin pipe
            'output_file': None         # Output file to read from
        }
        
        # Extract information
        uses_file_io = bool(io_details.get('input'))
        input_file_name = io_details.get('input')
        output_file_name = io_details.get('output')
        io_methods = io_details.get('methods', [])
        is_adaptive = io_details.get('adaptive', False)
        name_macro = io_details.get('name_macro')
        
        # Get solution directory
        solution_dir = os.path.dirname(solution_path)
        
        # Special handling for adaptive programs - always use file IO for adaptive programs
        # even in standard mode, since they'll fall back to stdin/stdout if files don't exist
        if is_adaptive:
            print(f"Handling adaptive program with special logic")
            
            # Create the input file
            temp_in_path = os.path.join(solution_dir, input_file_name)
            with open(temp_in_path, 'w') as f:
                f.write(input_data)
            print(f"Created input file for adaptive program: {temp_in_path}")
            config['temp_files'].append(temp_in_path)
            
            # Configure output file path
            if output_file_name:
                temp_out_path = os.path.join(solution_dir, output_file_name)
                # Remove existing output file if any
                if os.path.exists(temp_out_path):
                    os.remove(temp_out_path)
                config['output_file'] = temp_out_path
                print(f"Set output file path: {temp_out_path}")
            
            # For adaptive programs with direct fopen check, we need to ensure stdin still works
            # as some programs may use both methods depending on file existence
            config['input_data'] = input_data
            config['use_stdin_pipe'] = True
            print(f"Also providing stdin input for adaptive program (dual I/O capability)")
            
            return config
        
        # Non-adaptive program handling
        if io_mode == "standard":
            config['input_data'] = input_data
            config['use_stdin_pipe'] = True
            print(f"Using standard IO mode (pipe stdin)")
            
        elif io_mode == "file" or (io_mode == "auto" and uses_file_io):
            # Create the input file
            temp_in_path = os.path.join(solution_dir, input_file_name)
            with open(temp_in_path, 'w') as f:
                f.write(input_data)
            print(f"Created input file: {temp_in_path}")
            config['temp_files'].append(temp_in_path)
            
            # Configure output file path
            if output_file_name:
                temp_out_path = os.path.join(solution_dir, output_file_name)
                # Remove existing output file if any
                if os.path.exists(temp_out_path):
                    os.remove(temp_out_path)
                config['output_file'] = temp_out_path
                
            # Configure stdin based on whether the program uses freopen
            if 'freopen_stdin' in io_methods:
                # For freopen, we still use stdin pipe but send empty input
                config['input_data'] = ""
                config['use_stdin_pipe'] = True
                print("Program uses freopen for stdin, sending empty input")
            else:
                # For normal file IO, don't use stdin
                config['use_stdin_pipe'] = False
                print("Program uses direct file IO, not using stdin pipe")
        else:
            # Default to standard IO for any other mode
            config['input_data'] = input_data
            config['use_stdin_pipe'] = True
            
        return config
    
    @staticmethod
    def _get_actual_output(stdout: str, output_file: str, io_details: dict, io_mode: str) -> str:
        """Get the actual output from either file or stdout"""
        is_adaptive = io_details.get('adaptive', False)
        result_output = ""
        
        # If we have an output file path and it exists, read from there first
        if output_file and os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    file_output = f.read().strip()
                    if file_output:  # Only use file output if it's not empty
                        print(f"Reading output from file: {output_file} ({len(file_output)} bytes)")
                        result_output = file_output
                    else:
                        print(f"Output file exists but is empty")
            except Exception as e:
                print(f"Error reading output file: {str(e)}")
        
        # For adaptive programs or if file output was empty, also check stdout
        if not result_output or is_adaptive:
            stdout_output = stdout.strip()
            if stdout_output:
                print(f"Found output in stdout ({len(stdout_output)} bytes)")
                if not result_output:  # Only use stdout if we don't have file output
                    result_output = stdout_output
                elif len(stdout_output) > len(result_output):
                    # If stdout has more content, use that instead
                    print(f"Using stdout output which is longer than file output")
                    result_output = stdout_output
        
        # If we still have no output, use whatever is available
        if not result_output:
            if stdout.strip():
                print(f"Using stdout as fallback ({len(stdout.strip())} bytes)")
                result_output = stdout.strip()
            elif output_file and os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    file_output = f.read().strip()
                    print(f"Using file output as fallback ({len(file_output)} bytes)")
                    result_output = file_output
            else:
                print(f"WARNING: No output found in either stdout or file!")
                
        return result_output
        
    @staticmethod
    def _compare_output(actual: str, expected: str) -> bool:
        """Compare actual and expected output, ignoring whitespace differences"""
        actual_lines = actual.strip().split('\n')
        expected_lines = expected.strip().split('\n')
        
        if len(actual_lines) != len(expected_lines):
            return False
        
        for a_line, e_line in zip(actual_lines, expected_lines):
            if a_line.strip() != e_line.strip():
                return False
                
        return True