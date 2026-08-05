"""
Colors module - ANSI color codes for terminal output
"""
import random

class Colors:
    """ANSI color codes for terminal output"""
    
    # Standard colors
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DARK_GREEN = '\033[32m'
    LIGHT_GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    PURPLE = '\033[95m'
    
    # Hacker theme colors
    HACKER_GREEN = '\033[38;5;46m'
    HACKER_BRIGHT = '\033[38;5;82m'
    HACKER_DIM = '\033[38;5;34m'
    MATRIX = '\033[38;5;40m'
    
    # Neon colors
    NEON_BLUE = '\033[38;5;45m'
    NEON_PINK = '\033[38;5;198m'
    NEON_PURPLE = '\033[38;5;129m'
    NEON_ORANGE = '\033[38;5;214m'
    NEON_YELLOW = '\033[38;5;226m'
    NEON_RED = '\033[38;5;196m'
    NEON_GREEN = '\033[38;5;46m'
    GOLD = '\033[38;5;220m'
    SILVER = '\033[38;5;250m'
    
    # Cyber colors
    CYBER_BLUE = '\033[38;5;39m'
    CYBER_PINK = '\033[38;5;207m'
    
    # Background colors
    BG_GREEN = '\033[42m'
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    
    # Effects
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    HIDDEN = '\033[8m'
    
    @classmethod
    def random_color(cls):
        """Get a random color from neon colors"""
        neon_colors = [
            cls.NEON_BLUE, cls.NEON_PINK, cls.NEON_PURPLE, 
            cls.NEON_ORANGE, cls.NEON_YELLOW, cls.NEON_RED,
            cls.NEON_GREEN, cls.CYBER_BLUE, cls.CYBER_PINK
        ]
        return random.choice(neon_colors)
    
    @classmethod
    def get_status_color(cls, status_type):
        """Get color for git status type"""
        colors = {
            'MOD': cls.NEON_ORANGE,
            'ADD': cls.NEON_GREEN,
            'DEL': cls.NEON_RED,
            'REN': cls.NEON_PURPLE,
            'COP': cls.CYBER_BLUE,
            'NEW': cls.NEON_YELLOW,
            'UPD': cls.NEON_PINK,
            'IGN': cls.HACKER_DIM,
            'CHG': cls.WARNING
        }
        return colors.get(status_type, cls.HACKER_DIM)
    
    @classmethod
    def get_status_symbol(cls, status_type):
        """Get symbol for git status type"""
        symbols = {
            'MOD': '▸',
            'ADD': '+',
            'DEL': '-',
            'REN': '↻',
            'COP': '≋',
            'NEW': '✦',
            'UPD': '◆',
            'IGN': '⊙',
            'CHG': '•'
        }
        return symbols.get(status_type, '•')