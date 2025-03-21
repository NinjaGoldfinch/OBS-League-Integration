"""Button style configurations."""

from tkinter import ttk
from .theme import ColorScheme

def configure_button_styles(style: ttk.Style, colors: ColorScheme):
    """Configure button styles."""
    
    # Accent button style
    style.configure(
        "Accent.TButton",
        background=colors.accent,
        foreground=colors.foreground,
        padding=(10, 5),
        relief="flat"
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
        padding=(10, 5),
        relief="flat"
    )
    
    style.map(
        "TButton",
        background=[
            ("active", colors.tertiary_bg),
            ("pressed", colors.background)
        ]
    )