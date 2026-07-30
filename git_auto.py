# D:\Sachin Chakrawarti\eth_bot\git_auto.py

import os
import sys
import time
import subprocess
import json
from pathlib import Path
from datetime import datetime
import threading
import queue
import shutil
import random

# Try to import optional dependencies
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️ Watchdog not installed. Install with: pip install watchdog")
    print("⚠️ Using fallback polling method...")

try:
    from plyer import notification
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False
    print("⚠️ Plyer not installed. Install with: pip install plyer")
    print("⚠️ Desktop notifications disabled")

# Hacker-style ANSI color codes
class Colors:
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

class HackerAnimator:
    """Hacker-style animations and effects"""
    
    @staticmethod
    def matrix_rain(lines=3):
        """Create a Matrix-like rain effect"""
        chars = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+-=[]{}|;:,.<>?/~"
        for _ in range(lines):
            line = ''.join(random.choice(chars) for _ in range(random.randint(20, 40)))
            print(f"{Colors.MATRIX}{line}{Colors.END}")
    
    @staticmethod
    def typing_effect(text, delay=0.03):
        """Type text with a hacking effect"""
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()
    
    @staticmethod
    def glitch_text(text, intensity=0.1):
        """Create glitch effect on text"""
        glitched = []
        for char in text:
            if random.random() < intensity:
                glitched.append(random.choice("!@#$%^&*()_+{}|:<>?~"))
            else:
                glitched.append(char)
        return ''.join(glitched)

