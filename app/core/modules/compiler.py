import os
import platform
import subprocess

class Compiler:
    """Module for compiling source code"""
    
    @staticmethod
    def compile(solution_path: str) -> bool or str:
        """
        Compile the solution if needed
        
        Args:
            solution_path: Path to the solution file
            
        Returns:
            True if compilation succeeds, or error message string if it fails
        """
        ext = os.path.splitext(solution_path)[1]
        executable_path = os.path.splitext(solution_path)[0]
        
        # Platform-specific executable extension
        if platform.system() == 'Windows':
            executable_path += '.exe'
        
        try:
            creationflags = 0
            startupinfo = None
            if platform.system() == 'Windows':
                creationflags = subprocess.CREATE_NO_WINDOW
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            if ext == '.c':
                # Use platform-appropriate compiler flags
                compile_cmd = ['gcc', solution_path, '-o', executable_path]
                if platform.system() != 'Windows':
                    compile_cmd.append('-lm')  # Link math library on Unix
                
                process = subprocess.run(
                    compile_cmd,
                    capture_output=True, text=True,
                    creationflags=creationflags,
                    startupinfo=startupinfo
                )
            elif ext == '.cpp':
                compile_cmd = ['g++', '-std=c++20', solution_path, '-o', executable_path]
                if platform.system() != 'Windows':
                    compile_cmd.append('-lm')
                
                process = subprocess.run(
                    compile_cmd,
                    capture_output=True, text=True,
                    creationflags=creationflags,
                    startupinfo=startupinfo
                )
            else:
                # No compilation needed
                return True
                
            if process.returncode != 0:
                return process.stderr
            return True
        except Exception as e:
            return str(e)
