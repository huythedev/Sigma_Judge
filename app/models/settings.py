import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

@dataclass
class ProblemSettings:
    time_limit: float = 1.0  # in seconds
    memory_limit: float = 512.0  # in MB
    io_mode: str = "auto"  # "auto", "standard", or "file"
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        # For backward compatibility with old settings files that don't have io_mode
        if 'io_mode' not in data:
            data['io_mode'] = "auto"
        return cls(**data)

@dataclass
class Settings:
    thread_count: int = 4
    global_time_limit: float = 1.0  # in seconds 
    global_memory_limit: int = 512  # in MB
    global_io_mode: str = "auto"  # "auto", "standard", or "file"
    problem_settings: Dict[str, ProblemSettings] = field(default_factory=dict)
    last_directory: Optional[str] = None
    
    def __post_init__(self):
        """Initialize after the dataclass initialization"""
        # Make sure problem_settings is always initialized
        if self.problem_settings is None:
            self.problem_settings = {}
            
        # Convert any dict problem settings to ProblemSettings objects
        for problem_id, settings in list(self.problem_settings.items()):
            if isinstance(settings, dict):
                self.problem_settings[problem_id] = ProblemSettings.from_dict(settings)
                
        # For backward compatibility with old settings
        if hasattr(self, 'default_time_limit'):
            self.global_time_limit = self.default_time_limit
        if hasattr(self, 'default_memory_limit'):
            self.global_memory_limit = self.default_memory_limit
        if hasattr(self, 'io_mode'):
            self.global_io_mode = self.io_mode
            
    def get_problem_settings(self, problem_id: str) -> ProblemSettings:
        """Get settings for a specific problem, or default if not found"""
        if problem_id in self.problem_settings:
            return self.problem_settings[problem_id]
        return ProblemSettings(
            time_limit=self.global_time_limit,
            memory_limit=self.global_memory_limit,
            io_mode=self.global_io_mode
        )
    
    def set_problem_settings(self, problem_id: str, settings: ProblemSettings):
        """Set settings for a specific problem"""
        self.problem_settings[problem_id] = settings
    
    def apply_global_settings_to_all(self):
        """Apply global settings to all problem-specific settings"""
        for problem_id in self.problem_settings:
            self.problem_settings[problem_id].time_limit = self.global_time_limit
            self.problem_settings[problem_id].memory_limit = self.global_memory_limit
            self.problem_settings[problem_id].io_mode = self.global_io_mode
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        result = asdict(self)
        # Convert problem settings to dicts
        result['problem_settings'] = {
            pid: settings.to_dict() 
            for pid, settings in self.problem_settings.items()
        }
        return result
    
    @classmethod
    def from_dict(cls, data):
        """Create settings from dictionary"""
        # For backward compatibility with old settings
        if 'default_time_limit' in data and 'global_time_limit' not in data:
            data['global_time_limit'] = data['default_time_limit']
        if 'default_memory_limit' in data and 'global_memory_limit' not in data:
            data['global_memory_limit'] = data['default_memory_limit']
        if 'io_mode' in data and 'global_io_mode' not in data:
            data['global_io_mode'] = data['io_mode']
            
        # Handle problem settings explicitly
        problem_settings = {}
        if 'problem_settings' in data:
            for pid, settings in data['problem_settings'].items():
                problem_settings[pid] = ProblemSettings.from_dict(settings)
            data['problem_settings'] = problem_settings
        return cls(**data)
    
    def save(self, filepath=None):
        """Save settings to file with debug output"""
        if filepath is None:
            filepath = os.path.join(os.path.dirname(__file__), "../../resources/settings.json")
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            data = self.to_dict()
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            print(f"Settings saved successfully to {filepath}")
            print(f"- thread_count: {self.thread_count}")
            print(f"- global_time_limit: {self.global_time_limit}")
            print(f"- global_memory_limit: {self.global_memory_limit}")
            print(f"- last_directory: {self.last_directory}")
            print(f"- problem_settings: {len(self.problem_settings)} items")
        except Exception as e:
            print(f"Error saving settings: {e}")
            # Try alternate location if primary fails
            try:
                backup_path = os.path.join(os.path.expanduser("~"), "sigma_judge_settings.json")
                with open(backup_path, 'w') as f:
                    json.dump(self.to_dict(), f, indent=2)
                print(f"Settings saved to backup location: {backup_path}")
            except Exception as backup_error:
                print(f"Error saving settings to backup location: {backup_error}")
    
    @classmethod
    def load(cls, filepath=None):
        """Load settings from file with improved error handling"""
        if filepath is None:
            filepath = os.path.join(os.path.dirname(__file__), "../../resources/settings.json")
        
        if not os.path.exists(filepath):
            print(f"Settings file not found at {filepath}, creating default settings")
            default_settings = cls()
            default_settings.save(filepath)  # Create a default settings file
            return default_settings
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Debug loaded data
            print(f"Loaded settings from {filepath}")
            if 'problem_settings' in data:
                print(f"Found {len(data['problem_settings'])} problem settings in file")
            
            return cls.from_dict(data)
        except Exception as e:
            print(f"Error loading settings from {filepath}: {e}")
            return cls()  # Return default settings if loading fails
