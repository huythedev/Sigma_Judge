from dataclasses import dataclass, field
from typing import Dict
import os

@dataclass
class Contestant:
    id: str
    name: str
    directory: str  # Directory containing solutions
    solutions: Dict[str, str] = field(default_factory=dict)  # Maps problem_id to solution_path
    
    def has_solution_for(self, problem_id: str) -> bool:
        """Check if contestant has a solution for given problem"""
        return problem_id in self.solutions
    
    def get_solution_path(self, problem_id: str) -> str:
        """Get the path to the solution for given problem"""
        if not self.has_solution_for(problem_id):
            raise ValueError(f"No solution found for problem {problem_id}")
        
        # Ensure path is normalized and absolute
        path = self.solutions[problem_id]
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        
        # Verify file exists
        if not os.path.isfile(path):
            raise ValueError(f"Solution file not found: {path}")
            
        return path
    
    def get_solution_name(self, problem_id: str) -> str:
        """Get the filename (without path) of the solution"""
        if not self.has_solution_for(problem_id):
            return None
        return os.path.basename(self.solutions[problem_id])
