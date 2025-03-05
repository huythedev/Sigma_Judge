import psutil
import threading
import time
import subprocess
import os

class ProcessManager:
    """Module for managing processes and monitoring memory usage"""
    
    @staticmethod
    def run_with_memory_monitoring(cmd, input_data=None, timeout=None, cwd=None, 
                                  stdin_file=None, use_stdin_pipe=True, temp_files=None):
        """
        Run a process with memory monitoring
        
        Args:
            cmd: Command to run
            input_data: Input data to send to stdin
            timeout: Timeout in seconds
            cwd: Working directory
            stdin_file: File to use as stdin instead of pipe
            use_stdin_pipe: Whether to use subprocess.PIPE for stdin
            temp_files: List of temporary files to clean up
        
        Returns:
            Tuple of (stdout, stderr, execution_time, max_memory, returncode)
        """
        max_memory = 0
        execution_time = 0
        start_time = time.time()
        temp_files = temp_files or []
        
        # Configure stdin
        stdin_src = None
        if stdin_file:
            stdin_src = open(stdin_file, 'r')
        elif use_stdin_pipe:
            stdin_src = subprocess.PIPE
        
        # Start the process
        try:
            process = subprocess.Popen(
                cmd,
                stdin=stdin_src,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd
            )
            
            # Setup memory monitoring
            memory_thread_stop = threading.Event()
            
            def memory_monitor():
                nonlocal max_memory
                try:
                    while not memory_thread_stop.is_set():
                        try:
                            proc = psutil.Process(process.pid)
                            mem_info = proc.memory_info()
                            max_memory = max(max_memory, mem_info.rss / (1024 * 1024))  # Convert to MB
                        except:
                            pass
                        time.sleep(0.05)  # Check every 50ms
                except:
                    pass
            
            # Start memory monitoring
            memory_thread = threading.Thread(target=memory_monitor)
            memory_thread.daemon = True
            memory_thread.start()
            
            # Communicate with the process
            try:
                if stdin_src == subprocess.PIPE:
                    stdout, stderr = process.communicate(input=input_data, timeout=timeout)
                else:
                    stdout, stderr = process.communicate(timeout=timeout)
                
                memory_thread_stop.set()
                memory_thread.join(0.1)
                
                execution_time = time.time() - start_time
                return stdout, stderr, execution_time, max_memory, process.returncode
                
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                memory_thread_stop.set()
                memory_thread.join(0.1)
                
                return stdout, stderr, timeout, max_memory, -1
                
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
