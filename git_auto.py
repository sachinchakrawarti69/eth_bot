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

# ANSI color codes for terminal
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

class GitAutoPusher:
    def __init__(self, repo_path=None, check_interval=5, excluded_dirs=None):
        """
        Initialize Git Auto Pusher
        
        Args:
            repo_path: Path to git repository (default: current directory)
            check_interval: Interval in seconds to check for changes
            excluded_dirs: List of directory names to exclude from monitoring
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.check_interval = check_interval
        self.excluded_dirs = excluded_dirs or ['.git', '__pycache__', 'node_modules', 'venv', 'env']
        self.file_changes = queue.Queue()
        self.running = False
        self.changed_files = set()
        self.last_commit_time = 0
        self.commit_cooldown = 10  # Seconds to wait before committing again
        
        # Progress animation characters
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.progress_chars = ['░', '▒', '▓', '█']
        
        # Stats
        self.total_commits = 0
        self.total_files_changed = 0
        
        self.setup_repo()
        
    def setup_repo(self):
        """Check if the directory is a git repository"""
        git_dir = self.repo_path / '.git'
        if not git_dir.exists():
            print(f"{Colors.WARNING}⚠️ Not a git repository: {self.repo_path}{Colors.END}")
            print(f"{Colors.BLUE}Initializing git repository...{Colors.END}")
            try:
                subprocess.run(['git', 'init'], cwd=self.repo_path, check=True)
                print(f"{Colors.GREEN}✅ Git repository initialized{Colors.END}")
            except subprocess.CalledProcessError as e:
                print(f"{Colors.FAIL}❌ Failed to initialize git: {e}{Colors.END}")
                sys.exit(1)
        else:
            print(f"{Colors.GREEN}✅ Git repository found at: {self.repo_path}{Colors.END}")
    
    def get_git_status(self):
        """Get git status and return changed files"""
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
                        # Parse git status format
                        status = line[:2]
                        file_path = line[3:].strip()
                        # Filter excluded directories
                        if not any(excl in file_path for excl in self.excluded_dirs):
                            changed.append({
                                'status': status,
                                'file': file_path,
                                'type': self._get_change_type(status)
                            })
            return changed
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}❌ Git status error: {e}{Colors.END}")
            return []
    
    def _get_change_type(self, status):
        """Convert git status code to human-readable type"""
        status_map = {
            'M': 'Modified',
            'A': 'Added',
            'D': 'Deleted',
            'R': 'Renamed',
            'C': 'Copied',
            'U': 'Updated but unmerged',
            '??': 'Untracked',
            '!': 'Ignored'
        }
        return status_map.get(status.strip(), 'Changed')
    
    def auto_add_and_commit(self, changes):
        """Auto add and commit changes with a meaningful message"""
        if not changes:
            return False
        
        # Add all changes
        try:
            subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True)
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}❌ Git add failed: {e}{Colors.END}")
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
            
            # Update stats
            self.total_commits += 1
            self.total_files_changed += len(changes)
            self.last_commit_time = time.time()
            
            # Show commit success with animation
            self._show_commit_success(changes, commit_msg)
            
            # Send desktop notification
            self._send_notification(f"✅ Commit successful", 
                                  f"{len(changes)} files changed\n{commit_msg}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in e.stderr:
                print(f"{Colors.WARNING}⚠️ No changes to commit{Colors.END}")
                return False
            else:
                print(f"{Colors.FAIL}❌ Commit failed: {e.stderr}{Colors.END}")
                return False
    
    def _generate_commit_message(self, changes):
        """Generate a meaningful commit message based on changes"""
        # Group changes by type
        types = {}
        for change in changes:
            change_type = change['type']
            if change_type not in types:
                types[change_type] = []
            types[change_type].append(change['file'])
        
        # Generate message
        parts = []
        for change_type, files in types.items():
            if len(files) == 1:
                parts.append(f"{change_type}: {files[0]}")
            else:
                parts.append(f"{change_type}: {len(files)} files")
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Auto-commit: {', '.join(parts)} [{timestamp}]"
        
        # Truncate if too long (max 72 chars for subject line)
        if len(message) > 72:
            message = message[:69] + "..."
        
        return message
    
    def push_changes(self):
        """Push changes to remote repository"""
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
                print(f"{Colors.WARNING}⚠️ No remote configured. Skipping push.{Colors.END}")
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
                print(f"{Colors.WARNING}⚠️ Not on a branch. Skipping push.{Colors.END}")
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
                print(f"\n{Colors.GREEN}✅ Push successful to {branch}{Colors.END}")
                self._send_notification("✅ Push successful", f"Pushed to {branch}")
                return True
            else:
                print(f"\n{Colors.FAIL}❌ Push failed: {push_result.stderr}{Colors.END}")
                self._send_notification("❌ Push failed", push_result.stderr[:100])
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}❌ Push error: {e}{Colors.END}")
            return False
    
    def _show_commit_success(self, changes, commit_msg):
        """Display commit success with nice formatting"""
        print(f"\n{Colors.GREEN}✅ Commit successful!{Colors.END}")
        print(f"{Colors.BLUE}📝 Message: {commit_msg}{Colors.END}")
        print(f"{Colors.CYAN}📁 Changed files:{Colors.END}")
        
        for change in changes[:5]:  # Show first 5 files
            status_symbol = {
                'Modified': '📝',
                'Added': '➕',
                'Deleted': '➖',
                'Renamed': '🔄',
                'Copied': '📋'
            }.get(change['type'], '📄')
            
            print(f"  {status_symbol} {change['type']}: {change['file']}")
        
        if len(changes) > 5:
            print(f"  {Colors.WARNING}... and {len(changes) - 5} more files{Colors.END}")
    
    def _show_push_animation(self):
        """Show a fancy animation while pushing"""
        print(f"\n{Colors.CYAN}🚀 Pushing changes to remote...{Colors.END}")
        
        # Simple progress animation
        for i in range(20):
            progress = (i + 1) / 20
            bar_length = 30
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            # Spinner
            spinner = self.spinner_chars[i % len(self.spinner_chars)]
            
            print(f'\r{spinner} {Colors.BLUE}[{bar}]{Colors.END} {int(progress * 100)}%', end='')
            time.sleep(0.05)  # Fast animation
        
        print()  # New line after animation
    
    def _send_notification(self, title, message):
        """Send desktop notification"""
        if NOTIFICATION_AVAILABLE:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name="Git Auto Pusher",
                    timeout=5
                )
            except Exception as e:
                print(f"{Colors.WARNING}⚠️ Notification failed: {e}{Colors.END}")
    
    def _print_status_header(self):
        """Print status header with stats"""
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
        print(f"{Colors.HEADER}{Colors.BOLD}╔══════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}║         🔄 GIT AUTO PUSHER - MONITORING ACTIVE      ║{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}╚══════════════════════════════════════════════════════╝{Colors.END}")
        print(f"{Colors.CYAN}📂 Repository: {self.repo_path}{Colors.END}")
        print(f"{Colors.BLUE}⏱️  Check interval: {self.check_interval}s{Colors.END}")
        print(f"{Colors.GREEN}📊 Total commits: {self.total_commits}{Colors.END}")
        print(f"{Colors.GREEN}📁 Total files changed: {self.total_files_changed}{Colors.END}")
        print(f"{Colors.WARNING}⏸️  Press Ctrl+C to stop{Colors.END}")
        print("─" * 50)
    
    def process_changes(self):
        """Process detected file changes"""
        current_time = time.time()
        
        # Check if enough time has passed since last commit
        if current_time - self.last_commit_time < self.commit_cooldown:
            return
        
        changes = self.get_git_status()
        
        if changes:
            # Show changes with animation
            print(f"\n{Colors.WARNING}🔄 Changes detected!{Colors.END}")
            
            # Auto add and commit
            if self.auto_add_and_commit(changes):
                # Push changes
                self.push_changes()
            
            # Clear changed files list
            self.changed_files.clear()
    
    def run_polling(self):
        """Run using polling method (fallback)"""
        print(f"{Colors.WARNING}⚠️ Using polling method (less efficient){Colors.END}")
        
        while self.running:
            self._print_status_header()
            
            # Check for changes
            changes = self.get_git_status()
            
            if changes:
                print(f"\n{Colors.WARNING}🔄 Changes detected: {len(changes)} files{Colors.END}")
                
                # Show changed files
                for change in changes[:10]:
                    status_symbol = {
                        'Modified': '📝',
                        'Added': '➕',
                        'Deleted': '➖'
                    }.get(change['type'], '📄')
                    print(f"  {status_symbol} {change['file']}")
                
                if len(changes) > 10:
                    print(f"  {Colors.WARNING}... and {len(changes) - 10} more files{Colors.END}")
                
                # Process changes
                self.process_changes()
            else:
                print(f"\n{Colors.GREEN}✅ No changes detected{Colors.END}")
            
            # Wait for next check
            time.sleep(self.check_interval)
    
    def run_watchdog(self):
        """Run using Watchdog for file change detection"""
        if not WATCHDOG_AVAILABLE:
            print(f"{Colors.FAIL}❌ Watchdog not available. Using polling method.{Colors.END}")
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
                # Ignore events in excluded directories
                if any(excl in str(event.src_path) for excl in self.parent.excluded_dirs):
                    return
                
                # Debounce events (avoid duplicate notifications)
                current_time = time.time()
                if current_time - self.last_event_time < 1:
                    return
                self.last_event_time = current_time
                
                # Queue the event for processing
                self.parent.file_changes.put(event)
                print(f"\n{Colors.WARNING}🔄 File changed: {Path(event.src_path).name}{Colors.END}")
        
        # Set up observer
        event_handler = FileChangeHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.repo_path), recursive=True)
        observer.start()
        
        print(f"{Colors.GREEN}✅ Watchdog monitoring started{Colors.END}")
        
        try:
            while self.running:
                self._print_status_header()
                
                # Process any queued changes
                if not self.file_changes.empty():
                    # Process changes
                    self.process_changes()
                
                # Show status
                print(f"\n{Colors.CYAN}👀 Watching for file changes...{Colors.END}")
                print(f"{Colors.BLUE}⏱️  Press Ctrl+C to stop{Colors.END}")
                
                time.sleep(1)  # Short sleep to reduce CPU usage
                
        except KeyboardInterrupt:
            observer.stop()
            print(f"\n{Colors.WARNING}⏹️ Stopping watcher...{Colors.END}")
        
        observer.join()
    
    def start(self):
        """Start the auto-push service"""
        self.running = True
        print(f"{Colors.HEADER}{Colors.BOLD}🚀 Starting Git Auto Pusher...{Colors.END}")
        print(f"{Colors.BLUE}📂 Monitoring: {self.repo_path}{Colors.END}")
        print(f"{Colors.WARNING}⏸️  Press Ctrl+C to stop{Colors.END}")
        print("─" * 50)
        
        try:
            if WATCHDOG_AVAILABLE:
                self.run_watchdog()
            else:
                self.run_polling()
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}⏹️ Stopping Git Auto Pusher...{Colors.END}")
            self.running = False
            print(f"{Colors.GREEN}✅ Stopped gracefully{Colors.END}")
            
            # Show final stats
            print(f"\n{Colors.BOLD}📊 Final Statistics:{Colors.END}")
            print(f"  Total commits: {self.total_commits}")
            print(f"  Total files changed: {self.total_files_changed}")

def main():
    """Main entry point"""
    # Configuration
    repo_path = Path(__file__).parent  # Use script's directory as repo
    check_interval = 3  # Check every 3 seconds
    excluded_dirs = ['.git', '__pycache__', 'node_modules', 'venv', 'env', '.idea', '.vscode']
    
    # Create and start auto pusher
    pusher = GitAutoPusher(
        repo_path=repo_path,
        check_interval=check_interval,
        excluded_dirs=excluded_dirs
    )
    
    try:
        pusher.start()
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}👋 Goodbye!{Colors.END}")

if __name__ == "__main__":
    main()