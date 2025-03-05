#!/usr/bin/env python3
"""
Robust entry point for Sigma Judge application
Properly handles stdin/stdout issues in packaged executables
"""

import os
import sys
import platform
import traceback
from datetime import datetime

def setup_environment():
    """Set up environment variables and paths"""
    # Get the application base directory
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as compiled executable
        app_dir = sys._MEIPASS
    else:
        # Running as script
        app_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Add the app directory to the path so we can import modules
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    
    # Set current working directory to app directory
    os.chdir(app_dir)
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(app_dir, 'logs')
    if not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir)
        except:
            pass
            
    return app_dir

def start_gui_application():
    """Start the main GUI application"""
    try:
        # Import PyQt or equivalent GUI framework
        from PyQt6.QtWidgets import QApplication
        
        # Import the main application window
        from app.main import main as app_main
        
        # Run the main application
        return app_main()
    except ImportError as e:
        show_error(f"Failed to import GUI components: {str(e)}")
        return 1
    except Exception as e:
        show_error(f"Error starting application: {str(e)}\n{traceback.format_exc()}")
        return 1

def show_error(error_msg):
    """Show error message in the most appropriate way"""
    # Log the error to a file
    try:
        log_path = os.path.join('logs', 'error.log')
        with open(log_path, 'a') as f:
            f.write(f"[{datetime.now()}] {error_msg}\n")
    except:
        pass
    
    # Try to show error using GUI
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        if not QApplication.instance():
            app = QApplication(sys.argv)
        QMessageBox.critical(None, "Sigma Judge Error", error_msg)
    except:
        # Fall back to console
        try:
            print(f"ERROR: {error_msg}")
        except:
            pass
        
        # Last resort for Windows
        if platform.system() == 'Windows':
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, error_msg, "Sigma Judge Error", 0x10)
            except:
                pass

def main():
    """Main entry point with robust error handling"""
    try:
        # Set up environment
        app_dir = setup_environment()
        
        print(f"Starting Sigma Judge from {app_dir}")
        
        # If we made it this far, we can try to start the real application
        return start_gui_application()
        
    except Exception as e:
        error_msg = f"Unhandled exception: {str(e)}\n{traceback.format_exc()}"
        show_error(error_msg)
        return 1

if __name__ == "__main__":
    sys.exit(main())
