"""
Git Handler module - Git operations
"""
import subprocess
import time
from datetime import datetime
from pathlib import Path
from .colors import Colors
from .animator import HackerAnimator
from .notifier import Notifier

class GitHandler:
    """Handle all Git operations"""
    
    def __init__(self, repo_path, excluded_dirs=None, notifier=None):
        self.repo_path = Path(repo_path)
        self.excluded_dirs = excluded_dirs or ['.git', '__pycache__', 'node_modules']
        self.animator = HackerAnimator()
        self.notifier = notifier or Notifier()
        self.total_commits = 0
        self.total_files_changed = 0
        self.last_commit_time = 0
        self.commit_cooldown = 10
        
        self._setup_repo()
    
    def _setup_repo(self):
        """Initialize git repository if needed"""
        git_dir = self.repo_path / '.git'
        if not git_dir.exists():
            print(f"{Colors.HACKER_DIM}╔══════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.NEON_RED}║  [!] WARNING: GIT REPOSITORY NOT FOUND          ║{Colors.END}")
            print(f"{Colors.HACKER_DIM}╚══════════════════════════════════════════════════════╝{Colors.END}")
            print(f"{Colors.HACKER_GREEN}▶ INITIALIZING NEW GIT REPOSITORY...{Colors.END}")
            self.animator.matrix_rain(2)
            try:
                subprocess.run(['git', 'init'], cwd=self.repo_path, check=True)
                print(f"{Colors.NEON_GREEN}[+] GIT REPOSITORY INITIALIZED SUCCESSFULLY{Colors.END}")
                print(f"{Colors.HACKER_DIM}  └─ Location: {self.repo_path}{Colors.END}")
            except subprocess.CalledProcessError as e:
                print(f"{Colors.NEON_RED}[!] INITIALIZATION FAILED: {e}{Colors.END}")
                sys.exit(1)
        else:
            print(f"{Colors.HACKER_DIM}╔══════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.CYBER_BLUE}║  [*] GIT REPOSITORY DETECTED                     ║{Colors.END}")
            print(f"{Colors.HACKER_DIM}╚══════════════════════════════════════════════════════╝{Colors.END}")
            print(f"{Colors.HACKER_GREEN}  └─ Repository: {Colors.HACKER_BRIGHT}{self.repo_path}{Colors.END}")
            self._show_repo_info()
    
    def _show_repo_info(self):
        """Display repository information"""
        try:
            remote = subprocess.run(['git', 'remote', '-v'], cwd=self.repo_path, capture_output=True, text=True)
            if remote.stdout:
                remote_url = remote.stdout.split()[1] if remote.stdout else "None"
                print(f"{Colors.HACKER_DIM}  └─ Remote: {Colors.CYBER_BLUE}{remote_url}{Colors.END}")
            
            branch = subprocess.run(['git', 'branch', '--show-current'], cwd=self.repo_path, capture_output=True, text=True)
            if branch.stdout:
                print(f"{Colors.HACKER_DIM}  └─ Branch: {Colors.NEON_PINK}{branch.stdout.strip()}{Colors.END}")
            
            commit_count = subprocess.run(['git', 'rev-list', '--count', 'HEAD'], 
                                        cwd=self.repo_path, capture_output=True, text=True)
            if commit_count.stdout:
                print(f"{Colors.HACKER_DIM}  └─ Commits: {Colors.NEON_YELLOW}{commit_count.stdout.strip()}{Colors.END}")
        except:
            pass
    
    def get_status(self):
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
            print(f"{Colors.NEON_RED}[!] GIT STATUS ERROR: {e}{Colors.END}")
            return []
    
    def _get_change_type(self, status):
        """Convert git status code to human-readable type"""
        status_map = {
            'M': 'MOD',
            'A': 'ADD',
            'D': 'DEL',
            'R': 'REN',
            'C': 'COP',
            'U': 'UPD',
            '??': 'NEW',
            '!': 'IGN'
        }
        return status_map.get(status.strip(), 'CHG')
    
    def add_and_commit(self, changes):
        """Add and commit changes"""
        if not changes:
            return False
        
        try:
            subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True)
        except subprocess.CalledProcessError as e:
            print(f"{Colors.NEON_RED}[!] GIT ADD FAILED: {e}{Colors.END}")
            return False
        
        commit_msg = self._generate_commit_message(changes)
        
        try:
            subprocess.run(['git', 'commit', '-m', commit_msg], cwd=self.repo_path, check=True)
            
            self.total_commits += 1
            self.total_files_changed += len(changes)
            self.last_commit_time = time.time()
            
            self._show_commit_success(changes, commit_msg)
            
            self.notifier.send("✅ Commit successful", f"{len(changes)} files changed")
            
            return True
            
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in e.stderr:
                print(f"{Colors.NEON_YELLOW}[!] NO CHANGES TO COMMIT{Colors.END}")
                return False
            else:
                print(f"{Colors.NEON_RED}[!] COMMIT FAILED: {e.stderr}{Colors.END}")
                return False
    
    def _generate_commit_message(self, changes):
        """Generate commit message"""
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
    
    def _show_commit_success(self, changes, commit_msg):
        """Display commit success"""
        print(f"\n{Colors.HACKER_DIM}╔══════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.NEON_GREEN}║  [✓] COMMIT SUCCESSFUL!                          ║{Colors.END}")
        print(f"{Colors.HACKER_DIM}╚══════════════════════════════════════════════════════╝{Colors.END}")
        
        hash_val = self._get_commit_hash()
        print(f"{Colors.HACKER_GREEN}  └─ Hash: {Colors.CYBER_BLUE}{hash_val}{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  └─ Message: {Colors.NEON_PINK}{commit_msg}{Colors.END}")
        print(f"{Colors.HACKER_GREEN}  └─ Files: {Colors.NEON_YELLOW}{len(changes)} changed{Colors.END}")
        print(f"{Colors.HACKER_DIM}  └─ Details:{Colors.END}")
        
        for change in changes[:5]:
            status_color = Colors.get_status_color(change['type'])
            status_symbol = Colors.get_status_symbol(change['type'])
            print(f"    {status_color}{status_symbol} {change['type']} {change['file']}{Colors.END}")
        
        if len(changes) > 5:
            print(f"    {Colors.HACKER_DIM}... and {len(changes) - 5} more files{Colors.END}")
        
        self.animator.color_scan_line()
    
    def _get_commit_hash(self):
        """Get the latest commit hash"""
        try:
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  cwd=self.repo_path, capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def push(self):
        """Push changes to remote"""
        try:
            result = subprocess.run(['git', 'remote'], cwd=self.repo_path, capture_output=True, text=True)
            
            if not result.stdout.strip():
                print(f"{Colors.NEON_YELLOW}[!] NO REMOTE CONFIGURED - SKIPPING PUSH{Colors.END}")
                self.notifier.send("⚠️ No remote configured", "Please add a remote repository")
                return False
            
            branch_result = subprocess.run(['git', 'branch', '--show-current'], cwd=self.repo_path, capture_output=True, text=True)
            branch = branch_result.stdout.strip()
            
            if not branch:
                print(f"{Colors.NEON_YELLOW}[!] NOT ON A BRANCH - SKIPPING PUSH{Colors.END}")
                return False
            
            self._show_push_animation()
            
            push_result = subprocess.run(['git', 'push', 'origin', branch], cwd=self.repo_path, capture_output=True, text=True)
            
            if push_result.returncode == 0:
                print(f"\n{Colors.NEON_GREEN}[+] PUSH SUCCESSFUL → {Colors.CYBER_PINK}{branch}{Colors.END}")
                self.notifier.send("✅ Push successful", f"Pushed to {branch}")
                return True
            else:
                print(f"\n{Colors.NEON_RED}[!] PUSH FAILED: {push_result.stderr[:100]}{Colors.END}")
                self.notifier.send("❌ Push failed", push_result.stderr[:100])
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"{Colors.NEON_RED}[!] PUSH ERROR: {e}{Colors.END}")
            return False
    
    def _show_push_animation(self):
        """Show push animation"""
        print(f"\n{Colors.HACKER_DIM}╔══════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.CYBER_BLUE}║  [↻] INITIATING PUSH SEQUENCE...                ║{Colors.END}")
        print(f"{Colors.HACKER_DIM}╚══════════════════════════════════════════════════════╝{Colors.END}")
        
        self.animator.matrix_rain(2)
        
        for i in range(30):
            packets = ['[DATA]', '[SYNC]', '[PUSH]', '[UPLOAD]', '[TRANSFER]', '[STREAM]']
            self.animator.progress_bar(i, 30, prefix=random.choice(packets))
            time.sleep(0.03)
        
        print()
        self.animator.color_scan_line()
    
    def process_changes(self):
        """Process detected changes"""
        current_time = time.time()
        
        if current_time - self.last_commit_time < self.commit_cooldown:
            return
        
        changes = self.get_status()
        
        if changes:
            print(f"\n{Colors.NEON_YELLOW}[!] CHANGE DETECTED! {Colors.NEON_RED}{len(changes)}{Colors.NEON_YELLOW} FILE(S) MODIFIED{Colors.END}")
            
            if self.add_and_commit(changes):
                self.push()
    
    def get_stats(self):
        """Get statistics"""
        return {
            'total_commits': self.total_commits,
            'total_files_changed': self.total_files_changed
        }