import threading
import queue
import time

class WorkerThread(threading.Thread):
    def __init__(self, task_queue, result_queue, thread_id):
        super().__init__()
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.thread_id = thread_id
        self.daemon = True
        self.stop_flag = threading.Event()
        self.status = "Idle"
    
    def run(self):
        while not self.stop_flag.is_set():
            try:
                # Get task with timeout to check stop flag periodically
                task = self.task_queue.get(timeout=0.5)
                
                if task is None:  # Sentinel value to stop thread
                    self.status = "Stopped"
                    self.task_queue.task_done()
                    break
                    
                func, args, kwargs, callback = task
                
                # Update status with task info - safely extract IDs
                if len(args) >= 2 and hasattr(args[0], 'id') and hasattr(args[1], 'id'):
                    self.status = f"Evaluating {args[0].id}/{args[1].id}"
                else:
                    self.status = "Evaluating task"
                
                # Execute the task
                try:
                    result = func(*args, **kwargs)
                    if callback and not self.stop_flag.is_set():
                        callback(result)
                except Exception as e:
                    self.status = f"Error: {str(e)}"
                    print(f"Thread {self.thread_id} error: {str(e)}")
                    
                self.status = "Idle"
                self.task_queue.task_done()
            except queue.Empty:
                # No tasks available, just continue checking stop flag
                pass
                
        self.status = "Terminated"

    def stop(self):
        """Signal the thread to stop"""
        self.stop_flag.set()

class ParallelEvaluator:
    def __init__(self, thread_count=4):
        self.thread_count = thread_count
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.threads = []
    
    def start_threads(self):
        """Start worker threads"""
        for i in range(self.thread_count):
            thread = WorkerThread(self.task_queue, self.result_queue, i)
            thread.start()
            self.threads.append(thread)
    
    def add_task(self, func, args=None, callback=None, **kwargs):
        """
        Add a task to the queue
        
        Args:
            func: Function to call
            args: Tuple of positional arguments to pass to the function
            callback: Function to call with the result
            **kwargs: Keyword arguments to pass to the function
        """
        # Use empty tuple as default for args if None is provided
        task_args = args if args is not None else ()
        self.task_queue.put((func, task_args, kwargs, callback))
    
    def wait_completion(self):
        """Wait for all tasks to complete"""
        self.task_queue.join()
    
    def stop_all(self):
        """Stop all worker threads"""
        # Clear any remaining tasks
        try:
            while True:
                self.task_queue.get_nowait()
                self.task_queue.task_done()
        except queue.Empty:
            pass
        
        # Signal threads to stop
        for _ in self.threads:
            self.task_queue.put(None)  # Sentinel value
            
        # Wait for threads to terminate
        for thread in self.threads:
            thread.stop()
            
        # Replace thread list
        self.threads = []
    
    def get_thread_status(self):
        """Get status of all threads"""
        return {i: thread.status for i, thread in enumerate(self.threads)}
