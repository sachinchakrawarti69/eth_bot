"""
Notifier module - Desktop notifications
"""
try:
    from plyer import notification
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False

class Notifier:
    """Handle desktop notifications"""
    
    def __init__(self, enabled=True):
        self.enabled = enabled and NOTIFICATION_AVAILABLE
        self.app_name = "GIT-HACKER"
    
    def send(self, title, message, timeout=5):
        """Send a desktop notification"""
        if self.enabled:
            try:
                notification.notify(
                    title=f"🖥️ {title}",
                    message=message,
                    app_name=self.app_name,
                    timeout=timeout
                )
            except Exception as e:
                pass  # Silent fail for notifications
        else:
            # Fallback to console notification
            print(f"\n{Colors.NEON_YELLOW}[NOTIFICATION] {title}: {message}{Colors.END}")