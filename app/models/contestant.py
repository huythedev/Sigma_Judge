from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class Contestant:
    id: str
    name: str
    directory: str  # Directory containing contestant's solutions
    solutions: Dict[str, str] = None  # Map of problem_id -> solution file path
    
    def __post_init__(self):
        if self.solutions is None:
            self.solutions = {}
    
    def has_solution_for(self, problem_id: str) -> bool:
        """Check if contestant has a solution for the given problem"""
        return problem_id in self.solutions
    
    def get_solution_path(self, problem_id: str) -> Optional[str]:
        """Get the solution file path for the given problem"""
        return self.solutions.get(problem_id, None)