class GitAutoPusher:
    def __init__(self, repo_path=None, check_interval=5, excluded_dirs=None):
        """
        Initialize Git Auto Pusher - Hacker Edition
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.check_interval = check_interval
        self.excluded_dirs = excluded_dirs or ['.git', '__pycache__', 'node_modules', 'venv', 'env']
        self.file_changes = queue.Queue()
        self.running = False
        self.changed_files = set()
        self.last_commit_time = 0
        self.commit_cooldown = 10
        
        # Progress animation characters - hacker style
        self.spinner_chars = ['◈', '◆', '◇', '●', '○', '■', '□', '▲', '△', '★']
        self.progress_chars = ['▱', '▱', '▰', '▰']
        
        # Stats
        self.total_commits = 0
        self.total_files_changed = 0
        self.hacker = HackerAnimator()
        
        self.setup_repo()
        
    def setup_repo(self):
        """Check if the directory is a git repository - Hacker style"""
        git_dir = self.repo_path / '.git'
        if not git_dir.exists():
            print(f"{Colors.HACKER_DIM}╔══════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.HACKER_BRIGHT}║  [!] WARNING: GIT REPOSITORY NOT FOUND          ║{Colors.END}")
            print(f"{Colors.HACKER_DIM}╚══════════════════════════════════════════════════════╝{Colors.END}")
            print(f"{Colors.HACKER_GREEN}▶ INITIALIZING NEW GIT REPOSITORY...{Colors.END}")
            self.hacker.matrix_rain(2)
            try:
                subprocess.run(['git', 'init'], cwd=self.repo_path, check=True)
                print(f"{Colors.HACKER_BRIGHT}[+] GIT REPOSITORY INITIALIZED SUCCESSFULLY{Colors.END}")
                print(f"{Colors.HACKER_DIM}  └─ Location: {self.repo_path}{Colors.END}")
            except subprocess.CalledProcessError as e:
                print(f"{Colors.RED}[!] INITIALIZATION FAILED: {e}{Colors.END}")
                sys.exit(1)
        else:
            print(f"{Colors.HACKER_DIM}╔══════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.HACKER_BRIGHT}║  [*] GIT REPOSITORY DETECTED                     ║{Colors.END}")
            print(f"{Colors.HACKER_DIM}╚══════════════════════════════════════════════════════╝{Colors.END}")
            print(f"{Colors.HACKER_GREEN}  └─ Repository: {self.repo_path}{Colors.END}")
            self._show_repo_info()
    
    def _show_repo_info(self):
        """Display repository information - Hacker style"""
        try:
            # Get remote info
            remote = subprocess.run(['git', 'remote', '-v'], cwd=self.repo_path, capture_output=True, text=True)
            if remote.stdout:
                remote_url = remote.stdout.split()[1] if remote.stdout else "None"
                print(f"{Colors.HACKER_DIM}  └─ Remote: {Colors.HACKER_GREEN}{remote_url}{Colors.END}")
            
            # Get branch info
            branch = subprocess.run(['git', 'branch', '--show-current'], cwd=self.repo_path, capture_output=True, text=True)
            if branch.stdout:
                print(f"{Colors.HACKER_DIM}  └─ Branch: {Colors.HACKER_GREEN}{branch.stdout.strip()}{Colors.END}")
        except:
            pass

    def get_git_status(self):
        """Get git status and return changed files - Hacker style"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            changed = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        status = line[:2]
                        file_path = line[3:].strip()
                        if not any(excl in file_path for excl in self.excluded_dirs):
                            changed.append({
                                'status': status,
                                'file': file_path,
                                'type': self._get_change_type(status)
                            })
            return changed
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}[!] GIT STATUS ERROR: {e}{Colors.END}")
            return []
    
    def _get_change_type(self, status):
        """Convert git status code to human-readable type - Hacker style"""
        status_map = {
            'M': '[MOD]',
            'A': '[ADD]',
            'D': '[DEL]',
            'R': '[REN]',
            'C': '[COP]',
            'U': '[UPD]',
            '??': '[NEW]',
            '!': '[IGN]'
        }
        return status_map.get(status.strip(), '[CHG]')
    
    def auto_add_and_commit(self, changes):
        """Auto add and commit changes - Hacker style"""
        if not changes:
            return False
        
        # Add all changes
        try:
            subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True)
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}[!] GIT ADD FAILED: {e}{Colors.END}")
            return False
        
        # Generate commit message
        commit_msg = self._generate_commit_message(changes)
        
        # Commit
        try:
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.total_commits += 1
            self.total_files_changed += len(changes)
            self.last_commit_time = time.time()
            
            self._show_commit_success(changes, commit_msg)
            
            self._send_notification(f"✅ Commit successful", 
                                  f"{len(changes)} files changed\n{commit_msg}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in e.stderr:
                print(f"{Colors.YELLOW}[!] NO CHANGES TO COMMIT{Colors.END}")
                return False
            else:
                print(f"{Colors.RED}[!] COMMIT FAILED: {e.stderr}{Colors.END}")
                return False
    
    def _generate_commit_message(self, changes):
        """Generate a meaningful commit message - Hacker style"""
        types = {}
        for change in changes:
            change_type = change['type']
            if change_type not in types:
                types[change_type] = []
            types[change_type].append(change['file'])
        
        parts = []
        for change_type, files in types.items():
            if len(files) == 1:
                parts.append(f"{change_type} {files[0]}")
            else:
                parts.append(f"{change_type} {len(files)} files")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[AUTO] {' | '.join(parts)} [{timestamp}]"
        
        if len(message) > 72:
            message = message[:69] + "..."
        
        return message
    
    def push_changes(self):
        """Push changes to remote repository - Hacker style"""
        try:
            # Check if remote exists
            result = subprocess.run(
                ['git', 'remote'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                print(f"{Colors.YELLOW}[!] NO REMOTE CONFIGURED - SKIPPING PUSH{Colors.END}")
                self._send_notification("⚠️ No remote configured", "Please add a remote repository")
                return False
            
            # Get current branch
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            branch = branch_result.stdout.strip()
            
            if not branch:
                print(f"{Colors.YELLOW}[!] NOT ON A BRANCH - SKIPPING PUSH{Colors.END}")
                return False
            
            # Show push animation
            self._show_push_animation()
            
            # Push to remote
            push_result = subprocess.run(
                ['git', 'push', 'origin', branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if push_result.returncode == 0:
                print(f"\n{Colors.HACKER_BRIGHT}[+] PUSH SUCCESSFUL → {branch}{Colors.END}")
                self._send_notification("✅ Push successful", f"Pushed to {branch}")
                return True
            else:
                print(f"\n{Colors.RED}[!] PUSH FAILED: {push_result.stderr[:100]}{Colors.END}")
                self._send_notification("❌ Push failed", push_result.stderr[:100])
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}[!] PUSH ERROR: {e}{Colors.END}")
            return False
    
    def _show_commit_success(self, changes, commit_msg):
        """Display commit success - Hacker style"""
        print(f"\n{Colors.HACKER_DIM}╔══════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  [✓] COMMIT SUCCESSFUL!                          ║{Colors.END}")
        print(f"{Colors.HACKER_DIM}╚══════════════════════════════════════════════════════╝{Colors.END}")
        
        print(f"{Colors.HACKER_GREEN}  └─ Hash: {Colors.HACKER_DIM}{self._get_commit_hash()}{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  └─ Message: {Colors.HACKER_BRIGHT}{commit_msg}{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  └─ Files: {Colors.HACKER_DIM}{len(changes)} changed{Colors.END}")
        print(f"{Colors.HACKER_DIM}  └─ Details:{Colors.END}")
        
        for change in changes[:5]:
            status_symbol = {
                '[MOD]': '▸',
                '[ADD]': '+',
                '[DEL]': '-',
                '[REN]': '↻',
                '[COP]': '≋',
                '[NEW]': '✦'
            }.get(change['type'], '•')
            
            status_color = {
                '[MOD]': Colors.YELLOW,
                '[ADD]': Colors.HACKER_BRIGHT,
                '[DEL]': Colors.RED,
                '[REN]': Colors.PURPLE,
                '[COP]': Colors.BLUE,
                '[NEW]': Colors.HACKER_GREEN
            }.get(change['type'], Colors.HACKER_DIM)
            
            print(f"    {status_color}{status_symbol} {change['type']} {change['file']}{Colors.END}")
        
        if len(changes) > 5:
            print(f"    {Colors.HACKER_DIM}... and {len(changes) - 5} more files{Colors.END}")
    
    def _get_commit_hash(self):
        """Get the latest commit hash"""
        try:
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  cwd=self.repo_path, capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def _show_push_animation(self):
        """Show a hacking-style push animation"""
        print(f"\n{Colors.HACKER_DIM}╔══════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  [↻] INITIATING PUSH SEQUENCE...                ║{Colors.END}")
        print(f"{Colors.HACKER_DIM}╚══════════════════════════════════════════════════════╝{Colors.END}")
        
        # Matrix rain before push
        self.hacker.matrix_rain(2)
        
        # Progress animation
        for i in range(30):
            progress = (i + 1) / 30
            bar_length = 40
            filled = int(bar_length * progress)
            
            # Hacker-style progress bar
            bar = '█' * filled + '░' * (bar_length - filled)
            spinner = self.spinner_chars[i % len(self.spinner_chars)]
            
            # Random "data" packets for hacker feel
            packets = ['[DATA]', '[SYNC]', '[PUSH]', '[UPLOAD]', '[TRANSFER]']
            packet = random.choice(packets)
            
            print(f'\r  {spinner} {Colors.HACKER_GREEN}[{bar}]{Colors.END} {int(progress * 100)}% {Colors.HACKER_DIM}{packet}{Colors.END}', end='')
            time.sleep(0.03)
        
        print()  # New line after animation
    
    def _send_notification(self, title, message):
        """Send desktop notification"""
        if NOTIFICATION_AVAILABLE:
            try:
                notification.notify(
                    title=f"🖥️ {title}",
                    message=message,
                    app_name="GIT-HACKER",
                    timeout=3
                )
            except Exception as e:
                pass  # Silent fail for notifications
    
    def _print_status_header(self):
        """Print status header - Hacker style (no screen clear)"""
        print(f"\n{Colors.HACKER_DIM}╔══════════════════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  ██████╗ ██╗████████╗    ██████╗ ██╗   ██╗███████╗██╗  ██╗   ║{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  ██╔══██╗██║╚══██╔══╝    ██╔══██╗██║   ██║██╔════╝██║  ██║   ║{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  ██████╔╝██║   ██║       ██████╔╝██║   ██║███████╗███████║   ║{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  ██╔══██╗██║   ██║       ██╔═══╝ ██║   ██║╚════██║██╔══██║   ║{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  ██████╔╝██║   ██║       ██║     ╚██████╔╝███████║██║  ██║   ║{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  ╚═════╝ ╚═╝   ╚═╝       ╚═╝      ╚═════╝ ╚══════╝╚═╝  ╚═╝   ║{Colors.END}")
        print(f"{Colors.HACKER_DIM}╚══════════════════════════════════════════════════════════════════╝{Colors.END}")
        
        print(f"{Colors.HACKER_GREEN}  ├─ Repository: {Colors.HACKER_BRIGHT}{self.repo_path}{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  ├─ Interval: {Colors.HACKER_DIM}{self.check_interval}s{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  ├─ Commits: {Colors.HACKER_BRIGHT}{self.total_commits}{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  ├─ Files: {Colors.HACKER_BRIGHT}{self.total_files_changed}{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  └─ Status: {Colors.HACKER_BRIGHT}[ACTIVE]{Colors.END}")
        print(f"{Colors.HACKER_DIM}─" * 60 + f"{Colors.END}")
    
    def process_changes(self):
        """Process detected file changes - Hacker style"""
        current_time = time.time()
        
        if current_time - self.last_commit_time < self.commit_cooldown:
            return
        
        changes = self.get_git_status()
        
        if changes:
            print(f"\n{Colors.YELLOW}[!] CHANGE DETECTED! {len(changes)} FILE(S) MODIFIED{Colors.END}")
            
            if self.auto_add_and_commit(changes):
                self.push_changes()
            
            self.changed_files.clear()
    
    def run_polling(self):
        """Run using polling method (fallback) - Hacker style"""
        print(f"{Colors.YELLOW}[!] USING POLLING MODE (LESS EFFICIENT){Colors.END}")
        
        while self.running:
            self._print_status_header()
            
            changes = self.get_git_status()
            
            if changes:
                print(f"\n{Colors.YELLOW}[!] DETECTED {len(changes)} FILE CHANGE(S){Colors.END}")
                
                # Show changed files with hacker style
                for change in changes[:10]:
                    status_symbol = {
                        '[MOD]': '▸',
                        '[ADD]': '+',
                        '[DEL]': '-'
                    }.get(change['type'], '•')
                    
                    print(f"  {Colors.HACKER_DIM}{status_symbol} {change['type']} {change['file']}{Colors.END}")
                
                if len(changes) > 10:
                    print(f"  {Colors.HACKER_DIM}... and {len(changes) - 10} more files{Colors.END}")
                
                self.process_changes()
            else:
                print(f"\n{Colors.HACKER_DIM}[*] SYSTEM IDLE - NO CHANGES DETECTED{Colors.END}")
            
            time.sleep(self.check_interval)
    
    def run_watchdog(self):
        """Run using Watchdog for file change detection - Hacker style"""
        if not WATCHDOG_AVAILABLE:
            print(f"{Colors.RED}[!] WATCHDOG NOT AVAILABLE - USING POLLING{Colors.END}")
            self.run_polling()
            return
        
        class FileChangeHandler(FileSystemEventHandler):
            def __init__(self, parent):
                self.parent = parent
                self.last_event_time = 0
                
            def on_modified(self, event):
                self._handle_event(event)
                
            def on_created(self, event):
                self._handle_event(event)
                
            def on_deleted(self, event):
                self._handle_event(event)
                
            def _handle_event(self, event):
                if any(excl in str(event.src_path) for excl in self.parent.excluded_dirs):
                    return
                
                current_time = time.time()
                if current_time - self.last_event_time < 1:
                    return
                self.last_event_time = current_time
                
                self.parent.file_changes.put(event)
                print(f"\n{Colors.YELLOW}[!] FILE MODIFIED: {Path(event.src_path).name}{Colors.END}")
        
        event_handler = FileChangeHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.repo_path), recursive=True)
        observer.start()
        
        print(f"{Colors.HACKER_BRIGHT}[+] WATCHDOG ACTIVE - MONITORING FILE SYSTEM{Colors.END}")
        print(f"{Colors.HACKER_DIM}[*] PRESS CTRL+C TO TERMINATE{Colors.END}")
        
        try:
            while self.running:
                self._print_status_header()
                
                if not self.file_changes.empty():
                    self.process_changes()
                
                print(f"\n{Colors.HACKER_DIM}[*] MONITORING: {self.repo_path}{Colors.END}")
                print(f"{Colors.HACKER_DIM}[*] PRESS CTRL+C TO EXIT{Colors.END}")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            observer.stop()
            print(f"\n{Colors.YELLOW}[!] TERMINATING WATCHDOG...{Colors.END}")
        
        observer.join()
    
    def start(self):
        """Start the auto-push service - Hacker style"""
        self.running = True
        
        # Hacker welcome sequence
        self.hacker.matrix_rain(3)
        print(f"{Colors.HACKER_BRIGHT}╔════════════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  ██████╗ ██╗████████╗    ██████╗ ██╗   ██╗███████╗██╗  ██╗  ║{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  ██╔══██╗██║╚══██╔══╝    ██╔══██╗██║   ██║██╔════╝██║  ██║  ║{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  ██████╔╝██║   ██║       ██████╔╝██║   ██║███████╗███████║  ║{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  ██╔══██╗██║   ██║       ██╔═══╝ ██║   ██║╚════██║██╔══██║  ║{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  ██████╔╝██║   ██║       ██║     ╚██████╔╝███████║██║  ██║  ║{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}║  ╚═════╝ ╚═╝   ╚═╝       ╚═╝      ╚═════╝ ╚══════╝╚═╝  ╚═╝  ║{Colors.END}")
        print(f"{Colors.HACKER_BRIGHT}╚════════════════════════════════════════════════════════════╝{Colors.END}")
        
        print(f"{Colors.HACKER_GREEN}  ▸ SYSTEM: GIT AUTO-PUSHER v3.0{HACKER}{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  ▸ STATUS: {Colors.HACKER_BRIGHT}INITIALIZING...{Colors.END}")
        print(f"{Colors.HACKER_DIM}  ▸ REPOSITORY: {self.repo_path}{Colors.END}")
        print(f"{Colors.HACKER_DIM}  ▸ PRESS CTRL+C TO ABORT{Colors.END}")
        print(f"{Colors.HACKER_DIM}─" * 60 + f"{Colors.END}")
        
        try:
            if WATCHDOG_AVAILABLE:
                self.run_watchdog()
            else:
                self.run_polling()
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}[!] SHUTDOWN SEQUENCE INITIATED...{Colors.END}")
            self.running = False
            
            self.hacker.matrix_rain(2)
            print(f"{Colors.HACKER_BRIGHT}[✓] SYSTEM TERMINATED GRACEFULLY{Colors.END}")
            
            print(f"\n{Colors.HACKER_GREEN}╔════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.HACKER_GREEN}║  FINAL STATISTICS                                    ║{Colors.END}")
            print(f"{Colors.HACKER_GREEN}╚════════════════════════════════════════════════════════╝{Colors.END}")
            print(f"{Colors.HACKER_DIM}  ├─ Total Commits: {Colors.HACKER_BRIGHT}{self.total_commits}{Colors.END}")
            print(f"{Colors.HACKER_DIM}  ├─ Files Changed: {Colors.HACKER_BRIGHT}{self.total_files_changed}{Colors.END}")
            print(f"{Colors.HACKER_DIM}  └─ Runtime: {Colors.HACKER_BRIGHT}{time.strftime('%H:%M:%S', time.gmtime(time.time() - self.last_commit_time if self.last_commit_time else 0))}{Colors.END}")

def main():
    """Main entry point - Hacker style"""
    # Configuration
    repo_path = Path(__file__).parent
    check_interval = 3
    excluded_dirs = ['.git', '__pycache__', 'node_modules', 'venv', 'env', '.idea', '.vscode']
    
    # Hacker intro
    print(f"{Colors.HACKER_DIM}LOADING SYSTEM...{Colors.END}")
    time.sleep(0.5)
    
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