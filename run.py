import sys
import os

# Add the parent directory to sys.path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main function
from app.main import main

if __name__ == "__main__":
    main()
