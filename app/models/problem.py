from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import os

@dataclass
class TestCase:
    input_path: str
    output_path: str
    weight: float = 1.0  # Weight for scoring

@dataclass
class Problem:
    id: str
    name: str
    directory: str  # Directory containing test cases
    test_cases: List[TestCase] = field(default_factory=list)
    
    def load_test_cases(self):
        """Load test cases from the problem directory"""
        self.test_cases = []
        if not os.path.exists(self.directory):
            print(f"Problem directory not found: {self.directory}")
            return
        
        print(f"\nLoading test cases for problem {self.id}")
        print(f"Scanning directory: {self.directory}")
        
        # Look for different test case organization patterns
        test_cases_found = False
        
        # Pattern 1: Test directories (test01, test02, etc.)
        test_dirs = []
        for item in os.listdir(self.directory):
            item_path = os.path.join(self.directory, item)
            if os.path.isdir(item_path) and (item.lower().startswith('test') or 
                                            item.isdigit() or 
                                            'test' in item.lower()):
                test_dirs.append(item_path)
        
        if test_dirs:
            test_dirs.sort()  # Sort test directories
            print(f"Found {len(test_dirs)} test directories")
            
            # Process each test directory
            for test_dir in test_dirs:
                print(f"Scanning test directory: {test_dir}")
                
                # Try different file naming patterns
                input_file = None
                output_file = None
                
                # Priority 1: Standard competition format: ProblemID.INP/OUT
                pattern1_in = os.path.join(test_dir, f"{self.id}.INP")
                pattern1_out = os.path.join(test_dir, f"{self.id}.OUT")
                if os.path.exists(pattern1_in) and os.path.exists(pattern1_out):
                    input_file = pattern1_in
                    output_file = pattern1_out
                
                # Also check case-insensitive versions
                if not input_file or not output_file:
                    for file in os.listdir(test_dir):
                        file_path = os.path.join(test_dir, file)
                        if file.upper() == f"{self.id}.INP" and not input_file:
                            input_file = file_path
                        elif file.upper() == f"{self.id}.OUT" and not output_file:
                            output_file = file_path
                
                # Pattern 2: input.txt/output.txt (fallback)
                if not input_file or not output_file:
                    pattern2_in = os.path.join(test_dir, "input.txt")
                    pattern2_out = os.path.join(test_dir, "output.txt")
                    if os.path.exists(pattern2_in) and os.path.exists(pattern2_out):
                        input_file = pattern2_in
                        output_file = pattern2_out
                
                # Pattern 3: Case-insensitive search
                if not input_file or not output_file:
                    for file in os.listdir(test_dir):
                        file_path = os.path.join(test_dir, file)
                        if file.upper() == f"{self.id}.INP".upper() or file.lower() == "input.txt":
                            input_file = file_path
                        elif file.upper() == f"{self.id}.OUT".upper() or file.lower() == "output.txt":
                            output_file = file_path
                
                if input_file and output_file:
                    self.test_cases.append(TestCase(
                        input_path=input_file,
                        output_path=output_file
                    ))
                    test_cases_found = True
                    print(f"Found test case: {os.path.basename(test_dir)}")
                    print(f"  Input: {os.path.basename(input_file)}")
                    print(f"  Output: {os.path.basename(output_file)}")
                else:
                    print(f"WARNING: Missing input/output files in {test_dir}")
                    print(f"  Files found: {os.listdir(test_dir)}")
        
        # Pattern 2: Direct files in problem directory
        if not test_cases_found:
            print("No test directories found, looking for direct test files...")
            input_files = []
            output_files = []
            
            # Find all input/output files
            for file in os.listdir(self.directory):
                file_path = os.path.join(self.directory, file)
                if not os.path.isfile(file_path):
                    continue
                    
                if ('input' in file.lower() or 'inp' in file.lower() or 
                    file.lower().endswith('.in') or file.lower().startswith('in')):
                    input_files.append(file_path)
                elif ('output' in file.lower() or 'out' in file.lower() or 
                     file.lower().endswith('.out') or file.lower().startswith('out')):
                    output_files.append(file_path)
            
            print(f"Found {len(input_files)} potential input files and {len(output_files)} potential output files")
            
            # Match inputs with outputs based on naming patterns
            if input_files and output_files:
                # Sort to ensure consistent matching
                input_files.sort()
                output_files.sort()
                
                # Try to match files with similar names
                for in_file in input_files:
                    in_basename = os.path.basename(in_file)
                    in_name = os.path.splitext(in_basename)[0]
                    
                    # Find best matching output file
                    best_match = None
                    for out_file in output_files:
                        out_basename = os.path.basename(out_file)
                        out_name = os.path.splitext(out_basename)[0]
                        
                        # Look for exact prefix match
                        if (in_name.startswith(out_name) or out_name.startswith(in_name) or
                            in_name.replace('input', '') == out_name.replace('output', '') or
                            in_name.replace('in', '') == out_name.replace('out', '')):
                            best_match = out_file
                            break
                    
                    # If no match found, just take the first output file
                    if not best_match and output_files:
                        best_match = output_files.pop(0)
                        
                    if best_match:
                        self.test_cases.append(TestCase(
                            input_path=in_file,
                            output_path=best_match
                        ))
                        test_cases_found = True
                        print(f"Matched input '{os.path.basename(in_file)}' with output '{os.path.basename(best_match)}'")
        
        # Print final results
        if self.test_cases:
            print(f"\nLoaded {len(self.test_cases)} test cases for problem {self.id}")
        else:
            print(f"\nWARNING: No test cases found for problem {self.id}")
            print(f"Contents of directory {self.directory}:")
            try:
                for item in os.listdir(self.directory):
                    print(f"  {item}")
                    if os.path.isdir(os.path.join(self.directory, item)):
                        try:
                            subdir = os.path.join(self.directory, item)
                            print(f"    Contents of {item}/:")
                            for subitem in os.listdir(subdir):
                                print(f"      {subitem}")
                        except Exception as e:
                            print(f"    Error listing subdir: {e}")
            except Exception as e:
                print(f"  Error listing directory: {e}")
