"""
Animation module - Hacker-style animations and effects
"""
import time
import random
from .colors import Colors

class HackerAnimator:
    """Hacker-style animations and effects with multiple colors"""
    
    def __init__(self):
        self.spinner_chars = ['◈', '◆', '◇', '●', '○', '■', '□', '▲', '△', '★', '✦', '✧']
        self.spinner_colors = [
            Colors.NEON_BLUE, Colors.CYBER_PINK, Colors.NEON_PURPLE, 
            Colors.HACKER_GREEN, Colors.NEON_ORANGE, Colors.NEON_YELLOW
        ]
        self.progress_chars = ['▱', '▱', '▰', '▰']
    
    def matrix_rain(self, lines=3, colors=None):
        """Create a Matrix-like rain effect with multiple colors"""
        if colors is None:
            colors = [Colors.MATRIX, Colors.HACKER_GREEN, Colors.HACKER_BRIGHT, Colors.HACKER_DIM]
        
        chars = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+-=[]{}|;:,.<>?/~"
        for _ in range(lines):
            line = ''.join(random.choice(chars) for _ in range(random.randint(20, 50)))
            color = random.choice(colors)
            print(f"{color}{line}{Colors.END}")
    
    def rainbow_text(self, text, speed=0.02):
        """Display text with rainbow colors"""
        colors = [
            Colors.NEON_RED, Colors.NEON_ORANGE, Colors.NEON_YELLOW, 
            Colors.HACKER_GREEN, Colors.CYBER_BLUE, Colors.NEON_PURPLE, Colors.NEON_PINK
        ]
        for i, char in enumerate(text):
            color = colors[i % len(colors)]
            print(f"{color}{char}{Colors.END}", end='', flush=True)
            time.sleep(speed)
        print()
    
    def glitch_text(self, text, intensity=0.15):
        """Create glitch effect on text with random colors"""
        glitched = []
        colors = [Colors.NEON_RED, Colors.NEON_BLUE, Colors.NEON_PURPLE, Colors.HACKER_GREEN]
        
        for char in text:
            if random.random() < intensity:
                glitched.append(f"{random.choice(colors)}{random.choice('!@#$%^&*()_+{}|:<>?~')}{Colors.END}")
            else:
                glitched.append(f"{Colors.HACKER_BRIGHT}{char}{Colors.END}")
        return ''.join(glitched)
    
    def color_scan_line(self, length=60):
        """Create a scanning line effect with multiple colors"""
        colors = [Colors.NEON_BLUE, Colors.CYBER_PINK, Colors.NEON_PURPLE, Colors.HACKER_GREEN]
        color = random.choice(colors)
        line = '═' * length
        print(f"{color}{line}{Colors.END}")
    
    def progress_bar(self, progress, total, prefix='', suffix=''):
        """Display a multi-color progress bar"""
        bar_length = 40
        filled = int(bar_length * (progress / total))
        
        # Multi-color progress bar
        bar_parts = []
        for j in range(bar_length):
            if j < filled:
                color_idx = j % len(self.spinner_colors)
                bar_parts.append(f"{self.spinner_colors[color_idx]}█{Colors.END}")
            else:
                bar_parts.append(f"{Colors.HACKER_DIM}░{Colors.END}")
        
        bar = ''.join(bar_parts)
        spinner = self.spinner_chars[progress % len(self.spinner_chars)]
        spinner_color = self.spinner_colors[progress % len(self.spinner_colors)]
        
        print(f'\r  {spinner_color}{spinner}{Colors.END} {bar} {Colors.NEON_YELLOW}{int((progress/total)*100)}%{Colors.END} {prefix} {suffix}', end='')
    
    def loading_animation(self, text="LOADING", duration=2):
        """Show a loading animation"""
        loading_chars = ['■', '□', '▪', '▫', '◆', '◇']
        loading_colors = [
            Colors.CYBER_BLUE, Colors.NEON_PURPLE, Colors.NEON_PINK, 
            Colors.NEON_ORANGE, Colors.NEON_GREEN, Colors.NEON_YELLOW
        ]
        
        print(f"{Colors.HACKER_DIM}{text}", end='')
        steps = int(duration * 10)
        for i in range(steps):
            color = loading_colors[i % len(loading_colors)]
            char = loading_chars[i % len(loading_chars)]
            print(f"{color}{char}{Colors.END}", end='', flush=True)
            time.sleep(0.1)
        print(f"{Colors.NEON_GREEN} DONE!{Colors.END}")