from typing import List, Dict, Tuple, Optional, Callable
import threading
import queue
import time

from app.models.contestant import Contestant
from app.models.problem import Problem
from app.models.submission import SubmissionResult

class ParallelEvaluator:
    def __init__(self, evaluator, num_threads=4):
        self.evaluator = evaluator
        # Number of threads will be capped by contestant count
        self.num_threads = num_threads
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.threads = []
        self.active_threads = 0
        self.stop_requested = False
        self.thread_status = {}  # For monitoring thread activity
    
    def worker(self, thread_id):
        """Worker thread function"""
        self.thread_status[thread_id] = "Starting"
        
        while not self.stop_requested:
            try:
                self.thread_status[thread_id] = "Waiting for task"
                task = self.task_queue.get(timeout=1)
                if task is None:  # Sentinel value to indicate thread should exit
                    self.task_queue.task_done()
                    break
                
                contestant, problem = task
                self.thread_status[thread_id] = f"Evaluating {contestant.id} - {problem.id}"
                
                result = self.evaluator.evaluate_submission(contestant, problem)
                self.result_queue.put(result)
                
                self.task_queue.task_done()
            except queue.Empty:
                if self.stop_requested:
                    break
        
        self.thread_status[thread_id] = "Stopped"
        with threading.Lock():
            self.active_threads -= 1
    
    def evaluate_all(self, 
                    contestants: List[Contestant], 
                    problems: List[Problem],
                    callback: Callable[[SubmissionResult], None] = None) -> Dict[Tuple[str, str], SubmissionResult]:
        """
        Evaluate all contestants' solutions for all problems in parallel
        
        Args:
            contestants: List of contestants
            problems: List of problems
            callback: Function to call with each result
            
        Returns:
            Dictionary mapping (contestant_id, problem_id) to SubmissionResult
        """
        results = {}
        self.stop_requested = False
        
        # Adjust number of threads based on contestant count
        actual_threads = min(self.num_threads, len(contestants))
        self.active_threads = actual_threads
        print(f"Using {actual_threads} threads for {len(contestants)} contestants")
        
        # Distribute contestants among threads
        contestant_groups = self._distribute_contestants(contestants, actual_threads)
        
        # Create and start worker threads
        self.threads = []
        self.thread_status = {}
        for i in range(actual_threads):
            thread = threading.Thread(
                target=self._contestant_worker, 
                args=(i, contestant_groups[i], problems)
            )
            self.threads.append(thread)
            thread.start()
        
        # Process results as they come in
        total_tasks = len(contestants) * len(problems)
        completed_tasks = 0
        
        try:
            while completed_tasks < total_tasks and not self.stop_requested:
                try:
                    result = self.result_queue.get(timeout=0.1)
                    key = (result.contestant_id, result.problem_id)
                    results[key] = result
                    
                    if callback:
                        callback(result)
                    
                    completed_tasks += 1
                    self.result_queue.task_done()
                except queue.Empty:
                    # Check if all threads died unexpectedly
                    if self.active_threads == 0:
                        break
        except KeyboardInterrupt:
            self.stop()
        
        # Wait for threads to finish
        self.stop()
        return results

    def _distribute_contestants(self, contestants: List[Contestant], num_threads: int) -> List[List[Contestant]]:
        """Distribute contestants evenly among threads"""
        groups = [[] for _ in range(num_threads)]
        for i, contestant in enumerate(contestants):
            groups[i % num_threads].append(contestant)
        return groups
    
    def _contestant_worker(self, thread_id: int, contestants: List[Contestant], problems: List[Problem]):
        """Worker thread that processes all problems for assigned contestants"""
        self.thread_status[thread_id] = f"Starting - Assigned {len(contestants)} contestants"
        
        for contestant in contestants:
            if self.stop_requested:
                break
                
            for problem in problems:
                if self.stop_requested:
                    break
                
                self.thread_status[thread_id] = f"Evaluating {contestant.id} - {problem.id}"
                result = self.evaluator.evaluate_submission(contestant, problem)
                self.result_queue.put(result)
        
        self.thread_status[thread_id] = "Finished"
        with threading.Lock():
            self.active_threads -= 1
    
    def stop(self):
        """Stop all worker threads"""
        self.stop_requested = True
        self.evaluator.stop()
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(1)
        
        # Clear queues
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
                self.task_queue.task_done()
            except queue.Empty:
                break
        
        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
                self.result_queue.task_done()
            except queue.Empty:
                break

    def get_thread_status(self):
        """Get status of all threads for monitoring"""
        return self.thread_status
