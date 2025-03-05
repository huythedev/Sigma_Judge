import os
import re

class FileIODetector:
    """Module for detecting file I/O patterns in source code"""
    
    @staticmethod
    def detect_file_io(solution_path: str, problem_id: str = None) -> dict:
        """
        Detect if the solution uses file I/O and return the input/output file names
        
        Args:
            solution_path: Path to the solution file
            problem_id: ID of the problem, used for default file names
        
        Returns:
            Dictionary with 'input', 'output' keys and additional 'methods' list
        """
        result = {
            'input': None, 
            'output': None,
            'methods': [],
            'input_methods': [],
            'output_methods': [],
            'conditional_io': False,  # Flag to indicate if file I/O is conditional
            'adaptive': False         # Flag for programs that adapt to environment
        }
        
        # Only check C/C++ files for now
        if not solution_path.endswith(('.c', '.cpp')):
            return result
        
        try:
            with open(solution_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # === DETECT NAME MACRO ===
                name_macro = FileIODetector._detect_name_macro(content)
                if name_macro:
                    result['name_macro'] = name_macro
                    
                    # If docfile function is present along with NAME macro, it's definitely adaptive
                    if 'docfile' in content:
                        result['conditional_io'] = True
                        result['adaptive'] = True
                        print(f"Detected NAME+docfile pattern - program adapts to environment")
                
                # === DETECT CONDITIONAL FILE I/O ===
                FileIODetector._detect_conditional_patterns(content, result)
                
                # === DETECT IO METHODS ===
                io_methods = FileIODetector._detect_io_methods(content)
                result.update(io_methods)
                
                # === DETECT FILE NAMES ===
                FileIODetector._detect_file_names(content, result, problem_id, name_macro)
                
                # Print debug summary
                FileIODetector._print_detection_summary(result, solution_path)
                
        except Exception as e:
            print(f"Error detecting file I/O: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    @staticmethod
    def _detect_name_macro(content: str) -> str:
        """Detect #define NAME macro in source code"""
        name_pattern = r'#define\s+NAME\s+["\']([^"\']+)["\']'
        name_match = re.search(name_pattern, content)
        if name_match:
            name_macro = name_match.group(1)
            print(f"Detected NAME macro: {name_macro}")
            return name_macro
        return None
    
    @staticmethod
    def _detect_conditional_patterns(content: str, result: dict):
        """Detect conditional file I/O patterns"""
        conditional_patterns = [
            r'if\s*\(\s*ifstream\s*\(',    # if (ifstream(...))
            r'if\s*\(\s*std::ifstream\s*\(',  # if (std::ifstream(...))
            r'if\s*\(\s*fopen\s*\(',        # if (fopen(...))
            r'if\s*\(.*\.is_open\(\)\)',     # if (file.is_open())
            r'if\s*\(\s*fopen\s*\(\s*NAME\s*"[^"]+"\s*,',  # if (fopen(NAME".INP", "r"))
            r'if\s*\(\s*fopen\s*\(\s*NAME\s*\'[^\']+\'\s*,' # if (fopen(NAME'.INP', 'r'))
        ]
        
        for pattern in conditional_patterns:
            if re.search(pattern, content):
                result['conditional_io'] = True
                result['adaptive'] = True
                print(f"Detected conditional file I/O pattern: {pattern}")
                break
        
        # Detect docfile pattern
        if re.search(r'void\s+docfile\s*\(\s*\)', content) and 'freopen' in content:
            result['conditional_io'] = True
            result['adaptive'] = True
            print("Detected docfile() pattern - program adapts to environment")
    
    @staticmethod
    def _detect_io_methods(content: str) -> dict:
        """Detect which I/O methods are used in the code"""
        result = {
            'methods': [],
            'input_methods': [],
            'output_methods': []
        }
        
        # Detect various methods
        uses_ifstream = 'ifstream' in content or 'std::ifstream' in content
        uses_ofstream = 'ofstream' in content or 'std::ofstream' in content
        uses_fstream = 'fstream' in content or 'std::fstream' in content
        uses_freopen_in = re.search(r'freopen\s*\([^,]+,\s*["\']\w+["\']\s*,\s*stdin\s*\)', content) is not None
        uses_freopen_out = re.search(r'freopen\s*\([^,]+,\s*["\']\w+["\']\s*,\s*stdout\s*\)', content) is not None
        uses_fopen = 'fopen' in content
        
        # Record methods in result
        if uses_ifstream:
            result['methods'].append('ifstream')
            result['input_methods'].append('ifstream')
        if uses_ofstream:
            result['methods'].append('ofstream')
            result['output_methods'].append('ofstream')
        if uses_fstream:
            result['methods'].append('fstream')
            result['input_methods'].append('fstream')
            result['output_methods'].append('fstream')
        if uses_freopen_in:
            result['methods'].append('freopen_stdin')
            result['input_methods'].append('freopen_stdin')
        if uses_freopen_out:
            result['methods'].append('freopen_stdout')
            result['output_methods'].append('freopen_stdout')
        if uses_fopen:
            result['methods'].append('fopen')
        
        return result
    
    @staticmethod
    def _detect_file_names(content: str, result: dict, problem_id: str = None, name_macro: str = None):
        """Detect input and output file names"""
        # Methods extracted from result for convenience
        methods = result.get('methods', [])
        input_methods = result.get('input_methods', [])
        output_methods = result.get('output_methods', [])
        
        # Flag to check if we're using any file I/O methods
        uses_ifstream = 'ifstream' in input_methods
        uses_ofstream = 'ofstream' in output_methods
        uses_fstream = 'fstream' in methods
        uses_freopen_in = 'freopen_stdin' in input_methods
        uses_freopen_out = 'freopen_stdout' in output_methods
        uses_fopen = 'fopen' in methods
        
        # === PRIORITY 1: Detect freopen since it redirects stdin/stdout ===
        if uses_freopen_in or uses_freopen_out:
            freopen_in_pattern = r'freopen\s*\(\s*["\']([^"\']+)["\'].*?,\s*["\']\w+["\']\s*,\s*stdin\s*\)'
            freopen_out_pattern = r'freopen\s*\(\s*["\']([^"\']+)["\'].*?,\s*["\']\w+["\']\s*,\s*stdout\s*\)'
            
            # Look for freopen calls
            for match in re.finditer(freopen_in_pattern, content):
                result['input'] = match.group(1)
                print(f"Detected freopen stdin redirect to: {result['input']}")
                break
            
            for match in re.finditer(freopen_out_pattern, content):
                result['output'] = match.group(1)
                print(f"Detected freopen stdout redirect to: {result['output']}")
                break
        
        # === PRIORITY 2: If no freopen found, check for C++ streams ===
        if not result['input'] and (uses_ifstream or uses_fstream):
            FileIODetector._detect_cpp_stream_input(content, result)
                
        # Similarly for output streams
        if not result['output'] and (uses_ofstream or uses_fstream):
            FileIODetector._detect_cpp_stream_output(content, result)
        
        # === PRIORITY 3: Check for competitive programming macros ===
        if not result['input'] or not result['output']:
            FileIODetector._detect_define_macros(content, result)
        
        # === PRIORITY 4: Check for direct fopen calls ===
        if (not result['input'] or not result['output']) and uses_fopen:
            FileIODetector._detect_fopen_calls(content, result)
        
        # === PRIORITY 5: Use NAME macro or problem ID for default filenames ===
        FileIODetector._set_default_file_names(result, name_macro, problem_id, uses_ifstream, uses_ofstream, uses_freopen_in, uses_freopen_out, uses_fopen)

    @staticmethod
    def _detect_cpp_stream_input(content: str, result: dict):
        """Detect C++ stream input file patterns"""
        patterns = [
            r'ifstream\s+\w+\s*\(\s*["\']([^"\']+)["\']',  # ifstream x("file.txt")
            r'std::ifstream\s+\w+\s*\(\s*["\']([^"\']+)["\']',  # std::ifstream x("file.txt")
            r'ifstream\s+\w+\s*{\s*["\']([^"\']+)["\']',  # ifstream x{"file.txt"} (C++11)
            r'fstream\s+\w+\s*\(\s*["\']([^"\']+)["\'].*\)',  # fstream x("file.txt", mode)
        ]
        
        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                result['input'] = match.group(1)
                print(f"Detected C++ stream input file: {result['input']}")
                break
                
        # Check for open method calls if no file found yet
        if not result['input']:
            open_pattern = r'\.\s*open\s*\(\s*["\']([^"\']+)["\']'
            open_match = re.search(open_pattern, content)
            if open_match:
                result['input'] = open_match.group(1)
                print(f"Detected stream.open() input file: {result['input']}")
    
    @staticmethod
    def _detect_cpp_stream_output(content: str, result: dict):
        """Detect C++ stream output file patterns"""
        patterns = [
            r'ofstream\s+\w+\s*\(\s*["\']([^"\']+)["\']',
            r'std::ofstream\s+\w+\s*\(\s*["\']([^"\']+)["\']',
            r'ofstream\s+\w+\s*{\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                result['output'] = match.group(1)
                print(f"Detected C++ stream output file: {result['output']}")
                break
    
    @staticmethod
    def _detect_define_macros(content: str, result: dict):
        """Detect #define macros for input/output files"""
        define_in_pattern = r'#define\s+\w+\s+["\']([^"\']+)["\']'
        define_matches = re.finditer(define_in_pattern, content)
        
        for match in define_matches:
            define_name = match.group(0).split()[1].strip()
            filename = match.group(1)
            
            # Common naming conventions for input/output files
            if define_name.lower() in ('fi', 'in', 'input', 'inputfile'):
                if not result['input']:
                    result['input'] = filename
                    print(f"Detected #define input file: {result['input']}")
            
            elif define_name.lower() in ('fo', 'out', 'output', 'outputfile'):
                if not result['output']:
                    result['output'] = filename
                    print(f"Detected #define output file: {result['output']}")
    
    @staticmethod
    def _detect_fopen_calls(content: str, result: dict):
        """Detect fopen calls for input/output files"""
        fopen_pattern = r'fopen\s*\(\s*["\']([^"\']+)["\'].*,\s*["\'](r|w)["\']'
        fopen_matches = list(re.finditer(fopen_pattern, content))
        
        # Try to determine which is input vs output based on mode
        for match in fopen_matches:
            filename = match.group(1)
            mode = match.group(2)
            
            if mode == 'r' and not result['input']:
                result['input'] = filename
                print(f"Detected fopen input file: {filename}")
            elif mode == 'w' and not result['output']:
                result['output'] = filename
                print(f"Detected fopen output file: {filename}")
    
    @staticmethod
    def _set_default_file_names(result: dict, name_macro: str, problem_id: str, 
                               uses_ifstream: bool, uses_ofstream: bool, 
                               uses_freopen_in: bool, uses_freopen_out: bool, 
                               uses_fopen: bool):
        """Set default file names based on detected methods, NAME macro, or problem ID"""
        # Input file
        if not result['input'] and (uses_ifstream or uses_freopen_in or uses_fopen):
            if name_macro:
                # Use NAME.INP as defined in the macro
                result['input'] = f"{name_macro}.INP"
                print(f"Using NAME macro for input file: {result['input']}")
            elif problem_id:
                # Use problem_id.INP as standard competition format
                result['input'] = f"{problem_id}.INP"
                print(f"Using competition format input: {result['input']}")
            else:
                # Fallback to input.txt
                result['input'] = 'input.txt'
                print("Using default input.txt (no problem ID provided)")
        
        # Output file
        if not result['output'] and (uses_ofstream or uses_freopen_out or uses_fopen):
            if name_macro:
                # Use NAME.OUT as defined in the macro
                result['output'] = f"{name_macro}.OUT"
                print(f"Using NAME macro for output file: {result['output']}")
            elif problem_id:
                # Use problem_id.OUT as standard competition format
                result['output'] = f"{problem_id}.OUT"
                print(f"Using competition format output: {result['output']}")
            else:
                # Fallback to output.txt
                result['output'] = 'output.txt'
                print("Using default output.txt (no problem ID provided)")
    
    @staticmethod
    def _print_detection_summary(result: dict, solution_path: str):
        """Print a summary of detected I/O methods and file names"""
        method_summary = ', '.join(result['methods']) if result['methods'] else 'none detected'
        input_methods = ', '.join(result['input_methods']) if result['input_methods'] else 'none'
        output_methods = ', '.join(result['output_methods']) if result['output_methods'] else 'none'
        
        print(f"I/O detection summary for {os.path.basename(solution_path)}:")
        print(f"  All methods: {method_summary}")
        print(f"  Input methods: {input_methods}")
        print(f"  Output methods: {output_methods}")
        print(f"  Input file: {result['input']}")
        print(f"  Output file: {result['output']}")
        
        # Important: Don't assume output file if only input methods detected
        if result['input'] and not result['output'] and not result['output_methods']:
            print(f"Note: Program uses file input but likely outputs to stdout")
