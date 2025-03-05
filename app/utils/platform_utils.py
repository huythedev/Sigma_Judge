import sys
import platform
import os
import subprocess
from PyQt6.QtWidgets import QFileDialog, QApplication

def get_platform():
    """Get current platform name"""
    system = platform.system()
    if system == 'Darwin':
        return 'mac'
    elif system == 'Windows':
        return 'windows'
    else:
        return 'linux'

def open_file_dialog(file_types=None, initial_dir=None, parent=None, title="Select File"):
    """Open a file dialog and return the selected file path"""
    if file_types is None:
        file_types = "All Files (*)"
    
    if initial_dir is None or not os.path.exists(initial_dir):
        initial_dir = os.path.expanduser("~")
    
    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        title,
        initial_dir,
        file_types
    )
    
    return file_path if file_path else None

def open_directory_dialog(initial_dir=None, parent=None, title="Select Directory"):
    """Open a directory dialog and return the selected directory path"""
    if initial_dir is None or not os.path.exists(initial_dir):
        initial_dir = os.path.expanduser("~")
    
    dir_path = QFileDialog.getExistingDirectory(
        parent,
        title,
        initial_dir,
        QFileDialog.Option.ShowDirsOnly
    )
    
    return dir_path if dir_path else None

def get_resources_path():
    """Get the path to the resources directory"""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle
        return os.path.join(sys._MEIPASS, 'resources')
    else:
        # If the application is run from source
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources')

def ensure_directory(path):
    """Ensure the directory exists, creating it if necessary"""
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            return True
        except Exception as e:
            print(f"Error creating directory {path}: {e}")
            return False
    return True
