"""Theme management for the application."""

class ThemeManager:
    """Manages application theme (dark/light mode)."""
    
    def __init__(self, default_theme='light'):
        self.current_theme = default_theme
        self.themes = {
            'light': {'bg': '#ffffff', 'text': '#000000'},
            'dark': {'bg': '#1e1e1e', 'text': '#ffffff'}
        }
    
    def toggle_theme(self):
        """Toggle between light and dark mode."""
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        return self.get_current_theme()
    
    def get_current_theme(self):
        """Get current theme config."""
        return self.themes.get(self.current_theme, {})
