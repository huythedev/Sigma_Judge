import os
import random
import string
import subprocess  # Add this import
from typing import List, Dict, Callable

class TestGenerator:
    @staticmethod
    def generate_number_sequence(count: int, min_val: int, max_val: int) -> str:
        """Generate a sequence of numbers"""
        return ' '.join(str(random.randint(min_val, max_val)) for _ in range(count))
    
    @staticmethod
    def generate_string(length: int, char_set: str = None) -> str:
        """Generate a random string"""
        if char_set is None:
            char_set = string.ascii_lowercase
        return ''.join(random.choice(char_set) for _ in range(length))
    
    @staticmethod
    def generate_graph(nodes: int, edges: int, weighted: bool = False, 
                      min_weight: int = 1, max_weight: int = 100) -> str:
        """Generate a graph with the given number of nodes and edges"""
        if edges > nodes * (nodes - 1) // 2:  # Maximum possible edges in an undirected graph
            edges = nodes * (nodes - 1) // 2
        
        result = [f"{nodes} {edges}"]
        
        # Generate random edges
        edge_set = set()
        while len(edge_set) < edges:
            u = random.randint(1, nodes)
            v = random.randint(1, nodes)
            if u != v and (u, v) not in edge_set and (v, u) not in edge_set:
                edge_set.add((u, v))
                
                if weighted:
                    weight = random.randint(min_weight, max_weight)
                    result.append(f"{u} {v} {weight}")
                else:
                    result.append(f"{u} {v}")
        
        return '\n'.join(result)
    
    @staticmethod
    def generate_tree(nodes: int, weighted: bool = False, 
                     min_weight: int = 1, max_weight: int = 100) -> str:
        """Generate a random tree with the given number of nodes"""
        if nodes <= 0:
            return ""
        
        result = [f"{nodes}"]
        
        # Generate a random tree by connecting each node to a random previous node
        for i in range(2, nodes + 1):
            parent = random.randint(1, i - 1)
            
            if weighted:
                weight = random.randint(min_weight, max_weight)
                result.append(f"{parent} {i} {weight}")
            else:
                result.append(f"{parent} {i}")
        
        return '\n'.join(result)
    
    @staticmethod
    def generate_matrix(rows: int, cols: int, min_val: int = 0, max_val: int = 100) -> str:
        """Generate a random matrix with the given dimensions"""
        result = [f"{rows} {cols}"]
        
        for _ in range(rows):
            row = ' '.join(str(random.randint(min_val, max_val)) for _ in range(cols))
            result.append(row)
        
        return '\n'.join(result)
    
    @staticmethod
    def generate_sorted_array(size: int, min_val: int = 0, max_val: int = 1000, 
                            unique: bool = True) -> str:
        """Generate a sorted array of integers"""
        if unique and max_val - min_val + 1 < size:
            # Cannot generate enough unique numbers
            size = max_val - min_val + 1
        
        if unique:
            numbers = random.sample(range(min_val, max_val + 1), size)
        else:
            numbers = [random.randint(min_val, max_val) for _ in range(size)]
        
        numbers.sort()
        return f"{size}\n" + ' '.join(str(num) for num in numbers)
    
    @staticmethod
    def create_test_case_files(problem_dir: str, test_number: int, 
                             input_generator: Callable[[], str],
                             output_generator: Callable[[str], str] = None,
                             solution_path: str = None) -> tuple:
        """
        Create a test case file pair in the problem directory
        
        Args:
            problem_dir: Directory to store the test cases
            test_number: Test case number
            input_generator: Function that generates input data
            output_generator: Function that generates output data from input
            solution_path: Path to a solution executable to generate output
            
        Returns:
            Tuple of (input_path, output_path)
        """
        os.makedirs(problem_dir, exist_ok=True)
        
        # Generate the input
        input_data = input_generator()
        input_path = os.path.join(problem_dir, f"input{test_number}.txt")
        with open(input_path, 'w') as f:
            f.write(input_data)
        
        # Generate the output
        output_path = os.path.join(problem_dir, f"output{test_number}.txt")
        
        if solution_path:
            # Use a reference solution to generate output
            if os.path.isfile(solution_path):
                ext = os.path.splitext(solution_path)[1]
                
                if ext == '.py':
                    cmd = ['python', solution_path]
                elif ext == '.java':
                    cmd = ['java', solution_path]
                elif ext in ['.c', '.cpp']:
                    if os.name == 'nt':  # Windows
                        cmd = [solution_path + '.exe']
                    else:
                        cmd = [solution_path]
                else:
                    cmd = [solution_path]
                
                try:
                    process = subprocess.run(
                        cmd,
                        input=input_data,
                        text=True,
                        capture_output=True
                    )
                    
                    if process.returncode == 0:
                        with open(output_path, 'w') as f:
                            f.write(process.stdout)
                    else:
                        print(f"Error running solution: {process.stderr}")
                        return None
                except Exception as e:
                    print(f"Error running solution: {e}")
                    return None
            else:
                print(f"Solution file not found: {solution_path}")
                return None
        elif output_generator:
            # Use the provided output generator function
            output_data = output_generator(input_data)
            with open(output_path, 'w') as f:
                f.write(output_data)
        else:
            print("Either solution_path or output_generator must be provided")
            return None
        
        return (input_path, output_path)
    
    @staticmethod
    def generate_standard_problem(problem_type: str, problem_dir: str, 
                                num_cases: int = 10, **kwargs) -> bool:
        """
        Generate standard test cases for common problem types
        
        Args:
            problem_type: Type of problem ('sorting', 'searching', etc.)
            problem_dir: Directory to store test cases
            num_cases: Number of test cases to generate
            **kwargs: Additional parameters for specific problem types
            
        Returns:
            True if successful, False otherwise
        """
        os.makedirs(problem_dir, exist_ok=True)
        
        if problem_type == "sorting":
            # Generate sorting test cases
            size_range = kwargs.get('size_range', (10, 1000))
            value_range = kwargs.get('value_range', (0, 10000))
            
            for i in range(1, num_cases + 1):
                # Scale sizes exponentially
                size = random.randint(
                    size_range[0], 
                    min(size_range[0] + (i * (size_range[1] - size_range[0]) // num_cases), 
                        size_range[1])
                )
                
                def input_gen():
                    numbers = [random.randint(value_range[0], value_range[1]) for _ in range(size)]
                    return f"{size}\n" + ' '.join(map(str, numbers))
                
                def output_gen(input_data):
                    lines = input_data.strip().split('\n')
                    numbers = list(map(int, lines[1].split()))
                    numbers.sort()
                    return ' '.join(map(str, numbers))
                
                TestGenerator.create_test_case_files(
                    problem_dir, i, 
                    input_gen,
                    output_gen
                )
                
        elif problem_type == "searching":
            # Generate searching test cases
            size_range = kwargs.get('size_range', (10, 1000))
            value_range = kwargs.get('value_range', (0, 10000))
            
            for i in range(1, num_cases + 1):
                # Scale sizes exponentially
                size = random.randint(
                    size_range[0], 
                    min(size_range[0] + (i * (size_range[1] - size_range[0]) // num_cases), 
                        size_range[1])
                )
                
                def input_gen():
                    numbers = sorted([random.randint(value_range[0], value_range[1]) for _ in range(size)])
                    # Generate queries
                    num_queries = random.randint(1, 20)
                    queries = []
                    
                    # Mix of present and not present values
                    for j in range(num_queries):
                        if random.random() < 0.7:  # 70% chance of element being present
                            q = random.choice(numbers)
                        else:
                            q = random.randint(value_range[0], value_range[1])
                        queries.append(q)
                    
                    return f"{size}\n{' '.join(map(str, numbers))}\n{num_queries}\n{' '.join(map(str, queries))}"
                
                def output_gen(input_data):
                    lines = input_data.strip().split('\n')
                    numbers = list(map(int, lines[1].split()))
                    queries = list(map(int, lines[3].split()))
                    
                    results = []
                    for query in queries:
                        if query in numbers:
                            results.append(f"Found at index {numbers.index(query)}")
                        else:
                            results.append("Not found")
                    
                    return '\n'.join(results)
                
                TestGenerator.create_test_case_files(
                    problem_dir, i, 
                    input_gen,
                    output_gen
                )
                
        elif problem_type == "graph":
            # Generate graph test cases
            node_range = kwargs.get('node_range', (5, 100))
            weighted = kwargs.get('weighted', False)
            
            for i in range(1, num_cases + 1):
                # Scale node count
                nodes = random.randint(
                    node_range[0], 
                    min(node_range[0] + (i * (node_range[1] - node_range[0]) // num_cases), 
                        node_range[1])
                )
                
                # Vary edge density
                max_edges = nodes * (nodes - 1) // 2
                edge_count = random.randint(nodes - 1, min(nodes * 2, max_edges))
                
                def input_gen():
                    return TestGenerator.generate_graph(nodes, edge_count, weighted)
                
                # For graph problems, usually need a solution executable
                solution_path = kwargs.get('solution_path', None)
                output_gen = kwargs.get('output_gen', None)
                
                TestGenerator.create_test_case_files(
                    problem_dir, i, 
                    input_gen,
                    output_gen,
                    solution_path
                )
                
        else:
            print(f"Unknown problem type: {problem_type}")
            return False
            
        return True
