"""
Configuration module for Git Auto Pusher
"""
from pathlib import Path
import os

class Config:
    """Configuration settings for Git Auto Pusher"""
    
    # Repository settings
    REPO_PATH = Path(__file__).parent.parent  # Default to parent directory
    CHECK_INTERVAL = 3  # Seconds between checks
    COMMIT_COOLDOWN = 10  # Seconds to wait before committing again
    
    # Excluded directories
    EXCLUDED_DIRS = [
        '.git', '__pycache__', 'node_modules', 'venv', 'env', 
        '.idea', '.vscode', 'dist', 'build', '*.pyc'
    ]
    
    # Notification settings
    ENABLE_NOTIFICATIONS = True
    NOTIFICATION_TIMEOUT = 5
    
    # Animation settings
    ENABLE_ANIMATIONS = True
    MATRIX_RAIN_LINES = 3
    PROGRESS_BAR_LENGTH = 40
    
    # Logging
    ENABLE_LOGGING = True
    LOG_FILE = REPO_PATH / 'git_auto.log'
    
    @classmethod
    def get_repo_path(cls):
        """Get the repository path"""
        return cls.REPO_PATH
    
    @classmethod
    def set_repo_path(cls, path):
        """Set the repository path"""
        cls.REPO_PATH = Path(path)
        cls.LOG_FILE = cls.REPO_PATH / 'git_auto.log'
    
    @classmethod
    def get_excluded_dirs(cls):
        """Get the list of excluded directories"""
        return cls.EXCLUDED_DIRS
    
    @classmethod
    def add_excluded_dir(cls, dir_name):
        """Add a directory to excluded list"""
        if dir_name not in cls.EXCLUDED_DIRS:
            cls.EXCLUDED_DIRS.append(dir_name)