"""
Git Auto Pusher - Main Entry Point
Multi-Color Hacker Edition
"""
import sys
import time
from pathlib import Path

# Add the git_auto module to path
sys.path.insert(0, str(Path(__file__).parent))

from git_auto import GitAutoPusher, Config, Colors, HackerAnimator

def main():
    """Main entry point"""
    # Show loading
    animator = HackerAnimator()
    animator.loading_animation("LOADING SYSTEM", duration=2)
    time.sleep(0.3)
    
    # Configure
    repo_path = Path(__file__).parent
    check_interval = 3
    excluded_dirs = ['.git', '__pycache__', 'node_modules', 'venv', 'env', '.idea', '.vscode']
    
    # Start the pusher
    pusher = GitAutoPusher(
        repo_path=repo_path,
        check_interval=check_interval,
        excluded_dirs=excluded_dirs
    )
    
    try:
        pusher.start()
    except KeyboardInterrupt:
        print(f"\n{Colors.HACKER_DIM}SYSTEM SHUTDOWN COMPLETE{Colors.END}")

if __name__ == "__main__":
    main()