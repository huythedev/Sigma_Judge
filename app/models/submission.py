from enum import Enum
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

class SubmissionStatus(Enum):
    PENDING = "Pending"
    CORRECT = "Correct"
    WRONG_ANSWER = "Wrong Answer"
    TIME_LIMIT_EXCEEDED = "Time Limit Exceeded"
    MEMORY_LIMIT_EXCEEDED = "Memory Limit Exceeded"
    RUNTIME_ERROR = "Runtime Error"
    COMPILATION_ERROR = "Compilation Error"

@dataclass
class TestCaseResult:
    status: SubmissionStatus = SubmissionStatus.PENDING
    execution_time: float = 0.0
    memory_used: float = 0.0
    error_message: str = ""
    input_excerpt: str = ""
    expected_output: str = ""
    actual_output: str = ""
    
@dataclass
class SubmissionResult:
    contestant_id: str
    problem_id: str
    status: SubmissionStatus = SubmissionStatus.PENDING
    score: float = 0.0
    max_score: float = 0.0
    execution_time: float = 0.0
    memory_used: float = 0.0
    test_case_results: List[TestCaseResult] = field(default_factory=list)
    
    def calculate_score(self, weights: List[float] = None, total_points: float = None, total_weight_override: float = None):
        """Calculate the score based on test case results"""
        if not self.test_case_results:
            self.status = SubmissionStatus.PENDING
            self.score = 0.0
            self.max_score = 0.0
            return
            
        # Use equal weights if none provided
        if weights is None or len(weights) != len(self.test_case_results):
            weights = [1.0] * len(self.test_case_results)
        
        total_weight = sum(weights)
        if total_weight_override is not None and total_weight_override > 0:
            total_weight = total_weight_override
        
        # Calculate score based on correct test cases
        correct_weight = sum(weights[i] for i, tc in enumerate(self.test_case_results) 
                             if tc.status == SubmissionStatus.CORRECT)

        if total_points is not None:
            self.max_score = total_points
            self.score = (correct_weight / total_weight) * total_points if total_weight > 0 else 0.0
        else:
            self.max_score = total_weight
            self.score = correct_weight
        
        # Calculate average execution time and max memory
        if self.test_case_results:
            self.execution_time = sum(tc.execution_time for tc in self.test_case_results) / len(self.test_case_results)
            self.memory_used = max((tc.memory_used for tc in self.test_case_results), default=0)
        
        # Determine overall status based on test cases
        # Fix: Ensure status is set even if it's not CORRECT or if priority isn't found
        if all(tc.status == SubmissionStatus.CORRECT for tc in self.test_case_results):
            self.status = SubmissionStatus.CORRECT
        else:
            # Find highest priority non-CORRECT status
            found_status = False
            for status in [SubmissionStatus.COMPILATION_ERROR, 
                          SubmissionStatus.RUNTIME_ERROR,
                          SubmissionStatus.TIME_LIMIT_EXCEEDED, 
                          SubmissionStatus.MEMORY_LIMIT_EXCEEDED,
                          SubmissionStatus.WRONG_ANSWER]:
                if any(tc.status == status for tc in self.test_case_results):
                    self.status = status
                    found_status = True
                    break
            
            # If no error found but not all CORRECT, use WRONG_ANSWER as fallback
            if not found_status:
                self.status = SubmissionStatus.WRONG_ANSWER
