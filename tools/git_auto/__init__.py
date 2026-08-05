"""
Git Auto Pusher - Multi-Color Hacker Edition
A modular Git automation tool with hacker-style UI
"""

from .colors import Colors
from .animator import HackerAnimator
from .git_handler import GitHandler
from .watcher import FileWatcher
from .notifier import Notifier
from .config import Config
from .main import GitAutoPusher

__version__ = "3.0.0"
__author__ = "Sachin Chakrawarti"