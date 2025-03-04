import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

@dataclass
class ProblemSettings:
    time_limit: float = 1.0  # in seconds
    memory_limit: int = 256  # in MB
    io_mode: str = "stdin"   # "stdin" or "file"
    input_file: str = ""
    output_file: str = ""

@dataclass
class Settings:
    global_time_limit: float = 1.0
    global_memory_limit: int = 256
    global_io_mode: str = "stdin"
    thread_count: int = 4
    problem_settings: Dict[str, ProblemSettings] = field(default_factory=dict)
    last_directory: str = ""
    
    def __post_init__(self):
        self.settings_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                         "resources", "settings.json")
    
    def save(self):
        """Save settings to a JSON file"""
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        
        # Convert dataclasses to dictionaries
        settings_dict = asdict(self)
        
        with open(self.settings_file, 'w') as f:
            json.dump(settings_dict, f, indent=2)
    
    def load(self):
        """Load settings from a JSON file"""
        if not os.path.exists(self.settings_file):
            # Create default settings if file doesn't exist
            self.save()
            return
        
        try:
            with open(self.settings_file, 'r') as f:
                settings_dict = json.load(f)
            
            # Update basic attributes
            for key, value in settings_dict.items():
                if key != "problem_settings" and hasattr(self, key):
                    setattr(self, key, value)
            
            # Handle problem settings
            if "problem_settings" in settings_dict:
                self.problem_settings = {}
                for problem_id, problem_dict in settings_dict["problem_settings"].items():
                    self.problem_settings[problem_id] = ProblemSettings(**problem_dict)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def get_problem_settings(self, problem_id: str) -> ProblemSettings:
        """Get settings for a specific problem, or create default settings"""
        if problem_id not in self.problem_settings:
            self.problem_settings[problem_id] = ProblemSettings(
                time_limit=self.global_time_limit,
                memory_limit=self.global_memory_limit,
                io_mode=self.global_io_mode
            )
        return self.problem_settings[problem_id]
