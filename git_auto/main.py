"""
Main module - Git Auto Pusher orchestrator
"""
import time
import sys
from pathlib import Path
from .colors import Colors
from .animator import HackerAnimator
from .git_handler import GitHandler
from .watcher import FileWatcher
from .notifier import Notifier
from .config import Config

class GitAutoPusher:
    """Main orchestrator for Git Auto Pusher"""
    
    def __init__(self, repo_path=None, check_interval=None, excluded_dirs=None):
        """Initialize the Git Auto Pusher"""
        self.config = Config()
        
        if repo_path:
            self.config.set_repo_path(repo_path)
        
        if check_interval:
            self.config.CHECK_INTERVAL = check_interval
        
        if excluded_dirs:
            for dir_name in excluded_dirs:
                self.config.add_excluded_dir(dir_name)
        
        self.repo_path = self.config.get_repo_path()
        self.animator = HackerAnimator()
        self.notifier = Notifier(self.config.ENABLE_NOTIFICATIONS)
        self.git = GitHandler(
            self.repo_path,
            self.config.get_excluded_dirs(),
            self.notifier
        )
        self.watcher = None
        self.running = False
        self.start_time = time.time()
    
    def start(self):
        """Start the auto-push service"""
        self.running = True
        
        # Welcome sequence
        self._show_welcome()
        
        # Start file watcher
        self.watcher = FileWatcher(
            self.repo_path,
            self.config.get_excluded_dirs(),
            self._on_file_change
        )
        self.watcher.start()
        
        # Main loop
        try:
            self._main_loop()
        except KeyboardInterrupt:
            self._shutdown()
    
    def _show_welcome(self):
        """Show welcome sequence"""
        self.animator.matrix_rain(3)
        
        ascii_art = [
            "╔════════════════════════════════════════════════════════════╗",
            "║  ██████╗ ██╗████████╗    ██████╗ ██╗   ██╗███████╗██╗  ██╗  ║",
            "║  ██╔══██╗██║╚══██╔══╝    ██╔══██╗██║   ██║██╔════╝██║  ██║  ║",
            "║  ██████╔╝██║   ██║       ██████╔╝██║   ██║███████╗███████║  ║",
            "║  ██╔══██╗██║   ██║       ██╔═══╝ ██║   ██║╚════██║██╔══██║  ║",
            "║  ██████╔╝██║   ██║       ██║     ╚██████╔╝███████║██║  ██║  ║",
            "║  ╚═════╝ ╚═╝   ╚═╝       ╚═╝      ╚═════╝ ╚══════╝╚═╝  ╚═╝  ║",
            "╚════════════════════════════════════════════════════════════╝"
        ]
        
        for line in ascii_art:
            color = Colors.random_color()
            print(f"{color}{line}{Colors.END}")
            time.sleep(0.05)
        
        print(f"{Colors.HACKER_GREEN}  ▸ SYSTEM: {Colors.NEON_PINK}GIT AUTO-PUSHER v3.0{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  ▸ STATUS: {Colors.NEON_GREEN}INITIALIZING...{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  ▸ REPOSITORY: {Colors.HACKER_BRIGHT}{self.repo_path}{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  ▸ PRESS {Colors.NEON_RED}CTRL+C{Colors.HACKER_GREEN} TO ABORT{Colors.END}")
        self.animator.color_scan_line()
    
    def _main_loop(self):
        """Main monitoring loop"""
        while self.running:
            self._print_status()
            time.sleep(1)
    
    def _print_status(self):
        """Print status header"""
        print(f"\n{Colors.HACKER_DIM}╔══════════════════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.CYBER_BLUE}║  ██████╗ ██╗████████╗    ██████╗ ██╗   ██╗███████╗██╗  ██╗   ║{Colors.END}")
        print(f"{Colors.NEON_PURPLE}║  ██╔══██╗██║╚══██╔══╝    ██╔══██╗██║   ██║██╔════╝██║  ██║   ║{Colors.END}")
        print(f"{Colors.NEON_BLUE}║  ██████╔╝██║   ██║       ██████╔╝██║   ██║███████╗███████║   ║{Colors.END}")
        print(f"{Colors.NEON_PINK}║  ██╔══██╗██║   ██║       ██╔═══╝ ██║   ██║╚════██║██╔══██║   ║{Colors.END}")
        print(f"{Colors.NEON_ORANGE}║  ██████╔╝██║   ██║       ██║     ╚██████╔╝███████║██║  ██║   ║{Colors.END}")
        print(f"{Colors.NEON_YELLOW}║  ╚═════╝ ╚═╝   ╚═╝       ╚═╝      ╚═════╝ ╚══════╝╚═╝  ╚═╝   ║{Colors.END}")
        print(f"{Colors.HACKER_DIM}╚══════════════════════════════════════════════════════════════════╝{Colors.END}")
        
        runtime = time.time() - self.start_time
        stats = self.git.get_stats()
        
        print(f"{Colors.HACKER_GREEN}  ├─ Repository: {Colors.HACKER_BRIGHT}{self.repo_path}{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  ├─ Interval: {Colors.CYBER_BLUE}{self.config.CHECK_INTERVAL}s{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  ├─ Commits: {Colors.NEON_PINK}{stats['total_commits']}{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  ├─ Files: {Colors.NEON_ORANGE}{stats['total_files_changed']}{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  ├─ Runtime: {Colors.NEON_YELLOW}{time.strftime('%H:%M:%S', time.gmtime(runtime))}{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  └─ Status: {Colors.NEON_GREEN}[ACTIVE]{Colors.END}")
        
        self.animator.color_scan_line()
        
        print(f"\n{Colors.HACKER_DIM}[*] MONITORING: {Colors.HACKER_BRIGHT}{self.repo_path}{Colors.END}")
        print(f"{Colors.NEON_YELLOW}[*] PRESS CTRL+C TO EXIT{Colors.END}")
    
    def _on_file_change(self):
        """Callback when file changes are detected"""
        self.git.process_changes()
    
    def _shutdown(self):
        """Shutdown the service"""
        print(f"\n{Colors.NEON_YELLOW}[!] SHUTDOWN SEQUENCE INITIATED...{Colors.END}")
        self.running = False
        
        if self.watcher:
            self.watcher.stop()
        
        self.animator.matrix_rain(2)
        print(f"{Colors.NEON_GREEN}[✓] SYSTEM TERMINATED GRACEFULLY{Colors.END}")
        
        runtime = time.time() - self.start_time
        stats = self.git.get_stats()
        
        print(f"\n{Colors.HACKER_DIM}╔════════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.NEON_PINK}║  FINAL STATISTICS                                    ║{Colors.END}")
        print(f"{Colors.HACKER_DIM}╚════════════════════════════════════════════════════════╝{Colors.END}")
        print(f"{Colors.HACKER_DIM}  ├─ Total Commits: {Colors.NEON_GREEN}{stats['total_commits']}{Colors.END}")
        print(f"{Colors.HACKER_DIM}  ├─ Files Changed: {Colors.NEON_ORANGE}{stats['total_files_changed']}{Colors.END}")
        print(f"{Colors.HACKER_DIM}  ├─ Runtime: {Colors.NEON_YELLOW}{time.strftime('%H:%M:%S', time.gmtime(runtime))}{Colors.END}")
        print(f"{Colors.HACKER_DIM}  └─ Status: {Colors.NEON_GREEN}COMPLETED{Colors.END}")