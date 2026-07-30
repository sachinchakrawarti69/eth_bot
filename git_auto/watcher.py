"""
File Watcher module - Monitor file system changes
"""
import time
from pathlib import Path
from .colors import Colors
from .animator import HackerAnimator

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

class FileWatcher:
    """Watch for file system changes"""
    
    def __init__(self, repo_path, excluded_dirs=None, callback=None):
        self.repo_path = Path(repo_path)
        self.excluded_dirs = excluded_dirs or []
        self.callback = callback
        self.animator = HackerAnimator()
        self.running = False
        self.observer = None
        
    def start(self):
        """Start watching for file changes"""
        if not WATCHDOG_AVAILABLE:
            print(f"{Colors.NEON_YELLOW}[!] WATCHDOG NOT AVAILABLE - USING POLLING{Colors.END}")
            return self._polling_watch()
        
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
                
                file_name = Path(event.src_path).name
                color = Colors.random_color()
                print(f"\n{color}[!] FILE MODIFIED: {file_name}{Colors.END}")
                
                if self.parent.callback:
                    self.parent.callback()
        
        event_handler = FileChangeHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.repo_path), recursive=True)
        self.observer.start()
        self.running = True
        
        print(f"{Colors.NEON_GREEN}[+] WATCHDOG ACTIVE - MONITORING FILE SYSTEM{Colors.END}")
        print(f"{Colors.HACKER_DIM}[*] PRESS CTRL+C TO TERMINATE{Colors.END}")
        
        return self.observer
    
    def _polling_watch(self):
        """Fallback polling method"""
        print(f"{Colors.NEON_YELLOW}[!] USING POLLING MODE (LESS EFFICIENT){Colors.END}")
        self.running = True
        
        while self.running:
            if self.callback:
                self.callback()
            time.sleep(3)
    
    def stop(self):
        """Stop watching"""
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print(f"\n{Colors.NEON_YELLOW}[!] TERMINATING WATCHDOG...{Colors.END}")