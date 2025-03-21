"""
Widget style configurations for the GUI.
"""

from tkinter import ttk
from .theme import ColorScheme

class WidgetStyles:
    """Configure ttk widget styles based on theme colors."""
    
    def __init__(self, style: ttk.Style, colors: ColorScheme):
        self.style = style
        self.colors = colors
        self._configure_styles()
    
    def _configure_styles(self):
        """Configure all widget styles."""
        self._configure_frames()
        self._configure_labels()
        self._configure_buttons()
        self._configure_entry()
        self._configure_checkbutton()
    
    def _configure_frames(self):
        """Configure frame styles."""
        self.style.configure(
            "Main.TFrame",
            background=self.colors.background
        )
        
        self.style.configure(
            "Main.TLabelframe",
            background=self.colors.background,
            foreground=self.colors.foreground
        )
        
    def _configure_labels(self):
        """Configure label styles."""
        self.style.configure(
            "Title.TLabel",
            background=self.colors.background,
            foreground=self.colors.foreground,
            font=("Arial", 10, "bold")
        )
        
        self.style.configure(
            "Status.TLabel",
            background=self.colors.background,
            foreground=self.colors.accent_light,
            font=("Arial", 9)
        )
    
    def _configure_buttons(self):
        """Configure button styles."""
        configure_button_styles(self.style, self.colors)
        
    def _configure_entry(self):
        """Configure entry styles."""
        self.style.configure(
            "TEntry",
            fieldbackground=self.colors.secondary_bg,
            foreground=self.colors.foreground,
            padding=5
        )
    
    def _configure_checkbutton(self):
        """Configure checkbutton styles."""
        self.style.configure(
            "TCheckbutton",
            background=self.colors.background,
            foreground=self.colors.foreground
        )

def configure_button_styles(style: ttk.Style, colors: ColorScheme):
    """Configure button styles with purple theme."""
    
    # Primary button style
    style.configure(
        "Accent.TButton",
        background=colors.accent,
        foreground=colors.foreground,
        font=("Arial", 9, "bold"),
        padding=(15, 8),
        relief="flat",
        borderwidth=0
    )
    
    style.map(
        "Accent.TButton",
        background=[
            ("active", colors.accent_light),
            ("pressed", colors.accent_dark)
        ],
        foreground=[
            ("active", colors.foreground),
            ("pressed", colors.foreground)
        ]
    )
    
    # Regular button style
    style.configure(
        "TButton", 
        background=colors.secondary_bg,
        foreground=colors.foreground,
        font=("Arial", 9),
        padding=(12, 6),
        relief="flat",
        borderwidth=0
    )
    
    style.map(
        "TButton",
        background=[
            ("active", colors.tertiary_bg),
            ("pressed", colors.background)
        ]
    )