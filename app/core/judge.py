import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor
import sys
import traceback

# Assume there are existing imports and code here

class JudgeEngine:
    # ...existing code...
    
    def judge_submission(self, submission, problem, callback=None, progress_callback=None):
        """
        Execute the judging process in a separate thread to prevent UI freezing
        
        Args:
            submission: The submission to judge
            problem: The problem definition
            callback: Function to call when judging is complete
            progress_callback: Function to call to update progress
        """
        def run_judging():
            try:
                result = self._execute_judging(submission, problem, progress_callback)
                if callback:
                    # Use the main thread to update UI if this is called from a UI
                    if hasattr(callback, '__self__') and hasattr(callback.__self__, 'after'):
                        callback.__self__.after(0, lambda: callback(result))
                    else:
                        callback(result)
            except Exception as e:
                error_info = {
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
                if callback:
                    # Use the main thread to update UI if this is called from a UI
                    if hasattr(callback, '__self__') and hasattr(callback.__self__, 'after'):
                        callback.__self__.after(0, lambda: callback(None, error_info))
                    else:
                        callback(None, error_info)
        
        # Start judging in a separate thread
        threading.Thread(target=run_judging, daemon=True).start()
    
    def _execute_judging(self, submission, problem, progress_callback=None):
        """
        The actual judging logic, separated from the threading mechanism
        """
        # ...existing judging code...
        
        # Make sure to periodically update the UI using progress_callback
        # Example (insert at appropriate points in your existing code):
        if progress_callback:
            # Use the main thread to update UI if this is called from a UI
            if hasattr(progress_callback, '__self__') and hasattr(progress_callback.__self__, 'after'):
                progress_callback.__self__.after(0, lambda: progress_callback(progress_info))
            else:
                progress_callback(progress_info)
        
        # ...rest of judging code...
        
        return result
    
    # ...existing code...
